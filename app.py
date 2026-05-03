import os
from flask import Flask, request, jsonify, render_template_string

# Gemini API
import google.generativeai as genai

# ==============================
# CONFIG
# ==============================
PROJECT_ID = "project-7eb55a30-5579-43cc-8d1"

# Load API Key from ENV
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)

# FIXED MODEL NAME ✅
MODEL_NAME = "gemini-1.5-flash-latest"

model = genai.GenerativeModel(MODEL_NAME)

# ==============================
# APP
# ==============================
app = Flask(__name__)

# ==============================
# HTML (YOUR UI EMBEDDED)
# ==============================
HTML_PAGE = """<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Election Process Education</title>
  <link href="https://api.fontshare.com/v2/css?f[]=satoshi@400,500,700&f[]=boska@500,700&display=swap" rel="stylesheet">
  <style>
    :root, [data-theme="light"] {
      --text-xs: clamp(0.75rem, 0.7rem + 0.25vw, 0.875rem);
      --text-sm: clamp(0.875rem, 0.8rem + 0.35vw, 1rem);
      --text-base: clamp(1rem, 0.95rem + 0.25vw, 1.125rem);
      --text-lg: clamp(1.125rem, 1rem + 0.75vw, 1.5rem);
      --text-xl: clamp(1.5rem, 1.2rem + 1.25vw, 2.25rem);
      --space-1: 0.25rem; --space-2: 0.5rem; --space-3: 0.75rem; --space-4: 1rem;
      --space-5: 1.25rem; --space-6: 1.5rem; --space-8: 2rem; --space-10: 2.5rem;
      --space-12: 3rem; --space-16: 4rem; --space-20: 5rem;
      --color-bg: #f7f6f2; --color-surface: #f9f8f5; --color-surface-2: #fbfbf9;
      --color-surface-offset: #edeae5; --color-border: #d4d1ca; --color-divider: #dcd9d5;
      --color-text: #28251d; --color-text-muted: #7a7974; --color-text-faint: #bab9b4;
      --color-text-inverse: #f9f8f4; --color-primary: #01696f; --color-primary-hover: #0c4e54;
      --color-success: #437a22; --color-warning: #964219; --radius-sm: 0.375rem; --radius-md: 0.5rem;
      --radius-lg: 0.75rem; --radius-xl: 1rem; --radius-full: 9999px; --shadow-sm: 0 1px 2px rgba(0,0,0,.06);
      --shadow-md: 0 4px 12px rgba(0,0,0,.08); --content-wide: 1200px;
      --font-display: 'Boska', Georgia, serif; --font-body: 'Satoshi', Inter, sans-serif;
    }
    [data-theme="dark"] {
      --color-bg: #171614; --color-surface: #1c1b19; --color-surface-2: #201f1d;
      --color-surface-offset: #22211f; --color-border: #393836; --color-divider: #262523;
      --color-text: #cdccca; --color-text-muted: #979592; --color-text-faint: #6d6b67;
      --color-text-inverse: #171614; --color-primary: #4f98a3; --color-primary-hover: #227f8b;
      --color-success: #6daa45; --color-warning: #bb653b; --shadow-sm: 0 1px 2px rgba(0,0,0,.2);
      --shadow-md: 0 4px 12px rgba(0,0,0,.3);
    }
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    html { scroll-behavior: smooth; }
    body { min-height: 100vh; font-family: var(--font-body); font-size: var(--text-base); line-height: 1.6; color: var(--color-text); background: var(--color-bg); }
    img, svg { display: block; max-width: 100%; }
    button, input, select { font: inherit; color: inherit; }
    button { cursor: pointer; border: none; background: none; }
    a { color: inherit; }
    :focus-visible { outline: 2px solid var(--color-primary); outline-offset: 3px; border-radius: var(--radius-sm); }
    .skip-link { position: absolute; left: -999px; top: var(--space-4); background: var(--color-primary); color: var(--color-text-inverse); padding: var(--space-3) var(--space-4); z-index: 1000; border-radius: var(--radius-md); }
    .skip-link:focus { left: var(--space-4); }
    .container { width: min(calc(100% - 2rem), var(--content-wide)); margin-inline: auto; }
    header { position: sticky; top: 0; z-index: 100; backdrop-filter: blur(14px); background: color-mix(in srgb, var(--color-bg) 88%, transparent); border-bottom: 1px solid color-mix(in srgb, var(--color-text) 10%, transparent); }
    .nav { display: flex; align-items: center; justify-content: space-between; gap: var(--space-4); padding: var(--space-4) 0; }
    .brand { display: flex; align-items: center; gap: var(--space-3); font-weight: 700; }
    .brand-logo { width: 42px; height: 42px; border-radius: 12px; background: linear-gradient(135deg, var(--color-primary), color-mix(in srgb, var(--color-primary) 65%, white)); display: grid; place-items: center; color: white; box-shadow: var(--shadow-sm); }
    .brand-name { font-size: var(--text-sm); letter-spacing: .04em; text-transform: uppercase; }
    .nav-actions { display: flex; align-items: center; gap: var(--space-3); }
    .theme-toggle, .mode-btn, .mini-btn { min-width: 44px; min-height: 44px; border-radius: var(--radius-full); border: 1px solid color-mix(in srgb, var(--color-text) 12%, transparent); background: var(--color-surface); display: inline-flex; align-items: center; justify-content: center; box-shadow: var(--shadow-sm); }
    .hero { padding: clamp(var(--space-10), 7vw, var(--space-20)) 0 var(--space-10); }
    .hero-grid { display: grid; grid-template-columns: 1.2fr .8fr; gap: var(--space-8); align-items: start; }
    .eyebrow { display: inline-flex; align-items: center; gap: var(--space-2); padding: var(--space-2) var(--space-3); border-radius: var(--radius-full); background: color-mix(in srgb, var(--color-primary) 10%, var(--color-surface)); color: var(--color-primary); font-size: var(--text-xs); font-weight: 700; text-transform: uppercase; letter-spacing: .08em; }
    h1 { font-family: var(--font-display); font-size: var(--text-xl); line-height: 1.05; margin-top: var(--space-4); max-width: 11ch; }
    .hero p { margin-top: var(--space-4); color: var(--color-text-muted); max-width: 62ch; }
    .hero-actions { display: flex; flex-wrap: wrap; gap: var(--space-3); margin-top: var(--space-6); }
    .btn { min-height: 44px; padding: var(--space-3) var(--space-5); border-radius: var(--radius-full); font-size: var(--text-sm); font-weight: 700; display: inline-flex; align-items: center; gap: var(--space-2); text-decoration: none; }
    .btn-primary { background: var(--color-primary); color: var(--color-text-inverse); }
    .btn-primary:hover { background: var(--color-primary-hover); }
    .btn-secondary { background: var(--color-surface); border: 1px solid color-mix(in srgb, var(--color-text) 12%, transparent); }
    .hero-card, .panel, .card, .timeline-item, .quiz-card { background: var(--color-surface); border: 1px solid color-mix(in srgb, var(--color-text) 10%, transparent); border-radius: var(--radius-xl); box-shadow: var(--shadow-sm); }
    .hero-card { padding: var(--space-6); }
    .hero-card h2, .panel h2, .section-title { font-size: var(--text-lg); line-height: 1.2; }
    .status-list { display: grid; gap: var(--space-4); margin-top: var(--space-5); }
    .status-row { display: flex; align-items: flex-start; gap: var(--space-3); }
    .status-dot { width: 12px; height: 12px; border-radius: 50%; margin-top: 0.5rem; background: var(--color-success); flex: 0 0 auto; }
    main { padding-bottom: var(--space-16); }
    .section { padding: var(--space-8) 0; }
    .layout { display: grid; grid-template-columns: 280px 1fr; gap: var(--space-6); align-items: start; }
    .sidebar { position: sticky; top: 88px; display: grid; gap: var(--space-4); }
    .panel { padding: var(--space-5); }
    .helper-text { color: var(--color-text-muted); font-size: var(--text-sm); margin-top: var(--space-2); }
    .chip-group { display: flex; flex-wrap: wrap; gap: var(--space-2); margin-top: var(--space-4); }
    .chip { padding: var(--space-2) var(--space-3); border-radius: var(--radius-full); border: 1px solid color-mix(in srgb, var(--color-text) 10%, transparent); background: var(--color-surface-2); font-size: var(--text-xs); font-weight: 600; }
    .stepper { display: grid; gap: var(--space-4); }
    .step-btn { width: 100%; text-align: left; padding: var(--space-4); border-radius: var(--radius-lg); background: var(--color-surface-2); border: 1px solid transparent; }
    .step-btn.active { border-color: color-mix(in srgb, var(--color-primary) 40%, transparent); background: color-mix(in srgb, var(--color-primary) 10%, var(--color-surface-2)); }
    .content-grid { display: grid; gap: var(--space-6); }
    .cards { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: var(--space-4); }
    .card { padding: var(--space-5); }
    .card h3 { font-size: var(--text-base); margin-bottom: var(--space-2); }
    .card p, .timeline-item p, .quiz-card p, .panel p, .detail p { color: var(--color-text-muted); }
    .timeline { display: grid; gap: var(--space-4); }
    .timeline-item { padding: var(--space-5); display: grid; gap: var(--space-2); }
    .timeline-top { display: flex; justify-content: space-between; gap: var(--space-3); align-items: center; }
    .badge { display: inline-flex; align-items: center; padding: .3rem .65rem; border-radius: var(--radius-full); font-size: var(--text-xs); font-weight: 700; }
    .badge.pre { background: color-mix(in srgb, var(--color-warning) 14%, var(--color-surface)); color: var(--color-warning); }
    .badge.during { background: color-mix(in srgb, var(--color-primary) 14%, var(--color-surface)); color: var(--color-primary); }
    .badge.post { background: color-mix(in srgb, var(--color-success) 14%, var(--color-surface)); color: var(--color-success); }
    .filters { display: flex; flex-wrap: wrap; gap: var(--space-3); }
    .select, .search { width: 100%; min-height: 48px; border-radius: var(--radius-lg); border: 1px solid color-mix(in srgb, var(--color-text) 12%, transparent); background: var(--color-surface-2); padding: 0 var(--space-4); }
    .quiz-card { padding: var(--space-6); }
    .quiz-options { display: grid; gap: var(--space-3); margin-top: var(--space-5); }
    .quiz-option { text-align: left; padding: var(--space-4); border-radius: var(--radius-lg); border: 1px solid color-mix(in srgb, var(--color-text) 12%, transparent); background: var(--color-surface-2); }
    .quiz-option.correct { border-color: color-mix(in srgb, var(--color-success) 50%, transparent); background: color-mix(in srgb, var(--color-success) 10%, var(--color-surface-2)); }
    .quiz-option.wrong { border-color: color-mix(in srgb, #b00020 50%, transparent); background: color-mix(in srgb, #b00020 8%, var(--color-surface-2)); }
    .result { margin-top: var(--space-4); font-size: var(--text-sm); font-weight: 600; }
    .progress { height: 10px; border-radius: var(--radius-full); background: var(--color-surface-offset); overflow: hidden; margin-top: var(--space-4); }
    .progress-bar { height: 100%; width: 0%; background: linear-gradient(90deg, var(--color-primary), var(--color-success)); transition: width .25s ease; }
    .detail { padding: var(--space-6); border-radius: var(--radius-xl); background: var(--color-surface); border: 1px solid color-mix(in srgb, var(--color-text) 10%, transparent); }
    .detail ul { margin-top: var(--space-4); padding-left: 1.2rem; color: var(--color-text-muted); }
    .detail li + li { margin-top: var(--space-2); }
    footer { padding: var(--space-10) 0 var(--space-16); color: var(--color-text-muted); }
    .footer-card { padding: var(--space-5); border-radius: var(--radius-xl); background: var(--color-surface); border: 1px solid color-mix(in srgb, var(--color-text) 10%, transparent); }
    @media (max-width: 960px) {
      .hero-grid, .layout, .cards { grid-template-columns: 1fr; }
      .sidebar { position: static; }
      h1 { max-width: 14ch; }
    }
    @media (prefers-reduced-motion: reduce) {
      *, *::before, *::after { animation-duration: 0.01ms !important; transition-duration: 0.01ms !important; scroll-behavior: auto !important; }
    }
  </style>
</head>
<body>
  <a href="#main" class="skip-link">Skip to content</a>
  <header>
    <div class="container nav">
      <div class="brand" aria-label="CivicPath logo and name">
        <div class="brand-logo" aria-hidden="true">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <path d="M4 9 12 4l8 5"></path>
            <path d="M6 10v8"></path>
            <path d="M12 7v11"></path>
            <path d="M18 10v8"></path>
            <path d="M3 19h18"></path>
          </svg>
        </div>
        <div>
          <div class="brand-name">CivicPath</div>
          <div class="helper-text" style="margin:0">Election learning assistant</div>
        </div>
      </div>
      <div class="nav-actions">
        <button class="mini-btn" id="focusQuiz" aria-label="Jump to quiz">?</button>
        <button class="theme-toggle" id="themeToggle" data-theme-toggle aria-label="Switch theme">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>
        </button>
      </div>
    </div>
  </header>

  <main id="main">
    <section class="hero">
      <div class="container hero-grid">
        <div>
          <span class="eyebrow">Interactive civic learning</span>
          <h1>Understand election steps without getting lost in the process.</h1>
          <p>This assistant explains what happens before, during, and after an election using a guided step flow, a timeline view, and a quick knowledge quiz. It is designed to make complex civic procedures easier to follow for students, first-time voters, and general users.</p>
          <div class="hero-actions">
            <a class="btn btn-primary" href="#guide">Start the guide</a>
            <a class="btn btn-secondary" href="#timeline">View timeline</a>
          </div>
        </div>
        <aside class="hero-card" aria-labelledby="snapshotTitle">
          <h2 id="snapshotTitle">What this assistant covers</h2>
          <div class="status-list">
            <div class="status-row"><span class="status-dot"></span><div><strong>Preparation:</strong> voter registration, candidate nomination, and campaign period.</div></div>
            <div class="status-row"><span class="status-dot"></span><div><strong>Election day:</strong> polling, identification checks, ballot casting, and counting basics.</div></div>
            <div class="status-row"><span class="status-dot"></span><div><strong>After voting:</strong> counting, result declaration, dispute handling, and transition steps.</div></div>
          </div>
          <div class="chip-group" aria-label="audience tags">
            <span class="chip">Students</span>
            <span class="chip">First-time voters</span>
            <span class="chip">Civic education</span>
            <span class="chip">Interactive learning</span>
          </div>
        </aside>
      </div>
    </section>

    <section class="section" id="guide">
      <div class="container layout">
        <aside class="sidebar">
          <div class="panel">
            <h2>Guided steps</h2>
            <p class="helper-text">Choose a stage to see the main tasks, people involved, and common questions.</p>
            <div class="stepper" id="stepper"></div>
          </div>
          <div class="panel">
            <h2>Modes</h2>
            <p class="helper-text">Switch between concise learning and deeper detail.</p>
            <div class="chip-group">
              <button class="mode-btn" data-mode="simple" aria-pressed="true">S</button>
              <button class="mode-btn" data-mode="detailed" aria-pressed="false">D</button>
            </div>
          </div>
        </aside>

        <div class="content-grid">
          <section class="detail" id="detailPanel" aria-live="polite"></section>
          <section>
            <h2 class="section-title">Key parts</h2>
            <p class="helper-text">Each card highlights a piece of the election process that users often want clarified.</p>
            <div class="cards" id="cards"></div>
          </section>
        </div>
      </div>
    </section>

    <section class="section" id="timeline">
      <div class="container">
        <h2 class="section-title">Election timeline</h2>
        <p class="helper-text">Use the filter to focus on the stage you want to learn first.</p>
        <div class="filters" style="margin: var(--space-4) 0 var(--space-5)">
          <select class="select" id="timelineFilter" aria-label="Filter election timeline">
            <option value="all">All stages</option>
            <option value="pre">Before voting</option>
            <option value="during">Voting day</option>
            <option value="post">After voting</option>
          </select>
        </div>
        <div class="timeline" id="timelineList"></div>
      </div>
    </section>

    <section class="section" id="quiz">
      <div class="container">
        <div class="quiz-card">
          <h2 class="section-title">Quick check</h2>
          <p>Answer a few questions to test whether the sequence and responsibilities are becoming clear.</p>
          <div class="progress" aria-hidden="true"><div class="progress-bar" id="progressBar"></div></div>
          <div id="quizArea"></div>
        </div>
      </div>
    </section>
  </main>

  <footer>
    <div class="container">
      <div class="footer-card">
        This concept fits an educational civic-assistant theme because it teaches a structured public process through step-by-step guidance, timeline navigation, and interactive checks.
      </div>
    </div>
  </footer>

  <script>
    const steps = [
      {
        title: 'Voter registration',
        simple: 'Eligible citizens register so they can appear on the voter list before election day.',
        detailed: 'Election authorities prepare rolls, publish deadlines, and allow eligible citizens to confirm or correct their registration details. This stage is critical because voters who are not properly listed may face problems when they try to vote.',
        points: ['Check eligibility rules and deadlines.', 'Verify name, address, and constituency details.', 'Resolve corrections before final voter rolls close.']
      },
      {
        title: 'Candidate nomination',
        simple: 'Political parties or independent candidates submit documents to contest the election.',
        detailed: 'Candidates file nominations, submit required forms, and go through scrutiny by the election authority. Valid nominations are accepted, rejected ones can be challenged under the rules.',
        points: ['Submission of nomination papers.', 'Verification and scrutiny of documents.', 'Publication of the final contesting candidate list.']
      },
      {
        title: 'Campaign period',
        simple: 'Candidates explain their promises and ask voters for support within legal campaign limits.',
        detailed: 'The campaign period includes rallies, outreach, debates, media messaging, and spending restrictions. Election rules usually control silence periods, campaign conduct, and fairness requirements.',
        points: ['Public meetings and communication.', 'Rules on spending and conduct.', 'Campaign silence before polling.']
      },
      {
        title: 'Polling day',
        simple: 'Voters arrive at polling stations, confirm identity, and cast their ballots.',
        detailed: 'Polling officials verify identity, check the voter list, issue ballots or enable voting machines, and ensure secrecy of the vote. The process also includes queue management, observer presence, and accessibility support.',
        points: ['Identity and voter-list verification.', 'Ballot casting in a secret manner.', 'Polling station management and closing procedure.']
      },
      {
        title: 'Counting and results',
        simple: 'Votes are counted and the winner is declared based on the official rules.',
        detailed: 'After polling closes, ballots or machine records are secured and counting begins under supervision. Authorities tabulate results, resolve counting issues, and formally declare winners once the legal process is complete.',
        points: ['Secure transport or sealing of records.', 'Counting under supervision.', 'Official declaration and publication of results.']
      }
    ];

    const cards = [
      { title: 'Who runs the process?', text: 'Election commissions or similar authorities prepare schedules, supervise polling, and certify results.' },
      { title: 'Why timelines matter', text: 'Every stage has deadlines, so missing a registration or nomination date can change who participates.' },
      { title: 'What makes voting fair?', text: 'Rules around secrecy, equal treatment, monitoring, and counting transparency help protect trust.' },
      { title: 'What happens if there is a dispute?', text: 'Many systems allow recounts, complaints, or legal challenges after counting or declaration.' }
    ];

    const timeline = [
      { phase: 'pre', label: 'Pre-election', name: 'Roll preparation and registration', detail: 'Authorities prepare and update voter lists; citizens confirm enrollment and corrections.', badge: 'pre' },
      { phase: 'pre', label: 'Pre-election', name: 'Candidate filing and scrutiny', detail: 'Nomination papers are submitted and checked before the final candidate list is published.', badge: 'pre' },
      { phase: 'pre', label: 'Pre-election', name: 'Campaign window', detail: 'Candidates campaign under rules about publicity, spending, and conduct.', badge: 'pre' },
      { phase: 'during', label: 'Polling day', name: 'Voting opens', detail: 'Officials prepare booths, verify voters, and allow ballots or machine-based voting.', badge: 'during' },
      { phase: 'during', label: 'Polling day', name: 'Poll closing', detail: 'Voting ends at the scheduled time and materials are sealed for counting.', badge: 'during' },
      { phase: 'post', label: 'Post-election', name: 'Counting process', detail: 'Votes are tabulated in the presence of observers and authorized agents.', badge: 'post' },
      { phase: 'post', label: 'Post-election', name: 'Result declaration', detail: 'Final results are published and the winner is officially declared.', badge: 'post' }
    ];

    const quiz = [
      {
        q: 'Which stage usually comes first?',
        options: ['Counting votes', 'Voter registration', 'Result declaration'],
        answer: 1,
        explain: 'Registration or roll preparation generally happens before voting and counting.'
      },
      {
        q: 'What is a core purpose of polling-day identity checks?',
        options: ['To speed up campaigns', 'To verify the voter is eligible to vote', 'To announce winners early'],
        answer: 1,
        explain: 'Identity checks help confirm the person is the correct eligible voter.'
      },
      {
        q: 'What usually happens after polls close?',
        options: ['Campaign speeches begin again', 'Counting and tabulation start', 'Registration reopens'],
        answer: 1,
        explain: 'Once polling ends, ballots or voting records move into the counting stage.'
      }
    ];

    let mode = 'simple';
    let quizIndex = 0;
    let score = 0;

    const stepper = document.getElementById('stepper');
    const detailPanel = document.getElementById('detailPanel');
    const cardsWrap = document.getElementById('cards');
    const timelineList = document.getElementById('timelineList');
    const timelineFilter = document.getElementById('timelineFilter');
    const quizArea = document.getElementById('quizArea');
    const progressBar = document.getElementById('progressBar');
    const focusQuiz = document.getElementById('focusQuiz');

    function renderSteps(active = 0) {
      stepper.innerHTML = '';
      steps.forEach((step, index) => {
        const btn = document.createElement('button');
        btn.className = 'step-btn' + (index === active ? ' active' : '');
        btn.innerHTML = `<strong>${index + 1}. ${step.title}</strong><div class="helper-text">Tap to open this stage</div>`;
        btn.addEventListener('click', () => {
          renderSteps(index);
          renderDetail(index);
        });
        stepper.appendChild(btn);
      });
    }

    function renderDetail(index) {
      const step = steps[index];
      detailPanel.innerHTML = `
        <h2>${step.title}</h2>
        <p style="margin-top: var(--space-3)">${mode === 'simple' ? step.simple : step.detailed}</p>
        <ul>
          ${step.points.map(point => `<li>${point}</li>`).join('')}
        </ul>
      `;
    }

    function renderCards() {
      cardsWrap.innerHTML = cards.map(card => `
        <article class="card">
          <h3>${card.title}</h3>
          <p>${card.text}</p>
        </article>
      `).join('');
    }

    function renderTimeline(filter = 'all') {
      const filtered = filter === 'all' ? timeline : timeline.filter(item => item.phase === filter);
      timelineList.innerHTML = filtered.map(item => `
        <article class="timeline-item">
          <div class="timeline-top">
            <strong>${item.name}</strong>
            <span class="badge ${item.badge}">${item.label}</span>
          </div>
          <p>${item.detail}</p>
        </article>
      `).join('');
    }

    function updateProgress() {
      progressBar.style.width = `${(quizIndex / quiz.length) * 100}%`;
    }

    function renderQuiz() {
      updateProgress();
      if (quizIndex >= quiz.length) {
        progressBar.style.width = '100%';
        quizArea.innerHTML = `
          <div class="result">You scored ${score} out of ${quiz.length}.</div>
          <p style="margin-top: var(--space-3)">This quick check reinforces the order of election stages and the purpose of each step.</p>
          <div class="hero-actions">
            <button class="btn btn-primary" id="restartQuiz">Retake quiz</button>
          </div>
        `;
        document.getElementById('restartQuiz').addEventListener('click', () => {
          quizIndex = 0; score = 0; renderQuiz();
        });
        return;
      }
      const item = quiz[quizIndex];
      quizArea.innerHTML = `
        <div style="margin-top: var(--space-5)">
          <div class="helper-text">Question ${quizIndex + 1} of ${quiz.length}</div>
          <h3 style="font-size: var(--text-lg); margin-top: var(--space-2)">${item.q}</h3>
          <div class="quiz-options">
            ${item.options.map((opt, i) => `<button class="quiz-option" data-index="${i}">${opt}</button>`).join('')}
          </div>
          <div class="result" id="quizResult" aria-live="polite"></div>
        </div>
      `;
      document.querySelectorAll('.quiz-option').forEach(btn => {
        btn.addEventListener('click', () => {
          const selected = Number(btn.dataset.index);
          const buttons = document.querySelectorAll('.quiz-option');
          buttons.forEach((b, idx) => {
            b.disabled = true;
            if (idx === item.answer) b.classList.add('correct');
            if (idx === selected && idx !== item.answer) b.classList.add('wrong');
          });
          const result = document.getElementById('quizResult');
          const correct = selected === item.answer;
          if (correct) score += 1;
          result.textContent = (correct ? 'Correct. ' : 'Not quite. ') + item.explain;
          setTimeout(() => { quizIndex += 1; renderQuiz(); }, 1200);
        });
      });
    }

    document.querySelectorAll('[data-mode]').forEach(btn => {
      btn.addEventListener('click', () => {
        mode = btn.dataset.mode;
        document.querySelectorAll('[data-mode]').forEach(b => b.setAttribute('aria-pressed', String(b === btn)));
        renderDetail([...stepper.children].findIndex(el => el.classList.contains('active')) || 0);
      });
    });

    timelineFilter.addEventListener('change', (e) => renderTimeline(e.target.value));
    focusQuiz.addEventListener('click', () => document.getElementById('quiz').scrollIntoView({ behavior: 'smooth' }));

    (function(){
      const t = document.getElementById('themeToggle');
      const r = document.documentElement;
      let d = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
      r.setAttribute('data-theme', d);
      function icon() {
        t.innerHTML = d === 'dark'
          ? '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg>'
          : '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>';
      }
      icon();
      t.addEventListener('click', () => {
        d = d === 'dark' ? 'light' : 'dark';
        r.setAttribute('data-theme', d);
        icon();
      });
    })();

    renderSteps(0);
    renderDetail(0);
    renderCards();
    renderTimeline();
    renderQuiz();
  </script>
</body>
</html>
"""
# ⬆️ Replace this line with your full HTML (exactly what you sent)

# ==============================
# ROUTES
# ==============================

@app.route("/")
def home():
    return render_template_string(HTML_PAGE)


@app.route("/generate", methods=["POST"])
def generate():
    try:
        data = request.json
        prompt = data.get("prompt", "")

        full_prompt = f"""
        You are an Election Commission assistant.
        Explain clearly and simply.

        {prompt}
        """

        response = model.generate_content(full_prompt)

        return jsonify({
            "status": "success",
            "response": response.text
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        })


# ==============================
# RUN
# ==============================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
