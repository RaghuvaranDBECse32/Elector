from flask import Flask, request, jsonify, render_template_string
import google.generativeai as genai
import os, time, uuid
from collections import defaultdict
from dotenv import load_dotenv

load_dotenv()

# ── CONFIG ────────────────────────────────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
MODEL_NAME     = os.getenv("MODEL_NAME", "gemini-1.5-flash")

app   = Flask(__name__)
model = None

if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel(MODEL_NAME)
        print(f"[OK] Gemini connected → {MODEL_NAME}")
    except Exception as e:
        print(f"[WARN] Gemini init failed: {e}")
else:
    print("[WARN] No GEMINI_API_KEY — running in fallback mode")

SYSTEM_PROMPT = (
    "You are ELECTOR, an official Election Commission of India (ECI) civic education AI. "
    "Answer only questions about Indian elections, voter rights, ECI rules, EVMs, VVPAT, "
    "voter registration, Model Code of Conduct, nominations, and results. "
    "Be formal, accurate, unbiased, and concise. Use bullet points for steps. "
    "If the question is unrelated to elections or Indian civics, politely redirect."
)

# ── RATE LIMITING ─────────────────────────────────────────────────────────────
_rate = defaultdict(list)
def is_limited(ip):
    now = time.time()
    _rate[ip] = [t for t in _rate[ip] if now - t < 60]
    if len(_rate[ip]) >= 20: return True
    _rate[ip].append(now); return False

# ── CHAT SESSIONS ─────────────────────────────────────────────────────────────
sessions = {}

# ── STATIC FALLBACK ANSWERS ───────────────────────────────────────────────────
FALLBACK = {
    "mcc":      "The Model Code of Conduct (MCC) is a set of ECI guidelines activated when the election schedule is announced. It prevents the ruling government from using state resources for electoral gain.",
    "evm":      "EVMs (Electronic Voting Machines) are standalone, air-gapped devices with no internet, Wi-Fi, or Bluetooth. Voters press a button next to their chosen candidate's name.",
    "vvpat":    "VVPAT (Voter Verifiable Paper Audit Trail) prints a slip showing your chosen candidate's name and symbol, visible through a glass window for 7 seconds.",
    "register": "To register: visit voters.eci.gov.in or the Voter Helpline App → fill Form 6 → upload photo and address proof. Must be 18+ on the qualifying date.",
    "eci":      "The Election Commission of India is an independent body under Article 324 of the Constitution. It supervises all elections to Parliament and State Legislatures.",
    "epic":     "EPIC (Electors' Photo Identity Card) is India's primary voter ID. Aadhaar, passport, and 11 other documents are also accepted at polling booths.",
    "result":   "After polling ends, EVMs are sealed and transported to counting centres. Votes are counted in rounds under observer supervision, and the Returning Officer officially declares the winner.",
    "nomination":"Candidates file nomination papers with the Returning Officer within the notified schedule. Papers are scrutinised and candidates may withdraw within the allowed window.",
}

# ── HTML ──────────────────────────────────────────────────────────────────────
HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1.0"/>
<title>ELECTOR — India Election Assistant</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet"/>
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0;}
html{scroll-behavior:smooth;}
body{font-family:'Inter',sans-serif;background:#f4f6fb;color:#222;}
/* NAV */
nav{position:sticky;top:0;z-index:200;background:rgba(244,246,251,0.93);
  backdrop-filter:blur(12px);border-bottom:1px solid #e0e4ed;
  display:flex;align-items:center;justify-content:space-between;
  padding:0 clamp(16px,4vw,64px);height:60px;}
.nav-brand{font-weight:800;color:#003366;font-size:1.1rem;display:flex;align-items:center;gap:10px;}
.nav-links{display:flex;gap:4px;}
.nav-links a{padding:7px 14px;border-radius:999px;text-decoration:none;color:#444;
  font-size:0.85rem;font-weight:600;transition:background .15s,color .15s;}
.nav-links a:hover,.nav-links a.active{background:#003366;color:#fff;}
@media(max-width:640px){.nav-links{display:none;}}
/* TRICOLOR */
.tricolor{height:5px;background:linear-gradient(90deg,#FF9933 33%,#fff 33%,#fff 66%,#138808 66%);}
/* HERO */
.hero{background:linear-gradient(135deg,#003366 0%,#0057b7 55%,#0096c7 100%);
  color:#fff;padding:clamp(40px,6vw,80px) clamp(16px,5vw,64px);
  display:grid;grid-template-columns:1fr 1fr;gap:32px;align-items:center;}
@media(max-width:768px){.hero{grid-template-columns:1fr;}}
.hero-badge{display:inline-block;background:rgba(255,255,255,0.15);border-radius:999px;
  padding:5px 14px;font-size:0.78rem;font-weight:700;text-transform:uppercase;
  letter-spacing:.07em;margin-bottom:14px;}
.hero h1{font-size:clamp(1.8rem,4vw,2.8rem);font-weight:800;line-height:1.1;margin-bottom:12px;}
.hero p{opacity:.88;font-size:1rem;line-height:1.6;max-width:480px;}
.hero-btns{display:flex;flex-wrap:wrap;gap:12px;margin-top:22px;}
.btn{display:inline-flex;align-items:center;gap:8px;padding:11px 22px;border-radius:999px;
  font-weight:700;font-size:0.9rem;text-decoration:none;border:none;cursor:pointer;
  transition:transform .15s,box-shadow .15s;}
.btn:hover{transform:translateY(-2px);box-shadow:0 6px 18px rgba(0,0,0,.15);}
.btn-white{background:#fff;color:#003366;}
.btn-outline{background:rgba(255,255,255,.12);color:#fff;border:2px solid rgba(255,255,255,.5);}
.btn-primary{background:#01696f;color:#fff;box-shadow:0 4px 14px rgba(1,105,111,.35);}
.hero-card{background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.2);
  border-radius:20px;padding:24px;backdrop-filter:blur(8px);}
.hero-card h3{font-size:.95rem;margin-bottom:16px;opacity:.9;}
.stat-row{display:grid;grid-template-columns:1fr 1fr;gap:10px;}
.stat{background:rgba(255,255,255,.1);border-radius:12px;padding:14px;text-align:center;}
.stat-num{font-size:1.6rem;font-weight:800;}
.stat-lbl{font-size:.75rem;opacity:.8;margin-top:2px;}
/* SECTIONS */
.section{padding:clamp(40px,5vw,72px) clamp(16px,5vw,64px);}
.section-alt{background:#fff;}
.section-header{margin-bottom:28px;}
.section-header h2{font-size:clamp(1.3rem,3vw,1.8rem);font-weight:800;color:#003366;}
.section-header p{color:#666;margin-top:6px;}
/* CARDS GRID */
.cards-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:16px;}
.card{background:#fff;border-radius:16px;padding:20px;box-shadow:0 2px 12px rgba(0,0,0,.06);
  border:1px solid #e8eaf0;transition:transform .2s,box-shadow .2s;}
.card:hover{transform:translateY(-3px);box-shadow:0 8px 28px rgba(0,51,102,.1);}
.card-icon{font-size:1.7rem;margin-bottom:8px;}
.card h3{font-size:.97rem;font-weight:700;color:#003366;margin-bottom:6px;}
.card p{color:#555;font-size:.87rem;line-height:1.55;}
/* STEPS */
.steps-list{display:grid;gap:12px;}
.step{display:flex;align-items:flex-start;gap:16px;background:#fff;border-radius:16px;
  padding:18px 20px;box-shadow:0 2px 10px rgba(0,0,0,.06);border:1px solid #e8eaf0;
  transition:box-shadow .2s;}
.step:hover{box-shadow:0 6px 22px rgba(0,51,102,.1);}
.step-num{min-width:40px;height:40px;border-radius:50%;
  background:linear-gradient(135deg,#003366,#0096c7);color:#fff;
  font-weight:800;display:flex;align-items:center;justify-content:center;flex-shrink:0;}
.step-body h4{color:#003366;font-weight:700;margin-bottom:4px;}
.step-body p{color:#555;font-size:.88rem;}
.badge{display:inline-block;padding:3px 10px;border-radius:999px;
  font-size:.73rem;font-weight:700;margin-left:8px;}
.pre{background:#fff3e0;color:#e65100;}
.poll{background:#e3f2fd;color:#0d47a1;}
.post{background:#e8f5e9;color:#1b5e20;}
/* TIMELINE */
.tl-filters{display:flex;flex-wrap:wrap;gap:10px;margin-bottom:22px;}
.tl-btn{padding:8px 18px;border-radius:999px;border:2px solid #d0d7e8;background:#fff;
  font-weight:600;font-size:.85rem;cursor:pointer;transition:all .15s;}
.tl-btn.active,.tl-btn:hover{background:#003366;color:#fff;border-color:#003366;}
.timeline{position:relative;padding-left:26px;}
.timeline::before{content:'';position:absolute;left:0;top:0;bottom:0;width:3px;
  background:linear-gradient(180deg,#003366,#0096c7,#138808);border-radius:999px;}
.tl-item{position:relative;margin-bottom:14px;}
.tl-item::before{content:'';position:absolute;left:-33px;top:18px;width:14px;height:14px;
  border-radius:50%;background:#0057b7;border:3px solid #fff;box-shadow:0 0 0 2px #0057b7;}
.tl-card{background:#fff;border-radius:14px;padding:14px 18px;
  box-shadow:0 2px 10px rgba(0,0,0,.06);border:1px solid #e8eaf0;}
.tl-card h4{color:#003366;font-weight:700;font-size:.95rem;margin-bottom:4px;}
.tl-card p{color:#666;font-size:.86rem;}
/* FACTS */
.facts-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:16px;}
.fact-card{background:#fff;border-radius:16px;padding:20px;
  box-shadow:0 2px 12px rgba(0,0,0,.06);border:1px solid #e8eaf0;}
.fact-card h4{color:#003366;font-weight:700;margin-bottom:8px;}
.fact-card p{color:#555;font-size:.88rem;line-height:1.55;}
/* QUIZ */
.quiz-box{background:#fff;border-radius:20px;padding:32px;
  box-shadow:0 4px 20px rgba(0,0,0,.07);border:1px solid #e8eaf0;max-width:680px;margin:0 auto;}
.quiz-prog{height:8px;background:#e8eaf0;border-radius:999px;margin-bottom:24px;overflow:hidden;}
.quiz-bar{height:100%;background:linear-gradient(90deg,#003366,#0096c7);
  border-radius:999px;transition:width .3s ease;width:0%;}
.quiz-q{font-size:1.05rem;font-weight:700;color:#003366;margin-bottom:18px;}
.quiz-opts{display:grid;gap:10px;}
.quiz-opt{text-align:left;padding:13px 18px;border-radius:12px;border:2px solid #e0e4ed;
  background:#f7f8fb;font-size:.92rem;cursor:pointer;transition:all .15s;font-weight:500;}
.quiz-opt:hover{border-color:#0057b7;background:#eef3fb;}
.quiz-opt.correct{border-color:#2e7d32;background:#e8f5e9;color:#1b5e20;}
.quiz-opt.wrong{border-color:#c62828;background:#ffebee;color:#b71c1c;}
.quiz-exp{margin-top:12px;padding:12px 16px;border-radius:10px;
  background:#f0f4ff;color:#003366;font-size:.87rem;display:none;}
.quiz-next{margin-top:16px;display:none;}
.quiz-score{text-align:center;padding:24px 0;}
.quiz-score h3{font-size:1.5rem;font-weight:800;color:#003366;}
/* GLOSSARY */
.gloss-search{width:100%;max-width:400px;padding:11px 18px;border-radius:999px;
  border:2px solid #d0d7e8;font-size:.95rem;margin-bottom:22px;outline:none;
  transition:border .15s;}
.gloss-search:focus{border-color:#0057b7;}
.gloss-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:14px;}
.gloss-card{background:#fff;border-radius:14px;padding:16px 18px;
  box-shadow:0 2px 10px rgba(0,0,0,.06);border:1px solid #e8eaf0;}
.gloss-card strong{color:#003366;font-size:.95rem;}
.gloss-card p{color:#555;font-size:.86rem;margin-top:4px;}
/* CHATBOT */
#fab{position:fixed;bottom:24px;right:24px;width:58px;height:58px;border-radius:50%;
  background:linear-gradient(135deg,#01696f,#0096c7);color:#fff;font-size:1.5rem;
  border:none;cursor:pointer;display:flex;align-items:center;justify-content:center;
  box-shadow:0 6px 24px rgba(1,105,111,.5);z-index:9999;transition:transform .2s;}
#fab:hover{transform:scale(1.1);}
#chat-panel{position:fixed;bottom:94px;right:24px;width:340px;background:#fff;
  border-radius:18px;box-shadow:0 16px 48px rgba(0,0,0,.18);z-index:9998;
  display:none;flex-direction:column;max-height:500px;overflow:hidden;}
#chat-panel.open{display:flex;}
#chat-hdr{background:linear-gradient(90deg,#003366,#0096c7);color:#fff;
  padding:13px 16px;display:flex;align-items:center;justify-content:space-between;}
#chat-hdr span{font-weight:700;font-size:.95rem;}
#chat-hdr button{background:none;border:none;color:#fff;font-size:1.1rem;cursor:pointer;}
#chat-body{flex:1;overflow-y:auto;padding:12px;display:flex;flex-direction:column;
  gap:8px;background:#f7f8fb;}
.cm{max-width:86%;padding:10px 14px;border-radius:14px;font-size:.87rem;
  line-height:1.5;word-break:break-word;}
.cu{background:#003366;color:#fff;align-self:flex-end;border-bottom-right-radius:3px;}
.cb{background:#fff;color:#222;align-self:flex-start;border:1px solid #e0e4ed;
  border-bottom-left-radius:3px;box-shadow:0 1px 4px rgba(0,0,0,.06);}
.ct{color:#999;font-style:italic;font-size:.82rem;align-self:flex-start;padding:8px 12px;}
#chat-chips{display:flex;flex-wrap:wrap;gap:6px;padding:8px 12px;
  background:#f7f8fb;border-top:1px solid #e8eaf0;}
.chip{background:#e8f5f5;color:#01696f;border:1px solid #b2dfdb;border-radius:999px;
  padding:5px 12px;font-size:.76rem;font-weight:600;cursor:pointer;transition:background .15s;}
.chip:hover{background:#b2dfdb;}
#chat-input-row{display:flex;align-items:center;border-top:1px solid #e0e4ed;
  background:#fff;padding:8px 10px;gap:6px;}
#chat-inp{flex:1;border:1.5px solid #d0d7e8;border-radius:999px;padding:9px 16px;
  font-size:.88rem;outline:none;background:#f7f8fb;transition:border .15s;}
#chat-inp:focus{border-color:#01696f;}
.csend{width:38px;height:38px;border-radius:50%;background:#01696f;color:#fff;
  border:none;cursor:pointer;font-size:1rem;transition:background .15s;}
.csend:hover{background:#0c4e54;}
.cmic{width:38px;height:38px;border-radius:50%;background:#f0f2f5;color:#333;
  border:none;cursor:pointer;font-size:1rem;}
.cmic.on{background:#e53935;color:#fff;animation:pulse .8s infinite;}
@keyframes pulse{0%,100%{transform:scale(1)}50%{transform:scale(1.15)}}
/* AI STATUS */
.ai-status{display:inline-flex;align-items:center;gap:6px;padding:5px 14px;
  border-radius:999px;font-size:.8rem;font-weight:700;margin-bottom:16px;}
.ai-on{background:#e8f5e9;color:#2e7d32;}
.ai-off{background:#fff3e0;color:#e65100;}
/* FOOTER */
footer{background:#003366;color:rgba(255,255,255,.75);text-align:center;
  padding:28px 16px;font-size:.87rem;}
footer a{color:#7dc8ff;}
/* BACK TOP */
#top-btn{position:fixed;bottom:96px;right:24px;width:38px;height:38px;border-radius:50%;
  background:#003366;color:#fff;border:none;font-size:1rem;cursor:pointer;
  display:none;z-index:500;box-shadow:0 4px 12px rgba(0,0,0,.2);}
@media(max-width:480px){
  #chat-panel{width:calc(100vw - 24px);right:12px;}
  .hero h1{font-size:1.5rem;}
}
</style>
</head>
<body>
<nav>
  <div class="nav-brand">
    <svg width="30" height="30" viewBox="0 0 32 32" fill="none">
      <rect width="32" height="32" rx="8" fill="#003366"/>
      <path d="M8 24V12l8-5 8 5v12" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
      <path d="M13 24v-6h6v6" stroke="#FF9933" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
      <circle cx="16" cy="10" r="1.5" fill="#138808"/>
    </svg>
    ELECTOR
  </div>
  <div class="nav-links">
    <a href="#home" class="active">Home</a>
    <a href="#steps">Steps</a>
    <a href="#timeline">Timeline</a>
    <a href="#facts">Facts</a>
    <a href="#quiz">Quiz</a>
    <a href="#glossary">Glossary</a>
  </div>
</nav>
<div class="tricolor"></div>

<!-- HERO -->
<section class="hero" id="home">
  <div>
    <div class="hero-badge">🇮🇳 Civic Education Platform</div>
    <h1>Understand Every Step of India's Election Process</h1>
    <p>ELECTOR is an AI-powered civic assistant explaining voter registration, EVMs, ECI rules, and result declaration — in plain language.</p>
    <div class="hero-btns">
      <a href="#steps" class="btn btn-white">📋 Explore Steps</a>
      <a href="#quiz" class="btn btn-outline">🧠 Take Quiz</a>
    </div>
  </div>
  <div class="hero-card">
    <h3>📊 India Election at a Glance</h3>
    <div class="stat-row">
      <div class="stat"><div class="stat-num">970M+</div><div class="stat-lbl">Registered Voters</div></div>
      <div class="stat"><div class="stat-num">543</div><div class="stat-lbl">Lok Sabha Seats</div></div>
      <div class="stat"><div class="stat-num">7</div><div class="stat-lbl">Election Stages</div></div>
      <div class="stat"><div class="stat-num">48h</div><div class="stat-lbl">Campaign Silence</div></div>
    </div>
  </div>
</section>

<!-- FEATURES -->
<section class="section">
  <div class="section-header">
    <h2>What ELECTOR Covers</h2>
    <p>Six interactive sections making every election stage clear and easy to follow.</p>
  </div>
  <div class="cards-grid">
    <div class="card"><div class="card-icon">💬</div><h3>AI Chat Assistant</h3><p>Ask any election question — get accurate Gemini AI answers with full session memory.</p></div>
    <div class="card"><div class="card-icon">📋</div><h3>Step-by-Step Guide</h3><p>All 7 election stages with tasks, key people, and deadlines that matter.</p></div>
    <div class="card"><div class="card-icon">📊</div><h3>Visual Timeline</h3><p>Filter the complete timeline by phase — pre-election, polling day, or post-election.</p></div>
    <div class="card"><div class="card-icon">⚡</div><h3>Quick Facts</h3><p>Key facts on ECI, EVMs, VVPAT, EPIC cards, MCC, and dispute resolution.</p></div>
    <div class="card"><div class="card-icon">🧠</div><h3>Knowledge Quiz</h3><p>5 questions with instant feedback to test your understanding of elections.</p></div>
    <div class="card"><div class="card-icon">📖</div><h3>Glossary</h3><p>Plain-language definitions of all election terms — searchable.</p></div>
  </div>
</section>

<!-- STEPS -->
<section class="section section-alt" id="steps">
  <div class="section-header">
    <h2>The 7 Stages of an Indian Election</h2>
    <p>From voter registration to government formation — every step explained clearly.</p>
  </div>
  <div class="steps-list" id="steps-list"></div>
</section>

<!-- TIMELINE -->
<section class="section" id="timeline">
  <div class="section-header">
    <h2>Election Timeline</h2>
    <p>Filter events by phase to focus on what matters to you.</p>
  </div>
  <div class="tl-filters" id="tl-filters">
    <button class="tl-btn active" data-ph="all">All Phases</button>
    <button class="tl-btn" data-ph="pre">Pre-Election</button>
    <button class="tl-btn" data-ph="poll">Polling Day</button>
    <button class="tl-btn" data-ph="post">Post-Election</button>
  </div>
  <div class="timeline" id="tl-list"></div>
</section>

<!-- FACTS -->
<section class="section section-alt" id="facts">
  <div class="section-header">
    <h2>Key Facts Every Voter Should Know</h2>
    <p>Essential knowledge about how India's election system works.</p>
  </div>
  <div class="facts-grid" id="facts-list"></div>
</section>

<!-- QUIZ -->
<section class="section" id="quiz">
  <div class="section-header">
    <h2>Test Your Knowledge</h2>
    <p>5 questions on ECI, EVMs, MCC, timelines, and voting procedures.</p>
  </div>
  <div class="quiz-box">
    <div class="quiz-prog"><div class="quiz-bar" id="qbar"></div></div>
    <div id="quiz-area"></div>
  </div>
</section>

<!-- GLOSSARY -->
<section class="section section-alt" id="glossary">
  <div class="section-header">
    <h2>Election Glossary</h2>
    <p>Plain-language definitions of key election terms.</p>
  </div>
  <input class="gloss-search" id="gsearch" type="text" placeholder="🔍 Search — e.g. EVM, MCC, EPIC..."/>
  <div class="gloss-grid" id="glist"></div>
</section>

<footer>
  <strong>ELECTOR</strong> — AI-Powered Civic Education &nbsp;·&nbsp;
  Powered by Gemini AI &nbsp;·&nbsp;
  <a href="https://eci.gov.in" target="_blank">eci.gov.in</a>
</footer>

<button id="top-btn" onclick="scrollTo({top:0,behavior:'smooth'})">↑</button>

<!-- CHATBOT FAB -->
<button id="fab" onclick="toggleChat()" aria-label="Open Civic AI">🗳️</button>

<!-- CHAT PANEL -->
<div id="chat-panel">
  <div id="chat-hdr">
    <span>🤖 Civic AI — Election Assistant</span>
    <button onclick="toggleChat()">✕</button>
  </div>
  <div id="chat-body">
    <div class="cm cb">👋 Hi! I am Civic AI. Ask me anything about India's election process — EVMs, MCC, voter registration, VVPAT, and more!</div>
  </div>
  <div id="chat-chips">
    <button class="chip" onclick="qs('What is MCC?')">What is MCC?</button>
    <button class="chip" onclick="qs('How does EVM work?')">How EVM works?</button>
    <button class="chip" onclick="qs('How do I register to vote?')">Register to vote</button>
    <button class="chip" onclick="qs('What is VVPAT?')">What is VVPAT?</button>
  </div>
  <div id="chat-input-row">
    <input id="chat-inp" type="text" placeholder="Ask about elections..." autocomplete="off"
      onkeydown="if(event.key==='Enter')sendMsg()"/>
    <button class="csend" onclick="sendMsg()">➤</button>
    <button class="cmic" id="mic" onclick="voiceIn()">🎤</button>
  </div>
</div>

<script>
// ── DATA ────────────────────────────────────────────────────────────────────
const STEPS=[
  {n:"Voter Registration",d:"Citizens verify or update their name on the electoral roll before the ECI deadline. Visit voters.eci.gov.in.",ph:"Pre-election"},
  {n:"Candidate Nomination",d:"Eligible candidates file nomination papers with the Returning Officer within the notified schedule.",ph:"Pre-election"},
  {n:"Scrutiny & Withdrawal",d:"Nominations are verified; candidates may withdraw within the allowed window before the final list is published.",ph:"Pre-election"},
  {n:"Campaign Period",d:"Parties campaign under ECI rules on spending, conduct, and the Model Code of Conduct.",ph:"Pre-election"},
  {n:"Polling Day",d:"Registered voters cast ballots at assigned booths after identity verification using EPIC or other valid documents.",ph:"Polling Day"},
  {n:"Vote Counting",d:"EVMs are counted under observer supervision in counting centres after polling ends.",ph:"Post-election"},
  {n:"Result Declaration",d:"The Returning Officer officially declares the winner; ECI publishes final results.",ph:"Post-election"},
];
const TL=[
  {ph:"pre",lbl:"Pre-Election",n:"Voter Roll Preparation",d:"ECI updates electoral rolls; citizens check enrollment at voters.eci.gov.in"},
  {ph:"pre",lbl:"Pre-Election",n:"Election Notification",d:"President/Governor issues formal notification; MCC comes into effect immediately"},
  {ph:"pre",lbl:"Pre-Election",n:"Nomination Filing",d:"Candidates submit nomination papers to the Returning Officer"},
  {ph:"pre",lbl:"Pre-Election",n:"Scrutiny of Nominations",d:"Returning Officer checks all papers; defective nominations are rejected"},
  {ph:"pre",lbl:"Pre-Election",n:"Withdrawal Deadline",d:"Candidates can withdraw; final list of contesting candidates is published"},
  {ph:"pre",lbl:"Pre-Election",n:"Campaign Period",d:"Active campaigning with rallies, media, outreach within ECI guidelines"},
  {ph:"pre",lbl:"Pre-Election",n:"Campaign Silence (48h)",d:"All campaigning must stop 48 hours before polling day begins"},
  {ph:"poll",lbl:"Polling Day",n:"Booth Setup & EVM Testing",d:"Officials prepare booths, test EVMs, open polling at scheduled time"},
  {ph:"poll",lbl:"Polling Day",n:"Voting Process",d:"Voters verify identity, press EVM button, see VVPAT confirmation slip"},
  {ph:"poll",lbl:"Polling Day",n:"Poll Closing & Sealing",d:"EVMs sealed and secured for transport to counting centres"},
  {ph:"post",lbl:"Post-Election",n:"Counting Day",d:"Votes tabulated in rounds under observer and polling-agent supervision"},
  {ph:"post",lbl:"Post-Election",n:"Result Declaration",d:"Returning Officer declares winner; results published by ECI officially"},
  {ph:"post",lbl:"Post-Election",n:"Government Formation",d:"Winning party/coalition invited by President/Governor to form government"},
];
const FACTS=[
  {t:"🗓️ Model Code of Conduct",d:"Activated when the election schedule is announced. Stops governments from using state resources or making new policy promises for electoral gain."},
  {t:"🏛️ Election Commission of India",d:"Independent constitutional body under Article 324. Supervises, directs and controls all elections to Parliament and State Legislatures."},
  {t:"📋 Voter ID — EPIC Card",d:"Electors' Photo Identity Card is the primary ID for voting. Aadhaar, passport, and 11 other documents are also accepted at polling booths."},
  {t:"🔒 EVM Security",d:"EVMs are fully standalone and air-gapped — no internet, Wi-Fi, or Bluetooth. They cannot be hacked remotely or tampered with wirelessly."},
  {t:"📊 VVPAT System",d:"Prints a slip showing your candidate's name and symbol, visible for 7 seconds through a glass window, then drops into a sealed box."},
  {t:"⚖️ Election Disputes",d:"Post-result disputes go to High Courts (State) or Supreme Court (Parliament) via Election Petitions — not to ECI."},
];
const QUIZ=[
  {q:"Which Article establishes the Election Commission of India?",o:["Article 19","Article 324","Article 226","Article 356"],a:1,e:"Article 324 grants the ECI power to superintend, direct and control all elections."},
  {q:"How long before polling day must all campaigning stop?",o:["12 hours","24 hours","48 hours","72 hours"],a:2,e:"ECI mandates a 48-hour campaign silence period before polls open."},
  {q:"What does VVPAT stand for?",o:["Voter Verified Paper Audit Trail","Voter Verifiable Paper Audit Trail","Verified Voter Paper Audit Terminal","Vote Validity Paper Audit Trail"],a:1,e:"Voter Verifiable Paper Audit Trail — the slip is visible for 7 seconds."},
  {q:"Who officially declares election results in a constituency?",o:["Chief Election Commissioner","District Magistrate","Returning Officer","State Election Commissioner"],a:2,e:"The Returning Officer of each constituency officially declares the winner."},
  {q:"What is the nature of the Model Code of Conduct?",o:["A law under the Constitution","Part of the RPA 1951","ECI guidelines — not a statutory law","An order of the Supreme Court"],a:2,e:"MCC is not a law — it is a set of ECI guidelines that all political parties agree to follow."},
];
const GLOSSARY=[
  {t:"ECI",d:"Election Commission of India — constitutional body that manages all elections."},
  {t:"MCC",d:"Model Code of Conduct — ECI guidelines restricting political activity during elections."},
  {t:"EVM",d:"Electronic Voting Machine — standalone tamper-proof device used for voting."},
  {t:"VVPAT",d:"Voter Verifiable Paper Audit Trail — printed slip confirming your vote for 7 seconds."},
  {t:"EPIC",d:"Electors' Photo Identity Card — the standard voter ID card in India."},
  {t:"Returning Officer",d:"Government official responsible for conducting elections in a constituency."},
  {t:"Constituency",d:"A geographic area whose registered voters elect one representative."},
  {t:"By-election",d:"An election held to fill a vacancy between general elections."},
  {t:"Lok Sabha",d:"Lower house of India's Parliament with 543 elected members."},
  {t:"Rajya Sabha",d:"Upper house of India's Parliament; members elected by State Assemblies."},
];

// ── RENDER STEPS ────────────────────────────────────────────────────────────
const phC={"Pre-election":"pre","Polling Day":"poll","Post-election":"post"};
document.getElementById("steps-list").innerHTML=STEPS.map((s,i)=>`
<div class="step">
  <div class="step-num">${i+1}</div>
  <div class="step-body">
    <h4>${s.n}<span class="badge ${phC[s.ph]}">${s.ph}</span></h4>
    <p>${s.d}</p>
  </div>
</div>`).join('');

// ── RENDER TIMELINE ─────────────────────────────────────────────────────────
function renderTL(f="all"){
  const items=f==="all"?TL:TL.filter(t=>t.ph===f);
  document.getElementById("tl-list").innerHTML=items.map(t=>`
  <div class="tl-item">
    <div class="tl-card">
      <h4>${t.n} <span class="badge ${t.ph==="pre"?"pre":t.ph==="poll"?"poll":"post"}">${t.lbl}</span></h4>
      <p>${t.d}</p>
    </div>
  </div>`).join('');
}
renderTL();
document.getElementById("tl-filters").onclick=e=>{
  const btn=e.target.closest(".tl-btn");if(!btn)return;
  document.querySelectorAll(".tl-btn").forEach(b=>b.classList.remove("active"));
  btn.classList.add("active");renderTL(btn.dataset.ph);
};

// ── RENDER FACTS ────────────────────────────────────────────────────────────
document.getElementById("facts-list").innerHTML=FACTS.map(f=>`
<div class="fact-card"><h4>${f.t}</h4><p>${f.d}</p></div>`).join('');

// ── QUIZ ────────────────────────────────────────────────────────────────────
let qi=0,qs_=0,qa=false;
function renderQuiz(){
  document.getElementById("qbar").style.width=`${(qi/QUIZ.length)*100}%`;
  const area=document.getElementById("quiz-area");
  if(qi>=QUIZ.length){
    document.getElementById("qbar").style.width="100%";
    const ico=qs_===QUIZ.length?"🏆":qs_>=3?"✅":"📚";
    const msg=qs_===QUIZ.length?"Perfect! You are election-ready.":qs_>=3?"Great civic knowledge!":"Keep exploring ELECTOR!";
    area.innerHTML=`<div class="quiz-score"><div style="font-size:2.5rem;margin-bottom:12px">${ico}</div>
      <h3>You scored ${qs_} / ${QUIZ.length}</h3>
      <p style="color:#666;margin:10px 0 20px">${msg}</p>
      <button class="btn btn-primary" onclick="qi=0;qs_=0;qa=false;renderQuiz()">🔄 Retake Quiz</button></div>`;
    return;
  }
  const item=QUIZ[qi];
  area.innerHTML=`<p style="color:#666;font-size:.85rem;margin-bottom:8px">Question ${qi+1} of ${QUIZ.length}</p>
    <div class="quiz-q">${item.q}</div>
    <div class="quiz-opts">${item.o.map((o,i)=>`<button class="quiz-opt" data-i="${i}">${o}</button>`).join('')}</div>
    <div class="quiz-exp" id="qexp">${item.e}</div>
    <button class="btn btn-primary quiz-next" id="qnext" onclick="qi++;qa=false;renderQuiz()">Next →</button>`;
  document.querySelectorAll(".quiz-opt").forEach(b=>{
    b.onclick=()=>{
      if(qa)return;qa=true;
      const sel=+b.dataset.i;
      document.querySelectorAll(".quiz-opt").forEach((x,idx)=>{
        x.disabled=true;
        if(idx===item.a)x.classList.add("correct");
        if(idx===sel&&idx!==item.a)x.classList.add("wrong");
      });
      if(sel===item.a)qs_++;
      document.getElementById("qexp").style.display="block";
      document.getElementById("qnext").style.display="inline-flex";
    };
  });
}
renderQuiz();

// ── GLOSSARY ────────────────────────────────────────────────────────────────
function renderGloss(f=""){
  const fl=f.toLowerCase();
  const items=GLOSSARY.filter(g=>!fl||g.t.toLowerCase().includes(fl)||g.d.toLowerCase().includes(fl));
  document.getElementById("glist").innerHTML=items.length
    ?items.map(g=>`<div class="gloss-card"><strong>${g.t}</strong><p>${g.d}</p></div>`).join('')
    :`<p style="color:#888;padding:12px 0">No terms found. Try another keyword.</p>`;
}
renderGloss();
document.getElementById("gsearch").oninput=e=>renderGloss(e.target.value);

// ── NAV ACTIVE ──────────────────────────────────────────────────────────────
const obs=new IntersectionObserver(entries=>{
  entries.forEach(e=>{
    if(e.isIntersecting){
      document.querySelectorAll(".nav-links a").forEach(a=>a.classList.remove("active"));
      const l=document.querySelector(`.nav-links a[href="#${e.target.id}"]`);
      if(l)l.classList.add("active");
    }
  });
},{threshold:0.45});
["home","steps","timeline","facts","quiz","glossary"].forEach(id=>{
  const el=document.getElementById(id);if(el)obs.observe(el);
});

// ── BACK TO TOP ──────────────────────────────────────────────────────────────
window.onscroll=()=>{document.getElementById("top-btn").style.display=scrollY>400?"block":"none";};

// ── CHATBOT ──────────────────────────────────────────────────────────────────
let sid=crypto.randomUUID(),open=false;

function toggleChat(){
  open=!open;
  document.getElementById("chat-panel").classList.toggle("open",open);
  document.getElementById("fab").textContent=open?"✕":"🗳️";
  if(open)document.getElementById("chat-inp").focus();
}

function addMsg(txt,cls){
  const b=document.getElementById("chat-body");
  const d=document.createElement("div");
  d.className="cm "+cls;d.textContent=txt;
  b.appendChild(d);b.scrollTop=b.scrollHeight;return d;
}

async function sendMsg(){
  const inp=document.getElementById("chat-inp");
  const txt=inp.value.trim();if(!txt)return;
  inp.value="";
  addMsg(txt,"cu");
  const typing=addMsg("Typing...","ct");
  try{
    const res=await fetch("/chat",{
      method:"POST",
      headers:{"Content-Type":"application/json"},
      body:JSON.stringify({message:txt,session_id:sid})
    });
    const data=await res.json();
    typing.remove();addMsg(data.reply,"cb");
  }catch(e){
    typing.remove();addMsg("Connection error. Please try again.","cb");
  }
}

function qs(t){document.getElementById("chat-inp").value=t;sendMsg();}

function voiceIn(){
  const SR=window.SpeechRecognition||window.webkitSpeechRecognition;
  if(!SR){alert("Voice input requires Chrome browser.");return;}
  const r=new SR();r.lang="en-IN";
  const m=document.getElementById("mic");
  m.classList.add("on");m.textContent="🔴";
  r.onresult=e=>{
    document.getElementById("chat-inp").value=e.results[0][0].transcript;
    m.classList.remove("on");m.textContent="🎤";sendMsg();
  };
  r.onerror=r.onend=()=>{m.classList.remove("on");m.textContent="🎤";};
  r.start();
}
</script>
</body>
</html>"""

# ── ROUTES ────────────────────────────────────────────────────────────────────
@app.route("/")
def home():
    return render_template_string(HTML)

@app.route("/chat", methods=["POST"])
def chat():
    ip = request.remote_addr
    if is_limited(ip):
        return jsonify({"reply": "⚠️ Too many requests. Please wait a moment."}), 429

    data     = request.get_json(silent=True) or {}
    msg      = (data.get("message") or "").strip()
    sess_id  = data.get("session_id", "default")

    if not msg:
        return jsonify({"reply": "Please type a question."}), 400

    # Fallback if no AI
    if model is None:
        lower = msg.lower()
        for key, reply in FALLBACK.items():
            if key in lower:
                return jsonify({"reply": reply})
        return jsonify({"reply": (
            "I can answer questions about Indian elections — voter registration, EVMs, "
            "VVPAT, MCC, ECI, EPIC cards, and results.\n\n"
            "💡 To enable full AI: add GEMINI_API_KEY to your .env file.\n"
            "Get free key → https://aistudio.google.com/apikey"
        )})

    # Start or reuse session
    if sess_id not in sessions:
        sessions[sess_id] = model.start_chat(history=[
            {"role": "user",  "parts": [SYSTEM_PROMPT]},
            {"role": "model", "parts": ["Understood. I am ELECTOR, ready to assist with Indian election education."]}
        ])

    try:
        resp = sessions[sess_id].send_message(msg)
        return jsonify({"reply": resp.text})
    except Exception as e:
        err = str(e)
        if "403" in err or "PermissionDenied" in err:
            return jsonify({"reply": "🔒 Permission error. Check your GEMINI_API_KEY in .env."})
        return jsonify({"reply": "AI error. Please try again."})

@app.route("/health")
def health():
    return jsonify({
        "status":       "ok",
        "ai_connected": model is not None,
        "model":        MODEL_NAME,
        "sessions":     len(sessions)
    })

# ── RUN ────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    port  = int(os.environ.get("PORT", 8080))
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    print(f"\n🗳️  ELECTOR starting on http://localhost:{port}")
    print(f"   AI : {'✅ Gemini connected' if model else '⚠️  Offline — set GEMINI_API_KEY in .env'}")
    print(f"   Get free key → https://aistudio.google.com/apikey\n")
    app.run(host="0.0.0.0", port=port, debug=debug)
