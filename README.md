# Voice-Only AI Language Tutor & Conversation Coach

A real-time spoken language conversation coach and tutor powered by open-weight models that analyzes what you say, corrects grammar and vocabulary mistakes both visually and verbally in natural speech, saves conversation history, and turns your actual mistakes into personalized interactive practice quizzes.

Built for the Hacktoberfest hackathon. See [`PLAN.md`](./PLAN.md) and [`gemini_plan.md`](./gemini_plan.md) for architectural plans.

## ✨ Features

- **End-to-End Voice Pipeline**:
  - **Speech-to-Text (STT)**: High-precision verbatim speech transcription using **Faster-Whisper (Large-v3-Turbo)** (or Groq Whisper API). Tuned specifically for language learners to capture phonetic grammar errors verbatim without artificial autocorrection.
  - **Conversational AI & Tutor Engine**: Active language coach powered by open-weight LLMs (`qwen3.8-fast` / local SGLang or Groq `gpt-oss-120b`). Identifies mistakes against a predefined grammar taxonomy, verbally explains corrections in natural speech, and keeps dialogues engaging.
  - **Text-to-Speech (TTS)**: High-fidelity natural voice streaming via Edge-TTS / Resemble Chatterbox.
- **Immediate Verbal & Visual Feedback**:
  - Spoken feedback: The coach directly explains the correction in the speech output before continuing the conversation.
  - Visual cards: Structured mistake cards tagged by grammar topic (e.g., *Subject-Verb Agreement*, *Irregular Past Forms*).
  - Feedback controls: Mark false positives as **"Not a mistake"** or transcription slips as **"Misheard"**.
- **Personalized Interactive Practice Quiz**:
  - Automatically generates dynamic multiple-choice and fill-in-the-blank questions derived strictly from the learner's actual recorded mistakes (*"Practising this because you said: ..."*).
  - Deterministic grading with immediate explanation and review.
- **Conversation Scenarios & Levels**:
  - ☕ Casual Coffee Chat
  - 💼 Job Interview Practice
  - 💻 Tech & Software Discussion
  - ✈️ Travel & Daily Life
  - 📚 Strict Grammar Drill
- **Hands-Free / Continuous Dialogue**:
  - Built-in Voice Activity Detection (VAD) automatically detects when you finish speaking and submits turns seamlessly.
  - Push-to-Talk via interactive microphone orb or Spacebar.

## 🚀 Quickstart

### Prerequisites
- Python 3.10+
- `ffmpeg` installed on the system (for audio transcoding)
- CUDA-enabled GPU (optional, falls back gracefully to CPU)

### Installation

```bash
git clone https://github.com/FINN-SCH/Hacktoberfest.git
cd Hacktoberfest
git checkout voice-language-tutor

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Running the App

```bash
# Starts the server on port 5050
python server.py
```

Then open your browser at:
`http://localhost:5050`

## 📁 Architecture

```
.
├── PLAN.md               # Team Hackathon technical plan & taxonomy
├── gemini_plan.md        # Architecture & system design plan
├── server.py             # FastAPI backend (STT, LLM, TTS, Quizzes, Stats)
├── database.py           # Lightweight SQLite storage for sessions, turns, mistakes & quizzes
├── topics.py             # Predefined grammar topics taxonomy (EN & DE)
├── start.sh              # Runner script
├── requirements.txt      # Python dependencies
└── static/
    ├── index.html        # Interactive voice tutor & quiz UI
    ├── style.css         # Modern dark-mode UI & animated waveform
    └── app.js            # Web Audio recording, VAD, TTS queue & Quiz engine
```
