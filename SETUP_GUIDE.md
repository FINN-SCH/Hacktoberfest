# Setup guide: Voice Language Tutor

This guide sets up branch `tutor-v2` on Klabundo's Linux machine.
FastAPI serves the built React app on **http://127.0.0.1:5050**.
Use the local profile unless you deliberately choose hosted Groq.
For coding agents, [AGENTS.md](AGENTS.md) and [GEMINI.md](GEMINI.md) contain the same instructions.

## 1. Check prerequisites

Run in a terminal:

```bash
git --version
python3 --version
node --version
npm --version
```

Expected: Git, Python **3.10+** with venv/pip, Node **22.11+**, npm.
Python 3.13.5 and Node 22.11 were used on Windows; Linux local inference still needs verification on your GPU.
If Python cannot create a venv, install your distribution's matching `python3-venv` package.
Keep Vite 6 pinned. Do not replace the project with the prototype or install Ollama.

Use Chrome or Edge on the same computer as the server. Microphone access needs localhost or HTTPS.
Internet access is needed for npm/pip installation, the first Whisper model download, and **Edge-TTS**.
Edge voices are a proprietary Microsoft cloud service; they are not offline or open-weight.
The hosted profile also sends audio/text to Groq and optionally DeepInfra.
The app has no authentication: use localhost for this setup.

Local STT needs an NVIDIA driver and, for the pinned CTranslate2 4.6.0, CUDA 12 cuBLAS and cuDNN 9.
System `ffmpeg` is not required: browser uploads are PCM WAV; faster-whisper uses PyAV's bundled decoding libraries.
See the [faster-whisper requirements](https://github.com/SYSTRAN/faster-whisper#requirements).

## 2. Get the correct branch

Wait until Amir has pushed `tutor-v2`. The repository is private; use your existing GitHub access.

New clone:

```bash
git clone --branch tutor-v2 https://github.com/FINN-SCH/Hacktoberfest.git
cd Hacktoberfest
git branch --show-current
```

Expected: `tutor-v2`. If the remote branch does not exist, ask Amir; do not create a substitute from main.

Existing clone: run `git status --short` first. If it shows changes, preserve them and resolve with the owner before switching.
For a clean clone:

```bash
git fetch origin
git switch tutor-v2
git pull --ff-only origin tutor-v2
```

If `git switch` cannot find the local branch but `origin/tutor-v2` exists, use:
`git switch --track origin/tutor-v2`. Do not merge the old `voice-language-tutor` branch into this branch.

## 3. Install backend dependencies

All remaining Linux commands start at the **repository root**, unless a block contains its own `cd`.

```bash
python3 -m venv backend/.venv
backend/.venv/bin/python -m pip install -r backend/requirements.txt
backend/.venv/bin/python -m pip install -r backend/requirements-dev.txt
# LOCAL profile only:
backend/.venv/bin/python -m pip install -r backend/requirements-local-stt.txt
```

Expected: successful installs. Hosted Groq does not need faster-whisper or CUDA.
Do not use sudo pip. Do not copy a Windows venv to Linux.

For local GPU inference, check `nvidia-smi`. A working driver alone does not prove cuDNN is available.
If the CUDA libraries are missing, one supported Linux venv option is:

```bash
backend/.venv/bin/python -m pip install nvidia-cublas-cu12 'nvidia-cudnn-cu12==9.*'
export LD_LIBRARY_PATH="$(backend/.venv/bin/python -c 'import os; import nvidia.cublas.lib; import nvidia.cudnn.lib; print(os.path.dirname(nvidia.cublas.lib.__file__) + ":" + os.path.dirname(nvidia.cudnn.lib.__file__))')${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
```

Set this variable in the same terminal that launches `start.sh`.
`STT_DEVICE=auto` tries CUDA with `int8_float16`, then makes one CPU `int8` fallback on failure.
A logged CPU fallback is a working but slower path. Use `STT_DEVICE=cpu` for explicit CPU operation.
The first local transcription downloads `large-v3-turbo`; allow time and disk space.

## 4. Choose ONE provider profile

Do not overwrite an existing `backend/.env`. Inspect/edit it locally; never paste its keys into chat or commit it.
Environment variables override the file. Stop and restart the server after changes.

### A. LOCAL: Klabundo's existing LiteLLM + faster-whisper + Edge

```bash
if [ ! -f backend/.env ]; then
  cp backend/.env.example backend/.env
else
  printf '%s\n' 'backend/.env already exists; preserve and review it locally.'
fi
```

Confirm these values in `backend/.env`:

```dotenv
HOST=127.0.0.1
PORT=5050
DB_PATH=tutor.db
LLM_BASE_URL=http://localhost:4000/v1
LLM_MODEL=qwen3.8-fast
LLM_API_KEY=dummy
LLM_JSON_MODE=prompt
LLM_EXTRA_JSON={"extra_body":{"chat_template_kwargs":{"enable_thinking":false}}}
STT_PROVIDER=faster_whisper
STT_MODEL=large-v3-turbo
STT_DEVICE=auto
TTS_PROVIDER=edge
EDGE_VOICE_EN=en-US-AndrewNeural
EDGE_VOICE_DE=de-DE-ConradNeural
```

Start your **existing** LiteLLM proxy with its existing model configuration. This repo does not install the LLM backend.
Check it:

```bash
curl --fail --silent --show-error http://localhost:4000/v1/models -H 'Authorization: Bearer dummy'
```

Expected: JSON model list including the configured alias, or confirmation from your proxy config.
Connection refused means the proxy is not running on that address. An unknown model means the alias/config is wrong.
Do not replace the model/backend on guesswork.

`LLM_EXTRA_JSON` is merged **verbatim** into the HTTP JSON body.
The default above reproduces the prototype's literal top-level `extra_body` key.
Some backends instead require the flattened shape already noted in `.env.example`:

```dotenv
LLM_EXTRA_JSON={"chat_template_kwargs":{"enable_thinking":false}}
```

Choose the shape supported by the existing proxy/backend. The adapter does not automatically change it.
`qwen3.8-fast` is a proxy alias: verify what model and license it actually fronts.
Prompt mode requests a single JSON object without assuming backend support for `json_schema`.

### B. HOSTED: Groq LLM + Groq Whisper

If `backend/.env` does not exist:

```bash
cp -n backend/.env.groq.example backend/.env
```

In your editor set **both** `LLM_API_KEY` and `GROQ_API_KEY` to your Groq key. Do not leave placeholders.
Use:

```dotenv
HOST=127.0.0.1
PORT=5050
DB_PATH=tutor.db
LLM_BASE_URL=https://api.groq.com/openai/v1
LLM_MODEL=openai/gpt-oss-120b
LLM_JSON_MODE=json_schema
LLM_EXTRA_JSON={"reasoning_effort":"low"}
STT_PROVIDER=groq
STT_MODEL=whisper-large-v3
GROQ_BASE_URL=https://api.groq.com/openai/v1
TTS_PROVIDER=edge
```

The team's **2026-10-04 measured free-tier limit** was 8,000 tokens/minute for gpt-oss-120b.
A turn used about 1.8K tokens: roughly **4 turns/minute**, with reports/quizzes/analysis also consuming tokens.
This is account-specific evidence, not a guaranteed current quota. Check your Groq account limits.
Space out checks; local LiteLLM or sufficient paid quota is preferable for a fast live demo.

For open-weight TTS via DeepInfra, change only the TTS settings and add your key locally:

```dotenv
TTS_PROVIDER=deepinfra
DEEPINFRA_API_KEY=replace-in-your-editor
DEEPINFRA_BASE_URL=https://api.deepinfra.com/v1/inference
TTS_MODEL=ResembleAI/chatterbox-multilingual
```

Chatterbox is the open-weight path; Edge remains the easier default.
DeepInfra credentials and synthesis must be verified on your account. No automatic provider failover occurs.

## 5. Build the frontend

```bash
(cd frontend && npm ci && npm run build)
```

Expected: VAD/runtime assets copied, TypeScript succeeds, Vite produces `frontend/dist/index.html`.
Assets are served locally under `/vad/`; no CDN is needed during conversation.

## 6. Add demo data without calling an API

Stop the app before seeding/resetting. Run:

```bash
(cd backend && .venv/bin/python -m app.seed)
```

Expected: `PASS demo profile ...: 3 German + 1 English ended sessions; no provider calls.`
A second run prints `REFUSED Demo data already exists...` and exits 1 without adding rows.
The fixtures have ratings, recurring topics and an improving topic. They are labelled **Demo data** in the UI.
Choose **Demo learner** to inspect them; create a separate personal profile for actual practice.

To replace demo data deliberately:

```bash
(cd backend && .venv/bin/python -m app.seed --reset-demo)
```

Only labelled demo sessions, their dependent rows, and the demo profile are replaced.
Other profiles and real sessions are preserved. Reset refuses if Demo learner contains non-demo sessions.
Never delete `tutor.db` as a shortcut. Relative `DB_PATH` values resolve inside `backend/`.

## 7. Verify before starting a conversation

```bash
(cd backend && .venv/bin/python -m pytest -p no:cacheprovider --basetemp=.pytest_tmp2)
(cd frontend && npm test && npm run build && npm run types:check)
(cd backend && .venv/bin/python -m scripts.check_providers)
```

Expected: tests pass, frontend builds, types match, provider checks print `PASS` or explained `SKIPPED` lines.
Any `FAIL` makes the provider command exit 1. It retries only 429s, at 20/40/60 seconds, then fails.
The direct form also works: `(cd backend && .venv/bin/python scripts/check_providers.py)`.

**Edge produces MP3**, so the default probe says `SKIPPED STT/... no compatible TTS WAV`.
That is not a successful STT test. The browser's spoken turn below is still required.
To check STT separately using an existing German speech recording:

```bash
(cd backend && .venv/bin/python -m scripts.check_providers --stt-wav /absolute/path/to/speech-16k-mono-pcm16.wav)
```

The script never converts MP3 or installs ffmpeg. A TTS WAV with another encoding/rate is also explicitly skipped.
Synthetic audio checks prove plumbing, not preservation of learner mistakes. Try deliberate mistakes with your own voice.

## 8. Launch and verify the UI

```bash
chmod +x start.sh
./start.sh
```

Expected: `Frontend build is current.` or a successful rebuild, then `Tutor URL: http://127.0.0.1:5050` and Uvicorn startup.
Keep this terminal open; Ctrl+C stops the server. The launcher uses one backend process and does not install dependencies.
It rebuilds when source/config/assets are newer than dist or required VAD assets are missing.

Open **http://127.0.0.1:5050** in Chrome/Edge:
1. Select Demo learner; open History and a German report. Check three ratings and the Demo data badge.
2. Open Analysis, German. Check recurring verb-position/accusative topics and improving dative.
3. Create a separate profile. Select German / A2 / café in Talk.
4. Click **Check microphone & sound**, allow microphone access, and verify you hear the tone.
5. Start, listen to the opening, then say “Ich habe nach Berlin gegangen.”
6. Pause. Expect a transcript, correction card, spoken reply, and resumed listening.
7. End; inspect the report. A short test correctly shows insufficient speech for ratings.
8. For scored practice, speak at least five substantive eligible turns and 60 seconds of voiced speech.
9. Exclude a wrong correction or misheard turn; check scores and stale-feedback labels. Try Quiz.
10. Written Analysis unlocks after two ended sessions; use Refresh if generation is still finishing.

## Windows setup (PowerShell)

Run from the repository root after checking out `tutor-v2`. Run each command separately and stop if it fails.
For this Windows machine use the hosted profile; do not install local STT just to run the tests.

```powershell
python -m venv backend/.venv
backend/.venv/Scripts/python.exe -m pip install -r backend/requirements-dev.txt
if (-not (Test-Path backend/.env)) { Copy-Item backend/.env.groq.example backend/.env }
# Enter both Groq key fields in backend/.env using your editor.
$env:npm_config_prefix = 'C:/Program Files/nodejs'
$env:npm_config_cache = "$env:TEMP/tutor-v2-npm"
Push-Location frontend
npm.cmd ci
npm.cmd test
npm.cmd run build
npm.cmd run types:check
Pop-Location
Push-Location backend
.venv/Scripts/python.exe -m pytest -p no:cacheprovider --basetemp=.pytest_tmp2
.venv/Scripts/python.exe -m app.seed
.venv/Scripts/python.exe -m scripts.check_providers
Pop-Location
powershell -NoProfile -ExecutionPolicy Bypass -File .\start.ps1
```

The last command allows this launcher for that child process only; it does not change your machine-wide execution policy.
Use `npm.cmd` to avoid PowerShell's npm.ps1 execution-policy issue.
If a shared pytest temp folder gives Access denied, use a new ignored name such as `.pytest_tmp2_local`; do not change ownership or delete another agent's test files.

## Troubleshooting

| Symptom | Do this |
|---|---|
| Microphone denied or absent | Allow microphone for 127.0.0.1, check OS privacy settings, use Chrome/Edge and localhost/HTTPS, then retry the audio check. |
| VAD/model/WASM 404 or detector stuck loading | Run `npm ci` then `npm run build` in frontend; restart and reload. Check `/vad/silero_vad_v5.onnx` returns a file, not HTML. |
| LLM connection refused | Start the existing LiteLLM proxy on port 4000; check `/v1/models`. |
| Unknown model or 400 | Check model alias and `LLM_EXTRA_JSON` against the proxy configuration; do not assume SDK-style flattening. |
| JSON schema unsupported | Use `LLM_JSON_MODE=prompt` for the local profile. Keep `json_schema` for the verified Groq profile. No automatic downgrade happens. |
| JSON output fails validation | Retry once through the UI. Check language/model configuration. Do not remove evidence validation to force a pass. |
| Groq 401 / authentication | Check both key fields locally. Do not print or share them. |
| Groq 429 | Let the probe back off; pause other calls. Check account limits before the demo. |
| CUDA/cuDNN missing or GPU memory exhausted | Confirm CUDA 12/cuDNN 9 and available VRAM. Read the logged CPU fallback; try `STT_DEVICE=cpu` if needed. |
| First local STT is slow | Wait for model download/load; confirm network/cache space. CPU inference is slower than GPU. |
| Edge TTS fails | Confirm network access; run `python -m edge_tts --list-voices` in the venv. Use the configured en-US-AndrewNeural/de-DE-ConradNeural voices. |
| Provider check skips STT | Expected for Edge MP3. Supply `--stt-wav` or verify one browser-spoken turn. |
| Address already in use | Stop your previous tutor process, or set `PORT=5051` in .env and open that port. Do not kill an unrelated process. |
| `frontend_not_built` / 503 | Build frontend and relaunch through start.sh/start.ps1. |
| Type drift | Run `npm run types:generate`, review the diff, then `npm run types:check`. Do not hand-edit generated.ts. |
| Seed reset refused | Preserve real practice; use a separate profile. Never delete the database to bypass the refusal. |
| Script has CRLF / permission denied | Refresh from Git with .gitattributes applied; run `chmod +x start.sh` or `bash start.sh`. |

For frontend development only, run `npm run dev` in frontend while the backend runs on 5050; Vite proxies `/api`.
If you choose another backend port, update the local Vite proxy deliberately. Production uses one origin and needs no proxy changes.
