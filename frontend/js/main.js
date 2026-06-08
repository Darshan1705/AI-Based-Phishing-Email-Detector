/**
 * main.js
 * Core UI orchestrator:
 *  - Calls /predict for textarea analysis
 *  - Delegates file uploads to Uploader
 *  - Renders results via renderResult()
 *  - Controls dark-mode toggle
 *  - Manages history dashboard
 */

const API_BASE = 'http://localhost:5000';

// ---------------------------------------------------------------------------
// DOM references (populated on DOMContentLoaded)
// ---------------------------------------------------------------------------
let emailInput, analyzeBtn, clearBtn, loadingOverlay;
let resultSection, predictionBadge, confidenceBar, confidenceValue;
let reasonsList, highlightedText, resultIcon, resultTitle;
let toastEl, historyList, historySection;
let darkModeToggle, analysisCount;

// scan history stored in memory
const history = [];

// ---------------------------------------------------------------------------
// Bootstrap
// ---------------------------------------------------------------------------
document.addEventListener('DOMContentLoaded', () => {
  emailInput     = document.getElementById('email-input');
  analyzeBtn     = document.getElementById('analyze-btn');
  clearBtn       = document.getElementById('clear-btn');
  loadingOverlay = document.getElementById('loading-overlay');

  resultSection    = document.getElementById('result-section');
  predictionBadge  = document.getElementById('prediction-badge');
  confidenceBar    = document.getElementById('confidence-bar');
  confidenceValue  = document.getElementById('confidence-value');
  reasonsList      = document.getElementById('reasons-list');
  highlightedText  = document.getElementById('highlighted-text');
  resultIcon       = document.getElementById('result-icon');
  resultTitle      = document.getElementById('result-title');

  toastEl         = document.getElementById('toast');
  historyList     = document.getElementById('history-list');
  historySection  = document.getElementById('history-section');
  darkModeToggle  = document.getElementById('dark-mode-toggle');
  analysisCount   = document.getElementById('analysis-count');

  // Dark mode — restore preference
  const savedTheme = localStorage.getItem('theme');
  if (savedTheme === 'light') {
    document.body.classList.remove('dark');
    document.body.classList.add('light');
    if (darkModeToggle) darkModeToggle.checked = false;
  }

  // Buttons
  analyzeBtn?.addEventListener('click', handleAnalyze);
  clearBtn?.addEventListener('click', handleClear);
  darkModeToggle?.addEventListener('change', handleThemeToggle);

  // Keyboard shortcut: Ctrl+Enter → analyze
  emailInput?.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') handleAnalyze();
  });

  // File upload
  Uploader.init(
    'drop-zone',
    'file-input',
    (data, meta) => renderResult(data, meta),
    (msg)        => showToast(msg, 'error'),
    (loading)    => setLoading(loading)
  );

  updateAnalysisCount();
});

// ---------------------------------------------------------------------------
// Analyze (text input)
// ---------------------------------------------------------------------------
async function handleAnalyze() {
  const text = emailInput?.value.trim();

  if (!text) {
    showToast('Please paste some email content before analyzing.', 'warning');
    emailInput?.focus();
    return;
  }

  setLoading(true);

  try {
    const response = await fetch(`${API_BASE}/predict`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text }),
    });

    const data = await response.json();

    if (!response.ok) {
      showToast(data.error || 'Prediction failed.', 'error');
      return;
    }

    renderResult(data, { fromFile: false });

  } catch {
    showToast(
      'Cannot connect to the backend. Make sure Flask is running on port 5000.',
      'error'
    );
  } finally {
    setLoading(false);
  }
}

// ---------------------------------------------------------------------------
// Render result
// ---------------------------------------------------------------------------
function renderResult(data, meta = {}) {
  const { prediction, confidence, reasons = [], explanation = {} } = data;
  const isSpam = prediction === 'spam';

  // ---- Badge & icon ----
  predictionBadge.textContent = isSpam ? '⚠ SPAM' : '✓ NOT SPAM';
  predictionBadge.className   = 'prediction-badge ' + (isSpam ? 'badge-spam' : 'badge-ham');

  resultIcon.textContent  = isSpam ? '🛡️' : '✅';
  resultTitle.textContent = isSpam ? 'Spam Detected' : 'Looks Clean';
  resultSection.className = 'result-section ' + (isSpam ? 'result-spam' : 'result-ham');

  // ---- Confidence bar ----
  const displayConf = Math.round(confidence);
  confidenceValue.textContent = `${displayConf}%`;
  confidenceBar.style.width   = `${displayConf}%`;
  confidenceBar.className     = 'confidence-fill ' + (isSpam ? 'fill-spam' : 'fill-ham');

  // ---- Reasons ----
  reasonsList.innerHTML = '';
  if (reasons.length === 0) {
    const li = document.createElement('li');
    li.textContent = 'No specific triggers detected.';
    li.className   = 'reason-item reason-none';
    reasonsList.appendChild(li);
  } else {
    for (const reason of reasons) {
      const li = document.createElement('li');
      li.textContent = reason;
      li.className   = 'reason-item';
      reasonsList.appendChild(li);
    }
  }

  // ---- Highlighted text ----
  const rawText = emailInput?.value || '';
  const highlighted = Highlighter.highlight(rawText, explanation);
  highlightedText.innerHTML = highlighted || '<em>No text to display.</em>';

  // ---- Legend visibility ----
  const legendSpam    = document.getElementById('legend-spam');
  const legendUrgency = document.getElementById('legend-urgency');
  const legendLink    = document.getElementById('legend-link');

  if (legendSpam)    legendSpam.style.display    = explanation.spam_keywords?.length    ? '' : 'none';
  if (legendUrgency) legendUrgency.style.display = explanation.urgency_phrases?.length  ? '' : 'none';
  if (legendLink)    legendLink.style.display    = explanation.suspicious_links?.length ? '' : 'none';

  // ---- Show result section ----
  resultSection.style.display = 'block';
  resultSection.scrollIntoView({ behavior: 'smooth', block: 'start' });

  // ---- History ----
  addToHistory({ prediction, confidence, reasons, meta });
}

// ---------------------------------------------------------------------------
// History dashboard
// ---------------------------------------------------------------------------
function addToHistory(entry) {
  history.unshift({ ...entry, timestamp: new Date() });
  if (history.length > 10) history.pop();

  if (historySection) historySection.style.display = 'block';
  renderHistory();
  updateAnalysisCount();
}

function renderHistory() {
  if (!historyList) return;
  historyList.innerHTML = '';

  for (const item of history) {
    const isSpam = item.prediction === 'spam';
    const card   = document.createElement('div');
    card.className = 'history-card ' + (isSpam ? 'hc-spam' : 'hc-ham');

    const time = item.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const src  = item.meta?.fromFile
      ? `File: ${item.meta.filename}`
      : 'Text input';

    const badge = document.createElement('span');
    badge.className = `hc-badge ${isSpam ? 'hc-badge-spam' : 'hc-badge-ham'}`;
    badge.textContent = isSpam ? 'SPAM' : 'HAM';

    const confidence = document.createElement('span');
    confidence.className = 'hc-conf';
    confidence.textContent = `${Math.round(item.confidence)}%`;

    const source = document.createElement('span');
    source.className = 'hc-source';
    source.textContent = src;

    const timeEl = document.createElement('span');
    timeEl.className = 'hc-time';
    timeEl.textContent = time;

    card.appendChild(badge);
    card.appendChild(confidence);
    card.appendChild(source);
    card.appendChild(timeEl);

    historyList.appendChild(card);
  }
}

function updateAnalysisCount() {
  if (analysisCount) analysisCount.textContent = history.length;
}

// ---------------------------------------------------------------------------
// Utilities
// ---------------------------------------------------------------------------
function handleClear() {
  if (emailInput) emailInput.value = '';
  if (resultSection) resultSection.style.display = 'none';
}

function setLoading(state) {
  if (loadingOverlay) loadingOverlay.style.display = state ? 'flex' : 'none';
  if (analyzeBtn)     analyzeBtn.disabled           = state;
}

function handleThemeToggle() {
  const isLight = !darkModeToggle.checked;
  document.body.classList.toggle('light', isLight);
  document.body.classList.toggle('dark', !isLight);
  localStorage.setItem('theme', isLight ? 'light' : 'dark');
}

let toastTimer;
function showToast(message, type = 'info') {
  if (!toastEl) return;
  toastEl.textContent = message;
  toastEl.className   = `toast toast-${type} show`;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toastEl.classList.remove('show'), 4000);
}
