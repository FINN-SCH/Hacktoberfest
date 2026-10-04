# Coding-agent setup instructions

Applies to opencode and Gemini CLI. AGENTS.md and GEMINI.md intentionally contain the same text.
Goal: run **tutor-v2** on Klabundo's Linux machine using his EXISTING LiteLLM/Qwen, local faster-whisper, and Edge-TTS.
Read SETUP_GUIDE.md for the full human guide. PLAN.md is the application specification.
Run commands one at a time. If a command fails, STOP that step, read its error, and use the recovery list below.
Do not call a green build a successful microphone/provider test.

## Hard rules

- Work on tutor-v2. Never push to main. Never commit or push anything without explicit owner authorization.
- Never read out, print, paste, or commit backend/.env, API keys, recordings, or private transcripts.
- Never overwrite an existing .env; review/edit locally with the owner. Environment variables override it.
- Never edit PLAN.md or README.md unless asked. Preserve .claude/ and other agents' work.
- Do not merge the old prototype or replace React/Vite/SQLite with Next.js, vanilla JS, Postgres, or auth.
- Do not install Ollama or invent a LiteLLM model mapping. qwen3.8-fast is the teammate's existing proxy alias.
- Keep dependencies pinned. Do not run npm audit fix --force or upgrade Vite beyond 6 during setup.
- Preserve correction evidence checks, case-sensitive quiz answers, German umlauts and ß, and exclusion rules.
- Never bypass a failing provider by returning fake success. Report PASS, FAIL, or SKIPPED accurately.
- Run backend tests, frontend tests/build/types:check, provider checks, AND one actual spoken browser turn.
- Use one backend process. Per-session locks are in process; do not add multiple Uvicorn workers.
- Do not delete the database to fix setup. --reset-demo refuses if the demo profile has real sessions.
- Use a separate personal profile for actual speech; Demo learner is for labelled fixtures.

## Numbered setup (Linux)

All blocks run from repository root unless they use a subshell with cd.

### 1. Verify checkout and tools

```bash
git status --short
git branch --show-current
python3 --version
node --version
npm --version
```

Expected: tutor-v2, Python 3.10+, Node 22.11+, npm.
If dirty, preserve changes. Do not switch/reset automatically.
If a fresh clone is needed AFTER Amir pushes the branch:

```bash
git clone --branch tutor-v2 https://github.com/FINN-SCH/Hacktoberfest.git
cd Hacktoberfest
```

If branch missing remotely, ask the owner; never push a substitute.

### 2. Install into a repo-local venv

```bash
python3 -m venv backend/.venv
backend/.venv/bin/python -m pip install -r backend/requirements-dev.txt
backend/.venv/bin/python -m pip install -r backend/requirements-local-stt.txt
```

Expected: successful install; requirements-dev includes runtime requirements.
For hosted Groq, omit the last line. Do not copy a venv across operating systems.
Local STT needs CUDA 12 cuBLAS + cuDNN 9 for the pinned CTranslate2; see SETUP_GUIDE.md for exact Linux install/export commands.
No system ffmpeg is required. CPU int8 fallback is supported; it can be slower.

### 3. Set LOCAL configuration without overwriting secrets

```bash
if [ ! -f backend/.env ]; then cp backend/.env.example backend/.env; fi
```

Verify these values locally:
- LLM_BASE_URL=http://localhost:4000/v1
- LLM_MODEL=qwen3.8-fast; LLM_API_KEY=dummy; LLM_JSON_MODE=prompt
- LLM_EXTRA_JSON={"extra_body":{"chat_template_kwargs":{"enable_thinking":false}}}
- STT_PROVIDER=faster_whisper; STT_MODEL=large-v3-turbo; STT_DEVICE=auto
- TTS_PROVIDER=edge; EDGE_VOICE_EN=en-US-AndrewNeural; EDGE_VOICE_DE=de-DE-ConradNeural
- HOST=127.0.0.1 (default); PORT=5050; DB_PATH=tutor.db

Start the teammate's existing LiteLLM proxy, then:
```bash
curl --fail --silent --show-error http://localhost:4000/v1/models -H 'Authorization: Bearer dummy'
```

Expected: proxy responds; its configuration supplies qwen3.8-fast.
LLM_EXTRA_JSON is merged verbatim, NOT flattened like an SDK's extra_body argument.
If the proxy needs flat arguments, use {"chat_template_kwargs":{"enable_thinking":false}} instead.
Confirm which shape it accepts; never guess the underlying model from an alias.

HOSTED alternative: copy backend/.env.groq.example ONLY if .env does not exist; enter the owner's Groq key in BOTH LLM_API_KEY and GROQ_API_KEY locally.
Use LLM_BASE_URL=https://api.groq.com/openai/v1, LLM_MODEL=openai/gpt-oss-120b, LLM_JSON_MODE=json_schema,
LLM_EXTRA_JSON={"reasoning_effort":"low"}, STT_PROVIDER=groq, STT_MODEL=whisper-large-v3, TTS_PROVIDER=edge.
For open-weight TTS choose deepinfra with DEEPINFRA_API_KEY and TTS_MODEL=ResembleAI/chatterbox-multilingual.
Edge-TTS is a proprietary Microsoft cloud voice, not an open-weight or offline TTS model.
Team measurement on 2026-10-04: Groq free-tier gpt-oss-120b 8000 tokens/min, about 1.8K per turn (~4 turns/min).
Check actual account quota; space out calls. Reports, quizzes and analysis share LLM quota.

### 4. Install and build frontend

```bash
(cd frontend && npm ci && npm run build)
```

Expected: local VAD assets copied and dist/index.html generated. No credentials required.

### 5. Seed offline fixtures (stop the app first)

```bash
(cd backend && .venv/bin/python -m app.seed)
```

Expected: PASS, 3 German + 1 English ended demo sessions, no provider calls.
If already seeded, REFUSED + exit 1 is expected; do not treat this as a broken application.
Only if the owner wants fresh demo data:
```bash
(cd backend && .venv/bin/python -m app.seed --reset-demo)
```

Expected: demo fixtures replaced; real sessions preserved. If real practice exists under Demo learner, reset refuses.

### 6. Run verification

```bash
(cd backend && .venv/bin/python -m pytest -p no:cacheprovider --basetemp=.pytest_tmp2)
(cd frontend && npm test && npm run build && npm run types:check)
(cd backend && .venv/bin/python -m scripts.check_providers)
```

Expected: all tests/build/types pass. Probe prints configured models without keys, then PASS/FAIL/SKIPPED.
Only 429s get up to three retries with 20/40/60-second waits. Any FAIL returns exit 1.
Edge returns MP3, so STT is explicitly SKIPPED unless a compatible WAV is available.
A skip is NOT STT verification. To probe a supplied German recording:
```bash
(cd backend && .venv/bin/python -m scripts.check_providers --stt-wav /absolute/path/to/speech.wav)
```
The file must be mono PCM16 16000Hz WAV. No MP3 conversion or synthetic quality claims.

### 7. Launch

```bash
chmod +x start.sh
./start.sh
```

Expected: current frontend or rebuild; Uvicorn serves http://127.0.0.1:5050. Keep the terminal open.
The launcher does not install packages or choose providers. Ctrl+C stops it.

### 8. Browser acceptance checklist

- [ ] Chrome/Edge opens http://127.0.0.1:5050; /api/health returns JSON with status="ok".
- [ ] Select Demo learner: History has 4 labelled sessions and German reports have 3 ratings.
- [ ] German Analysis shows recurring verb-position/accusative topics and improving dative.
- [ ] Create a separate profile; choose German/A2/café; Check microphone & sound succeeds.
- [ ] Start, hear opening, say “Ich habe nach Berlin gegangen.”, pause.
- [ ] See transcript/correction; hear tutor; microphone resumes only after playback.
- [ ] End and open report. Short practice correctly has insufficient sample; ratings need >=5 eligible turns AND >=60s voiced.
- [ ] Quiz generates/grades; Not a mistake/Misheard exclusions affect evidence.
- [ ] Report exact commands, outputs, provider configuration names, and any skipped/failed verification; never keys.
- [ ] No commit/push unless explicitly authorized.

## Windows equivalents

Use SETUP_GUIDE.md's PowerShell block. Invoke backend/.venv/Scripts/python.exe directly; no activation required.
Set $env:npm_config_prefix='C:/Program Files/nodejs' and use npm.cmd.
Run pytest from backend with --basetemp=.pytest_tmp2; if inaccessible use a fresh .pytest_tmp2_local name and report it.
Launch: powershell -NoProfile -ExecutionPolicy Bypass -File .\start.ps1 (process-local policy only).
Do not install faster-whisper on Amir's machine for hosted verification.

## If X fails, do Y

- Missing venv/node_modules: run steps 2/4; do not patch application code.
- Microphone denied: allow browser/OS permission; use localhost or HTTPS; retry the audio check.
- VAD assets missing: npm ci then npm run build in frontend; check /vad/silero_vad_v5.onnx is not HTML.
- LLM unavailable/unknown model: check existing proxy and alias; do not invent its backend.
- Unsupported response_format: LOCAL uses prompt; Groq uses json_schema. No automatic downgrade.
- Invalid JSON: retry through the service once; preserve evidence checks and inspect the selected model/configuration.
- CUDA error: confirm CUDA 12/cuDNN 9; read CPU fallback warning; STT_DEVICE=cpu is explicit fallback.
- First local STT slow: wait for the model download and load; check network/cache space.
- 401: check key fields locally. Never paste .env or keys.
- 429: wait; check actual quota; do not loop requests rapidly.
- Edge voice failure: check network and venv python -m edge_tts --list-voices.
- STT SKIPPED: supply compatible --stt-wav or complete the required spoken browser turn.
- Port in use: stop your own previous server or change PORT; never kill unrelated processes.
- frontend_not_built 503: build frontend; launch from start script.
- Type drift: npm run types:generate; review generated.ts diff; run types:check. Never hand-edit it.
- Dirty checkout or seed collision: preserve data and ask the owner; never reset/delete to make tests pass.

## Repo map

- backend/app/__init__.py: application package.
- backend/app/main.py: FastAPI factory, lifespan, error envelopes, static SPA serving.
- backend/app/config.py: environment settings and provider defaults; reads backend/.env.
- backend/app/deps.py: per-request DB session, settings, and provider dependencies.
- backend/app/db.py: SQLite engine, tables, interrupted-turn recovery.
- backend/app/models.py: profiles, sessions, turns, mistakes, quizzes, analyses.
- backend/app/topics.py: fixed German/English topic IDs.
- backend/app/languages.py: languages, scenarios, openings, explanation language, spoken recasts.
- backend/app/seed.py: offline labelled demo data and guarded reset.
- backend/app/schemas/: API and LLM Pydantic contracts.
- backend/app/providers/: interfaces, factory, OpenAI-compatible LLM, STT and TTS adapters.
- backend/app/prompts/: tutor, report, quiz, analysis prompt builders.
- backend/app/services/validation.py: correction evidence matching/highlight offsets.
- backend/app/services/eligibility.py: single definition of eligible turns and active errors.
- backend/app/services/scoring.py: deterministic grammar/fluency, sample minimum.
- backend/app/services/turns.py: session creation, idempotent STT/analysis turns, TTS.
- backend/app/services/exclusions.py: Misheard and Not a mistake mutations.
- backend/app/services/errors.py: stable ApiError envelope.
- backend/app/services/reports.py: end/regenerate snapshots and evidence cutoffs.
- backend/app/services/quizzes.py: source selection, validation, deterministic grading.
- backend/app/services/analysis.py: topic/progress statistics and written snapshots.
- backend/app/routers/: thin /api HTTP endpoints; calls services.
- backend/scripts/check_providers.py: real provider probe with bounded rate-limit retries.
- backend/tests/: fake-provider, HTTP, scoring, evidence, seed, and probe tests.
- frontend/src/App.tsx: profile picker/creator and navigation.
- frontend/src/pages/: Talk, History, Report, Quiz, Analysis.
- frontend/src/components/: shared controls, scores, transcript and Unicode highlighting.
- frontend/src/audio/: VAD, sample-count timing, WAV encoding, playback, mic state machine.
- frontend/src/api/: typed client and generated.ts (from FastAPI OpenAPI).
- frontend/src/mocks/: reserved test mock directory.
- frontend/scripts/: local VAD assets, API type generation, optional fake-provider browser smoke test.
- start.sh / start.ps1: dependency/build checks and single-process application launch.
