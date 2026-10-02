DASHBOARD_HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>AgentOps Platform</title>

<style>
:root{
  --bg:#0b0d12;
  --panel:#12151c;
  --panel2:#191d26;
  --border:#272c37;
  --text:#f2f4f8;
  --muted:#98a1b2;
  --accent:#c2411a;
  --accent2:#e05a24;
  --success:#34d399;
  --danger:#f87171;
  --shadow:0 20px 60px rgba(0,0,0,.25);
}

*{
  box-sizing:border-box;
}

html{
  scroll-behavior:smooth;
}

body{
  margin:0;
  background:
    radial-gradient(circle at 15% 10%,rgba(194,65,26,.10),transparent 28%),
    radial-gradient(circle at 85% 15%,rgba(224,90,36,.08),transparent 25%),
    var(--bg);
  color:var(--text);
  font:14px system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
}

button,
input,
textarea,
select{
  font:inherit;
}

button{
  cursor:pointer;
}

button:disabled{
  opacity:.6;
  cursor:not-allowed;
}

/* Navigation */

.topbar{
  position:sticky;
  top:0;
  z-index:20;
  backdrop-filter:blur(14px);
  background:rgba(11,13,18,.88);
  border-bottom:1px solid var(--border);
}

.nav{
  width:min(1180px,calc(100% - 32px));
  margin:auto;
  min-height:68px;
  display:flex;
  align-items:center;
  justify-content:space-between;
  gap:20px;
}

.brand{
  display:flex;
  align-items:center;
  gap:10px;
  font-weight:800;
  font-size:18px;
}

.brand-mark{
  width:36px;
  height:36px;
  display:grid;
  place-items:center;
  border-radius:10px;
  background:linear-gradient(135deg,var(--accent),var(--accent2));
  color:white;
  font-weight:900;
}

.nav-actions{
  display:flex;
  align-items:center;
  gap:6px;
  flex-wrap:wrap;
}

.nav-btn{
  border:0;
  background:transparent;
  color:var(--muted);
  padding:9px 12px;
  border-radius:8px;
}

.nav-btn:hover,
.nav-btn.active{
  background:var(--panel2);
  color:var(--text);
}

.nav-cta{
  border:0;
  padding:10px 14px;
  border-radius:9px;
  background:linear-gradient(135deg,var(--accent),var(--accent2));
  color:white;
  font-weight:800;
}

/* Global */

.container{
  width:min(1180px,calc(100% - 32px));
  margin:auto;
}

.page{
  display:none;
}

.page.active{
  display:block;
}

.primary{
  border:0;
  padding:13px 18px;
  border-radius:10px;
  background:linear-gradient(135deg,var(--accent),var(--accent2));
  color:white;
  font-weight:800;
}

.secondary{
  border:1px solid var(--border);
  padding:13px 18px;
  border-radius:10px;
  background:var(--panel);
  color:var(--text);
  font-weight:700;
}

.primary:hover,
.nav-cta:hover{
  filter:brightness(1.08);
}

.secondary:hover{
  background:var(--panel2);
}

.badge{
  display:inline-flex;
  align-items:center;
  gap:8px;
  padding:6px 9px;
  border-radius:999px;
  background:rgba(52,211,153,.10);
  color:var(--success);
  font-size:12px;
  font-weight:700;
}

.status-dot{
  width:8px;
  height:8px;
  border-radius:50%;
  background:var(--success);
  box-shadow:0 0 12px rgba(52,211,153,.65);
}

/* Home */

.hero{
  min-height:640px;
  display:grid;
  grid-template-columns:1.08fr .92fr;
  align-items:center;
  gap:45px;
  padding:75px 0 60px;
}

.hero-badge{
  display:inline-flex;
  align-items:center;
  gap:8px;
  padding:8px 12px;
  border:1px solid var(--border);
  border-radius:999px;
  background:rgba(18,21,28,.8);
  color:var(--muted);
  margin-bottom:20px;
}

.hero h1{
  margin:0;
  font-size:clamp(43px,6vw,74px);
  line-height:.98;
  letter-spacing:-2.8px;
}

.hero h1 span{
  background:linear-gradient(135deg,#f08a5b,#e05a24);
  -webkit-background-clip:text;
  background-clip:text;
  color:transparent;
}

.hero p{
  max-width:700px;
  color:var(--muted);
  font-size:18px;
  line-height:1.7;
  margin:25px 0;
}

.hero-actions{
  display:flex;
  flex-wrap:wrap;
  gap:12px;
}

.hero-card{
  background:linear-gradient(145deg,rgba(25,29,38,.95),rgba(18,21,28,.95));
  border:1px solid var(--border);
  border-radius:22px;
  padding:22px;
  box-shadow:var(--shadow);
}

.window-bar{
  display:flex;
  gap:7px;
  margin-bottom:20px;
}

.window-dot{
  width:10px;
  height:10px;
  border-radius:50%;
  background:#444b58;
}

.preview{
  background:#0a0c10;
  border:1px solid var(--border);
  border-radius:14px;
  padding:18px;
}

.preview-row{
  display:flex;
  align-items:center;
  justify-content:space-between;
  padding:14px 0;
  border-bottom:1px solid var(--border);
  gap:15px;
}

.preview-row:last-child{
  border-bottom:0;
}

.preview-label{
  color:var(--muted);
}

.preview-value{
  font-weight:800;
}

.section{
  padding:70px 0;
}

.section-title{
  margin:0 0 12px;
  font-size:34px;
  letter-spacing:-1px;
}

.section-subtitle{
  margin:0 0 30px;
  color:var(--muted);
  font-size:16px;
  line-height:1.6;
}

.feature-grid{
  display:grid;
  grid-template-columns:repeat(3,1fr);
  gap:16px;
}

.feature-card{
  background:var(--panel);
  border:1px solid var(--border);
  border-radius:16px;
  padding:22px;
}

.feature-icon{
  width:42px;
  height:42px;
  display:grid;
  place-items:center;
  border-radius:12px;
  background:var(--panel2);
  color:var(--accent);
  font-weight:900;
  margin-bottom:18px;
}

.feature-card h3{
  margin:0 0 8px;
  font-size:17px;
}

.feature-card p{
  margin:0;
  color:var(--muted);
  line-height:1.6;
}

.code-card{
  background:#080a0e;
  border:1px solid var(--border);
  border-radius:16px;
  padding:22px;
  overflow:auto;
}

.code-card pre{
  margin:0;
  color:#dbeafe;
  line-height:1.7;
  white-space:pre-wrap;
  word-break:break-word;
}

/* Playground */

.playground-wrap{
  padding:60px 0 80px;
}

.page-head{
  display:flex;
  align-items:flex-end;
  justify-content:space-between;
  gap:20px;
  margin-bottom:24px;
}

.page-head h1{
  margin:0;
  font-size:34px;
  letter-spacing:-1px;
}

.page-head p{
  margin:8px 0 0;
  color:var(--muted);
  line-height:1.5;
}

.notice{
  padding:13px 15px;
  border:1px solid var(--border);
  background:var(--panel2);
  color:var(--muted);
  border-radius:10px;
  margin-bottom:18px;
  line-height:1.5;
}

.playground{
  display:grid;
  grid-template-columns:1fr 1fr;
  gap:18px;
}

.panel{
  background:var(--panel);
  border:1px solid var(--border);
  border-radius:16px;
  padding:22px;
}

.panel h2{
  margin:0 0 18px;
  font-size:20px;
}

.field{
  margin-bottom:16px;
}

.field label{
  display:block;
  margin-bottom:8px;
  color:var(--muted);
  font-weight:600;
}

.field input,
.field textarea,
.field select{
  width:100%;
  border:1px solid var(--border);
  background:#0c0f14;
  color:var(--text);
  border-radius:10px;
  padding:12px 14px;
  outline:none;
}

.field input:focus,
.field textarea:focus,
.field select:focus{
  border-color:var(--accent);
  box-shadow:0 0 0 3px rgba(194,65,26,.12);
}

.field textarea{
  min-height:190px;
  resize:vertical;
}

.playground-actions{
  display:flex;
  gap:10px;
  flex-wrap:wrap;
}

.output-box{
  min-height:310px;
  background:#0a0c10;
  border:1px solid var(--border);
  border-radius:12px;
  padding:16px;
  white-space:pre-wrap;
  word-break:break-word;
  line-height:1.6;
  overflow:auto;
}

.meta-grid{
  display:grid;
  grid-template-columns:repeat(2,1fr);
  gap:10px;
  margin-top:14px;
}

.meta{
  background:var(--panel2);
  border-radius:10px;
  padding:12px;
  min-width:0;
}

.meta span{
  display:block;
  color:var(--muted);
  font-size:12px;
  margin-bottom:5px;
}

.meta strong{
  font-size:14px;
  word-break:break-word;
}

/* Dashboard */

.dashboard{
  padding:50px 0 80px;
}

.grid{
  display:grid;
  grid-template-columns:repeat(6,1fr);
  gap:10px;
}

.card{
  background:var(--panel);
  border:1px solid var(--border);
  border-radius:12px;
  padding:15px;
}

.card b{
  display:block;
  font-size:22px;
  color:var(--accent);
  margin-bottom:5px;
}

.card span{
  color:var(--muted);
  font-size:12px;
}

.dashboard-section{
  margin-top:18px;
  background:var(--panel);
  border:1px solid var(--border);
  border-radius:16px;
  padding:20px;
}

.dashboard-section h2{
  margin:0 0 14px;
  font-size:18px;
}

.wrap{
  overflow-x:auto;
}

table{
  width:100%;
  border-collapse:collapse;
  min-width:620px;
}

td,
th{
  text-align:left;
  padding:11px 10px;
  border-bottom:1px solid var(--border);
}

th{
  color:var(--muted);
  font-size:12px;
  text-transform:uppercase;
  letter-spacing:.05em;
}

tr.t{
  cursor:pointer;
}

tr.t:hover{
  background:rgba(255,255,255,.025);
}

.err{
  color:var(--danger);
}

.detail{
  margin:0;
  background:#0a0c10;
  border:1px solid var(--border);
  padding:14px;
  border-radius:12px;
  overflow:auto;
  white-space:pre-wrap;
  line-height:1.6;
}

/* Docs */

.docs{
  padding:60px 0 80px;
}

.docs-grid{
  display:grid;
  grid-template-columns:repeat(3,1fr);
  gap:16px;
}

.doc-block{
  margin-top:18px;
}

.doc-block h2{
  font-size:24px;
  margin-bottom:12px;
}

.doc-block p{
  color:var(--muted);
  line-height:1.7;
}

/* Footer */

.footer{
  border-top:1px solid var(--border);
  padding:28px 0 40px;
  color:var(--muted);
  text-align:center;
}

/* Responsive */

@media(max-width:950px){
  .hero{
    grid-template-columns:1fr;
  }

  .feature-grid,
  .docs-grid{
    grid-template-columns:1fr 1fr;
  }

  .playground{
    grid-template-columns:1fr;
  }

  .grid{
    grid-template-columns:repeat(3,1fr);
  }
}

@media(max-width:650px){
  .nav{
    padding:12px 0;
    align-items:flex-start;
    flex-direction:column;
  }

  .nav-actions{
    width:100%;
  }

  .nav-btn{
    padding:8px 9px;
  }

  .hero{
    padding-top:45px;
  }

  .hero h1{
    letter-spacing:-1.8px;
  }

  .feature-grid,
  .docs-grid{
    grid-template-columns:1fr;
  }

  .grid{
    grid-template-columns:repeat(2,1fr);
  }

  .meta-grid{
    grid-template-columns:1fr;
  }

  .page-head{
    align-items:flex-start;
    flex-direction:column;
  }
}

/* AgentOps Deep Orange Motion */

@keyframes aopNavIn {
  from { opacity:0; transform:translateY(-18px); }
  to { opacity:1; transform:translateY(0); }
}

@keyframes aopHeroIn {
  from { opacity:0; transform:translateY(28px); }
  to { opacity:1; transform:translateY(0); }
}

@keyframes aopHeroCardIn {
  from { opacity:0; transform:translateX(35px) scale(.97); }
  to { opacity:1; transform:translateX(0) scale(1); }
}

@keyframes aopOrangeGlow {
  0%,100% { box-shadow:0 20px 60px rgba(0,0,0,.25); }
  50% { box-shadow:0 0 35px rgba(194,65,26,.14),0 25px 70px rgba(0,0,0,.32); }
}

.topbar {
  animation:aopNavIn .7s cubic-bezier(.2,.8,.2,1) both;
}

.hero > div:first-child {
  animation:aopHeroIn .8s cubic-bezier(.2,.8,.2,1) .1s both;
}

.hero-card {
  animation:
    aopHeroCardIn .9s cubic-bezier(.2,.8,.2,1) .18s both,
    aopOrangeGlow 4s ease-in-out 1.2s infinite;
}

.hero-card:hover {
  transform:translateY(-5px);
  border-color:rgba(194,65,26,.5);
}

.primary,
.secondary,
.nav-btn,
.nav-cta {
  transition:transform .22s ease,box-shadow .22s ease,border-color .22s ease;
}

.primary:hover,
.nav-cta:hover {
  transform:translateY(-3px);
  box-shadow:0 10px 30px rgba(194,65,26,.25);
}

.secondary:hover,
.nav-btn:hover {
  transform:translateY(-2px);
}

.feature-card {
  transition:transform .3s ease,border-color .3s ease,box-shadow .3s ease;
}

.feature-card:hover {
  transform:translateY(-7px);
  border-color:rgba(194,65,26,.42);
  box-shadow:0 18px 50px rgba(0,0,0,.28),0 0 28px rgba(194,65,26,.08);
}

.feature-icon {
  transition:transform .3s ease,box-shadow .3s ease;
}

.feature-card:hover .feature-icon {
  transform:scale(1.08) rotate(-3deg);
}

.status-dot {
  animation:aopOrangeGlow 3s ease-in-out infinite;
}

@media (prefers-reduced-motion:reduce) {
  *,
  *::before,
  *::after {
    animation-duration:.01ms !important;
    animation-iteration-count:1 !important;
    transition-duration:.01ms !important;
  }
}

/* ===== AgentOps Live Status Glow ===== */

@keyframes aopLivePulse {
  0%, 100% {
    opacity: .78;
    box-shadow:
      0 0 0 0 rgba(34,197,94,.30),
      0 0 6px rgba(34,197,94,.30);
  }

  50% {
    opacity: 1;
    box-shadow:
      0 0 0 6px rgba(34,197,94,0),
      0 0 18px rgba(34,197,94,.75),
      0 0 32px rgba(34,197,94,.25);
  }
}

.status-dot {
  background: #22c55e !important;
  animation: aopLivePulse 2s ease-in-out infinite !important;
}

.hero-badge .status-dot {
  box-shadow: 0 0 8px rgba(34,197,94,.45);
}

/* ===== Strong Live Green Glow ===== */

@keyframes aopLivePulse {
  0%, 100% {
    opacity: .9;
    transform: scale(1);
    box-shadow:
      0 0 5px rgba(34,197,94,.9),
      0 0 14px rgba(34,197,94,.75),
      0 0 28px rgba(34,197,94,.45),
      0 0 45px rgba(34,197,94,.20);
    filter: brightness(1.15);
  }

  50% {
    opacity: 1;
    transform: scale(1.18);
    box-shadow:
      0 0 8px rgba(34,197,94,1),
      0 0 22px rgba(34,197,94,.95),
      0 0 42px rgba(34,197,94,.75),
      0 0 70px rgba(34,197,94,.40);
    filter: brightness(1.45);
  }
}

.status-dot {
  background: #22c55e !important;
  animation: aopLivePulse 1.8s ease-in-out infinite !important;
  border-radius: 50%;
  position: relative;
  z-index: 2;
}

.hero-badge .status-dot {
  box-shadow:
    0 0 8px rgba(34,197,94,.9),
    0 0 22px rgba(34,197,94,.65),
    0 0 40px rgba(34,197,94,.35);
}
</style>
</head>

<body>

<header class="topbar">
  <div class="nav">

    <div class="brand">
      <div class="brand-mark">A</div>
      <div>AgentOps</div>
    </div>

    <div class="nav-actions">
      <button class="nav-btn active" data-page="home">Home</button>
      <button class="nav-btn" data-page="playground">Playground</button>
      <button class="nav-btn" data-page="dashboard">Dashboard</button>
      <button class="nav-btn" data-page="docs">Docs</button>
      <button class="nav-cta" onclick="showPage('playground')">
        Try AgentOps
      </button>
    </div>

  </div>
</header>

<main>

<!-- HOME -->

<section id="home" class="page active">

  <div class="container">

    <div class="hero">

      <div>

        <div class="hero-badge">
          <span class="status-dot"></span>
          AI infrastructure and observability
        </div>

        <h1>
          Build safer,
          <span>observable AI.</span>
        </h1>

        <p>
          AgentOps gives AI applications an OpenAI-compatible gateway,
          tracing, security controls, cost tracking, and evaluation tooling
          from one platform.
        </p>

        <div class="hero-actions">

          <button
            class="primary"
            onclick="showPage('playground')">
            Try AgentOps
          </button>

          <button
            class="secondary"
            onclick="showPage('dashboard')">
            Open Dashboard
          </button>

          <button
            class="secondary"
            onclick="showPage('docs')">
            Documentation
          </button>

        </div>

      </div>

      <div class="hero-card">

        <div class="window-bar">
          <span class="window-dot"></span>
          <span class="window-dot"></span>
          <span class="window-dot"></span>
        </div>

        <div class="preview">

          <div class="preview-row">
            <span class="preview-label">Gateway</span>
            <span class="preview-value">Online</span>
          </div>

          <div class="preview-row">
            <span class="preview-label">Tracing</span>
            <span class="preview-value">Enabled</span>
          </div>

          <div class="preview-row">
            <span class="preview-label">PII protection</span>
            <span class="preview-value">Enabled</span>
          </div>

          <div class="preview-row">
            <span class="preview-label">Budget control</span>
            <span class="preview-value">Enabled</span>
          </div>

          <div class="preview-row">
            <span class="preview-label">Evaluations</span>
            <span class="preview-value">CI gated</span>
          </div>

        </div>

      </div>

    </div>

    <div class="section">

      <h2 class="section-title">
        Everything around your AI calls
      </h2>

      <p class="section-subtitle">
        Monitor requests, understand model behavior, protect sensitive data,
        and keep model spending under control.
      </p>

      <div class="feature-grid">

        <div class="feature-card">
          <div class="feature-icon">G</div>
          <h3>LLM Gateway</h3>
          <p>
            OpenAI-compatible chat completions with request validation,
            rate limiting, budget enforcement, and provider forwarding.
          </p>
        </div>

        <div class="feature-card">
          <div class="feature-icon">T</div>
          <h3>Tracing</h3>
          <p>
            Track traces, spans, latency, token usage, model information,
            errors, and costs for AI operations.
          </p>
        </div>

        <div class="feature-card">
          <div class="feature-icon">S</div>
          <h3>Security controls</h3>
          <p>
            PII redaction, API authentication, request limits,
            loop detection, and budget controls around model execution.
          </p>
        </div>

        <div class="feature-card">
          <div class="feature-icon">E</div>
          <h3>Evaluations</h3>
          <p>
            Run JSONL datasets against configurable evaluators with
            thresholds, regression checks, and CI integration.
          </p>
        </div>

        <div class="feature-card">
          <div class="feature-icon">C</div>
          <h3>Cost tracking</h3>
          <p>
            Track estimated model costs and enforce per-session spending
            limits before expensive requests execute.
          </p>
        </div>

        <div class="feature-card">
          <div class="feature-icon">O</div>
          <h3>Operations</h3>
          <p>
            Use readiness checks, trace promotion, workflow generation,
            and the dashboard to operate AI systems consistently.
          </p>
        </div>

      </div>

    </div>

    <div class="section">

      <h2 class="section-title">
        Connect an application
      </h2>

      <p class="section-subtitle">
        AgentOps exposes an OpenAI-compatible endpoint, so applications can
        send chat completion requests through the gateway.
      </p>

      <div class="code-card">
<pre>curl https://your-agentops-host/v1/chat/completions \
  -H 'content-type: application/json' \
  -H 'x-aop-session: demo1' \
  -H 'x-aop-agent: my-agent' \
  -d '{"model":"mock-1","messages":[{"role":"user","content":"Hello AgentOps"}]}'</pre>
      </div>

    </div>

  </div>

</section>


<!-- PLAYGROUND -->

<section id="playground" class="page">

  <div class="container playground-wrap">

    <div class="page-head">

      <div>
        <h1>AgentOps Playground</h1>
        <p>
          Send a request through the live AgentOps gateway.
        </p>
      </div>

      <span class="badge">
        <span class="status-dot"></span>
        Live gateway
      </span>

    </div>

    <div class="notice">
      The public playground currently uses the built-in mock provider.
      No external model API key is required for this demo.
    </div>

    <div class="playground">

      <div class="panel">

        <h2>Send a request</h2>

        <div class="field">

          <label for="play-model">
            Model
          </label>

          <select id="play-model">
            <option value="mock-1">
              mock-1
            </option>
          </select>

        </div>

        <div class="field">

          <label for="play-prompt">
            Prompt
          </label>

          <textarea
            id="play-prompt"
            placeholder="Ask something...">Hello from the AgentOps public playground.</textarea>

        </div>

        <div class="playground-actions">

          <button
            class="primary"
            id="send-btn"
            onclick="sendPlayground()">
            Send request
          </button>

          <button
            class="secondary"
            onclick="clearPlayground()">
            Clear
          </button>

        </div>

      </div>

      <div class="panel">

        <h2>Response</h2>

        <div
          id="play-output"
          class="output-box">No request sent yet.</div>

        <div class="meta-grid">

          <div class="meta">
            <span>Trace ID</span>
            <strong id="meta-trace">—</strong>
          </div>

          <div class="meta">
            <span>Tokens</span>
            <strong id="meta-tokens">—</strong>
          </div>

          <div class="meta">
            <span>Cost</span>
            <strong id="meta-cost">—</strong>
          </div>

          <div class="meta">
            <span>Status</span>
            <strong id="meta-status">—</strong>
          </div>

        </div>

      </div>

    </div>

  </div>

</section>


<!-- DASHBOARD -->

<section id="dashboard" class="page">

  <div class="container dashboard">

    <div class="page-head">

      <div>
        <h1>AgentOps Dashboard</h1>
        <p>
          Live traces, tokens, costs, models, and errors.
        </p>
      </div>

      <button
        class="secondary"
        onclick="loadDashboard(true)">
        Refresh
      </button>

    </div>

    <div
      class="grid"
      id="cards">
    </div>

    <div class="dashboard-section">

      <h2>By model</h2>

      <div class="wrap">
        <table id="models"></table>
      </div>

    </div>

    <div class="dashboard-section">

      <h2>Traces</h2>

      <div class="wrap">
        <table id="traces"></table>
      </div>

    </div>

    <div class="dashboard-section">

      <h2>Trace detail</h2>

      <pre
        id="detail"
        class="detail">Click a trace.</pre>

    </div>

  </div>

</section>


<!-- DOCS -->

<section id="docs" class="page">

  <div class="container docs">

    <div class="page-head">

      <div>
        <h1>AgentOps Documentation</h1>
        <p>
          Quick integration reference for the AgentOps gateway.
        </p>
      </div>

    </div>

    <div class="docs-grid">

      <div class="feature-card">

        <div class="feature-icon">1</div>

        <h3>Install</h3>

        <p>
          Install AgentOps locally with Python and use
          the <code>aop</code> command-line interface.
        </p>

      </div>

      <div class="feature-card">

        <div class="feature-icon">2</div>

        <h3>Gateway</h3>

        <p>
          Send OpenAI-compatible requests to
          <code>/v1/chat/completions</code>.
        </p>

      </div>

      <div class="feature-card">

        <div class="feature-icon">3</div>

        <h3>Tracing</h3>

        <p>
          Review traces, spans, model usage, latency,
          cost, and errors through the dashboard.
        </p>

      </div>

    </div>

    <div class="section doc-block">

      <h2>Quick start</h2>

      <div class="code-card">
<pre>pip install -e .

aop doctor
aop demo
aop traces
aop eval run
aop gateway</pre>
      </div>

    </div>

    <div class="section doc-block">

      <h2>Gateway example</h2>

      <div class="code-card">
<pre>curl https://agentops-platform-4d6p.onrender.com/v1/chat/completions \
  -H 'content-type: application/json' \
  -H 'x-aop-session: demo1' \
  -H 'x-aop-agent: my-agent' \
  -d '{"model":"mock-1","messages":[{"role":"user","content":"What is 6 x 7?"}]}'</pre>
      </div>

    </div>

    <div class="section doc-block">

      <h2>Security controls</h2>

      <div class="feature-grid">

        <div class="feature-card">
          <h3>PII redaction</h3>
          <p>
            Supported sensitive information is redacted before
            trace text is persisted.
          </p>
        </div>

        <div class="feature-card">
          <h3>Budget protection</h3>
          <p>
            Requests can be rejected before provider execution
            when estimated cost exceeds the configured session budget.
          </p>
        </div>

        <div class="feature-card">
          <h3>Loop detection</h3>
          <p>
            Repeated identical prompts can be detected and rejected
            to reduce runaway agent loops.
          </p>
        </div>

      </div>

    </div>

  </div>

</section>

</main>

<footer class="footer">
  <div class="container">
    AgentOps Platform · AI infrastructure, observability, security, and evaluation
  </div>
</footer>


<script>
const pages = [
  "home",
  "playground",
  "dashboard",
  "docs"
];

const esc = (value) =>
  String(value ?? "").replace(
    /[&<>"]/g,
    (character) => ({
      "&":"&amp;",
      "<":"&lt;",
      ">":"&gt;",
      '"':"&quot;"
    }[character])
  );

const num = (value, digits = 4) =>
  Number(value || 0).toFixed(digits);

function showPage(page){

  pages.forEach((name) => {

    const element =
      document.getElementById(name);

    if(element){
      element.classList.toggle(
        "active",
        name === page
      );
    }

  });

  document
    .querySelectorAll(".nav-btn")
    .forEach((button) => {

      button.classList.toggle(
        "active",
        button.dataset.page === page
      );

    });

  window.scrollTo({
    top:0,
    behavior:"smooth"
  });

  if(page === "dashboard"){
    loadDashboard();
  }

}

document
  .querySelectorAll(".nav-btn")
  .forEach((button) => {

    button.addEventListener(
      "click",
      () => showPage(button.dataset.page)
    );

  });


function createSessionId(){

  return (
    "public-" +
    Math.random()
      .toString(36)
      .slice(2,12)
  );

}


async function sendPlayground(){

  const button =
    document.getElementById("send-btn");

  const output =
    document.getElementById("play-output");

  const model =
    document.getElementById("play-model").value;

  const prompt =
    document.getElementById("play-prompt")
      .value
      .trim();

  if(!prompt){

    output.textContent =
      "Please enter a prompt.";

    return;

  }

  button.disabled = true;
  button.textContent = "Sending...";

  output.textContent =
    "Sending request...";

  document.getElementById(
    "meta-trace"
  ).textContent = "—";

  document.getElementById(
    "meta-tokens"
  ).textContent = "—";

  document.getElementById(
    "meta-cost"
  ).textContent = "—";

  document.getElementById(
    "meta-status"
  ).textContent = "Sending";

  const session =
    createSessionId();

  try{

    const response =
      await fetch(
        "/v1/chat/completions",
        {
          method:"POST",

          headers:{
            "content-type":
              "application/json",

            "x-aop-session":
              session,

            "x-aop-agent":
              "public-playground"
          },

          body:JSON.stringify({
            model:model,

            messages:[
              {
                role:"user",
                content:prompt
              }
            ]
          })
        }
      );

    const data =
      await response.json();

    if(!response.ok){

      output.textContent =
        data?.error?.message ||
        "Request failed.";

      document.getElementById(
        "meta-status"
      ).textContent =
        String(response.status);

      return;

    }

    const content =
      data?.choices?.[0]?.message?.content ||
      "No response content.";

    output.textContent =
      content;

    const traceId =
      response.headers.get(
        "x-aop-trace-id"
      ) || "—";

    const cost =
      response.headers.get(
        "x-aop-cost-usd"
      ) || "0.00000000";

    document.getElementById(
      "meta-trace"
    ).textContent =
      traceId;

    document.getElementById(
      "meta-tokens"
    ).textContent =
      `${data?.usage?.prompt_tokens ?? 0} in / ${data?.usage?.completion_tokens ?? 0} out`;

    document.getElementById(
      "meta-cost"
    ).textContent =
      "$" + cost;

    document.getElementById(
      "meta-status"
    ).textContent =
      "200 OK";

  }
  catch(error){

    output.textContent =
      "Unable to reach the AgentOps gateway.";

    document.getElementById(
      "meta-status"
    ).textContent =
      "Network error";

  }
  finally{

    button.disabled = false;
    button.textContent =
      "Send request";

  }

}


function clearPlayground(){

  document.getElementById(
    "play-prompt"
  ).value = "";

  document.getElementById(
    "play-output"
  ).textContent =
    "No request sent yet.";

  document.getElementById(
    "meta-trace"
  ).textContent = "—";

  document.getElementById(
    "meta-tokens"
  ).textContent = "—";

  document.getElementById(
    "meta-cost"
  ).textContent = "—";

  document.getElementById(
    "meta-status"
  ).textContent = "—";

}


async function loadDashboard(showLoading = false){

  if(showLoading){

    document.getElementById(
      "cards"
    ).innerHTML =
      '<div class="card"><b>...</b><span>Loading</span></div>';

  }

  try{

    const statsResponse =
      await fetch("/api/stats");

    const stats =
      await statsResponse.json();

    if(!statsResponse.ok){

      throw new Error(
        stats?.error?.message ||
        "Dashboard unavailable"
      );

    }

    const totals =
      stats.totals || {};

    document.getElementById(
      "cards"
    ).innerHTML = [

      ["Traces",totals.traces],

      ["Spans",totals.spans],

      [
        "Cost (USD)",
        "$" + num(totals.cost_usd)
      ],

      ["Tokens in",totals.tokens_in],

      ["Tokens out",totals.tokens_out],

      ["Errors",totals.errors]

    ]
    .map(
      ([label,value]) =>
        `<div class="card">
          <b>${esc(value)}</b>
          <span>${esc(label)}</span>
        </div>`
    )
    .join("");


    document.getElementById(
      "models"
    ).innerHTML =

      "<tr>" +
      "<th>Model</th>" +
      "<th>Calls</th>" +
      "<th>Cost</th>" +
      "<th>Avg ms</th>" +
      "</tr>" +

      (stats.by_model || [])
        .map(
          (model) =>
            `<tr>
              <td>${esc(model.model)}</td>
              <td>${esc(model.calls)}</td>
              <td>$${num(model.cost_usd)}</td>
              <td>${num(model.avg_latency_ms,1)}</td>
            </tr>`
        )
        .join("");


    const tracesResponse =
      await fetch("/api/traces");

    const traces =
      await tracesResponse.json();

    if(!tracesResponse.ok){

      throw new Error(
        "Unable to load traces"
      );

    }

    const traceList =
      Array.isArray(traces)
        ? traces
        : [];

    document.getElementById(
      "traces"
    ).innerHTML =

      "<tr>" +
      "<th>Trace</th>" +
      "<th>Root</th>" +
      "<th>Spans</th>" +
      "<th>Cost</th>" +
      "<th>Err</th>" +
      "</tr>" +

      traceList
        .map(
          (trace) =>
            `<tr
              class="t"
              onclick="showTrace(${JSON.stringify(trace.trace_id)})">

              <td>
                ${esc(
                  String(trace.trace_id).slice(0,12)
                )}
              </td>

              <td>
                ${esc(trace.root || "-")}
              </td>

              <td>
                ${esc(trace.spans)}
              </td>

              <td>
                $${num(trace.cost_usd)}
              </td>

              <td
                class="${
                  trace.errors
                    ? "err"
                    : ""
                }">

                ${esc(trace.errors)}

              </td>

            </tr>`
        )
        .join("");

  }
  catch(error){

    document.getElementById(
      "cards"
    ).innerHTML =
      `<div class="card">
        <b>Unavailable</b>
        <span>${esc(error.message)}</span>
      </div>`;

    document.getElementById(
      "models"
    ).innerHTML =
      "<tr><td>Dashboard data unavailable.</td></tr>";

    document.getElementById(
      "traces"
    ).innerHTML =
      "<tr><td>Dashboard data unavailable.</td></tr>";

  }

}


async function showTrace(id){

  try{

    const response =
      await fetch(
        "/api/traces/" +
        encodeURIComponent(id)
      );

    const spans =
      await response.json();

    if(!response.ok){

      throw new Error(
        spans?.error ||
        "Trace not found"
      );

    }

    document.getElementById(
      "detail"
    ).textContent =

      spans
        .map(
          (span) =>

            `${String(span.kind || "")
              .padEnd(9)} ` +

            `${span.name || ""}  ` +

            `${(
              (span.end_ts - span.start_ts) *
              1000
            ).toFixed(1)}ms  ` +

            `$${num(span.cost_usd,6)}  ` +

            `${span.status || ""}\\n` +

            `   in: ${
              (span.input || "")
                .slice(0,120)
            }\\n` +

            `  out: ${
              (span.output || "")
                .slice(0,120)
            }`

        )
        .join("\\n\\n");

  }
  catch(error){

    document.getElementById(
      "detail"
    ).textContent =
      error.message;

  }

}


showPage("home");

</script>

</body>
</html>"""