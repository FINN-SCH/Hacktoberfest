/* English Voice Language Coach - Frontend Application */

// State
let appState = "idle"; // "idle" | "listening" | "thinking" | "speaking"
let isContinuousMode = false;
let currentScenario = "casual";
let currentVoice = "en-US-AndrewNeural";

let mediaRecorder = null;
let audioChunks = [];
let audioStream = null;
let audioCtx = null;
let analyser = null;
let dataArray = null;
let animFrameId = null;

// Speech Audio Queue
let audioQueue = [];
let isAudioPlaying = false;
let currentPlayingAudio = null;
let conversationHistory = [];

// Silence detection (VAD)
let silenceStartTime = null;
let speechDetected = false;
const SILENCE_TIMEOUT_MS = 1400;
const VAD_VOLUME_THRESHOLD = 0.035;

// DOM Elements
const orbWrapper = document.getElementById("orb-wrapper");
const orbLabel = document.getElementById("orb-label");
const statusDot = document.getElementById("status-dot");
const statusText = document.getElementById("status-text");
const userTranscript = document.getElementById("user-transcript");
const feedbackBanner = document.getElementById("feedback-banner");
const feedbackIcon = document.getElementById("feedback-icon");
const feedbackText = document.getElementById("feedback-text");
const coachResponse = document.getElementById("coach-response");
const canvasEl = document.getElementById("visualizer");
const canvasCtx = canvasEl.getContext("2d");
const continuousBtn = document.getElementById("continuous-btn");
const continuousLabel = document.getElementById("continuous-label");
const textInput = document.getElementById("text-input");
const scenarioSelect = document.getElementById("scenario-select");
const voiceSelect = document.getElementById("voice-select");

// Audio Tone Chimes
function playChime(kind) {
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.connect(gain);
    gain.connect(ctx.destination);

    const now = ctx.currentTime;
    if (kind === "start") {
      osc.frequency.setValueAtTime(523.25, now); // C5
      osc.frequency.exponentialRampToValueAtTime(659.25, now + 0.12); // E5
      gain.gain.setValueAtTime(0.06, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.18);
      osc.start(now);
      osc.stop(now + 0.18);
    } else if (kind === "stop") {
      osc.frequency.setValueAtTime(659.25, now);
      osc.frequency.exponentialRampToValueAtTime(440, now + 0.12);
      gain.gain.setValueAtTime(0.06, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.18);
      osc.start(now);
      osc.stop(now + 0.18);
    }
  } catch (e) {}
}

function setUIState(newState) {
  appState = newState;
  orbWrapper.className = "orb-wrapper " + (newState === "idle" ? "" : newState);
  statusDot.className = "status-dot " + (newState === "idle" ? "" : newState);

  if (newState === "idle") {
    orbLabel.textContent = isContinuousMode ? "LISTENING..." : "TAP TO SPEAK";
    statusText.textContent = isContinuousMode ? "HANDS-FREE ON" : "READY";
  } else if (newState === "listening") {
    orbLabel.textContent = "LISTENING...";
    statusText.textContent = "LISTENING";
  } else if (newState === "thinking") {
    orbLabel.textContent = "ANALYSING...";
    statusText.textContent = "COACH THINKING";
  } else if (newState === "speaking") {
    orbLabel.textContent = "TUTOR SPEAKING";
    statusText.textContent = "SPEAKING";
  }
}

// Waveform Visualizer
function drawVisualizer() {
  animFrameId = requestAnimationFrame(drawVisualizer);
  if (!analyser || !dataArray) return;

  analyser.getByteFrequencyData(dataArray);
  canvasCtx.clearRect(0, 0, canvasEl.width, canvasEl.height);

  const barWidth = (canvasEl.width / dataArray.length) * 2.2;
  let barHeight;
  let x = 0;

  for (let i = 0; i < dataArray.length; i++) {
    barHeight = (dataArray[i] / 255) * canvasEl.height * 0.85;

    const grad = canvasCtx.createLinearGradient(0, canvasEl.height, 0, 0);
    if (appState === "listening") {
      grad.addColorStop(0, "rgba(6, 182, 212, 0.2)");
      grad.addColorStop(1, "#06b6d4");
    } else if (appState === "speaking") {
      grad.addColorStop(0, "rgba(16, 185, 129, 0.2)");
      grad.addColorStop(1, "#10b981");
    } else {
      grad.addColorStop(0, "rgba(99, 102, 241, 0.2)");
      grad.addColorStop(1, "#6366f1");
    }

    canvasCtx.fillStyle = grad;
    canvasCtx.fillRect(x, canvasEl.height - barHeight, barWidth - 1, barHeight);
    x += barWidth + 1;
  }
}

async function ensureAudioContext() {
  if (!audioCtx) {
    audioCtx = new (window.AudioContext || window.webkitAudioContext)();
  }
  if (audioCtx.state === "suspended") {
    await audioCtx.resume();
  }
}

async function startRecording() {
  if (appState === "listening") return;
  await ensureAudioContext();

  try {
    audioStream = await navigator.mediaDevices.getUserMedia({
      audio: {
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true
      }
    });

    const source = audioCtx.createMediaStreamSource(audioStream);
    analyser = audioCtx.createAnalyser();
    analyser.fftSize = 64;
    dataArray = new Uint8Array(analyser.frequencyBinCount);
    source.connect(analyser);

    drawVisualizer();

    audioChunks = [];
    let mimeType = "audio/webm;codecs=opus";
    if (!MediaRecorder.isTypeSupported(mimeType)) {
      mimeType = MediaRecorder.isTypeSupported("audio/webm") ? "audio/webm" : "";
    }

    mediaRecorder = new MediaRecorder(audioStream, mimeType ? { mimeType } : {});
    mediaRecorder.ondataavailable = (e) => {
      if (e.data && e.data.size > 0) {
        audioChunks.push(e.data);
      }
    };

    mediaRecorder.start(100);
    setUIState("listening");
    playChime("start");

    userTranscript.classList.remove("empty");
    userTranscript.textContent = "Listening to your English...";

    speechDetected = false;
    silenceStartTime = null;

    if (isContinuousMode) {
      monitorContinuousVAD();
    }
  } catch (err) {
    console.error("Mic error:", err);
    userTranscript.textContent = "Microphone access denied: " + err.message;
    setUIState("idle");
  }
}

function monitorContinuousVAD() {
  if (appState !== "listening" || !isContinuousMode) return;

  if (analyser && dataArray) {
    analyser.getByteFrequencyData(dataArray);
    let sum = 0;
    for (let i = 0; i < dataArray.length; i++) sum += dataArray[i];
    const avg = sum / dataArray.length / 255;

    if (avg > VAD_VOLUME_THRESHOLD) {
      speechDetected = true;
      silenceStartTime = null;
    } else if (speechDetected) {
      if (!silenceStartTime) {
        silenceStartTime = Date.now();
      } else if (Date.now() - silenceStartTime > SILENCE_TIMEOUT_MS) {
        stopRecordingAndSubmit();
        return;
      }
    }
  }

  setTimeout(monitorContinuousVAD, 100);
}

function stopRecordingAndSubmit() {
  if (appState !== "listening" || !mediaRecorder) return;

  setUIState("thinking");
  playChime("stop");

  mediaRecorder.onstop = async () => {
    if (audioStream) {
      audioStream.getTracks().forEach(t => t.stop());
      audioStream = null;
    }

    if (audioChunks.length === 0) {
      userTranscript.textContent = "No audio recorded.";
      setUIState("idle");
      checkNextContinuousTurn();
      return;
    }

    const audioBlob = new Blob(audioChunks, { type: mediaRecorder.mimeType || "audio/webm" });
    await processAudioTurn(audioBlob);
  };

  try {
    mediaRecorder.stop();
  } catch (e) {}
}

async function processAudioTurn(audioBlob) {
  userTranscript.textContent = "Transcribing with Faster-Whisper...";

  try {
    const sttRes = await fetch("/api/stt", {
      method: "POST",
      headers: { "Content-Type": audioBlob.type || "audio/webm" },
      body: audioBlob
    });

    if (!sttRes.ok) throw new Error(`STT HTTP ${sttRes.status}`);
    const data = await sttRes.json();
    const query = (data.text || "").trim();

    if (!query) {
      userTranscript.textContent = "No clear English speech detected. Please speak again!";
      setUIState("idle");
      checkNextContinuousTurn();
      return;
    }

    userTranscript.textContent = `"${query}"`;
    await executeCoachTurn(query);
  } catch (err) {
    console.error("STT error:", err);
    userTranscript.textContent = "Transcription error: " + err.message;
    setUIState("idle");
    checkNextContinuousTurn();
  }
}

// Language Coach Execution & Feedback Parser
async function executeCoachTurn(userInput) {
  setUIState("thinking");
  coachResponse.textContent = "...";
  feedbackBanner.classList.add("empty");
  feedbackBanner.classList.remove("correct");
  feedbackText.textContent = "";

  conversationHistory.push({ role: "user", content: userInput });

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        messages: conversationHistory,
        topic: currentScenario,
        voice: currentVoice
      })
    });

    if (!res.ok) throw new Error(`LLM HTTP ${res.status}`);

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let rawOutput = "";
    let speechSentenceBuffer = "";
    audioQueue = [];

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;

      const raw = decoder.decode(value, { stream: true });
      const lines = raw.split("\n\n");

      for (const line of lines) {
        if (!line.startsWith("data: ")) continue;
        const jsonStr = line.slice(6).trim();
        if (jsonStr === "[DONE]") break;

        try {
          const parsed = JSON.parse(jsonStr);
          if (parsed.delta) {
            rawOutput += parsed.delta;
            parseAndRenderCoachOutput(rawOutput);

            // Stream spoken reply chunks into TTS queue (contains verbal correction + reply)
            let spokenPart = "";
            if (rawOutput.includes("SPOKEN:")) {
              spokenPart = rawOutput.split("SPOKEN:")[1] || "";
            } else if (rawOutput.includes("REPLY:")) {
              spokenPart = rawOutput.split("REPLY:")[1] || "";
            }

            if (spokenPart) {
              speechSentenceBuffer += parsed.delta;

              if (/[.!?]\s+$/.test(speechSentenceBuffer) || (speechSentenceBuffer.length > 70 && /[,;]\s+$/.test(speechSentenceBuffer))) {
                const cleanChunk = speechSentenceBuffer
                  .replace(/CORRECTION:[\s\S]*?SPOKEN:/i, "")
                  .replace(/FEEDBACK:[\s\S]*?REPLY:/i, "")
                  .replace(/SPOKEN:/i, "")
                  .replace(/REPLY:/i, "")
                  .trim();
                speechSentenceBuffer = "";
                if (cleanChunk) {
                  queueTTS(cleanChunk);
                }
              }
            }
          }
        } catch (e) {}
      }
    }

    // Flush any leftover sentence buffer for speech
    if (speechSentenceBuffer.trim()) {
      const cleanChunk = speechSentenceBuffer
        .replace(/CORRECTION:[\s\S]*?SPOKEN:/i, "")
        .replace(/FEEDBACK:[\s\S]*?REPLY:/i, "")
        .replace(/SPOKEN:/i, "")
        .replace(/REPLY:/i, "")
        .trim();
      if (cleanChunk) {
        queueTTS(cleanChunk);
      }
    }

    // Final clean display and history storage
    parseAndRenderCoachOutput(rawOutput, true);

    if (audioQueue.length === 0 && !isAudioPlaying) {
      setUIState("idle");
      checkNextContinuousTurn();
    }
  } catch (err) {
    console.error("Coach error:", err);
    coachResponse.textContent = "Error communicating with the coach: " + err.message;
    setUIState("idle");
    checkNextContinuousTurn();
  }
}

function parseAndRenderCoachOutput(raw, isFinal = false) {
  let correction = "";
  let spoken = "";

  if (raw.includes("CORRECTION:") && raw.includes("SPOKEN:")) {
    const parts = raw.split("SPOKEN:");
    correction = parts[0].replace("CORRECTION:", "").trim();
    spoken = parts[1].trim();
  } else if (raw.includes("FEEDBACK:") && raw.includes("REPLY:")) {
    const parts = raw.split("REPLY:");
    correction = parts[0].replace("FEEDBACK:", "").trim();
    spoken = parts[1].trim();
  } else if (raw.includes("CORRECTION:")) {
    correction = raw.replace("CORRECTION:", "").trim();
  } else if (raw.includes("FEEDBACK:")) {
    correction = raw.replace("FEEDBACK:", "").trim();
  } else {
    spoken = raw.trim();
  }

  // Render Correction / Feedback Banner
  if (correction) {
    feedbackBanner.classList.remove("empty");
    feedbackText.textContent = correction;

    const lower = correction.toLowerCase();
    const isFlawless = lower.includes("none") || lower.includes("perfect") || lower.includes("flawless") || lower.includes("spot on") || lower.includes("great english");

    if (isFlawless) {
      feedbackBanner.classList.add("correct");
      feedbackIcon.textContent = "✅";
    } else {
      feedbackBanner.classList.remove("correct");
      feedbackIcon.textContent = "💡";
    }
  }

  // Render Coach Response
  if (spoken) {
    coachResponse.textContent = spoken;
  }

  if (isFinal && spoken) {
    conversationHistory.push({ role: "assistant", content: spoken });
  }
}

// Queue TTS Audio chunks for consecutive seamless playback
function queueTTS(sentence) {
  if (!sentence) return;
  const audioUrl = `/api/tts?text=${encodeURIComponent(sentence)}&voice=${encodeURIComponent(currentVoice)}`;
  audioQueue.push({ url: audioUrl, text: sentence });

  if (!isAudioPlaying) {
    playNextAudio();
  }
}

async function playNextAudio() {
  if (audioQueue.length === 0) {
    isAudioPlaying = false;
    setUIState("idle");
    checkNextContinuousTurn();
    return;
  }

  isAudioPlaying = true;
  setUIState("speaking");
  const item = audioQueue.shift();

  try {
    currentPlayingAudio = new Audio(item.url);
    currentPlayingAudio.onended = () => {
      currentPlayingAudio = null;
      playNextAudio();
    };
    currentPlayingAudio.onerror = () => {
      console.warn("TTS chunk playback error:", item.text);
      currentPlayingAudio = null;
      playNextAudio();
    };
    await currentPlayingAudio.play();
  } catch (e) {
    console.warn("Play error:", e);
    playNextAudio();
  }
}

function checkNextContinuousTurn() {
  if (isContinuousMode && appState === "idle") {
    setTimeout(() => {
      if (isContinuousMode && appState === "idle") {
        startRecording();
      }
    }, 700);
  }
}

// User Actions
function handleOrbClick() {
  if (appState === "speaking" && currentPlayingAudio) {
    currentPlayingAudio.pause();
    currentPlayingAudio = null;
    audioQueue = [];
    isAudioPlaying = false;
    setUIState("idle");
    return;
  }

  if (appState === "idle") {
    startRecording();
  } else if (appState === "listening") {
    stopRecordingAndSubmit();
  }
}

function toggleContinuousMode() {
  isContinuousMode = !isContinuousMode;
  continuousBtn.classList.toggle("active", isContinuousMode);
  continuousLabel.textContent = isContinuousMode ? "Hands-Free: ON" : "Hands-Free: OFF";

  if (isContinuousMode && appState === "idle") {
    startRecording();
  }
}

function changeScenario(val) {
  currentScenario = val;
  console.log("Scenario changed to:", val);
}

function changeVoice(val) {
  currentVoice = val;
  console.log("Voice changed to:", val);
}

function quickSend(text) {
  if (appState === "listening" && mediaRecorder) {
    try { mediaRecorder.stop(); } catch (e) {}
  }
  userTranscript.classList.remove("empty");
  userTranscript.textContent = `"${text}"`;
  executeCoachTurn(text);
}

function handleFormSubmit(e) {
  e.preventDefault();
  const text = textInput.value.trim();
  if (!text) return;
  textInput.value = "";
  quickSend(text);
}

// Spacebar Key listener
window.addEventListener("keydown", (e) => {
  if (e.code === "Space" && e.target !== textInput) {
    e.preventDefault();
    handleOrbClick();
  }
});

window.addEventListener("DOMContentLoaded", () => {
  console.log("English Voice Coach ready.");
});
