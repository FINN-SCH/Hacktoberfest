# Voice Language Tutor

A voice-first language tutor with **pluggable providers and an open-weight model path**. Talk to it hands-free. It corrects your grammar out loud as you go, saves the full conversation as a transcript, rates the session, and turns your own past mistakes into a personalised quiz.

Built for the Hacktoberfest hackathon (theme: open-source / open-weight models).

> Status: implemented on `tutor-v2`. See [SETUP_GUIDE.md](SETUP_GUIDE.md) for setup and [PLAN.md](PLAN.md) for the technical plan.

## What it does

1. **Talk.** Pick a language (German or English), your level (A1-B2) and a scenario (cafe, job interview, doctor, free talk), then just speak. Voice activity detection decides when you have finished a sentence.
2. **Get corrected in real time.** After each turn the tutor says one short correction out loud ("Du meinst: Ich bin nach Berlin gegangen.") and then keeps the conversation going. Every detected mistake also appears as a card with an explanation in the language you choose.
3. **Review your session.** The full transcript is saved, with three ratings, each backed by evidence:
   - **Grammar**: computed from the corrections you saw, not a second guess by the model.
   - **Vocabulary**: rubric-based, with quoted examples from what you said.
   - **Fluency**: speaking rate and pauses.
4. **Practise your weaknesses.** A quiz (multiple choice and fill-in) is generated from the mistakes you actually made: *"Practising this because you said ..."*.
5. **See the big picture.** The **Analysis** tab tracks you across all sessions:
   - progress over sessions
   - mistakes you keep repeating
   - a frequency table of your mistakes by grammar topic (e.g. *Perfekt: haben vs. sein*, *Dative case*)
   - a written analysis of your strengths and what to work on, refreshed automatically after every session

Wrong correction? Mark it **Not a mistake**. Speech recognition got you wrong? Mark the turn **Misheard**. Excluded items stop counting toward scores and quizzes.

## How it works

```
Browser (React + Vite + TS)
  mic -> Silero VAD -> speech segment ----POST /turns----> FastAPI
                                                            |- STT  : faster-whisper or Groq Whisper
                                                            |- LLM  : OpenAI-compatible proxy/API
                                                            |- save turn + mistakes           (SQLite)
  correction cards + reply text   <-------------------------+
  tutor audio                     <----POST /speech---------- TTS : Edge or DeepInfra Chatterbox
  (mic paused while the tutor speaks, then listening resumes)
```

It's a cascaded speech-to-text, LLM, text-to-speech pipeline rather than a single speech-to-speech model. Corrections, transcripts, scoring and quizzes all need text, and a text pipeline lets us check every correction against what was actually said.

## Providers and open-weight models

The default local setup uses LiteLLM at `http://localhost:4000/v1` (`qwen3.8-fast`), local faster-whisper, and Edge-TTS.
**Edge-TTS is a proprietary Microsoft cloud voice, not an open-weight model or an offline service.**
The [edge-tts client](https://github.com/rany2/edge-tts) calls Microsoft's online service.
For the hackathon's open-weight theme, choose Whisper + gpt-oss/Qwen + Chatterbox instead.

| Component | Supported paths | Open-weight status |
|---|---|---|
| Speech-to-text | Local faster-whisper large-v3-turbo; Groq Whisper large-v3 | [Whisper](https://github.com/openai/whisper) weights/code use MIT |
| Tutor / report / quiz / analysis | OpenAI-compatible LiteLLM or Groq; local alias qwen3.8-fast or hosted gpt-oss-120b | [gpt-oss](https://huggingface.co/openai/gpt-oss-120b) is Apache 2.0; Qwen is an open-weight option, but verify the actual model/license behind the local proxy alias |
| Text-to-speech (default) | Edge: en-US-AndrewNeural / de-DE-ConradNeural | Proprietary Microsoft cloud voices |
| Text-to-speech (open-weight option) | DeepInfra ResembleAI/chatterbox-multilingual | [Chatterbox](https://github.com/resemble-ai/chatterbox) is MIT-licensed |
| Browser voice activity detection | Silero VAD via @ricky0123/vad-react, assets served locally | [Silero VAD](https://github.com/snakers4/silero-vad) is MIT-licensed |

Provider adapters are selected through `backend/.env`: `STT_PROVIDER=faster_whisper|groq`, `TTS_PROVIDER=edge|deepinfra`.
The LLM adapter accepts an OpenAI-compatible base URL, model and explicit JSON mode.
The local profile uses prompt-mode JSON; the hosted Groq profile uses json_schema. There is no automatic provider or JSON-mode downgrade.

## Tech stack

- **Frontend:** React, Vite, TypeScript, `@ricky0123/vad-react`, Recharts
- **Backend:** Python, FastAPI, SQLModel, SQLite
- **Inference:** local LiteLLM + faster-whisper by default; Groq hosted option; Edge or DeepInfra TTS

## Repository layout

```
frontend/   React app: voice capture + VAD, conversation, report, history, quiz, analysis
backend/    FastAPI: providers, services, routers, schemas, prompts, SQLite, tests, scripts
frontend/src/api/generated.ts  TypeScript contracts generated from FastAPI OpenAPI
backend/tests/  fake providers, HTTP contracts, scoring, evidence and setup checks
```

## Quick start

Use **branch tutor-v2**, Python **3.10+**, Node **22.11+**, and Chrome/Edge.
Follow [SETUP_GUIDE.md](SETUP_GUIDE.md) for copy-paste Linux/Windows setup, local/hosted provider profiles, and troubleshooting.
Coding agents should read [AGENTS.md](AGENTS.md) (opencode) or [GEMINI.md](GEMINI.md) (Gemini CLI).

After installing dependencies, configuring `backend/.env`, and building the frontend:

```bash
(cd backend && .venv/bin/python -m app.seed)
(cd backend && .venv/bin/python -m scripts.check_providers)
chmod +x start.sh
./start.sh
```

Open **http://127.0.0.1:5050**. Windows uses `start.ps1` instead.
The seed command creates **Demo learner**, three German sessions and one English session, all labelled demo data, without any API calls.
A second seed run refuses duplication; `--reset-demo` replaces only demo data and refuses if real practice would be affected.
Use a separate profile for actual practice. Five eligible turns and sixty seconds of voiced speech are needed for ratings.

Edge returns MP3, so the provider probe explicitly skips STT unless compatible WAV audio is supplied.
Verify a real spoken browser turn before calling setup complete. The app is local-first, has no authentication, and stores learning history in SQLite.

## Team

4 developers. Ownership and timeline are in [PLAN.md](PLAN.md#team-split-and-timeline).
