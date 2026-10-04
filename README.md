# Voice-Only AI Language Tutor & Conversation Coach

A real-time spoken English conversation coach and language tutor that analyzes what you say, corrects grammar and vocabulary mistakes both visually and verbally in natural speech, and keeps conversational dialogue flowing seamlessly.

Built in accordance with [`gemini_plan.md`](./gemini_plan.md).

## ✨ Features

- **End-to-End Voice Pipeline**:
  - **Speech-to-Text (STT)**: High-precision verbatim speech transcription using **Faster-Whisper (Large-v3-Turbo)**. Tuned specifically for language learners to capture phonetic grammar errors verbatim without artificial autocorrection.
  - **Conversational AI (LLM)**: Active language tutor agent. Identifies mistakes in grammar, tense, prepositions, or word choice, verbally explains the correction, and asks engaging conversational follow-up questions.
  - **Text-to-Speech (TTS)**: High-fidelity natural voice streaming via **Edge-TTS** with zero latency sentence chunking.
- **Immediate Verbal & Visual Feedback**:
  - Spoken feedback: The coach directly explains the correction in the speech output before continuing the conversation.
  - Visual banner: Highlights the exact correction, reason, and recommended phrasing.
- **Conversation Scenarios**:
  - ☕ Casual Coffee Chat
  - 💼 Job Interview Practice
  - 💻 Tech & Software Discussion
  - ✈️ Travel & Daily Life
  - 📚 Strict Grammar Drill
- **Multi-Accent Support**:
  - 🇺🇸 Andrew (US Natural / Friendly)
  - 🇺🇸 Ava (US Warm)
  - 🇬🇧 Ryan (UK British)
  - 🇬🇧 Sonia (UK Gentle)
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
├── gemini_plan.md        # Architecture & system design plan
├── server.py             # FastAPI backend (STT, LLM streaming, TTS endpoints)
├── start.sh              # Runner script
├── requirements.txt      # Python dependencies
├── static/
│   ├── index.html        # Interactive voice tutor interface
│   ├── style.css         # Modern dark-mode UI & animated waveform
│   └── app.js            # Web Audio recording, VAD, and TTS streaming queue
└── test.py
```
