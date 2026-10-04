import os
import io
import re
import sys
import glob
import ctypes
import asyncio
import json
from typing import Optional, List, Dict
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, StreamingResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import edge_tts

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

app = FastAPI(title="English Voice Language Coach", version="2.0.0")

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

SYSTEM_PROMPT = """You are an active, supportive, and friendly English Language Tutor and Conversation Coach.
Your primary mission is to actively correct Jonathan's English speech so he learns and improves on every turn, while maintaining a natural, engaging conversation.

RULES FOR YOUR RESPONSE:
1. CHECK FOR MISTAKES:
   Carefully check the user's input for any grammar mistakes, incorrect verb forms, wrong prepositions, German/Denglish words (like 'mein', 'ich', 'auch'), or unnatural phrasing.

2. IF THERE IS A MISTAKE:
   You MUST verbally correct it right away at the very start of your spoken response in a friendly, constructive way.
   Explain the correct phrasing (e.g. "Quick correction: say 'My name is Jonathan' instead of 'are', since 'name' is singular.").
   Then continue the conversation with an engaging comment and a follow-up question.

3. IF THE ENGLISH WAS FLAWLESS:
   Give brief verbal encouragement (e.g. "Spot on phrasing!"), then reply naturally with a follow-up question.

4. FORMAT:
   Always format your answer strictly as:
   CORRECTION: <Brief summary: Say '...' instead of '...' - explanation. Or 'None - great English!'>
   SPOKEN: <Your full spoken response to Jonathan. MUST include the verbal correction first if there was a mistake, followed by your conversational reply. 2-3 sentences total, no markdown or emojis so it speaks cleanly via audio.>"""

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

@app.api_route("/", methods=["GET", "HEAD"], response_class=HTMLResponse)
async def serve_index():
    index_file = os.path.join(os.path.dirname(__file__), "static", "index.html")
    if os.path.exists(index_file):
        with open(index_file, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>English Voice Coach Online</h1>")

@app.get("/api/health")
async def health():
    return {
        "status": "online",
        "service": "English Language Coach",
        "voice": DEFAULT_VOICE,
        "model": MODEL_NAME
    }

@app.post("/api/stt")
async def speech_to_text(request: Request):
    audio_bytes = await request.body()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Audio payload required")

    proc = await asyncio.create_subprocess_exec(
        "ffmpeg", "-threads", "2", "-i", "pipe:0", "-f", "wav", "-ar", "16000", "-ac", "1", "pipe:1",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL
    )
    wav_data, _ = await proc.communicate(input=audio_bytes)
    if not wav_data or len(wav_data) < 1000:
        return {"text": ""}

    async with _whisper_lock:
        loop = asyncio.get_running_loop()
        def transcribe():
            model = get_whisper_model()
            wav_io = io.BytesIO(wav_data)
            segments, _ = model.transcribe(
                wav_io,
                language="en",
                initial_prompt="Verbatim phonetic transcript of an ESL language learner. Transcribe every mistake, grammatical error, slip of the tongue, and exact word spoken without auto-correcting grammar or translating: mein name are Jonathan, he have, yesterday I go, she don't knows.",
                beam_size=1,
                condition_on_previous_text=False,
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=350)
            )
            return " ".join([s.text for s in segments]).strip()

        text = await loop.run_in_executor(None, transcribe)
        print(f"[STT] Transcribed verbatim: '{text}'", flush=True)

    if (text.startswith("[") and text.endswith("]")) or (text.startswith("(") and text.endswith(")")):
        text = ""

    hallucinations = {"thank you", "thanks for watching", "bye", "you", "so", "oh", "ah", "hmm"}
    if text.strip().lower() in hallucinations:
        text = ""

    return {"text": text}

@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    topic_context = ""
    if req.topic and req.topic != "casual":
        topic_context = f"\nCURRENT SCENARIO/TOPIC: {req.topic.capitalize()} mode. Guide the conversation around this theme."

    messages = [{"role": "system", "content": SYSTEM_PROMPT + topic_context}]
    for m in req.messages:
        messages.append({"role": m.role, "content": m.content})

    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "temperature": 0.4,
        "max_tokens": 280,
        "stream": True,
        "extra_body": {
            "chat_template_kwargs": {"enable_thinking": False}
        }
    }

    async def sse_generator():
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

                    raw_text = ""
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

            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(sse_generator(), media_type="text/event-stream")

@app.get("/api/tts")
async def tts_endpoint(text: str, voice: Optional[str] = None):
    clean = clean_speech_text(text)
    if not clean:
        raise HTTPException(status_code=400, detail="Text required")

    active_voice = voice or DEFAULT_VOICE
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
