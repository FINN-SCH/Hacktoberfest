# Voice Language Tutor

A voice-first language tutor powered entirely by **open-weight models**. Talk to it hands-free. It corrects your grammar out loud as you go, saves the full conversation as a transcript, rates the session, and turns your own past mistakes into a personalised quiz.

Built for the Hacktoberfest hackathon (theme: open-source / open-weight models).

> Status: planning complete, implementation starting. See [PLAN.md](PLAN.md) for the full technical plan.

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
                                                            |- STT  : Whisper large-v3        (Groq)
                                                            |- LLM  : gpt-oss-120b, JSON out  (Groq)
                                                            |- save turn + mistakes           (SQLite)
  correction cards + reply text   <-------------------------+
  tutor audio                     <----POST /speech---------- TTS : Chatterbox Multilingual (DeepInfra)
  (mic paused while the tutor speaks, then listening resumes)
```

It's a cascaded speech-to-text, LLM, text-to-speech pipeline rather than a single speech-to-speech model. Corrections, transcripts, scoring and quizzes all need text, and a text pipeline lets us check every correction against what was actually said.

## Open-weight models

| Component | Model | License | Served by |
|---|---|---|---|
| Speech-to-text | OpenAI Whisper large-v3 | MIT | Groq |
| Tutor / report / quiz / analysis LLM | OpenAI gpt-oss-120b | Apache 2.0 | Groq |
| Text-to-speech | Resemble AI Chatterbox Multilingual | MIT | DeepInfra |
| Voice activity detection | Silero VAD (via `@ricky0123/vad-react`) | MIT | runs in the browser |

Every model client is a thin adapter with its base URL and model ID in `.env`, so any of them can be pointed at another host serving the same open weights.

## Tech stack

- **Frontend:** React, Vite, TypeScript, `@ricky0123/vad-react`, Recharts
- **Backend:** Python, FastAPI, SQLModel, SQLite
- **Inference:** Groq (STT + LLM), DeepInfra (TTS), via hosted APIs

## Repository layout (planned)

```
frontend/   React app: voice capture + VAD, conversation, report, history, quiz, analysis
backend/    FastAPI app: providers (stt/llm/tts), tutoring, scoring, quizzes, analysis, grammar topics, db
contracts/  agreed request/response JSON examples (frontend and backend build against these)
tests/fixtures/  learner utterances and failure cases used by the spikes
```

## Getting started

Setup instructions land here once the scaffold exists. You will need:

- Node.js 20+, Python 3.11+
- A Groq API key and a DeepInfra API key in `backend/.env` (see `.env.example`)
- Chrome or Edge (microphone + Web Audio)

## Team

4 developers. Ownership and timeline are in [PLAN.md](PLAN.md#team-split-and-timeline).
