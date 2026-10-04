# Implementation Plan: Voice-Only AI Language Tutor App

## 1. Overview
A web application designed to help users practice new languages. Upon opening the app, users can choose between two distinct modes: **Talk with an Agent** or **Take a Quiz**. The conversation mode operates exclusively via voice chat, providing voice-based language corrections after the user speaks. Quizzes are dynamically generated on-demand based on a frequency table of the user's past mistakes.

## 2. Tech Stack Selection
*   **Frontend**: React / Next.js
*   **Backend**: Python (FastAPI) - Serves as the API for database operations, user management, and AI orchestration.
*   **AI Models (Open Source)**:
    *   **Conversational Agent & Correction**: Llama 3 (or similar open-source LLM like Mixtral).
    *   **Speech-to-Text (STT)**: Whisper.
    *   **Text-to-Speech (TTS)**: Open-source TTS like XTTSv2, Piper, or browser-native.
*   **Database**: PostgreSQL (via SQLAlchemy) to store users, transcripts, and mistake frequency tables.

## 3. Architecture & System Components

### Frontend (Next.js)
*   **Landing Dashboard**: Upon login, the user chooses between **"Talk with an Agent"** or **"Take a Quiz"**.
*   **Voice Interface**: Minimalist UI focused on a microphone button.
*   **Direct API Connection**: The frontend directly connects to the API to transmit audio and receive responses, replacing continuous WebSocket streaming.
*   **Quiz Interface**: A dedicated UI flow for answering questions generated on the fly.

### Backend (Python / FastAPI)
*   **API Endpoints**: RESTful endpoints to receive audio, process AI requests, and log mistake frequencies.
*   **Audio Processing Pipeline**:
    1.  Frontend sends user audio directly to the API once the user finishes speaking.
    2.  Audio -> STT (Whisper) -> Text.
    3.  Text -> Agent LLM -> AI Response Text.
    4.  Text -> Correction LLM -> identifies mistakes (if any).
    5.  AI merges the conversational response and the verbal correction -> TTS -> AI Audio returned to frontend.
*   **Mistake Frequency Tracker**: A system that updates a database table with the count of specific mistakes made by the user.

## 4. Core Features & Data Flow

### A. Real-Time Voice Conversation & Correction (Agent Mode)
1.  User selects "Talk with an Agent" and speaks into the microphone; the frontend sends the audio directly to the API once the user finishes their sentence.
2.  The API transcribes the audio using **Whisper**.
3.  The text is processed to generate a conversational reply and check for language mistakes.
4.  If a mistake is detected, the AI incorporates a verbal correction (e.g., "By the way, you should say X instead of Y") before or after answering the user's prompt.
5.  The backend converts this combined text to audio using **TTS** and sends it back to the frontend to play.

### B. Transcript & Mistake Logging
1.  The backend saves the transcribed user utterance and AI response into the database.
2.  Any identified mistakes are logged, and the user's mistake frequency table is updated (incrementing the count of that specific error type).

### C. Dynamic Quiz Generation (Quiz Mode)
1.  When the user explicitly chooses the "Take a Quiz" mode, the frontend requests a new quiz from the API.
2.  The backend checks the user's mistake frequency table and identifies the most common/frequent mistakes.
3.  An open-source LLM prompt is executed on-the-fly to dynamically generate questions targeting these top mistakes.
4.  The generated quiz is returned to the frontend for the user to solve.

## 5. Proposed Development Phases

### Phase 1: Foundation & Direct API Setup (PoC)
*   Set up Next.js frontend with microphone access.
*   Set up FastAPI backend with REST endpoints.
*   Integrate Whisper STT and basic TTS.

### Phase 2: Open Source LLM & Voice Corrections
*   Connect the backend to Llama (via Ollama, vLLM, or API).
*   Implement the prompt logic to combine conversational replies with verbal corrections.
*   Return AI audio responses.

### Phase 3: Mistake Frequency Tracking
*   Design the database schema for the frequency table.
*   Implement the logic to extract and log mistakes into this table during conversations.

### Phase 4: Dynamic Quizzes & Analytics
*   Develop the on-demand AI quiz generation pipeline based on the frequency table.
*   Build the dedicated "Quiz Mode" UI on the frontend.
*   Implement quiz scoring.

### Phase 5: Polish & Optimization
*   Optimize audio latency.
*   Add premium UI/UX designs (animations, dark mode) following modern web aesthetics.
