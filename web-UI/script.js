const appViews = {
  homeView: document.getElementById('homeView'),
  speakView: document.getElementById('speakView'),
  quizView: document.getElementById('quizView'),
  analyticsView: document.getElementById('analyticsView')
};

function showView(viewId) {
  Object.entries(appViews).forEach(([key, element]) => {
    element.classList.toggle('active', key === viewId || (viewId === 'homeView' && key === 'homeView'));
  });
}

function bindViewNavigation() {
  document.querySelectorAll('[data-target]').forEach((button) => {
    button.addEventListener('click', () => showView(button.dataset.target));
  });
}

function addBubble(containerId, text, sender, side) {
  const container = document.getElementById(containerId);
  const bubble = document.createElement('div');
  bubble.className = `message-bubble ${side}`;

  const label = document.createElement('span');
  label.className = 'message-meta';
  label.textContent = sender;

  const textNode = document.createElement('div');
  textNode.className = 'message-text';
  textNode.textContent = text;

  bubble.append(label, textNode);
  container.appendChild(bubble);
  container.scrollTop = container.scrollHeight;
}

function initSpeakView() {
  const micButton = document.getElementById('toggleMic');
  const micStatus = document.getElementById('micStatus');
  let isRecording = false;

  micButton.addEventListener('click', () => {
    isRecording = !isRecording;

    if (isRecording) {
      micButton.textContent = '⏹️ Aufnahme stoppen';
      micButton.style.background = 'linear-gradient(180deg, #ef4444, #dc2626)';
      micStatus.textContent = '🔴 Zuhören & Analysieren...';
      micStatus.classList.add('recording');
      addBubble('speakChat', 'Ich habe dein letztes Gespräch aufgenommen und analysiere gerade Satzbau und Aussprache.', 'VoxAI Feedback', 'left');
    } else {
      micButton.textContent = '🎙️ Aufnahme starten';
      micButton.style.background = 'linear-gradient(180deg, #10b981, #059669)';
      micStatus.textContent = 'Bereit für Spracheingabe';
      micStatus.classList.remove('recording');
      addBubble('speakChat', 'Aufnahme beendet. Die letzten Formulierungen wurden gespeichert.', 'VoxAI Feedback', 'left');
    }
  });

  addBubble('speakChat', 'Hallo! Sprich in dein Mikrofon, damit ich deine Grammatik und deinen Redefluss analysieren kann.', 'VoxAI Feedback', 'left');
}

function initQuizView() {
  const input = document.getElementById('quizInput');
  const sendBtn = document.getElementById('sendQuizAnswer');

  const addDemoQuiz = () => {
    addBubble('quizChat', 'Willkommen zum Grammatik-Quiz! Lass uns deine Schwachstellen trainieren.', 'VoxAI Quiz-Coach', 'left');
    addMultipleChoiceQuestion(
      'Welcher Satz verwendet den Dativ korrekt?',
      ['Ich gebe den Mann das Buch.', 'Ich gebe dem Mann das Buch.', 'Ich gebe das Mann ein Buch.'],
      1
    );
  };

  sendBtn.addEventListener('click', () => {
    const value = input.value.trim();
    if (!value) {
      return;
    }

    addBubble('quizChat', value, 'Du', 'right');
    input.value = '';
  });

  input.addEventListener('keydown', (event) => {
    if (event.key === 'Enter') {
      sendBtn.click();
    }
  });

  addDemoQuiz();
}

function addMultipleChoiceQuestion(question, options, correctIndex) {
  const container = document.getElementById('quizChat');
  const card = document.createElement('div');
  card.className = 'question-card';

  const title = document.createElement('h4');
  title.textContent = `❓ ${question}`;

  const optionList = document.createElement('div');
  optionList.className = 'answer-options';

  const buttons = options.map((option, index) => {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'answer-option';
    button.textContent = `${String.fromCharCode(65 + index)})  ${option}`;
    button.addEventListener('click', () => evaluateAnswer(buttons, index, correctIndex));
    return button;
  });

  buttons.forEach((button) => optionList.appendChild(button));
  card.append(title, optionList);
  container.appendChild(card);
  container.scrollTop = container.scrollHeight;
}

function evaluateAnswer(buttons, selectedIndex, correctIndex) {
  buttons.forEach((button) => button.disabled = true);

  if (selectedIndex === correctIndex) {
    buttons[selectedIndex].classList.add('correct');
    addFeedbackBox('success', 'Sehr gut! Das war die korrekte Antwort.');
  } else {
    buttons[selectedIndex].classList.add('wrong');
    buttons[correctIndex].classList.add('correct');
    addFeedbackBox('failure', `Die richtige Antwort wäre Option ${String.fromCharCode(65 + correctIndex)} gewesen.`);
  }
}

function addFeedbackBox(type, text) {
  const container = document.getElementById('quizChat');
  const box = document.createElement('div');
  box.className = `feedback-box ${type === 'success' ? 'success' : 'failure'}`;

  const title = document.createElement('h5');
  title.textContent = type === 'success' ? '✅ Richtig!' : '❌ Nicht ganz...';

  const message = document.createElement('p');
  message.textContent = text;

  box.append(title, message);
  container.appendChild(box);
  container.scrollTop = container.scrollHeight;
}

function renderAnalyticsData() {
  const categories = [
    { category: 'Artikel & Genus (der/die/das)', count: 18, percentage: 0.85, color: '#ef4444' },
    { category: 'Dativ vs. Akkusativ', count: 11, percentage: 0.55, color: '#f59e0b' },
    { category: 'Satzstellung / Verbstellung', count: 5, percentage: 0.25, color: '#10b981' },
    { category: 'Aussprache & Redefluss', count: 2, percentage: 0.1, color: '#3b82f6' }
  ];

  const categoriesPanel = document.getElementById('categoriesPanel');
  categoriesPanel.innerHTML = categories
    .map((item) => `
      <div class="category-row">
        <div class="category-name">${item.category}</div>
        <div class="progress-track">
          <div class="progress-fill" style="width:${item.percentage * 100}%; background:${item.color};"></div>
        </div>
        <div class="category-count">${item.count} Fehler</div>
      </div>
    `)
    .join('');

  const recommendations = [
    {
      title: 'Dativ nach Präpositionen festigen',
      description: "Du verwechselst häufig den Akkusativ mit dem Dativ bei Präpositionen wie 'mit', 'bei' und 'nach'. Mache hierzu am besten ein gezieltes Quiz.",
      color: '#ef4444'
    },
    {
      title: 'Sprechtempo leicht drosseln',
      description: 'In freien Gesprächsphasen neigst du bei Nebensätzen zu Satzbaufehlern. Etwas langsamer zu sprechen hilft dir, das Verb ans Ende zu stellen.',
      color: '#f59e0b'
    }
  ];

  const recommendationsPanel = document.getElementById('recommendationsPanel');
  recommendationsPanel.innerHTML = recommendations
    .map((item) => `
      <div class="recommendation-card">
        <div class="recommendation-bar" style="background:${item.color};"></div>
        <div class="recommendation-body">
          <h4>${item.title}</h4>
          <p>${item.description}</p>
        </div>
      </div>
    `)
    .join('');

  const details = [
    {
      wrong: 'Ich fahre mit das Auto.',
      correct: 'Ich fahre mit dem Auto.',
      explanation: "Die Präposition 'mit' verlangt immer den Dativ (das Auto -> dem Auto)."
    },
    {
      wrong: 'Weil ich habe keine Zeit.',
      correct: 'Weil ich keine Zeit habe.',
      explanation: "In Nebensätzen mit 'weil' wandert das konjugierte Verb an das Ende des Satzes."
    }
  ];

  const detailsPanel = document.getElementById('detailsPanel');
  detailsPanel.innerHTML = details
    .map((item) => `
      <div class="error-card">
        <p class="wrong">❌ Falsch: "${item.wrong}"</p>
        <p class="correct">✅ Richtig: "${item.correct}"</p>
        <div class="explanation">💡 Grund: ${item.explanation}</div>
      </div>
    `)
    .join('');
}

bindViewNavigation();
initSpeakView();
initQuizView();
renderAnalyticsData();
showView('homeView');
