/* Voice Language Coach & Quiz Tutor - Multi-Language Frontend Application */

// Language & Locale Configurations
const LANG_DATA = {
  en: {
    name: "English",
    flag: "🇬🇧",
    defaultVoice: "en-US-AndrewNeural",
    voices: [
      { id: "en-US-AndrewNeural", name: "Andrew (US · Natural & Warm)" },
      { id: "en-US-AvaNeural", name: "Ava (US · Clear & Expressive)" },
      { id: "en-US-BrianNeural", name: "Brian (US · Deep & Calm)" },
      { id: "en-US-EmmaNeural", name: "Emma (US · Cheerful)" },
      { id: "en-GB-RyanNeural", name: "Ryan (UK · Articulate)" },
      { id: "en-GB-SoniaNeural", name: "Sonia (UK · Bright)" }
    ],
    greeting: "Hello Jonathan! I am your English conversation coach. What would you like to discuss today?",
    starters: [
      { label: "Job interview practice", text: "Hi! Can you help me practice for a tech job interview?" },
      { label: "Check my grammar", text: "Yesterday I go to the supermarket and buyed some apples." },
      { label: "Fluency advice", text: "What are your top three tips for improving my English fluency?" },
      { label: "Tech discussion", text: "Let us have a debate about artificial intelligence and system architecture." }
    ],
    placeholder: "Type a sentence or prompt to practice...",
    emptyTranscript: "Click the microphone or press Spacebar to start speaking.",
    listeningText: "Listening to your English...",
    connectingText: "Connecting to coach...",
    voiceTest: "Hello Jonathan! Your neural voice output is functioning smoothly on the RTX 5090."
  },
  de: {
    name: "Deutsch",
    flag: "🇩🇪",
    defaultVoice: "de-DE-ConradNeural",
    voices: [
      { id: "de-DE-ConradNeural", name: "Conrad (DE · Warm & Klar)" },
      { id: "de-DE-KatjaNeural", name: "Katja (DE · Natürlich & Freundlich)" },
      { id: "de-DE-KillianNeural", name: "Killian (DE · Dynamisch)" },
      { id: "de-DE-FlorianMultilingualNeural", name: "Florian (DE · Vielseitig)" },
      { id: "de-DE-SeraphinaMultilingualNeural", name: "Seraphina (DE · Sanft)" },
      { id: "de-DE-AmalaNeural", name: "Amala (DE · Ausdrucksstark)" }
    ],
    greeting: "Hallo Jonathan! Ich bin dein Deutsch-Konversations-Coach. Worüber möchtest du heute sprechen?",
    starters: [
      { label: "Bewerbungstraining", text: "Hallo! Kannst du mir helfen, für ein Vorstellungsgespräch zu üben?" },
      { label: "Grammatik prüfen", text: "Gestern ich habe gegangen in die Stadt und ein Buch gekauft." },
      { label: "Tipps für fließendes Deutsch", text: "Was sind deine besten Tipps, um mein Deutsch zu verbessern?" },
      { label: "Tech-Diskussion", text: "Lass uns über künstliche Intelligenz und moderne Systemarchitektur sprechen." }
    ],
    placeholder: "Satz oder Frage zum Üben eingeben...",
    emptyTranscript: "Mikrofon anklicken oder Leertaste drücken, um zu sprechen.",
    listeningText: "Höre dir auf Deutsch zu...",
    connectingText: "Verbinde mit dem Coach...",
    voiceTest: "Hallo Jonathan! Deine neuronale Sprachausgabe läuft einwandfrei auf der RTX 5090."
  },
  es: {
    name: "Español",
    flag: "🇪🇸",
    defaultVoice: "es-ES-AlvaroNeural",
    voices: [
      { id: "es-ES-AlvaroNeural", name: "Álvaro (ES · Natural)" },
      { id: "es-ES-ElviraNeural", name: "Elvira (ES · Clara y Expresiva)" },
      { id: "es-ES-XimenaNeural", name: "Ximena (ES · Amable)" }
    ],
    greeting: "¡Hola Jonathan! Soy tu tutor de conversación en español. ¿De qué te gustaría hablar hoy?",
    starters: [
      { label: "Práctica de entrevista", text: "¡Hola! ¿Puedes ayudarme a practicar para una entrevista técnica?" },
      { label: "Comprobar gramática", text: "Ayer yo he ido al mercado y compré unas manzanas frescas." },
      { label: "Consejos de fluidez", text: "¿Cuáles son tus mejores consejos para hablar español con más soltura?" },
      { label: "Charla técnica", text: "Tengamos un debate sobre inteligencia artificial y arquitectura de software." }
    ],
    placeholder: "Escribe una frase o tema para practicar...",
    emptyTranscript: "Haz clic en el micrófono o presiona Espacio para comenzar a hablar.",
    listeningText: "Escuchando tu español...",
    connectingText: "Conectando con el tutor...",
    voiceTest: "¡Hola Jonathan! Tu síntesis de voz neuronal funciona perfectamente en la RTX 5090."
  },
  fr: {
    name: "Français",
    flag: "🇫🇷",
    defaultVoice: "fr-FR-HenriNeural",
    voices: [
      { id: "fr-FR-HenriNeural", name: "Henri (FR · Chaleureux)" },
      { id: "fr-FR-DeniseNeural", name: "Denise (FR · Articulée)" },
      { id: "fr-FR-EloiseNeural", name: "Eloise (FR · Naturelle)" },
      { id: "fr-FR-RemyMultilingualNeural", name: "Remy (FR · Polyvalent)" },
      { id: "fr-FR-VivienneMultilingualNeural", name: "Vivienne (FR · Douce)" }
    ],
    greeting: "Bonjour Jonathan ! Je suis ton coach de conversation en français. De quoi aimerais-tu parler aujourd'hui ?",
    starters: [
      { label: "Entraînement entretien", text: "Bonjour ! Peux-tu m'entraîner pour un entretien technique ?" },
      { label: "Vérifier ma grammaire", text: "Hier je suis allé au magasin et j'ai acheté des pommes." },
      { label: "Conseils d'aisance", text: "Quels sont tes meilleurs conseils pour améliorer mon expression orale ?" },
      { label: "Discussion technique", text: "Débattons sur l'intelligence artificielle et l'architecture logicielle." }
    ],
    placeholder: "Tapez une phrase ou un sujet pour vous entraîner...",
    emptyTranscript: "Cliquez sur le micro ou appuyez sur Espace pour parler.",
    listeningText: "Écoute de votre français...",
    connectingText: "Connexion au coach...",
    voiceTest: "Bonjour Jonathan ! La synthèse vocale neuronale fonctionne à merveille sur la RTX 5090."
  },
  it: {
    name: "Italiano",
    flag: "🇮🇹",
    defaultVoice: "it-IT-DiegoNeural",
    voices: [
      { id: "it-IT-DiegoNeural", name: "Diego (IT · Naturale)" },
      { id: "it-IT-ElsaNeural", name: "Elsa (IT · Espressiva)" },
      { id: "it-IT-IsabellaNeural", name: "Isabella (IT · Vivace)" },
      { id: "it-IT-GiuseppeMultilingualNeural", name: "Giuseppe (IT · Caldo)" }
    ],
    greeting: "Ciao Jonathan! Sono il tuo tutor di conversazione in italiano. Di cosa vorresti parlare oggi?",
    starters: [
      { label: "Pratica colloquio", text: "Ciao! Puoi aiutarmi a fare pratica per un colloquio di lavoro?" },
      { label: "Controlla la grammatica", text: "Ieri sono andato in centro e ho comprato dei libri." },
      { label: "Consigli di fluidità", text: "Quali sono i tuoi migliori consigli per migliorare il mio italiano?" },
      { label: "Discussione tecnica", text: "Facciamo una discussione sull'intelligenza artificiale e l'architettura software." }
    ],
    placeholder: "Scrivi una frase per esercitarti...",
    emptyTranscript: "Fai clic sul microfono o premi Spazio per parlare.",
    listeningText: "Ascolto del tuo italiano...",
    connectingText: "Connessione al tutor...",
    voiceTest: "Ciao Jonathan! La sintesi vocale neurale funziona senza problemi sulla RTX 5090."
  }
};

const UI_TRANSLATIONS = {
  en: {
    brandTitle: "Language Coach",
    brandSubtitle: "Real-Time Conversation Practice & Feedback",
    tabVoice: "Conversation",
    tabQuiz: "Practice Quiz",
    tabAnalysis: "Analysis",
    tabSettings: "Settings",
    tapToSpeak: "Tap to speak",
    listening: "Listening...",
    thinking: "Processing...",
    speaking: "Coach speaking...",
    ready: "Ready",
    handsFreeOn: "Hands-Free: ON",
    handsFreeOff: "Hands-Free: OFF",
    pressSpace: "Press Space to toggle microphone",
    quizTitle: "Practice Your Weaknesses",
    quizSubtitle: "Targeted quiz questions generated strictly from your real conversation mistakes.",
    quizFresh: "Fresh Questions",
    quizEmptyTitle: "No active mistakes yet",
    quizEmptyDesc: "Talk in Conversation mode. Any grammar or vocabulary slip will automatically turn into a personalized practice quiz here.",
    quizGoConv: "Go to Conversation",
    analysisTitle: "Cross-Session Analysis",
    analysisSubtitle: "Long-term tracking of grammar accuracy, recurring patterns, and fluency trends.",
    kpiAccLabel: "Error-Free Turns",
    kpiAccSub: "Overall grammatical consistency",
    kpiTurnsLabel: "Spoken Turns",
    kpiErrorsLabel: "Active Corrections",
    kpiErrorsSub: "Excluding dismissed slips",
    coachDiagnosisTitle: "Coach Diagnosis & Recommendations",
    topicFreqTitle: "Mistake Frequency by Grammar Topic",
    thTopic: "Topic",
    thErrors: "Errors",
    thShare: "Share",
    thSessions: "Sessions",
    thLastSeen: "Last Seen",
    recurringTitle: "Recurring Slips",
    settingsTitle: "Settings & System Status",
    settingsSubtitle: "Hardware configuration, model parameters, and storage management.",
    settingsCheck: "Check",
    pipeTitle: "Local Pipeline Infrastructure",
    settingsLangTitle: "Language, Voice & Scenario Settings",
    lblPracticeLang: "Practice Language",
    lblVoice: "Active Voice",
    lblScenario: "Active Scenario",
    lblUILang: "Interface Language",
    btnTestVoice: "Test Voice Output",
    testVoiceTip: "Synthesizes a short test sample via Edge-TTS and plays back locally.",
    dataMgmtTitle: "Data Management",
    clearHistoryHeading: "Clear Conversation History & Database",
    clearHistoryDesc: "Deletes all spoken turns, mistake logs, quiz records, and aggregated analytics from tutor.db.",
    btnClearHistory: "Clear History",
    scenarioCasual: "Casual Conversation",
    scenarioInterview: "Job Interview Practice",
    scenarioTech: "Tech & Architecture",
    scenarioTravel: "Travel & Daily Life",
    scenarioGrammar: "Grammar Focus & Drills"
  },
  de: {
    brandTitle: "Sprach-Coach",
    brandSubtitle: "Echtzeit-Sprachtraining & Grammatik-Feedback",
    tabVoice: "Konversation",
    tabQuiz: "Übungs-Quiz",
    tabAnalysis: "Analyse",
    tabSettings: "Einstellungen",
    tapToSpeak: "Tippen zum Sprechen",
    listening: "Höre zu...",
    thinking: "Verarbeite...",
    speaking: "Coach spricht...",
    ready: "Bereit",
    handsFreeOn: "Freisprechen: AN",
    handsFreeOff: "Freisprechen: AUS",
    pressSpace: "Leertaste drücken, um Mikrofon umzuschalten",
    quizTitle: "Schwachstellen gezielt üben",
    quizSubtitle: "Interaktive Quiz-Fragen, die exakt aus deinen realen Sprachfehlern generiert werden.",
    quizFresh: "Neue Fragen",
    quizEmptyTitle: "Noch keine aktiven Fehler",
    quizEmptyDesc: "Sprich im Konversations-Modus. Jeder Grammatik- oder Wortfehler wird hier automatisch zu einer maßgeschneiderten Übung.",
    quizGoConv: "Zur Konversation",
    analysisTitle: "Lernfortschritt & Analyse",
    analysisSubtitle: "Langzeit-Auswertung deiner Grammatik-Genauigkeit, wiederkehrenden Muster und Sprachflüssigkeit.",
    kpiAccLabel: "Fehlerfreie Runden",
    kpiAccSub: "Grammatikalische Zuverlässigkeit",
    kpiTurnsLabel: "Gesprochene Sätze",
    kpiErrorsLabel: "Aktive Korrekturen",
    kpiErrorsSub: "Ohne ignorierte Versprecher",
    coachDiagnosisTitle: "Diagnose & Empfehlungen des Coaches",
    topicFreqTitle: "Fehlerhäufigkeit nach Grammatik-Thema",
    thTopic: "Thema",
    thErrors: "Fehler",
    thShare: "Anteil",
    thSessions: "Sessions",
    thLastSeen: "Zuletzt",
    recurringTitle: "Wiederkehrende Fehler",
    settingsTitle: "Einstellungen & Systemstatus",
    settingsSubtitle: "Hardware-Konfiguration, Sprachauswahl und Speicherverwaltung.",
    settingsCheck: "Prüfen",
    pipeTitle: "Lokale Pipeline-Infrastruktur",
    settingsLangTitle: "Sprach-, Stimmen- & Szenario-Einstellungen",
    lblPracticeLang: "Lernsprache",
    lblVoice: "Aktive Stimme",
    lblScenario: "Aktives Szenario",
    lblUILang: "Benutzeroberfläche",
    btnTestVoice: "Stimme testen",
    testVoiceTip: "Erzeugt eine kurze Sprachprobe via Edge-TTS und gibt sie lokal wieder.",
    dataMgmtTitle: "Datenverwaltung",
    clearHistoryHeading: "Verlauf & Datenbank leeren",
    clearHistoryDesc: "Löscht alle Sprachrunden, Fehlerprotokolle, Quiz-Ergebnisse und Analysen aus tutor.db.",
    btnClearHistory: "Verlauf löschen",
    scenarioCasual: "Lockerer Plausch",
    scenarioInterview: "Bewerbungsgespräch",
    scenarioTech: "Tech & Architektur",
    scenarioTravel: "Reisen & Alltag",
    scenarioGrammar: "Grammatik-Fokus & Drills"
  },
  es: {
    brandTitle: "Coach de Idiomas",
    brandSubtitle: "Práctica de conversación y retroalimentación en tiempo real",
    tabVoice: "Conversación",
    tabQuiz: "Cuestionario",
    tabAnalysis: "Análisis",
    tabSettings: "Ajustes",
    tapToSpeak: "Toca para hablar",
    listening: "Escuchando...",
    thinking: "Procesando...",
    speaking: "El coach habla...",
    ready: "Listo",
    handsFreeOn: "Manos libres: ACTIVADO",
    handsFreeOff: "Manos libres: DESACTIVADO",
    pressSpace: "Presiona Espacio para alternar el micrófono",
    quizTitle: "Practica tus puntos débiles",
    quizSubtitle: "Preguntas interactivas generadas directamente a partir de tus errores reales.",
    quizFresh: "Nuevas preguntas",
    quizEmptyTitle: "Aún no hay errores activos",
    quizEmptyDesc: "Habla en modo Conversación. Cualquier error se convertirá en un ejercicio específico aquí.",
    quizGoConv: "Ir a conversación",
    analysisTitle: "Progreso y análisis",
    analysisSubtitle: "Seguimiento a largo plazo de precisión gramatical, patrones y fluidez.",
    kpiAccLabel: "Turnos sin errores",
    kpiAccSub: "Consistencia gramatical general",
    kpiTurnsLabel: "Turnos hablados",
    kpiErrorsLabel: "Correcciones activas",
    kpiErrorsSub: "Excluyendo errores descartados",
    coachDiagnosisTitle: "Diagnóstico y recomendaciones del tutor",
    topicFreqTitle: "Frecuencia de errores por tema",
    thTopic: "Tema",
    thErrors: "Errores",
    thShare: "Porcentaje",
    thSessions: "Sesiones",
    thLastSeen: "Última vez",
    recurringTitle: "Errores recurrentes",
    settingsTitle: "Ajustes y estado del sistema",
    settingsSubtitle: "Configuración de hardware, parámetros del modelo y almacenamiento.",
    settingsCheck: "Comprobar",
    pipeTitle: "Infraestructura local",
    settingsLangTitle: "Ajustes de idioma, voz y escenario",
    lblPracticeLang: "Idioma",
    lblVoice: "Voz activa",
    lblScenario: "Escenario activo",
    lblUILang: "Idioma de interfaz",
    btnTestVoice: "Probar voz",
    testVoiceTip: "Sintetiza una breve muestra de voz mediante Edge-TTS y la reproduce localmente.",
    dataMgmtTitle: "Gestión de datos",
    clearHistoryHeading: "Borrar historial y base de datos",
    clearHistoryDesc: "Elimina todos los turnos, errores, cuestionarios y análisis de tutor.db.",
    btnClearHistory: "Borrar historial",
    scenarioCasual: "Conversación casual",
    scenarioInterview: "Práctica de entrevista",
    scenarioTech: "Tecnología y arquitectura",
    scenarioTravel: "Viajes y vida diaria",
    scenarioGrammar: "Enfoque gramatical y drills"
  },
  fr: {
    brandTitle: "Coach Linguistique",
    brandSubtitle: "Entraînement à la conversation et retour en temps réel",
    tabVoice: "Conversation",
    tabQuiz: "Quiz d'entraînement",
    tabAnalysis: "Analyse",
    tabSettings: "Paramètres",
    tapToSpeak: "Appuyez pour parler",
    listening: "À l'écoute...",
    thinking: "Traitement en cours...",
    speaking: "Le coach parle...",
    ready: "Prêt",
    handsFreeOn: "Mains libres : ACTIVÉ",
    handsFreeOff: "Mains libres : DÉSACTIVÉ",
    pressSpace: "Appuyez sur Espace pour basculer le microphone",
    quizTitle: "Travaillez vos points faibles",
    quizSubtitle: "Questions interactives générées à partir de vos erreurs réelles en conversation.",
    quizFresh: "Nouvelles questions",
    quizEmptyTitle: "Aucune erreur active",
    quizEmptyDesc: "Parlez en mode Conversation. Chaque erreur deviendra un exercice sur mesure ici.",
    quizGoConv: "Aller à la conversation",
    analysisTitle: "Progression et analyse",
    analysisSubtitle: "Suivi à long terme de votre précision grammaticale et de votre aisance.",
    kpiAccLabel: "Tours sans erreur",
    kpiAccSub: "Cohérence grammaticale globale",
    kpiTurnsLabel: "Tours parlés",
    kpiErrorsLabel: "Corrections actives",
    kpiErrorsSub: "Hors erreurs ignorées",
    coachDiagnosisTitle: "Diagnostic et conseils du coach",
    topicFreqTitle: "Fréquence des erreurs par règle",
    thTopic: "Règle",
    thErrors: "Erreurs",
    thShare: "Part",
    thSessions: "Sessions",
    thLastSeen: "Dernière fois",
    recurringTitle: "Erreurs récurrentes",
    settingsTitle: "Paramètres & État du système",
    settingsSubtitle: "Configuration matérielle, modèles et gestion du stockage.",
    settingsCheck: "Vérifier",
    pipeTitle: "Infrastructure locale",
    settingsLangTitle: "Paramètres de langue, voix & scénario",
    lblPracticeLang: "Langue",
    lblVoice: "Voix active",
    lblScenario: "Scénario actif",
    lblUILang: "Langue de l'interface",
    btnTestVoice: "Tester la voix",
    testVoiceTip: "Synthétise un court extrait vocal via Edge-TTS et le lit localement.",
    dataMgmtTitle: "Gestion des données",
    clearHistoryHeading: "Effacer l'historique et la base",
    clearHistoryDesc: "Supprime tous les échanges, erreurs, quiz et analyses de tutor.db.",
    btnClearHistory: "Effacer l'historique",
    scenarioCasual: "Conversation décontractée",
    scenarioInterview: "Entraînement entretien",
    scenarioTech: "Tech & Architecture logicielle",
    scenarioTravel: "Voyages & Quotidien",
    scenarioGrammar: "Focus grammaire & Exercices"
  },
  it: {
    brandTitle: "Tutor Linguistico",
    brandSubtitle: "Pratica di conversazione e feedback in tempo reale",
    tabVoice: "Conversazione",
    tabQuiz: "Quiz di pratica",
    tabAnalysis: "Analisi",
    tabSettings: "Impostazioni",
    tapToSpeak: "Tocca per parlare",
    listening: "In ascolto...",
    thinking: "Elaborazione...",
    speaking: "Il tutor parla...",
    ready: "Pronto",
    handsFreeOn: "Vivavoce: ATTIVO",
    handsFreeOff: "Vivavoce: DISATTIVO",
    pressSpace: "Premi Spazio per attivare o disattivare il microfono",
    quizTitle: "Esercitati sui tuoi punti deboli",
    quizSubtitle: "Domande interattive generate direttamente dai tuoi errori reali.",
    quizFresh: "Nuove domande",
    quizEmptyTitle: "Nessun errore attivo finora",
    quizEmptyDesc: "Parla in modalità Conversazione. Qualsiasi errore diventerà automaticamente un quiz qui.",
    quizGoConv: "Vai alla conversazione",
    analysisTitle: "Progresso e analisi",
    analysisSubtitle: "Monitoraggio a lungo termine di accuratezza, schemi e fluidità.",
    kpiAccLabel: "Turni corretti",
    kpiAccSub: "Accuratezza grammaticale complessiva",
    kpiTurnsLabel: "Frasi pronunciate",
    kpiErrorsLabel: "Correzioni attive",
    kpiErrorsSub: "Esclusi errori ignorati",
    coachDiagnosisTitle: "Diagnosi ed indicazioni del tutor",
    topicFreqTitle: "Frequenza errori per argomento",
    thTopic: "Argomento",
    thErrors: "Errori",
    thShare: "Quota",
    thSessions: "Sessioni",
    thLastSeen: "Ultimo",
    recurringTitle: "Errori ricorrenti",
    settingsTitle: "Impostazioni e stato di sistema",
    settingsSubtitle: "Configurazione hardware, modelli e gestione database.",
    settingsCheck: "Verifica",
    pipeTitle: "Infrastruttura locale",
    settingsLangTitle: "Impostazioni lingua, voce e scenario",
    lblPracticeLang: "Lingua",
    lblVoice: "Voce attiva",
    lblScenario: "Scenario attivo",
    lblUILang: "Lingua interfaccia",
    btnTestVoice: "Prova voce",
    testVoiceTip: "Sintetizza un breve campione audio con Edge-TTS e lo riproduce localmente.",
    dataMgmtTitle: "Gestione dati",
    clearHistoryHeading: "Cancella cronologia e database",
    clearHistoryDesc: "Elimina tutte le conversazioni, gli errori, i quiz e le analisi da tutor.db.",
    btnClearHistory: "Cancella cronologia",
    scenarioCasual: "Conversazione informale",
    scenarioInterview: "Simulazione colloquio",
    scenarioTech: "Tecnologia & Architettura",
    scenarioTravel: "Viaggi & Vita quotidiana",
    scenarioGrammar: "Focus grammatica & Esercizi"
  }
};

// State
let appState = "idle"; // "idle" | "listening" | "thinking" | "speaking"
let isContinuousMode = false;
let isSessionStarted = false;
let currentLanguage = localStorage.getItem("jarvis_coach_lang") || "en";
let uiLanguage = localStorage.getItem("jarvis_ui_lang") || "en";
let currentScenario = "casual";
let currentVoice = localStorage.getItem(`jarvis_voice_${currentLanguage}`) || LANG_DATA[currentLanguage]?.defaultVoice || "en-US-AndrewNeural";
let currentSessionId = "session_" + Date.now();
let lastMistakeId = null;

let mediaRecorder = null;
let audioChunks = [];
let audioStream = null;
let audioCtx = null;
let analyser = null;
let dataArray = null;
let animFrameId = null;

// Audio Queue & Preloader
let audioQueue = [];
let isAudioPlaying = false;
let currentPlayingAudio = null;
let conversationHistory = [];

// Low-latency Silence detection (VAD)
let silenceStartTime = null;
let speechDetected = false;
const SILENCE_TIMEOUT_MS = 950; // Snappy turn cut-off
const VAD_VOLUME_THRESHOLD = 0.030;

// DOM Elements
const orbWrapper = document.getElementById("orb-wrapper");
const orbLabel = document.getElementById("orb-label");
const statusDot = document.getElementById("status-dot");
const statusText = document.getElementById("status-text");
const userTranscript = document.getElementById("user-transcript");
const feedbackBanner = document.getElementById("feedback-banner");
const feedbackIcon = document.getElementById("feedback-icon");
const feedbackText = document.getElementById("feedback-text");
const feedbackTopicBadge = document.getElementById("feedback-topic-badge");
const feedbackActions = document.getElementById("feedback-actions");
const coachResponse = document.getElementById("coach-response");
const canvasEl = document.getElementById("visualizer");
const canvasCtx = canvasEl.getContext("2d");
const continuousBtn = document.getElementById("continuous-btn");
const continuousLabel = document.getElementById("continuous-label");
const textInput = document.getElementById("text-input");
const languageSelect = document.getElementById("language-select");
const scenarioSelect = document.getElementById("scenario-select");
const voiceSelect = document.getElementById("voice-select");
const quizBadge = document.getElementById("quiz-badge");

// Navigation View Tabs
function switchView(viewName) {
  const voiceTab = document.getElementById("tab-voice");
  const quizTab = document.getElementById("tab-quiz");
  const analysisTab = document.getElementById("tab-analysis");
  const settingsTab = document.getElementById("tab-settings");

  const voiceView = document.getElementById("view-voice");
  const quizView = document.getElementById("view-quiz");
  const analysisView = document.getElementById("view-analysis");
  const settingsView = document.getElementById("view-settings");

  if (voiceTab) voiceTab.classList.toggle("active", viewName === "voice");
  if (quizTab) quizTab.classList.toggle("active", viewName === "quiz");
  if (analysisTab) analysisTab.classList.toggle("active", viewName === "analysis");
  if (settingsTab) settingsTab.classList.toggle("active", viewName === "settings");

  if (voiceView) voiceView.style.display = viewName === "voice" ? "block" : "none";
  if (quizView) quizView.style.display = viewName === "quiz" ? "block" : "none";
  if (analysisView) analysisView.style.display = viewName === "analysis" ? "block" : "none";
  if (settingsView) settingsView.style.display = viewName === "settings" ? "block" : "none";

  if (viewName === "quiz") {
    loadQuiz(false);
  } else if (viewName === "analysis") {
    loadAnalysis(false);
  } else if (viewName === "settings") {
    loadSettings(false);
  }
}

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
      osc.frequency.setValueAtTime(523.25, now);
      osc.frequency.exponentialRampToValueAtTime(659.25, now + 0.10);
      gain.gain.setValueAtTime(0.05, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.15);
      osc.start(now);
      osc.stop(now + 0.15);
    } else if (kind === "stop") {
      osc.frequency.setValueAtTime(659.25, now);
      osc.frequency.exponentialRampToValueAtTime(440, now + 0.10);
      gain.gain.setValueAtTime(0.05, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.15);
      osc.start(now);
      osc.stop(now + 0.15);
    }
  } catch (e) {}
}

function setUIState(newState) {
  appState = newState;
  if (!orbWrapper) return;
  orbWrapper.className = "orb-wrapper " + (newState === "idle" ? "" : newState);
  statusDot.className = "status-dot " + (newState === "idle" ? "" : newState);

  const t = UI_TRANSLATIONS[uiLanguage] || UI_TRANSLATIONS.en;

  if (newState === "idle") {
    if (!isSessionStarted) {
      orbLabel.textContent = t.tapToSpeak;
      statusText.textContent = t.ready;
    } else {
      orbLabel.textContent = isContinuousMode ? t.listening : t.tapToSpeak;
      statusText.textContent = isContinuousMode ? t.handsFreeOn : t.ready;
    }
  } else if (newState === "listening") {
    orbLabel.textContent = t.listening;
    statusText.textContent = t.listening.replace("...", "");
  } else if (newState === "thinking") {
    orbLabel.textContent = t.thinking;
    statusText.textContent = t.thinking.replace("...", "");
  } else if (newState === "speaking") {
    orbLabel.textContent = t.speaking;
    statusText.textContent = t.speaking.replace("...", "");
  }
}

// Waveform Visualizer
function drawVisualizer() {
  animFrameId = requestAnimationFrame(drawVisualizer);
  if (!analyser || !dataArray) return;

  analyser.getByteFrequencyData(dataArray);
  canvasCtx.clearRect(0, 0, canvasEl.width, canvasEl.height);

  const numBars = 32;
  const barWidth = 3;
  const gap = 3;
  const totalWidth = numBars * barWidth + (numBars - 1) * gap;
  const startX = (canvasEl.width - totalWidth) / 2;
  const centerY = canvasEl.height / 2;
  const step = Math.max(1, Math.floor(dataArray.length / numBars));

  for (let i = 0; i < numBars; i++) {
    const val = dataArray[i * step] || 0;
    const barHeight = Math.max(2, (val / 255) * (canvasEl.height - 4));
    const x = startX + i * (barWidth + gap);
    const y = centerY - barHeight / 2;

    if (appState === "listening") {
      canvasCtx.fillStyle = "rgba(56, 189, 248, 0.85)";
    } else if (appState === "speaking") {
      canvasCtx.fillStyle = "rgba(16, 185, 129, 0.85)";
    } else {
      canvasCtx.fillStyle = "rgba(148, 163, 184, 0.25)";
    }

    if (canvasCtx.roundRect) {
      canvasCtx.beginPath();
      canvasCtx.roundRect(x, y, barWidth, barHeight, 1.5);
      canvasCtx.fill();
    } else {
      canvasCtx.fillRect(x, y, barWidth, barHeight);
    }
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

    mediaRecorder.start(80);
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

  setTimeout(monitorContinuousVAD, 70);
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
    const sttRes = await fetch(`/api/stt?lang=${encodeURIComponent(currentLanguage)}`, {
      method: "POST",
      headers: {
        "Content-Type": audioBlob.type || "audio/webm",
        "X-Target-Language": currentLanguage
      },
      body: audioBlob
    });

    if (!sttRes.ok) throw new Error(`STT HTTP ${sttRes.status}`);
    const data = await sttRes.json();
    const query = (data.text || "").trim();

    if (!query) {
      userTranscript.textContent = "No speech detected. Please speak again!";
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

// Language Coach Execution & Low-Latency Streaming
async function executeCoachTurn(userInput) {
  setUIState("thinking");
  coachResponse.textContent = "...";
  feedbackBanner.classList.add("empty");
  feedbackBanner.classList.remove("correct");
  feedbackTopicBadge.textContent = "";
  feedbackActions.style.display = "none";
  feedbackText.textContent = "";
  lastMistakeId = null;

  conversationHistory.push({ role: "user", content: userInput });

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        messages: conversationHistory,
        topic: currentScenario,
        voice: currentVoice,
        session_id: currentSessionId,
        target_lang: currentLanguage,
        native_lang: "de"
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
          if (parsed.meta) {
            if (parsed.meta.corrections && parsed.meta.corrections.length > 0) {
              lastMistakeId = parsed.meta.corrections[0].id;
              feedbackActions.style.display = "flex";
              updateQuizBadge(1);
            }
          }
          if (parsed.delta) {
            rawOutput += parsed.delta;
            parseAndRenderCoachOutput(rawOutput);

            // Stream spoken reply chunks into TTS queue immediately
            let spokenPart = "";
            if (rawOutput.includes("SPOKEN:")) {
              spokenPart = rawOutput.split("SPOKEN:")[1] || "";
            }

            if (spokenPart) {
              speechSentenceBuffer += parsed.delta;

              // Dispatch sentence or clause to TTS as early as possible
              if (/[.!?]\s+$/.test(speechSentenceBuffer) || (speechSentenceBuffer.length > 45 && /[,;]\s+$/.test(speechSentenceBuffer))) {
                const cleanChunk = speechSentenceBuffer
                  .replace(/CORRECTION:[\s\S]*?SPOKEN:/i, "")
                  .replace(/TOPIC:[\s\S]*?SPOKEN:/i, "")
                  .replace(/ORIGINAL:[\s\S]*?SPOKEN:/i, "")
                  .replace(/CORRECTED:[\s\S]*?SPOKEN:/i, "")
                  .replace(/SPOKEN:/i, "")
                  .trim();
                speechSentenceBuffer = "";
                if (cleanChunk && cleanChunk.length > 2) {
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
        .replace(/TOPIC:[\s\S]*?SPOKEN:/i, "")
        .replace(/ORIGINAL:[\s\S]*?SPOKEN:/i, "")
        .replace(/CORRECTED:[\s\S]*?SPOKEN:/i, "")
        .replace(/SPOKEN:/i, "")
        .trim();
      if (cleanChunk && cleanChunk.length > 2) {
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
  let topic = "";
  let spoken = "";

  for (const line of raw.splitlines ? raw.splitlines() : raw.split("\n")) {
    const l = line.trim();
    if (l.startsWith("CORRECTION:")) correction = l.replace("CORRECTION:", "").trim();
    else if (l.startsWith("TOPIC:")) topic = l.replace("TOPIC:", "").trim();
  }

  if (raw.includes("SPOKEN:")) {
    spoken = raw.split("SPOKEN:")[1].trim();
  } else if (!correction) {
    spoken = raw.trim();
  }

  // Render Correction / Feedback Banner
  if (correction) {
    feedbackBanner.classList.remove("empty");
    feedbackText.textContent = correction;

    const lower = correction.toLowerCase();
    const flawlessMarkers = ["none", "perfect", "flawless", "spot on", "great", "kein fehler", "perfekt", "excelente", "bravo", "sans faute"];
    const isFlawless = flawlessMarkers.some(k => lower.includes(k));

    if (isFlawless) {
      feedbackBanner.classList.add("correct");
      feedbackIcon.innerHTML = `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>`;
      feedbackTopicBadge.textContent = "ACCURACY";
      feedbackActions.style.display = "none";
    } else {
      feedbackBanner.classList.remove("correct");
      feedbackIcon.innerHTML = `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>`;
      if (topic && topic !== "none") {
        let cleanTopic = topic;
        ["en_", "de_", "es_", "fr_", "it_"].forEach(p => {
          if (cleanTopic.startsWith(p)) cleanTopic = cleanTopic.slice(p.length);
        });
        feedbackTopicBadge.textContent = cleanTopic.replace(/_/g, " ").toUpperCase();
      } else {
        feedbackTopicBadge.textContent = "GRAMMAR SLIP";
      }
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

// Mistake Exclusion / Dismissal ("Not a mistake" / "Misheard")
async function dismissMistake(reason) {
  if (!lastMistakeId) return;
  try {
    const res = await fetch(`/api/mistakes/${lastMistakeId}/exclude`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ reason })
    });
    if (res.ok) {
      feedbackBanner.classList.add("correct");
      feedbackIcon.textContent = "👌";
      feedbackText.textContent = reason === "misheard" ? "Marked as misheard (removed from quiz & stats)." : "Marked as not a mistake (dismissed).";
      feedbackActions.style.display = "none";
      feedbackTopicBadge.textContent = "EXCLUDED";
      updateQuizBadge(-1);
    }
  } catch (e) {
    console.warn("Exclusion error:", e);
  }
}

function updateQuizBadge(delta) {
  if (!quizBadge) return;
  let count = parseInt(quizBadge.textContent || "0", 10) + delta;
  count = Math.max(0, count);
  quizBadge.textContent = count;
  quizBadge.style.display = count > 0 ? "inline-block" : "none";
}

// Low-latency Audio Queue with Preloading
function queueTTS(sentence) {
  if (!sentence) return;
  const audioUrl = `/api/tts?text=${encodeURIComponent(sentence)}&voice=${encodeURIComponent(currentVoice)}&lang=${encodeURIComponent(currentLanguage)}`;
  
  // Preload audio element right away so fetch happens concurrently
  const audioEl = new Audio();
  audioEl.preload = "auto";
  audioEl.src = audioUrl;

  audioQueue.push({ url: audioUrl, text: sentence, audio: audioEl });

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
    currentPlayingAudio = item.audio || new Audio(item.url);
    currentPlayingAudio.onended = () => {
      currentPlayingAudio = null;
      playNextAudio();
    };
    currentPlayingAudio.onerror = () => {
      console.warn("TTS playback error:", item.text);
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
    }, 500); // reduced delay for faster hands-free loop
  }
}

// Interactive Practice Quiz System
let quizQuestions = [];

async function loadQuiz(forceRefresh = false) {
  const loadingEl = document.getElementById("quiz-loading");
  const emptyEl = document.getElementById("quiz-empty");
  const cardsEl = document.getElementById("quiz-cards");

  if (!loadingEl || !emptyEl || !cardsEl) return;

  if (!forceRefresh && quizQuestions.length > 0) {
    return;
  }

  loadingEl.style.display = "block";
  emptyEl.style.display = "none";
  cardsEl.innerHTML = "";

  try {
    const res = await fetch(`/api/quiz/generate?session_id=${encodeURIComponent(currentSessionId)}&lang=${encodeURIComponent(currentLanguage)}`, {
      method: "POST"
    });
    const data = await res.json();
    loadingEl.style.display = "none";

    quizQuestions = data.questions || [];
    if (quizBadge) {
      quizBadge.textContent = quizQuestions.length;
      quizBadge.style.display = quizQuestions.length > 0 ? "inline-block" : "none";
    }

    if (quizQuestions.length === 0) {
      emptyEl.style.display = "block";
    } else {
      renderQuizQuestions(quizQuestions);
    }
  } catch (err) {
    loadingEl.style.display = "none";
    emptyEl.style.display = "block";
    console.error("Quiz load error:", err);
  }
}

function renderQuizQuestions(questions) {
  const cardsEl = document.getElementById("quiz-cards");
  if (!cardsEl) return;
  cardsEl.innerHTML = "";

  questions.forEach((q, qIdx) => {
    const card = document.createElement("div");
    card.className = "quiz-card";

    let originHtml = "";
    if (q.source_said) {
      originHtml = `<div class="quiz-card-origin">Practising this because you said: <strong>"${escapeHtml(q.source_said)}"</strong></div>`;
    }

    const optionsHtml = (q.options || []).map((opt, oIdx) => `
      <button type="button" class="quiz-option-btn" id="opt-${qIdx}-${oIdx}" onclick="answerQuizQuestion(${qIdx}, ${oIdx})">
        ${escapeHtml(opt)}
      </button>
    `).join("");

    card.innerHTML = `
      ${originHtml}
      <div class="quiz-card-q">${escapeHtml(q.question)}</div>
      <div class="quiz-options" id="opts-${qIdx}">
        ${optionsHtml}
      </div>
      <div class="quiz-explanation" id="exp-${qIdx}" style="display:none;"></div>
    `;

    cardsEl.appendChild(card);
  });
}

async function answerQuizQuestion(qIdx, oIdx) {
  const q = quizQuestions[qIdx];
  if (!q) return;

  const chosenOpt = (q.options || [])[oIdx];
  const container = document.getElementById(`opts-${qIdx}`);
  if (!container) return;
  const buttons = container.querySelectorAll(".quiz-option-btn");
  buttons.forEach(b => b.disabled = true);

  try {
    const res = await fetch("/api/quiz/grade", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        mistake_id: String(q.mistake_id || ""),
        question_text: q.question,
        user_answer: chosenOpt,
        correct_answer: q.correct_answer
      })
    });
    const result = await res.json();

    const clickedBtn = document.getElementById(`opt-${qIdx}-${oIdx}`);
    if (result.is_correct) {
      if (clickedBtn) clickedBtn.classList.add("correct");
    } else {
      if (clickedBtn) clickedBtn.classList.add("wrong");
      buttons.forEach(b => {
        if (b.textContent.trim().toLowerCase() === (q.correct_answer || "").trim().toLowerCase()) {
          b.classList.add("correct");
        }
      });
    }

    const expEl = document.getElementById(`exp-${qIdx}`);
    if (expEl) {
      expEl.style.display = "block";
      expEl.innerHTML = `<strong>${result.is_correct ? '✅ Correct!' : '❌ Not quite.'}</strong> ${escapeHtml(q.explanation || '')}`;
    }
  } catch (e) {
    console.error("Grade error:", e);
  }
}

function launchCelebrationConfetti() {
  const canvas = document.createElement("canvas");
  canvas.style.position = "fixed";
  canvas.style.inset = "0";
  canvas.style.width = "100vw";
  canvas.style.height = "100vh";
  canvas.style.pointerEvents = "none";
  canvas.style.zIndex = "9999";
  document.body.appendChild(canvas);

  const ctx = canvas.getContext("2d");
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;

  const particles = [];
  const colors = ["#10b981", "#38bdf8", "#f59e0b", "#6366f1", "#ec4899"];

  for (let i = 0; i < 70; i++) {
    particles.push({
      x: canvas.width / 2,
      y: canvas.height * 0.45,
      vx: (Math.random() - 0.5) * 14,
      vy: (Math.random() - 0.8) * 14,
      size: Math.random() * 6 + 4,
      color: colors[Math.floor(Math.random() * colors.length)],
      rotation: Math.random() * 360,
      rotationSpeed: (Math.random() - 0.5) * 8,
      opacity: 1
    });
  }

  const startTime = Date.now();
  function animate() {
    const elapsed = Date.now() - startTime;
    if (elapsed > 2200) {
      canvas.remove();
      return;
    }
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    particles.forEach(p => {
      p.x += p.vx;
      p.y += p.vy;
      p.vy += 0.25;
      p.rotation += p.rotationSpeed;
      p.opacity = Math.max(0, 1 - elapsed / 2200);

      ctx.save();
      ctx.translate(p.x, p.y);
      ctx.rotate((p.rotation * Math.PI) / 180);
      ctx.globalAlpha = p.opacity;
      ctx.fillStyle = p.color;
      ctx.fillRect(-p.size / 2, -p.size / 2, p.size, p.size);
      ctx.restore();
    });
    requestAnimationFrame(animate);
  }
  requestAnimationFrame(animate);
}

function escapeHtml(text) {
  if (!text) return "";
  return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

// User Actions
async function startConversationFlow() {
  await ensureAudioContext();
  isSessionStarted = true;
  setUIState("thinking");
  const info = LANG_DATA[currentLanguage] || LANG_DATA.en;
  coachResponse.textContent = info.connectingText;
  userTranscript.textContent = (UI_TRANSLATIONS[uiLanguage] || UI_TRANSLATIONS.en).tabVoice + "...";
  userTranscript.classList.remove("empty");

  try {
    const res = await fetch("/api/sessions/start", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: currentSessionId,
        scenario: currentScenario,
        voice: currentVoice,
        target_lang: currentLanguage,
        native_lang: "de"
      })
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    
    coachResponse.textContent = data.greeting;
    conversationHistory = [{ role: "assistant", content: data.greeting }];
    
    // Automatically speak the greeting aloud!
    queueTTS(data.greeting);
  } catch (err) {
    console.error("Start error:", err);
    coachResponse.textContent = info.greeting;
    conversationHistory = [{ role: "assistant", content: coachResponse.textContent }];
    queueTTS(coachResponse.textContent);
  }
}

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
    if (!isSessionStarted) {
      // First click: Coach takes the floor and initiates the conversation
      startConversationFlow();
    } else {
      // Subsequent clicks: User speaks their turn
      startRecording();
    }
  } else if (appState === "listening") {
    stopRecordingAndSubmit();
  }
}

function toggleContinuousMode() {
  isContinuousMode = !isContinuousMode;
  continuousBtn.classList.toggle("active", isContinuousMode);
  const t = UI_TRANSLATIONS[uiLanguage] || UI_TRANSLATIONS.en;
  continuousLabel.textContent = isContinuousMode ? t.handsFreeOn : t.handsFreeOff;

  if (isContinuousMode && appState === "idle") {
    if (!isSessionStarted) {
      startConversationFlow();
    } else {
      startRecording();
    }
  }
}

function changeScenario(val) {
  currentScenario = val;
  const settingsScenarioSelect = document.getElementById("settings-scenario-select");
  if (settingsScenarioSelect && settingsScenarioSelect.value !== val) {
    settingsScenarioSelect.value = val;
  }
  console.log("Scenario changed to:", val);
  
  // Starting a new scenario resets the session so the coach opens with the new scenario prompt
  currentSessionId = "session_" + Date.now();
  isSessionStarted = false;
  conversationHistory = [];
  setUIState("idle");
  userTranscript.textContent = `Scenario set to ${val}. Click the microphone to start speaking.`;
  userTranscript.classList.remove("empty");
  coachResponse.textContent = `Scenario ready. Click the microphone to start our ${val} practice.`;
}

// Returns the remembered speaker for a language, or its default if none/invalid
function resolveVoiceForLanguage(lang) {
  const info = LANG_DATA[lang] || LANG_DATA.en;
  const saved = localStorage.getItem(`jarvis_voice_${lang}`);
  if (saved && info.voices.some(v => v.id === saved)) return saved;
  return info.defaultVoice;
}

function stopAllAudio() {
  audioQueue.forEach(item => { try { item.audio && item.audio.pause(); } catch (e) {} });
  audioQueue = [];
  if (currentPlayingAudio) {
    try { currentPlayingAudio.pause(); } catch (e) {}
    currentPlayingAudio = null;
  }
  isAudioPlaying = false;
  if (typeof testVoiceAudio !== "undefined" && testVoiceAudio) {
    try { testVoiceAudio.pause(); } catch (e) {}
  }
}

function changeVoice(val) {
  const info = LANG_DATA[currentLanguage] || LANG_DATA.en;
  if (!info.voices.some(v => v.id === val)) val = info.defaultVoice;
  currentVoice = val;
  localStorage.setItem(`jarvis_voice_${currentLanguage}`, val);
  if (voiceSelect && voiceSelect.value !== val) {
    voiceSelect.value = val;
  }
  const settingsVoiceSelect = document.getElementById("settings-voice-select");
  if (settingsVoiceSelect && settingsVoiceSelect.value !== val) {
    settingsVoiceSelect.value = val;
  }
  const ttsVoiceEl = document.getElementById("settings-tts-voice");
  if (ttsVoiceEl) {
    ttsVoiceEl.textContent = `Voice: ${val} (audio/mpeg MP3)`;
  }
  console.log("Voice changed to:", val);
}

function changeLanguage(val, startFresh = true) {
  if (!LANG_DATA[val]) val = "en";
  currentLanguage = val;
  uiLanguage = val;
  localStorage.setItem("jarvis_coach_lang", val);
  localStorage.setItem("jarvis_ui_lang", val);

  if (languageSelect && languageSelect.value !== val) {
    languageSelect.value = val;
  }
  const settingsLangSelect = document.getElementById("settings-language-select");
  if (settingsLangSelect && settingsLangSelect.value !== val) {
    settingsLangSelect.value = val;
  }

  // Unified language switch: synchronize entire UI interface language with practice language
  applyUILanguage(val);

  // Stop any audio still playing/queued in the previous language's voice
  stopAllAudio();

  const info = LANG_DATA[val];
  currentVoice = resolveVoiceForLanguage(val);
  updateVoiceDropdowns(val);
  renderStarters(val);

  if (textInput) {
    textInput.placeholder = info.placeholder;
  }

  if (startFresh || !isSessionStarted) {
    userTranscript.textContent = info.emptyTranscript;
    userTranscript.classList.add("empty");
    coachResponse.textContent = `"${info.greeting}"`;
    currentSessionId = "session_" + Date.now();
    isSessionStarted = false;
    conversationHistory = [];
    setUIState("idle");
    updateQuizBadge(0);
  }

  console.log("Unified language set to:", val, "Voice:", currentVoice);
}

function updateVoiceDropdowns(lang) {
  const info = LANG_DATA[lang] || LANG_DATA.en;
  const buildOptions = () => {
    return info.voices.map(v => `<option value="${v.id}">${v.name}</option>`).join("");
  };

  if (voiceSelect) {
    voiceSelect.innerHTML = buildOptions();
    voiceSelect.value = currentVoice;
  }
  const settingsVoiceSelect = document.getElementById("settings-voice-select");
  if (settingsVoiceSelect) {
    settingsVoiceSelect.innerHTML = buildOptions();
    settingsVoiceSelect.value = currentVoice;
  }
  const ttsVoiceEl = document.getElementById("settings-tts-voice");
  if (ttsVoiceEl) {
    ttsVoiceEl.textContent = `Voice: ${currentVoice} (audio/mpeg MP3)`;
  }
}

function renderStarters(lang) {
  const container = document.getElementById("topic-chips");
  if (!container) return;
  const info = LANG_DATA[lang] || LANG_DATA.en;
  container.innerHTML = info.starters.map(s => `
    <button type="button" class="topic-chip" onclick="quickSend('${escapeHtml(s.text)}')">${escapeHtml(s.label)}</button>
  `).join("");
}

function applyUILanguage(lang) {
  const t = UI_TRANSLATIONS[lang] || UI_TRANSLATIONS.en;

  // Header Brand
  const brandTitle = document.querySelector(".brand-title");
  if (brandTitle) brandTitle.textContent = t.brandTitle;
  const brandSub = document.querySelector(".brand-subtitle");
  if (brandSub) brandSub.textContent = t.brandSubtitle;

  // Nav tabs
  const tabVoice = document.querySelector("#tab-voice span");
  if (tabVoice) tabVoice.textContent = t.tabVoice;
  const tabQuiz = document.querySelector("#tab-quiz span");
  if (tabQuiz) tabQuiz.textContent = t.tabQuiz;
  const tabAnalysis = document.querySelector("#tab-analysis span");
  if (tabAnalysis) tabAnalysis.textContent = t.tabAnalysis;
  const tabSettings = document.querySelector("#tab-settings span");
  if (tabSettings) tabSettings.textContent = t.tabSettings;

  // Continuous btn label
  if (continuousLabel) {
    continuousLabel.textContent = isContinuousMode ? t.handsFreeOn : t.handsFreeOff;
  }

  // Footer tip
  const footerTip = document.querySelector(".footer-tip");
  if (footerTip) {
    footerTip.innerHTML = `${t.pressSpace.replace("Space", "<kbd>Space</kbd>")}`;
  }

  // Quiz View elements
  const quizTitle = document.querySelector("#view-quiz .quiz-title");
  if (quizTitle) quizTitle.textContent = t.quizTitle;
  const quizSub = document.querySelector("#view-quiz .quiz-subtitle");
  if (quizSub) quizSub.textContent = t.quizSubtitle;
  const quizFreshBtn = document.querySelector("#view-quiz .btn-refresh-quiz span");
  if (quizFreshBtn) quizFreshBtn.textContent = t.quizFresh;
  const quizEmptyTitle = document.querySelector("#quiz-empty h3");
  if (quizEmptyTitle) quizEmptyTitle.textContent = t.quizEmptyTitle;
  const quizEmptyDesc = document.querySelector("#quiz-empty p");
  if (quizEmptyDesc) quizEmptyDesc.textContent = t.quizEmptyDesc;
  const quizGoConv = document.querySelector("#quiz-empty button");
  if (quizGoConv) quizGoConv.textContent = t.quizGoConv;

  // Analysis View elements
  const analysisTitle = document.querySelector("#view-analysis .quiz-title");
  if (analysisTitle) analysisTitle.textContent = t.analysisTitle;
  const analysisSub = document.querySelector("#view-analysis .quiz-subtitle");
  if (analysisSub) analysisSub.textContent = t.analysisSubtitle;

  // Settings labels
  const settingsTitle = document.querySelector("#view-settings .quiz-title");
  if (settingsTitle) settingsTitle.textContent = t.settingsTitle;
  const settingsSub = document.querySelector("#view-settings .quiz-subtitle");
  if (settingsSub) settingsSub.textContent = t.settingsSubtitle;
  const lblLang = document.getElementById("lbl-settings-lang");
  if (lblLang) lblLang.textContent = t.lblPracticeLang;
  const lblVoice = document.getElementById("lbl-settings-voice");
  if (lblVoice) lblVoice.textContent = t.lblVoice;
  const lblScenario = document.getElementById("lbl-settings-scenario");
  if (lblScenario) lblScenario.textContent = t.lblScenario;
  const btnTestVoice = document.querySelector("#btn-test-voice span");
  if (btnTestVoice) btnTestVoice.textContent = t.btnTestVoice;
  const tipVoice = document.querySelector(".settings-tip-text");
  if (tipVoice) tipVoice.textContent = t.testVoiceTip;
  const clearHeading = document.querySelector(".danger-heading");
  if (clearHeading) clearHeading.textContent = t.clearHistoryHeading;
  const clearDesc = document.querySelector(".danger-explanation");
  if (clearDesc) clearDesc.textContent = t.clearHistoryDesc;
  const btnClear = document.querySelector("#btn-reset-data span");
  if (btnClear) btnClear.textContent = t.btnClearHistory;

  // Scenarios dropdown options
  const updateScenarioOptions = (sel) => {
    if (!sel) return;
    const curVal = sel.value;
    sel.innerHTML = `
      <option value="casual">${t.scenarioCasual}</option>
      <option value="interview">${t.scenarioInterview}</option>
      <option value="tech">${t.scenarioTech}</option>
      <option value="travel">${t.scenarioTravel}</option>
      <option value="grammar">${t.scenarioGrammar}</option>
    `;
    sel.value = curVal;
  };
  updateScenarioOptions(scenarioSelect);
  updateScenarioOptions(document.getElementById("settings-scenario-select"));
}

function syncLanguageFromSettings(val) {
  changeLanguage(val);
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

// Cross-Session Analysis System
let analysisData = null;

async function loadAnalysis(forceRefresh = false) {
  if (!forceRefresh && analysisData) {
    renderAnalysis(analysisData);
    return;
  }

  const kpiAcc = document.getElementById("kpi-accuracy");
  const kpiTurns = document.getElementById("kpi-turns");
  const kpiErrors = document.getElementById("kpi-errors");
  const aiSummary = document.getElementById("ai-summary");

  aiSummary.textContent = "Loading speech history and computing grammar metrics...";

  try {
    const res = await fetch(`/api/analysis?session_id=${encodeURIComponent(currentSessionId)}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    analysisData = await res.json();
    renderAnalysis(analysisData);
  } catch (err) {
    console.error("Analysis load error:", err);
    aiSummary.textContent = "Could not load analysis: " + err.message;
  }
}

function renderAnalysis(data) {
  document.getElementById("kpi-accuracy").textContent = `${data.accuracy_pct || 100}%`;
  document.getElementById("kpi-turns").textContent = data.total_turns || 0;
  document.getElementById("kpi-errors").textContent = data.total_mistakes || 0;
  document.getElementById("kpi-sessions-sub").textContent = `Across ${data.total_sessions || 1} session(s)`;

  // AI Written Diagnosis
  const ai = data.ai_analysis || {};
  document.getElementById("ai-summary").textContent = ai.summary || "No active speech data yet.";

  const focusList = document.getElementById("ai-focus-areas");
  focusList.innerHTML = "";
  if (ai.focus_areas && ai.focus_areas.length > 0) {
    ai.focus_areas.forEach(f => {
      const el = document.createElement("div");
      el.className = "focus-item";
      el.innerHTML = `
        <div class="focus-item-topic">🎯 Focus Area: ${escapeHtml(f.topic)}</div>
        <div class="focus-item-tip">${escapeHtml(f.tip)}</div>
      `;
      focusList.appendChild(el);
    });
  }

  // Topic Frequency Table
  const tbody = document.getElementById("topic-freq-tbody");
  tbody.innerHTML = "";
  const topics = data.topic_frequency || [];

  if (topics.length === 0) {
    tbody.innerHTML = `<tr><td colspan="5" class="table-empty">No grammar mistakes recorded so far! Great job.</td></tr>`;
  } else {
    topics.forEach(t => {
      const row = document.createElement("tr");
      row.innerHTML = `
        <td><strong>${escapeHtml(t.label)}</strong></td>
        <td>${t.errors}</td>
        <td>${t.share_pct}%</td>
        <td>${t.sessions}</td>
        <td>${escapeHtml(t.last_seen)}</td>
      `;
      tbody.appendChild(row);
    });
  }

  // Recurring Slips
  const recList = document.getElementById("recurring-list");
  recList.innerHTML = "";
  const recurring = data.recurring_mistakes || [];

  if (recurring.length === 0) {
    recList.innerHTML = `<div class="table-empty">No recurring slips detected. You rarely make the same mistake twice!</div>`;
  } else {
    recurring.forEach(r => {
      const item = document.createElement("div");
      item.className = "recurring-item";

      const exHtml = (r.examples || []).map(e => `
        <div class="recurring-ex">
          <span class="wrong">${escapeHtml(e.original)}</span> &nbsp;➔&nbsp; <span class="right">${escapeHtml(e.corrected)}</span>
        </div>
      `).join("");

      item.innerHTML = `
        <div class="recurring-header">
          <span class="recurring-topic">${escapeHtml(r.label)}</span>
          <span class="recurring-badge">${r.count}x repeated</span>
        </div>
        <div class="recurring-examples">${exHtml}</div>
      `;
      recList.appendChild(item);
    });
  }
}

// ==========================================================================
// Settings View & System Configuration
// ==========================================================================
let settingsHealthData = null;

async function loadSettings(force = false) {
  const statusEl = document.getElementById("settings-pipeline-status");
  const sttModelEl = document.getElementById("settings-stt-model");
  const sttDeviceEl = document.getElementById("settings-stt-device");
  const llmModelEl = document.getElementById("settings-llm-model");
  const llmEndpointEl = document.getElementById("settings-llm-endpoint");
  const ttsModelEl = document.getElementById("settings-tts-model");
  const ttsVoiceEl = document.getElementById("settings-tts-voice");
  const settingsVoiceSelect = document.getElementById("settings-voice-select");
  const settingsScenarioSelect = document.getElementById("settings-scenario-select");

  if (settingsVoiceSelect) settingsVoiceSelect.value = currentVoice;
  if (settingsScenarioSelect) settingsScenarioSelect.value = currentScenario;
  if (ttsVoiceEl) ttsVoiceEl.textContent = `Voice: ${currentVoice} (audio/mpeg MP3)`;

  if (settingsHealthData && !force) return;

  try {
    const res = await fetch("/api/health");
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    settingsHealthData = data;

    if (statusEl) {
      statusEl.textContent = `PIPELINE ${data.status.toUpperCase()} (${data.pipeline?.stt?.device || 'CUDA RTX 5090'})`;
    }
    if (sttModelEl && data.pipeline?.stt) {
      sttModelEl.textContent = `Faster-Whisper (${data.pipeline.stt.model.toUpperCase()})`;
    }
    if (sttDeviceEl && data.pipeline?.stt) {
      sttDeviceEl.textContent = `Device: ${data.pipeline.stt.device} • ${data.pipeline.stt.compute_type}`;
    }
    if (llmModelEl && data.pipeline?.llm) {
      llmModelEl.textContent = `${data.pipeline.llm.model}`;
    }
    if (llmEndpointEl && data.pipeline?.llm) {
      llmEndpointEl.textContent = `Server: ${data.pipeline.llm.server}`;
    }
    if (ttsModelEl && data.pipeline?.tts) {
      ttsModelEl.textContent = `${data.pipeline.tts.engine}`;
    }
    if (ttsVoiceEl && data.pipeline?.tts) {
      ttsVoiceEl.textContent = `Voice: ${currentVoice} (${data.pipeline.tts.format})`;
    }
  } catch (err) {
    console.error("Health fetch error:", err);
    if (statusEl) statusEl.textContent = "PIPELINE OFFLINE / UNREACHABLE";
  }
}

function syncVoiceFromSettings(val) {
  if (voiceSelect) voiceSelect.value = val;
  changeVoice(val);
  const ttsVoiceEl = document.getElementById("settings-tts-voice");
  if (ttsVoiceEl) ttsVoiceEl.textContent = `Voice: ${val} (audio/mpeg MP3)`;
}

function syncScenarioFromSettings(val) {
  const scenarioSelect = document.getElementById("scenario-select");
  if (scenarioSelect) scenarioSelect.value = val;
  changeScenario(val);
}

let testVoiceAudio = null;
async function testCurrentVoice() {
  const btn = document.getElementById("btn-test-voice");
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = `<svg class="spinner-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><circle cx="12" cy="12" r="9" stroke-dasharray="28" stroke-dashoffset="10"/></svg><span>Testing Voice Output...</span>`;
  }

  const resetBtn = () => {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"/></svg><span>Test Neural Voice Output</span>`;
    }
  };

  try {
    if (testVoiceAudio) {
      testVoiceAudio.pause();
      testVoiceAudio = null;
    }
    const testPhrase = LANG_DATA[currentLanguage]?.voiceTest || "Hello Jonathan! Your neural voice output is functioning smoothly on the RTX 5090.";
    const sampleText = encodeURIComponent(testPhrase);
    const url = `/api/tts?text=${sampleText}&voice=${encodeURIComponent(currentVoice)}`;
    testVoiceAudio = new Audio(url);
    testVoiceAudio.onended = resetBtn;
    testVoiceAudio.onerror = (e) => {
      console.error("Voice test playback failed:", e);
      resetBtn();
    };
    await testVoiceAudio.play();
  } catch (e) {
    console.error("Voice test failed:", e);
    resetBtn();
  }
}

async function resetAllContextData() {
  const confirmed = confirm("Are you sure you want to clear all conversation turns, mistakes, quiz history, and analysis data? This action cannot be undone.");
  if (!confirmed) return;

  const btn = document.getElementById("btn-reset-data");
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = `<span>Clearing...</span>`;
  }

  try {
    const res = await fetch("/api/reset", { method: "POST" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    
    // Reset local client state
    conversationHistory = [];
    isSessionStarted = false;
    currentSessionId = "session_" + Date.now();
    lastMistakeId = null;
    quizQuestions = [];
    analysisData = null;

    if (quizBadge) {
      quizBadge.textContent = "0";
      quizBadge.style.display = "none";
    }

    // Reset Quiz DOM
    const quizCards = document.getElementById("quiz-cards");
    if (quizCards) quizCards.innerHTML = "";
    const quizEmpty = document.getElementById("quiz-empty");
    if (quizEmpty) quizEmpty.style.display = "none";
    const quizLoading = document.getElementById("quiz-loading");
    if (quizLoading) quizLoading.style.display = "none";

    // Reset Analysis DOM
    const topicTbody = document.getElementById("topic-freq-tbody");
    if (topicTbody) topicTbody.innerHTML = `<tr><td colspan="5" class="table-empty">No grammar mistakes recorded.</td></tr>`;
    const recurringList = document.getElementById("recurring-list");
    if (recurringList) recurringList.innerHTML = `<div class="table-empty">No recurring slips detected.</div>`;
    const kpiAcc = document.getElementById("kpi-accuracy");
    if (kpiAcc) kpiAcc.textContent = "--%";
    const kpiTurns = document.getElementById("kpi-turns");
    if (kpiTurns) kpiTurns.textContent = "0";
    const kpiErrors = document.getElementById("kpi-errors");
    if (kpiErrors) kpiErrors.textContent = "0";
    const aiSummary = document.getElementById("ai-summary");
    if (aiSummary) aiSummary.textContent = "Analyzing your speech history...";
    const aiFocus = document.getElementById("ai-focus-areas");
    if (aiFocus) aiFocus.innerHTML = "";

    const curInfo = LANG_DATA[currentLanguage] || LANG_DATA.en;
    userTranscript.textContent = curInfo.emptyTranscript;
    userTranscript.classList.add("empty");
    coachResponse.textContent = `"${curInfo.greeting}"`;
    feedbackBanner.classList.add("empty");
    feedbackActions.style.display = "none";
    setUIState("idle");

    alert("Context and conversation history have been successfully cleared!");
  } catch (err) {
    console.error("Reset error:", err);
    alert("Error resetting data: " + err.message);
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg><span>Clear All Context</span>`;
    }
  }
}

// Spacebar Key listener
window.addEventListener("keydown", (e) => {
  if (e.code === "Space" && e.target !== textInput && e.target.tagName !== "SELECT" && e.target.tagName !== "INPUT") {
    const voiceView = document.getElementById("view-voice");
    if (voiceView && voiceView.style.display === "none") return;
    e.preventDefault();
    handleOrbClick();
  }
});

window.addEventListener("DOMContentLoaded", () => {
  console.log("Language Coach ready.");
  changeLanguage(currentLanguage, false);
  // Pre-fetch health in background for settings tab
  loadSettings(false);
});
