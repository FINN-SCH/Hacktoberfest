import os
import io
import re
import sys
import glob
import ctypes
import asyncio
import json
import uuid
import time
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, StreamingResponse, Response, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import edge_tts

import database
from topics import TOPICS, get_topic_label

# Pre-load CUDA libraries for faster-whisper if present
try:
    site_packages = next(p for p in sys.path if "site-packages" in p)
    for lib_dir in glob.glob(f"{site_packages}/nvidia/*/lib"):
        for so in glob.glob(f"{lib_dir}/*.so*"):
            try:
                ctypes.CDLL(so)
            except Exception:
                pass
except Exception:
    pass

app = FastAPI(title="Voice Language Tutor & Coach", version="2.5.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

LITELLM_URL = os.getenv("LITELLM_URL", "http://localhost:4000/v1")
MODEL_NAME = os.getenv("COACH_MODEL", "qwen3.8-fast")
DEFAULT_VOICE = os.getenv("COACH_VOICE", "en-US-AndrewNeural")

SUPPORTED_LANGUAGES = {
    "en": {"name": "English", "native_name": "English", "flag": "🇬🇧", "default_voice": "en-US-AndrewNeural"},
    "de": {"name": "German", "native_name": "Deutsch", "flag": "🇩🇪", "default_voice": "de-DE-ConradNeural"},
    "es": {"name": "Spanish", "native_name": "Español", "flag": "🇪🇸", "default_voice": "es-ES-AlvaroNeural"},
    "fr": {"name": "French", "native_name": "Français", "flag": "🇫🇷", "default_voice": "fr-FR-HenriNeural"},
    "it": {"name": "Italian", "native_name": "Italiano", "flag": "🇮🇹", "default_voice": "it-IT-DiegoNeural"}
}

VOICES_BY_LANG = {
    "en": [
        {"id": "en-US-AndrewNeural", "name": "Andrew (US · Natural & Warm)", "gender": "male", "locale": "en-US"},
        {"id": "en-US-AvaNeural", "name": "Ava (US · Clear & Expressive)", "gender": "female", "locale": "en-US"},
        {"id": "en-US-BrianNeural", "name": "Brian (US · Deep & Calm)", "gender": "male", "locale": "en-US"},
        {"id": "en-US-EmmaNeural", "name": "Emma (US · Cheerful)", "gender": "female", "locale": "en-US"},
        {"id": "en-GB-RyanNeural", "name": "Ryan (UK · Articulate)", "gender": "male", "locale": "en-GB"},
        {"id": "en-GB-SoniaNeural", "name": "Sonia (UK · Bright)", "gender": "female", "locale": "en-GB"}
    ],
    "de": [
        {"id": "de-DE-ConradNeural", "name": "Conrad (DE · Warm & Klar)", "gender": "male", "locale": "de-DE"},
        {"id": "de-DE-KatjaNeural", "name": "Katja (DE · Natürlich & Freundlich)", "gender": "female", "locale": "de-DE"},
        {"id": "de-DE-KillianNeural", "name": "Killian (DE · Dynamisch)", "gender": "male", "locale": "de-DE"},
        {"id": "de-DE-FlorianMultilingualNeural", "name": "Florian (DE · Vielseitig)", "gender": "male", "locale": "de-DE"},
        {"id": "de-DE-SeraphinaMultilingualNeural", "name": "Seraphina (DE · Sanft)", "gender": "female", "locale": "de-DE"},
        {"id": "de-DE-AmalaNeural", "name": "Amala (DE · Ausdrucksstark)", "gender": "female", "locale": "de-DE"}
    ],
    "es": [
        {"id": "es-ES-AlvaroNeural", "name": "Álvaro (ES · Natural)", "gender": "male", "locale": "es-ES"},
        {"id": "es-ES-ElviraNeural", "name": "Elvira (ES · Clara y Expresiva)", "gender": "female", "locale": "es-ES"},
        {"id": "es-ES-XimenaNeural", "name": "Ximena (ES · Amable)", "gender": "female", "locale": "es-ES"}
    ],
    "fr": [
        {"id": "fr-FR-HenriNeural", "name": "Henri (FR · Chaleureux)", "gender": "male", "locale": "fr-FR"},
        {"id": "fr-FR-DeniseNeural", "name": "Denise (FR · Articulée)", "gender": "female", "locale": "fr-FR"},
        {"id": "fr-FR-EloiseNeural", "name": "Eloise (FR · Naturelle)", "gender": "female", "locale": "fr-FR"},
        {"id": "fr-FR-RemyMultilingualNeural", "name": "Remy (FR · Polyvalent)", "gender": "male", "locale": "fr-FR"},
        {"id": "fr-FR-VivienneMultilingualNeural", "name": "Vivienne (FR · Douce)", "gender": "female", "locale": "fr-FR"}
    ],
    "it": [
        {"id": "it-IT-DiegoNeural", "name": "Diego (IT · Naturale)", "gender": "male", "locale": "it-IT"},
        {"id": "it-IT-ElsaNeural", "name": "Elsa (IT · Espressiva)", "gender": "female", "locale": "it-IT"},
        {"id": "it-IT-IsabellaNeural", "name": "Isabella (IT · Vivace)", "gender": "female", "locale": "it-IT"},
        {"id": "it-IT-GiuseppeMultilingualNeural", "name": "Giuseppe (IT · Caldo)", "gender": "male", "locale": "it-IT"}
    ]
}

SCENARIOS_BY_LANG = {
    "en": {
        "casual": "Hello Jonathan! Great to talk with you today. What's on your mind or how has your week been?",
        "interview": "Good morning Jonathan, welcome to your practice interview! To get us started, could you briefly introduce yourself and your background?",
        "tech": "Hey Jonathan! Ready for some tech discussion. What interesting software, framework, or coding project have you been working on recently?",
        "travel": "Hello Jonathan! Let's talk about travel. If you could fly anywhere in the world tomorrow, where would you go and why?",
        "grammar": "Welcome to your grammar drill Jonathan! Let's speak in full sentences. Can you tell me what you did yesterday from morning to evening?"
    },
    "de": {
        "casual": "Hallo Jonathan! Schön, heute mit dir zu sprechen. Woran denkst du gerade oder wie war deine Woche bisher?",
        "interview": "Guten Morgen Jonathan, willkommen zu deinem Vorstellungsgespräch! Könntest du dich zu Beginn kurz vorstellen und von deinem Werdegang erzählen?",
        "tech": "Hallo Jonathan! Bereit für etwas Tech-Talk. An welchem spannenden Projekt, Framework oder Code hast du in letzter Zeit gearbeitet?",
        "travel": "Hallo Jonathan! Lass uns über das Reisen sprechen. Wenn du morgen überallhin fliegen könntest, wohin würdest du reisen und warum?",
        "grammar": "Willkommen zum Grammatik-Training, Jonathan! Lass uns in vollständigen Sätzen sprechen. Was hast du gestern von morgens bis abends gemacht?"
    },
    "es": {
        "casual": "¡Hola Jonathan! Qué alegría hablar contigo hoy. ¿De qué te gustaría hablar o cómo ha ido tu semana?",
        "interview": "¡Buenos días, Jonathan! Bienvenido a tu simulación de entrevista. Para comenzar, ¿podrías presentarte brevemente?",
        "tech": "¡Hola Jonathan! Listos para hablar de tecnología. ¿En qué proyecto o código interesante has estado trabajando?",
        "travel": "¡Hola Jonathan! Hablemos de viajes. Si pudieras viajar a cualquier lugar del mundo mañana, ¿a dónde irías?",
        "grammar": "¡Bienvenido a tu práctica de gramática, Jonathan! Hablemos con frases completas. ¿Qué hiciste ayer a lo largo del día?"
    },
    "fr": {
        "casual": "Bonjour Jonathan ! Ravi de discuter avec toi aujourd'hui. De quoi aimerais-tu parler ou comment s'est passée ta semaine ?",
        "interview": "Bonjour Jonathan, bienvenue à ta simulation d'entretien ! Pour commencer, pourrais-tu te présenter brièvement ?",
        "tech": "Salut Jonathan ! Prêt pour une discussion technique. Sur quel projet ou framework intéressant as-tu travaillé récemment ?",
        "travel": "Bonjour Jonathan ! Parlons de voyages. Si tu pouvais partir n'importe où dans le monde demain, où irais-tu et pourquoi ?",
        "grammar": "Bienvenue pour cette session de grammaire, Jonathan ! Faisons des phrases complètes. Raconte-moi ce que tu as fait hier ?"
    },
    "it": {
        "casual": "Ciao Jonathan! Che bello parlare con te oggi. A cosa stai pensando o come è andata la tua settimana?",
        "interview": "Buongiorno Jonathan, benvenuto al colloquio di prova! Per iniziare, potresti presentarti brevemente?",
        "tech": "Ciao Jonathan! Pronto per parlare di tecnologia. A quale progetto, framework o codice interessante hai lavorato di recente?",
        "travel": "Ciao Jonathan! Parliamo di viaggi. Se potessi volare ovunque nel mondo domani, dove andresti e perché?",
        "grammar": "Benvenuto alla sessione di grammatica, Jonathan! Parliamo con frasi complete. Cosa hai fatto ieri dalla mattina alla sera?"
    }
}

def get_system_prompt(target_lang: str = "en", native_lang: str = "de") -> str:
    lang_info = SUPPORTED_LANGUAGES.get(target_lang, SUPPORTED_LANGUAGES["en"])
    lang_name = lang_info["name"]
    
    # Get grammar taxonomy for this language
    taxonomy_dict = TOPICS.get(target_lang, TOPICS["en"])
    taxonomy_lines = "\n".join([f"- {k} ({v})" for k, v in taxonomy_dict.items()])
    sample_topic = next(iter(taxonomy_dict.keys()))

    return f"""You are an active, supportive, and friendly {lang_name} Language Tutor and Conversation Coach.
Your primary mission is to actively correct Jonathan's {lang_name} speech so he learns and improves on every turn, while maintaining a natural, engaging conversation strictly in {lang_name}.

GRAMMAR TAXONOMY & TOPIC KEYS FOR {lang_name.upper()}:
Available topic keys:
{taxonomy_lines}
- {target_lang}_other (General grammar / word choice)

RULES FOR YOUR RESPONSE:
1. CHECK FOR MISTAKES:
   Carefully check the user's input for any grammar mistakes, incorrect verb forms, wrong prepositions, slipped words from other languages, or unnatural phrasing in {lang_name}.

2. IF THERE IS A MISTAKE:
   You MUST verbally correct it right away at the very start of your spoken response in a friendly, constructive way.
   Explain the correct phrasing clearly (e.g. "Quick correction: ...").
   Then continue the conversation with an engaging comment and a follow-up question.
   Specify the exact taxonomy TOPIC key (e.g. {sample_topic}).

3. IF THE {lang_name.upper()} WAS FLAWLESS:
   Give brief verbal encouragement (e.g. "Spot on phrasing!"), then reply naturally with a follow-up question. Set TOPIC: none.

4. FORMAT:
   Always format your answer strictly in these 4 lines:
   CORRECTION: <Brief summary: Say '...' instead of '...' - explanation. Or 'None - great {lang_name}!'>
   TOPIC: <The matching topic key from the list above, e.g. {sample_topic}, or 'none'>
   ORIGINAL: <The exact wrong snippet the user said, or 'none'>
   CORRECTED: <The corrected replacement snippet, or 'none'>
   SPOKEN: <Your full spoken response to Jonathan in {lang_name}. MUST include the verbal correction first if there was a mistake, followed by your conversational reply. 2-3 sentences total, no markdown or emojis so it speaks cleanly via audio.>"""

# Faster-Whisper Model
_whisper_model = None
_whisper_lock = asyncio.Lock()

def get_whisper_model():
    global _whisper_model
    if _whisper_model is None:
        from faster_whisper import WhisperModel
        try:
            print("[STT] Loading faster-whisper (large-v3-turbo) on CUDA...", flush=True)
            _whisper_model = WhisperModel("large-v3-turbo", device="cuda", compute_type="int8_float16")
            print("[STT] faster-whisper ready on CUDA.", flush=True)
        except Exception as e:
            print(f"[STT] CUDA init fallback to CPU ({e})...", flush=True)
            _whisper_model = WhisperModel("large-v3-turbo", device="cpu", compute_type="int8", cpu_threads=6)
            print("[STT] faster-whisper ready on CPU.", flush=True)
    return _whisper_model

# TTS Cache
tts_cache: Dict[str, bytes] = {}
MAX_CACHE_ENTRIES = 500

def clean_speech_text(text: str) -> str:
    clean = text.replace("**", "").replace("*", "").replace("`", "").replace("#", "").replace("[[", "").replace("]]", "").strip()
    clean = re.sub(r'https?://\S+', '', clean)
    clean = re.sub(r'[\U00010000-\U0010ffff\u2600-\u27BF]', '', clean)
    clean = re.sub(r'\s+', ' ', clean).strip()
    return clean[:600]

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    topic: Optional[str] = "casual"
    voice: Optional[str] = DEFAULT_VOICE
    session_id: Optional[str] = "default_session"
    target_lang: Optional[str] = "en"
    native_lang: Optional[str] = "de"

class ExcludeMistakeRequest(BaseModel):
    reason: Optional[str] = "not_a_mistake"

class QuizGradeRequest(BaseModel):
    mistake_id: str
    question_text: str
    user_answer: str
    correct_answer: str

class StartSessionRequest(BaseModel):
    session_id: Optional[str] = None
    scenario: Optional[str] = "casual"
    level: Optional[str] = "B1"
    voice: Optional[str] = DEFAULT_VOICE
    target_lang: Optional[str] = "en"
    native_lang: Optional[str] = "de"

@app.api_route("/", methods=["GET", "HEAD"], response_class=HTMLResponse)
async def serve_index():
    index_file = os.path.join(os.path.dirname(__file__), "static", "index.html")
    if os.path.exists(index_file):
        with open(index_file, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>Voice Language Tutor Online</h1>")

@app.get("/api/health")
async def health():
    return {
        "status": "online",
        "service": "Voice Language Tutor & Coach",
        "voice": DEFAULT_VOICE,
        "model": MODEL_NAME,
        "pipeline": {
            "stt": {
                "engine": "Faster-Whisper (CTranslate2)",
                "model": "large-v3-turbo",
                "device": "CUDA (RTX 5090)",
                "compute_type": "int8_float16"
            },
            "llm": {
                "model": MODEL_NAME,
                "server": "LiteLLM / SGLang (local port 30050/4000)",
                "api_base": LITELLM_URL
            },
            "tts": {
                "engine": "Edge-TTS Neural Streaming",
                "default_voice": DEFAULT_VOICE,
                "format": "audio/mpeg (MP3)"
            },
            "database": {
                "engine": "SQLite3 (Embedded)",
                "tables": ["sessions", "turns", "mistakes", "quiz_attempts", "written_analyses"]
            }
        }
    }

@app.post("/api/reset")
async def reset_data_endpoint():
    database.clear_all_data()
    return {
        "status": "ok",
        "message": "All session turns, conversation history, mistakes, quiz attempts, and analysis data have been cleared."
    }

@app.get("/api/languages")
async def get_languages():
    return {
        "languages": [
            {
                "code": code,
                "name": info["name"],
                "native_name": info["native_name"],
                "flag": info["flag"],
                "default_voice": info["default_voice"],
                "voices": VOICES_BY_LANG.get(code, []),
                "scenarios": SCENARIOS_BY_LANG.get(code, {})
            }
            for code, info in SUPPORTED_LANGUAGES.items()
        ]
    }

@app.post("/api/sessions/start")
async def start_session_endpoint(req: StartSessionRequest):
    sid = req.session_id or f"session_{int(time.time()*1000)}"
    scenario = req.scenario or "casual"
    target_lang = req.target_lang or "en"
    if target_lang not in SUPPORTED_LANGUAGES:
        target_lang = "en"
    native_lang = req.native_lang or "de"

    database.create_session(sid, target_lang=target_lang, native_lang=native_lang, level=req.level or "B1", scenario=scenario)
    
    lang_scenarios = SCENARIOS_BY_LANG.get(target_lang, SCENARIOS_BY_LANG["en"])
    greeting = lang_scenarios.get(scenario, lang_scenarios.get("casual", "Hello Jonathan!"))
    turn_id = f"turn_{uuid.uuid4().hex[:10]}"
    database.record_turn(
        turn_id=turn_id,
        session_id=sid,
        user_transcript="[Session Started - Coach Opening]",
        assistant_reply=greeting,
        assistant_spoken=greeting,
        corrections=[]
    )
    return {
        "session_id": sid,
        "greeting": greeting,
        "turn_id": turn_id,
        "target_lang": target_lang
    }

@app.post("/api/stt")
async def speech_to_text(request: Request, lang: Optional[str] = None):
    audio_bytes = await request.body()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Audio payload required")

    target_lang = lang or request.headers.get("x-target-language") or "en"
    if target_lang not in SUPPORTED_LANGUAGES:
        target_lang = "en"

    proc = await asyncio.create_subprocess_exec(
        "ffmpeg", "-threads", "4", "-i", "pipe:0", "-f", "wav", "-ar", "16000", "-ac", "1", "pipe:1",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL
    )
    wav_data, _ = await proc.communicate(input=audio_bytes)
    if not wav_data or len(wav_data) < 1000:
        return {"text": ""}

    prompts = {
        "en": "Verbatim phonetic transcript of an ESL language learner. Transcribe every mistake, grammatical error, slip of the tongue, and exact word spoken without auto-correcting grammar or translating: mein name are Jonathan, he have, yesterday I go, she don't knows.",
        "de": "Wortgetreues phonetisches Transkript eines Deutschlernenden. Transkribiere jeden Grammatikfehler, falschen Kasus, Versprecher und jedes Wort exakt ohne Autokorrektur: ich bin nach Hause gegangen, ich habe gegangen, der Mädchen, weil ich bin müde.",
        "es": "Transcripción fonética literal de un estudiante de español. Transcribe cada error gramatical, palabra y fallo sin autocorrección: yo soy cansado, para tú, me gusto.",
        "fr": "Transcription phonétique littérale d'un apprenant de français. Transcrivez chaque erreur grammaticale, mot et faute sans autocorrection: je suis allé, j'ai tombé, le table.",
        "it": "Trascrizione fonetica letterale di uno studente d'italiano. Trascrivi ogni errore grammaticale e parola senza autocorrezione: io ho andato, la problema."
    }

    async with _whisper_lock:
        loop = asyncio.get_running_loop()
        def transcribe():
            model = get_whisper_model()
            wav_io = io.BytesIO(wav_data)
            segments, _ = model.transcribe(
                wav_io,
                language=target_lang,
                initial_prompt=prompts.get(target_lang, prompts["en"]),
                beam_size=1,
                best_of=1,
                temperature=0.0,
                condition_on_previous_text=False,
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=250, threshold=0.4)
            )
            return " ".join([s.text for s in segments]).strip()

        text = await loop.run_in_executor(None, transcribe)
        print(f"[STT][{target_lang}] Transcribed verbatim: '{text}'", flush=True)

    if (text.startswith("[") and text.endswith("]")) or (text.startswith("(") and text.endswith(")")):
        text = ""

    hallucinations = {"thank you", "thanks for watching", "bye", "you", "so", "oh", "ah", "hmm"}
    if text.strip().lower() in hallucinations:
        text = ""

    return {"text": text}

@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    target_lang = req.target_lang or "en"
    if target_lang not in SUPPORTED_LANGUAGES:
        target_lang = "en"
    native_lang = req.native_lang or "de"

    topic_context = ""
    if req.topic and req.topic != "casual":
        topic_context = f"\nCURRENT SCENARIO/TOPIC: {req.topic.capitalize()} mode. Guide the conversation around this theme."

    session_id = req.session_id or "default_session"
    database.create_session(session_id, target_lang=target_lang, native_lang=native_lang, level="B1", scenario=req.topic or "casual")

    system_prompt = get_system_prompt(target_lang=target_lang, native_lang=native_lang)
    user_last_msg = ""
    messages = [{"role": "system", "content": system_prompt + topic_context}]
    for m in req.messages:
        messages.append({"role": m.role, "content": m.content})
        if m.role == "user":
            user_last_msg = m.content

    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "temperature": 0.25,
        "max_tokens": 220,
        "stream": True,
        "extra_body": {
            "chat_template_kwargs": {"enable_thinking": False}
        }
    }

    async def sse_generator():
        raw_text = ""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                async with client.stream(
                    "POST",
                    f"{LITELLM_URL}/chat/completions",
                    json=payload,
                    headers={"Authorization": "Bearer dummy"}
                ) as resp:
                    if resp.status_code != 200:
                        yield f"data: {json.dumps({'error': f'LLM upstream HTTP {resp.status_code}'})}\n\n"
                        yield "data: [DONE]\n\n"
                        return

                    async for line in resp.aiter_lines():
                        if not line or not line.startswith("data: "):
                            continue
                        chunk = line[6:].strip()
                        if chunk == "[DONE]":
                            break
                        try:
                            data = json.loads(chunk)
                            choices = data.get("choices", [])
                            if choices:
                                delta = choices[0].get("delta", {}).get("content", "")
                                if delta:
                                    raw_text += delta
                                    yield f"data: {json.dumps({'delta': delta})}\n\n"
                        except Exception:
                            continue

            # Process completed turn and persist to database
            turn_id = f"turn_{uuid.uuid4().hex[:10]}"
            correction_summary = ""
            topic_key = f"{target_lang}_other"
            original_snippet = ""
            corrected_snippet = ""
            spoken_text = ""

            for line in raw_text.splitlines():
                line_str = line.strip()
                if line_str.startswith("CORRECTION:"):
                    correction_summary = line_str.replace("CORRECTION:", "").strip()
                elif line_str.startswith("TOPIC:"):
                    topic_key = line_str.replace("TOPIC:", "").strip().lower()
                elif line_str.startswith("ORIGINAL:"):
                    original_snippet = line_str.replace("ORIGINAL:", "").strip()
                elif line_str.startswith("CORRECTED:"):
                    corrected_snippet = line_str.replace("CORRECTED:", "").strip()
                elif line_str.startswith("SPOKEN:"):
                    spoken_text = line_str.replace("SPOKEN:", "").strip()

            if not spoken_text and "SPOKEN:" in raw_text:
                spoken_text = raw_text.split("SPOKEN:")[1].strip()
            elif not spoken_text:
                spoken_text = raw_text.strip()

            corrections = []
            is_error = False
            lower_corr = correction_summary.lower()
            flawless_markers = ["none", "spot on", "perfect", "flawless", "great", "kein fehler", "perfekt", "excelente", "bravo", "sans faute"]
            if correction_summary and not any(k in lower_corr for k in flawless_markers):
                is_error = True
                mistake_id = f"m_{uuid.uuid4().hex[:10]}"
                
                # Validate topic key against target language topics
                lang_topics = TOPICS.get(target_lang, TOPICS.get("en", {}))
                if topic_key not in lang_topics:
                    # Check if key exists in another language list
                    found_key = False
                    for l_code, l_dict in TOPICS.items():
                        if topic_key in l_dict:
                            found_key = True
                            break
                    if not found_key:
                        topic_key = f"{target_lang}_other"

                corrections.append({
                    "id": mistake_id,
                    "original": original_snippet if original_snippet != "none" else user_last_msg,
                    "corrected": corrected_snippet if corrected_snippet != "none" else correction_summary,
                    "corrected_sentence": user_last_msg,
                    "kind": "error",
                    "topic": topic_key,
                    "explanation": correction_summary
                })

            database.record_turn(
                turn_id=turn_id,
                session_id=session_id,
                user_transcript=user_last_msg,
                assistant_reply=raw_text,
                assistant_spoken=spoken_text,
                corrections=corrections
            )

            # Send turn metadata
            meta = {
                "turn_id": turn_id,
                "corrections": corrections,
                "is_error": is_error
            }
            yield f"data: {json.dumps({'meta': meta})}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            print(f"[CHAT] Error: {e}", flush=True)
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(sse_generator(), media_type="text/event-stream")

@app.post("/api/mistakes/{mistake_id}/exclude")
async def exclude_mistake_endpoint(mistake_id: str, req: ExcludeMistakeRequest):
    updated = database.exclude_mistake(mistake_id, req.reason or "not_a_mistake")
    if not updated:
        raise HTTPException(status_code=404, detail="Mistake not found")
    return {"status": "excluded", "mistake_id": mistake_id, "reason": req.reason}

@app.get("/api/mistakes")
async def list_active_mistakes(session_id: Optional[str] = None, lang: Optional[str] = None):
    target_lang = lang or "en"
    if session_id:
        s_lang = database.get_session_lang(session_id)
        if s_lang:
            target_lang = s_lang
    mistakes = database.get_active_mistakes(session_id=session_id, limit=30)
    for m in mistakes:
        m["topic_label"] = get_topic_label(m["topic"], lang=target_lang)
    return {"mistakes": mistakes}

@app.post("/api/quiz/generate")
async def generate_quiz_endpoint(session_id: Optional[str] = None, lang: Optional[str] = None):
    target_lang = lang or "en"
    if session_id:
        s_lang = database.get_session_lang(session_id)
        if s_lang:
            target_lang = s_lang

    active_mistakes = database.get_active_mistakes(session_id=session_id, limit=5)
    if not active_mistakes:
        return {
            "questions": [],
            "message": "No recorded mistakes yet! Have a conversation first, and mistakes will automatically form your practice quiz."
        }

    # Prompt LLM to create targeted practice questions based strictly on recorded mistakes
    mistake_context = []
    for idx, m in enumerate(active_mistakes):
        mistake_context.append(
            f"Mistake {idx+1} [ID: {m['id']}]:\n"
            f"- User said: \"{m['original']}\"\n"
            f"- Correction: \"{m['corrected']}\"\n"
            f"- Grammar Topic: {m['topic']} ({get_topic_label(m['topic'], lang=target_lang)})\n"
            f"- Explanation: {m['explanation']}"
        )

    prompt = (
        "Generate an interactive practice quiz with exactly " + str(min(3, len(active_mistakes))) + " multiple choice questions "
        "derived strictly from the user's actual mistakes below.\n\n"
        + "\n\n".join(mistake_context[:3]) +
        "\n\nOUTPUT RULES:\n"
        "Return ONLY a valid JSON object with the following structure:\n"
        "{\n"
        "  \"questions\": [\n"
        "    {\n"
        "      \"mistake_id\": \"<exact ID of the mistake from above>\",\n"
        "      \"question\": \"<The quiz question in the target language>\",\n"
        "      \"options\": [\"<Option 1>\", \"<Option 2>\", \"<Option 3>\", \"<Option 4>\"],\n"
        "      \"correct_answer\": \"<Exact match of one of the options>\",\n"
        "      \"source_said\": \"<What the user originally said>\",\n"
        "      \"explanation\": \"<Brief grammar rule explanation>\"\n"
        "    }\n"
        "  ]\n"
        "}"
    )

    try:
        async with httpx.AsyncClient(timeout=25.0) as client:
            resp = await client.post(
                f"{LITELLM_URL}/chat/completions",
                json={
                    "model": MODEL_NAME,
                    "messages": [
                        {"role": "system", "content": "You are an expert language quiz creator. Output ONLY valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.2,
                    "max_tokens": 500,
                    "extra_body": {"chat_template_kwargs": {"enable_thinking": False}}
                },
                headers={"Authorization": "Bearer dummy"}
            )
            if resp.status_code == 200:
                data = resp.json()
                content = data["choices"][0]["message"]["content"].strip()
                # Clean markdown backticks if any
                if content.startswith("```"):
                    content = re.sub(r'^```(?:json)?\s*', '', content)
                    content = re.sub(r'\s*```$', '', content)
                parsed = json.loads(content)
                return parsed
    except Exception as e:
        print(f"[QUIZ] Generation error: {e}", flush=True)

    # Deterministic fallback quiz if LLM JSON parsing fails
    fallback_questions = []
    for m in active_mistakes[:3]:
        fallback_questions.append({
            "mistake_id": m["id"],
            "question": f"Which sentence correctly fixes: \"{m['original']}\"?",
            "options": [
                m["corrected"],
                m["original"],
                m["original"].replace(" ", " not "),
                "None of the above"
            ],
            "correct_answer": m["corrected"],
            "source_said": m["original"],
            "explanation": m["explanation"] or f"Topic: {get_topic_label(m['topic'], lang=target_lang)}"
        })

    return {"questions": fallback_questions}

@app.post("/api/quiz/grade")
async def grade_quiz_endpoint(req: QuizGradeRequest):
    # Deterministic grading
    is_correct = (req.user_answer.strip().lower() == req.correct_answer.strip().lower())
    attempt_id = f"qa_{uuid.uuid4().hex[:10]}"
    database.record_quiz_attempt(
        attempt_id=attempt_id,
        mistake_id=req.mistake_id,
        question_text=req.question_text,
        user_answer=req.user_answer,
        is_correct=is_correct
    )
    return {
        "is_correct": is_correct,
        "correct_answer": req.correct_answer,
        "attempt_id": attempt_id
    }

@app.get("/api/stats")
async def get_stats_endpoint(session_id: Optional[str] = None):
    stats = database.get_stats(session_id=session_id)
    return stats

@app.get("/api/analysis")
async def get_analysis_endpoint(session_id: Optional[str] = None):
    data = database.get_analysis_data(session_id=session_id)
    
    # If there are active mistakes and at least 2 turns, provide an AI written diagnosis summary
    ai_summary = ""
    strengths = []
    focus_areas = []

    if data["total_mistakes"] > 0:
        top_topics = [t["label"] for t in data["topic_frequency"][:3]]
        ai_summary = f"Identified {data['total_mistakes']} grammar correction(s) across {data['total_turns']} spoken turns. The highest frequency areas to work on are: {', '.join(top_topics)}."
        
        for t in data["topic_frequency"][:3]:
            focus_areas.append({
                "topic": t["label"],
                "tip": f"Review rules for {t['label']}. Focus on practicing these forms in your next spoken conversation."
            })
    else:
        ai_summary = "Excellent fluency so far! Your turns have maintained a high level of grammatical accuracy."
        strengths.append("High accuracy across recent dialogue turns.")

    data["ai_analysis"] = {
        "summary": ai_summary,
        "strengths": strengths,
        "focus_areas": focus_areas
    }
    return data

@app.get("/api/tts")
async def tts_endpoint(text: str, voice: Optional[str] = None, lang: Optional[str] = None):
    clean = clean_speech_text(text)
    if not clean:
        raise HTTPException(status_code=400, detail="Text required")

    active_voice = None
    if voice and voice not in ("undefined", "null", ""):
        active_voice = voice
    elif lang and lang in SUPPORTED_LANGUAGES:
        active_voice = SUPPORTED_LANGUAGES[lang]["default_voice"]
    else:
        active_voice = DEFAULT_VOICE
    cache_key = f"{active_voice}:{clean}"
    if cache_key in tts_cache:
        return Response(content=tts_cache[cache_key], media_type="audio/mpeg")

    async def audio_stream():
        collected = bytearray()
        try:
            comm = edge_tts.Communicate(
                clean,
                active_voice,
                rate="+2%",
                volume="+4%"
            )
            async for chunk in comm.stream():
                if chunk.get("type") == "audio":
                    data = chunk.get("data")
                    collected.extend(data)
                    yield bytes(data)
            if collected:
                if len(tts_cache) >= MAX_CACHE_ENTRIES:
                    tts_cache.pop(next(iter(tts_cache)))
                tts_cache[cache_key] = bytes(collected)
        except Exception as e:
            print(f"[TTS] Error: {e}", flush=True)

    return StreamingResponse(audio_stream(), media_type="audio/mpeg")

# Mount static files
app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static")), name="static")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 5050))
    uvicorn.run(app, host="0.0.0.0", port=port)
