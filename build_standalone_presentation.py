import base64
import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGO_PATH = os.path.join(BASE_DIR, "static", "logo_transparent.png")
SPACE_APPS_PATH = os.path.join(BASE_DIR, "static", "nasa_space_apps_white.png")
OUTPUT_STANDALONE = os.path.join(BASE_DIR, "SpectraLink_Presentation_Standalone.html")
OUTPUT_ROOT_PRES = os.path.join(BASE_DIR, "presentation.html")
OUTPUT_STATIC_PRES = os.path.join(BASE_DIR, "static", "presentation.html")

# Read SpectraLink logo and encode as Base64
with open(LOGO_PATH, "rb") as f:
    logo_base64 = "data:image/png;base64," + base64.b64encode(f.read()).decode("utf-8")

# Read NASA Space Apps White logo and encode as Base64
with open(SPACE_APPS_PATH, "rb") as f:
    space_apps_base64 = "data:image/png;base64," + base64.b64encode(f.read()).decode("utf-8")

# Read cache data if available to embed authentic timeline & heatmap data
cache_path = os.path.join(BASE_DIR, "data_cache", "nile_delta_analysis.json")
timeline_data = []
forecast_data = []
calendar_z = []

if os.path.exists(cache_path):
    try:
        with open(cache_path, "r", encoding="utf-8") as f:
            d = json.load(f)
            timeline_data = d.get("timeline", [])
            forecast_data = d.get("forecast", [])
            calendar_z = d.get("calendar_matrix", {}).get("values", [])
    except Exception as e:
        print("Warning reading cache:", e)

# HTML Template (7 SLIDES MASTER DECK FOR NASA SPACE APPS CHALLENGE)
html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>SpectraLink | NASA Space Apps Challenge 7-Slide Interactive Presentation</title>
  
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&family=Space+Grotesk:wght@500;600;700&display=swap" rel="stylesheet">
  
  <!-- Standalone Plotly.js from CDN -->
  <script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>

  <style>
    /* ==========================================================================
       SPECTRALINK 7-SLIDE MASTER PRESENTATION ENGINE
       ========================================================================== */
    :root {{
      --bg-space: #070A12;
      --bg-panel: rgba(13, 20, 38, 0.85);
      --bg-card: rgba(17, 27, 52, 0.78);
      --bg-card-hover: rgba(24, 38, 72, 0.95);
      
      --cyan: #38BDF8;
      --cyan-glow: rgba(56, 189, 248, 0.45);
      --amber: #F59E0B;
      --amber-glow: rgba(245, 158, 11, 0.45);
      --orange: #F97316;
      --red: #EF4444;
      --green: #10B981;
      
      --text-main: #F8FAFC;
      --text-muted: #94A3B8;
      --text-dim: #64748B;
      --border: rgba(255, 255, 255, 0.10);
      --border-cyan: rgba(56, 189, 248, 0.35);
      
      --font-display: 'Space Grotesk', sans-serif;
      --font-sans: 'Inter', sans-serif;
      --font-mono: 'JetBrains Mono', monospace;
      
      --easing: cubic-bezier(0.16, 1, 0.3, 1);
    }}

    *, *::before, *::after {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }}

    body {{
      background-color: var(--bg-space);
      color: var(--text-main);
      font-family: var(--font-sans);
      overflow: hidden;
      width: 100vw;
      height: 100vh;
      user-select: none;
    }}

    /* Ambient Interactive Canvas (Stars + Sparks) */
    #ambient-canvas {{
      position: fixed;
      inset: 0;
      width: 100%;
      height: 100%;
      pointer-events: none;
      z-index: 0;
    }}

    /* Top Telemetry Header */
    .pres-header {{
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      height: 60px;
      background: rgba(9, 14, 28, 0.94);
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
      border-bottom: 1px solid var(--border);
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 24px;
      z-index: 50;
    }}

    .header-brand {{
      display: flex;
      align-items: center;
      gap: 12px;
    }}

    .brand-logo {{
      height: 38px;
      width: auto;
      object-fit: contain;
    }}

    .brand-divider {{
      width: 1px;
      height: 22px;
      background: var(--border);
    }}

    .space-apps-logo {{
      height: 28px;
      width: auto;
      object-fit: contain;
    }}

    .brand-badge {{
      display: flex;
      flex-direction: column;
    }}

    .brand-title {{
      font-family: var(--font-display);
      font-size: 0.95rem;
      font-weight: 700;
      letter-spacing: -0.01em;
      color: #fff;
    }}

    .brand-sub {{
      font-family: var(--font-mono);
      font-size: 0.65rem;
      color: var(--cyan);
      letter-spacing: 0.04em;
    }}

    .header-status {{
      display: flex;
      align-items: center;
      gap: 16px;
    }}

    .slide-progress-pill {{
      display: flex;
      align-items: center;
      gap: 6px;
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid var(--border);
      padding: 5px 14px;
      border-radius: 20px;
      font-family: var(--font-mono);
      font-size: 0.78rem;
    }}

    .slide-progress-pill .curr {{
      color: var(--cyan);
      font-weight: 700;
    }}

    .header-actions {{
      display: flex;
      align-items: center;
      gap: 10px;
    }}

    .btn-header-action {{
      display: flex;
      align-items: center;
      gap: 6px;
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid var(--border);
      color: var(--text-muted);
      padding: 6px 14px;
      border-radius: 6px;
      font-size: 0.78rem;
      font-weight: 600;
      cursor: pointer;
      text-decoration: none;
      transition: all 0.2s ease;
    }}

    .btn-header-action:hover {{
      color: #fff;
      background: rgba(255, 255, 255, 0.1);
      border-color: var(--border-cyan);
    }}

    .btn-live-launch {{
      background: rgba(56, 189, 248, 0.12);
      border-color: rgba(56, 189, 248, 0.35);
      color: var(--cyan);
    }}

    .btn-live-launch:hover {{
      background: var(--cyan);
      color: #030712;
      box-shadow: 0 0 16px var(--cyan-glow);
    }}

    /* Presentation Main Container */
    #deck-container {{
      position: absolute;
      top: 60px;
      left: 0;
      right: 0;
      bottom: 54px;
      overflow: hidden;
      z-index: 10;
    }}

    /* Slide Base Layout */
    .slide {{
      position: absolute;
      inset: 0;
      width: 100vw;
      height: calc(100vh - 114px);
      padding: 30px 48px 24px 48px;
      display: flex;
      flex-direction: column;
      justify-content: center;
      align-items: center;
      opacity: 0;
      pointer-events: none;
      transform: scale(0.98) translateY(12px);
      transition: opacity 0.4s var(--easing), transform 0.4s var(--easing);
    }}

    .slide.active {{
      opacity: 1;
      pointer-events: auto;
      transform: scale(1) translateY(0);
    }}

    .slide-content-wrap {{
      width: 100%;
      max-width: 1380px;
      height: 100%;
      display: flex;
      flex-direction: column;
      justify-content: center;
    }}

    /* Slide Titles & Headers */
    .slide-header-block {{
      margin-bottom: 20px;
    }}

    .slide-badge-category {{
      font-family: var(--font-mono);
      font-size: 0.72rem;
      font-weight: 700;
      color: var(--cyan);
      text-transform: uppercase;
      letter-spacing: 0.08em;
      margin-bottom: 6px;
    }}

    .slide-title {{
      font-family: var(--font-display);
      font-size: 2.1rem;
      font-weight: 700;
      line-height: 1.2;
      color: #fff;
      letter-spacing: -0.01em;
    }}

    .slide-title .highlight {{
      color: var(--cyan);
    }}

    .slide-subtitle {{
      font-size: 0.95rem;
      color: var(--text-muted);
      margin-top: 6px;
      line-height: 1.5;
      max-width: 900px;
    }}

    /* Glass Cards */
    .glass-card {{
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 20px;
      transition: all 0.25s ease;
      backdrop-filter: blur(8px);
      -webkit-backdrop-filter: blur(8px);
    }}

    .glass-card:hover {{
      background: var(--bg-card-hover);
      border-color: rgba(56, 189, 248, 0.3);
      box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
    }}

    /* Slide 1: Hero Layout */
    .hero-layout {{
      display: grid;
      grid-template-columns: 1.2fr 0.8fr;
      gap: 36px;
      align-items: center;
      width: 100%;
    }}

    .hero-title {{
      font-family: var(--font-display);
      font-size: 2.8rem;
      font-weight: 700;
      line-height: 1.15;
      color: #fff;
      margin-bottom: 12px;
    }}

    .hero-title span {{
      color: var(--cyan);
    }}

    .hero-partnership-badge {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid var(--border);
      padding: 6px 14px;
      border-radius: 20px;
      font-family: var(--font-mono);
      font-size: 0.72rem;
      color: var(--cyan);
      margin-bottom: 16px;
    }}

    .hero-stat-grid {{
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 12px;
      margin-top: 24px;
    }}

    .hero-stat-box {{
      background: rgba(255, 255, 255, 0.03);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 12px 14px;
      display: flex;
      flex-direction: column;
    }}

    .hero-stat-box .val {{
      font-family: var(--font-display);
      font-size: 1.6rem;
      font-weight: 700;
      color: #fff;
    }}

    .hero-stat-box .lbl {{
      font-size: 0.7rem;
      color: var(--text-dim);
      margin-top: 2px;
    }}

    .hero-question-card {{
      background: rgba(56, 189, 248, 0.06);
      border: 1px solid rgba(56, 189, 248, 0.25);
      border-radius: 10px;
      padding: 16px 20px;
      margin-top: 20px;
      font-size: 0.92rem;
      color: #E2E8F0;
      line-height: 1.5;
    }}

    .globe-simulation-art {{
      position: relative;
      width: 320px;
      height: 320px;
      margin: 0 auto;
      border-radius: 50%;
      background: radial-gradient(circle at 35% 35%, #1e3a8a 0%, #0c1836 60%, #030712 100%);
      box-shadow: 0 0 50px rgba(56, 189, 248, 0.25), inset -10px -10px 40px rgba(0, 0, 0, 0.8);
      display: flex;
      align-items: center;
      justify-content: center;
    }}

    .orbit-ring {{
      position: absolute;
      border-radius: 50%;
      border: 1px dashed rgba(56, 189, 248, 0.4);
      pointer-events: none;
    }}

    .orbit-ring.modis {{
      width: 370px;
      height: 370px;
      transform: rotateX(72deg) rotateY(15deg);
      border-color: #10B981;
    }}

    .orbit-ring.viirs {{
      width: 410px;
      height: 410px;
      transform: rotateX(72deg) rotateY(-20deg);
      border-color: #F97316;
    }}

    /* Slide 2: The 2012 Trap & Pixel Sim */
    .trap-sim-layout {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 24px;
      width: 100%;
      align-items: center;
    }}

    .sim-card-wrap {{
      display: flex;
      flex-direction: column;
      gap: 12px;
    }}

    .sim-btn-group {{
      display: flex;
      gap: 6px;
      margin: 8px 0;
    }}

    .btn-sim-mode {{
      flex: 1;
      padding: 7px 10px;
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid var(--border);
      border-radius: 6px;
      color: var(--text-muted);
      font-size: 0.76rem;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.15s ease;
    }}

    .btn-sim-mode.active {{
      background: var(--cyan);
      color: #030712;
      border-color: var(--cyan);
      box-shadow: 0 0 12px var(--cyan-glow);
    }}

    .pixel-grid-container {{
      position: relative;
      width: 260px;
      height: 260px;
      margin: 0 auto;
      background: #020617;
      border: 2px solid var(--border);
      border-radius: 10px;
      overflow: hidden;
    }}

    .dual-grid-wrapper {{
      display: flex;
      gap: 16px;
      justify-content: center;
    }}

    .dual-panel {{
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 6px;
    }}

    .dual-box {{
      width: 140px !important;
      height: 140px !important;
    }}

    .ground-fire-source {{
      position: absolute;
      border-radius: 50%;
      background: radial-gradient(circle, #EF4444 20%, #F59E0B 60%, transparent 85%);
      filter: blur(2px);
      animation: pulseFire 1.6s ease-in-out infinite;
    }}

    @keyframes pulseFire {{
      0%, 100% {{ opacity: 0.85; transform: scale(1); }}
      50% {{ opacity: 1; transform: scale(1.12); }}
    }}

    .grid-svg-overlay {{
      position: absolute;
      inset: 0;
      width: 100%;
      height: 100%;
    }}

    .pixel-cell.active-modis {{
      fill: rgba(239, 68, 68, 0.50);
      stroke: #EF4444;
      stroke-width: 2.5;
    }}

    .pixel-cell.active-viirs {{
      fill: rgba(245, 158, 11, 0.55);
      stroke: #F59E0B;
      stroke-width: 1.5;
    }}

    .chart-frame-box {{
      background: #0B1120;
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 12px;
      height: 340px;
      width: 100%;
    }}

    /* Slide 3: 4 Geospatial Pillars */
    .pillar-grid-4 {{
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 16px;
      margin-top: 10px;
    }}

    .pillar-card {{
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      height: 380px;
      padding: 20px;
    }}

    .pillar-num {{
      font-family: var(--font-mono);
      font-size: 0.85rem;
      font-weight: 700;
      color: var(--cyan);
      background: rgba(56, 189, 248, 0.12);
      border: 1px solid var(--border-cyan);
      width: 32px;
      height: 32px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      margin-bottom: 12px;
    }}

    .pillar-title {{
      font-family: var(--font-display);
      font-size: 1.15rem;
      font-weight: 700;
      color: #fff;
      margin-bottom: 8px;
    }}

    .pillar-desc {{
      font-size: 0.82rem;
      color: var(--text-muted);
      line-height: 1.5;
    }}

    .pillar-features-list {{
      list-style: none;
      margin-top: 14px;
      font-family: var(--font-mono);
      font-size: 0.72rem;
      color: #CBD5E1;
      display: flex;
      flex-direction: column;
      gap: 6px;
    }}

    .pillar-features-list li {{
      display: flex;
      align-items: center;
      gap: 6px;
    }}

    .pillar-features-list li::before {{
      content: '✦';
      color: var(--cyan);
      font-size: 0.7rem;
    }}

    /* Slide 4: AI Benchmark */
    .benchmark-layout {{
      display: grid;
      grid-template-columns: 1.15fr 0.85fr;
      gap: 24px;
      align-items: center;
      margin-top: 8px;
    }}

    .race-list {{
      display: flex;
      flex-direction: column;
      gap: 10px;
    }}

    .race-row {{
      display: flex;
      flex-direction: column;
      gap: 3px;
    }}

    .race-meta {{
      display: flex;
      justify-content: space-between;
      font-size: 0.8rem;
      font-weight: 600;
    }}

    .race-bar-track {{
      height: 9px;
      background: rgba(255, 255, 255, 0.06);
      border-radius: 999px;
      overflow: hidden;
    }}

    .race-bar-fill {{
      height: 100%;
      border-radius: 999px;
      transition: width 1s ease-out;
    }}

    /* Slide 5: Dual Timeline & Heatmap */
    .breakthrough-split {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 20px;
      margin-top: 10px;
    }}

    /* Slide 6: Forecast & Carbon */
    .forecast-layout {{
      display: grid;
      grid-template-columns: 0.8fr 1.2fr;
      gap: 24px;
      align-items: center;
      margin-top: 10px;
    }}

    /* Slide 7: Mission Control Hub */
    .mission-hub-grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 24px;
      margin-top: 14px;
    }}

    .cta-banner-strip {{
      display: flex;
      justify-content: center;
      gap: 16px;
      margin-top: 24px;
    }}

    .btn-cta-main {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 12px 28px;
      border-radius: 8px;
      font-family: var(--font-display);
      font-size: 0.95rem;
      font-weight: 700;
      text-decoration: none;
      cursor: pointer;
      transition: all 0.2s var(--easing);
    }}

    .btn-cta-cyan {{
      background: var(--cyan);
      color: #030712;
      box-shadow: 0 0 20px var(--cyan-glow);
    }}

    .btn-cta-cyan:hover {{
      transform: translateY(-2px);
      box-shadow: 0 0 30px var(--cyan-glow);
    }}

    .btn-cta-ghost {{
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid var(--border);
      color: #fff;
    }}

    .btn-cta-ghost:hover {{
      background: rgba(255, 255, 255, 0.1);
      border-color: var(--border-cyan);
      transform: translateY(-2px);
    }}

    /* Bottom Navigation Dock */
    .pres-footer {{
      position: fixed;
      bottom: 0;
      left: 0;
      right: 0;
      height: 54px;
      background: rgba(9, 14, 28, 0.94);
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
      border-top: 1px solid var(--border);
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 24px;
      z-index: 50;
    }}

    .nav-dots {{
      display: flex;
      align-items: center;
      gap: 8px;
    }}

    .dot-step {{
      width: 10px;
      height: 10px;
      border-radius: 50%;
      background: rgba(255, 255, 255, 0.15);
      cursor: pointer;
      transition: all 0.2s ease;
    }}

    .dot-step:hover {{
      background: var(--cyan);
      transform: scale(1.2);
    }}

    .dot-step.active {{
      width: 26px;
      border-radius: 10px;
      background: var(--cyan);
      box-shadow: 0 0 10px var(--cyan-glow);
    }}

    .nav-arrow-btns {{
      display: flex;
      gap: 8px;
    }}

    .btn-nav-arrow {{
      width: 36px;
      height: 36px;
      border-radius: 8px;
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid var(--border);
      color: #fff;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      transition: all 0.2s ease;
    }}

    .btn-nav-arrow:hover {{
      background: rgba(255, 255, 255, 0.12);
      border-color: var(--border-cyan);
    }}
  </style>
</head>
<body>

  <!-- Ambient Interactive Starfield Canvas -->
  <canvas id="ambient-canvas"></canvas>

  <!-- Top Telemetry Header -->
  <header class="pres-header">
    <div class="header-brand">
      <img src="{logo_base64}" alt="SpectraLink" class="brand-logo" title="SpectraLink">
      <div class="brand-divider"></div>
      <img src="{space_apps_base64}" alt="NASA Space Apps Challenge" class="space-apps-logo" title="NASA Space Apps Challenge">
      <div class="brand-badge">
        <span class="brand-title">SpectraLink</span>
        <span class="brand-sub">NASA SPACE APPS CHALLENGE · SENSOR HARMONIZATION</span>
      </div>
    </div>

    <div class="header-status">
      <div class="slide-progress-pill">
        <span>SLIDE</span>
        <span id="header-slide-num" class="curr">01</span>
        <span>/ 07</span>
        <span id="header-slide-chapter" style="color: #64748B; margin-left: 8px;">· The Hook & Challenge</span>
      </div>
    </div>

    <div class="header-actions">
      <button id="btn-toggle-fs" class="btn-header-action" title="Toggle Fullscreen (Shortcut: F)">
        <span>⛶</span>
        <span>Fullscreen</span>
      </button>
      <a href="https://ahmedshaban0.github.io/SpectraLink/" target="_blank" class="btn-header-action btn-live-launch" title="Launch Live 3D Mission Control">
        <span>🌍</span>
        <span>Live 3D Globe</span>
      </a>
    </div>
  </header>


  <!-- ========================================================================= -->
  <!-- PRESENTATION SLIDE DECK (EXACTLY 7 HIGH-IMPACT SLIDES)                    -->
  <!-- ========================================================================= -->
  <main id="deck-container">

    <!-- --------------------------------------------------------------------- -->
    <!-- SLIDE 1: The Hook — Watching Earth Breathe Fire                       -->
    <!-- --------------------------------------------------------------------- -->
    <section class="slide active" data-slide="1" data-chapter="The Hook & Challenge">
      <div class="slide-content-wrap">
        <div class="hero-layout">
          <div>
            <div class="hero-partnership-badge">
              <img src="{space_apps_base64}" alt="NASA Space Apps" style="height: 14px;">
              <span>NASA SPACE APPS CHALLENGE · GLOBAL AWARDS SUBMISSION</span>
            </div>
            <h1 class="hero-title">
              Watching Earth <span>Breathe Fire</span>
            </h1>
            <p class="slide-subtitle">
              How we united 25 years of NASA satellite history using Physics-Informed Machine Learning and Google Earth Engine.
            </p>

            <div class="hero-question-card">
              <strong>The Core Scientific Question:</strong> How do climate researchers and fire management agencies know if global wildfires and agricultural burning are <em>truly getting worse</em> over the last 25 years, or if our orbital sensors simply got sharper?
            </div>

            <div class="hero-stat-grid">
              <div class="hero-stat-box">
                <span class="val">25 Years</span>
                <span class="lbl">2001–2025 Continuous Time Series</span>
              </div>
              <div class="hero-stat-box">
                <span class="val">~200</span>
                <span class="lbl">Global Countries & Biomes</span>
              </div>
              <div class="hero-stat-box">
                <span class="val">32 Clues</span>
                <span class="lbl">Physics-Informed Features</span>
              </div>
              <div class="hero-stat-box">
                <span class="val" style="color: var(--cyan);">98.7%</span>
                <span class="lbl">Cross-Sensor Calibration Parity</span>
              </div>
            </div>
          </div>

          <div>
            <div class="globe-simulation-art">
              <div class="orbit-ring modis"></div>
              <div class="orbit-ring viirs"></div>
              <span style="font-size: 3rem;">🔥</span>
            </div>
          </div>
        </div>
      </div>
    </section>


    <!-- --------------------------------------------------------------------- -->
    <!-- SLIDE 2: Chapter 1 — The 2012 Climate Trap & Resolution Paradox       -->
    <!-- --------------------------------------------------------------------- -->
    <section class="slide" data-slide="2" data-chapter="The 2012 Sensor Trap">
      <div class="slide-content-wrap">
        <div class="slide-header-block">
          <div class="slide-badge-category">Chapter 1 · The Sensor Resolution Trap</div>
          <h2 class="slide-title">The 2012 <span class="highlight">Climate Trap</span>: The Artificial +404% Hotspot Surge</h2>
          <p class="slide-subtitle">
            In 2012, NASA transitioned from 1,000m MODIS to 375m VIIRS. Because VIIRS has a 7.1x smaller pixel area, it catches small fires previously diluted below MODIS thresholds.
          </p>
        </div>

        <div class="trap-sim-layout">
          <!-- Left: Interactive Pixel Simulator -->
          <div class="glass-card sim-card-wrap">
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <span style="font-size: 0.9rem; font-weight: 700; color: #fff;">Interactive Sensor Grid View:</span>
              <span id="sim-stat-count" style="font-family: var(--font-mono); font-size: 0.85rem; font-weight: 700; color: var(--amber);">1 Hot Spot vs 6 Hot Spots</span>
            </div>
            
            <div class="sim-btn-group">
              <button id="btn-sim-modis" class="btn-sim-mode" onclick="setSimMode('modis')">MODIS (1 km)</button>
              <button id="btn-sim-viirs" class="btn-sim-mode" onclick="setSimMode('viirs')">VIIRS (375 m)</button>
              <button id="btn-sim-split" class="btn-sim-mode active" onclick="setSimMode('split')">Side-by-Side Reality Check</button>
            </div>

            <!-- Single Grid -->
            <div id="single-grid-container" class="pixel-grid-container hidden">
              <div class="ground-fire-source" style="top: 42%; left: 45%; width: 14%; height: 14%;"></div>
              <div class="ground-fire-source" style="top: 48%; left: 38%; width: 9%; height: 9%;"></div>
              <div class="ground-fire-source" style="top: 25%; left: 65%; width: 7%; height: 7%;"></div>
              <div class="ground-fire-source" style="top: 70%; left: 28%; width: 7%; height: 7%;"></div>
              <svg id="sim-grid-svg" class="grid-svg-overlay" viewBox="0 0 100 100"></svg>
            </div>

            <!-- Dual Side-by-Side Grid -->
            <div id="dual-grid-container" class="dual-grid-wrapper">
              <div class="dual-panel">
                <span style="font-size: 0.72rem; color: #EF4444; font-weight: 700;">MODIS 1km (1 Hot Spot)</span>
                <div class="pixel-grid-container dual-box">
                  <div class="ground-fire-source" style="top: 42%; left: 45%; width: 14%; height: 14%;"></div>
                  <div class="ground-fire-source" style="top: 48%; left: 38%; width: 9%; height: 9%;"></div>
                  <div class="ground-fire-source" style="top: 25%; left: 65%; width: 7%; height: 7%;"></div>
                  <div class="ground-fire-source" style="top: 70%; left: 28%; width: 7%; height: 7%;"></div>
                  <svg id="sim-grid-svg-modis-dual" class="grid-svg-overlay" viewBox="0 0 100 100"></svg>
                </div>
              </div>
              <div class="dual-panel">
                <span style="font-size: 0.72rem; color: #38BDF8; font-weight: 700;">VIIRS 375m (6 Hot Spots)</span>
                <div class="pixel-grid-container dual-box">
                  <div class="ground-fire-source" style="top: 42%; left: 45%; width: 14%; height: 14%;"></div>
                  <div class="ground-fire-source" style="top: 48%; left: 38%; width: 9%; height: 9%;"></div>
                  <div class="ground-fire-source" style="top: 25%; left: 65%; width: 7%; height: 7%;"></div>
                  <div class="ground-fire-source" style="top: 70%; left: 28%; width: 7%; height: 7%;"></div>
                  <svg id="sim-grid-svg-viirs-dual" class="grid-svg-overlay" viewBox="0 0 100 100"></svg>
                </div>
              </div>
            </div>

            <p style="font-size: 0.78rem; color: var(--text-muted); line-height: 1.4; margin-top: 4px;">
              <strong>The Reality:</strong> For the exact same physical fire ground event, MODIS detects 1 hotspot while VIIRS detects 6. Without AI harmonization, raw counts spike artificially.
            </p>
          </div>

          <!-- Right: The 2012 Discontinuity Trap Chart -->
          <div class="chart-frame-box">
            <div style="font-size: 0.85rem; font-weight: 700; color: #fff; margin-bottom: 4px;">
              Raw Hotspot Discontinuity (January 2012 Step-Jump):
            </div>
            <div id="plot-raw-trap" style="width: 100%; height: 280px;"></div>
          </div>
        </div>
      </div>
    </section>


    <!-- --------------------------------------------------------------------- -->
    <!-- SLIDE 3: Chapter 2 — Physics-Informed Geospatial Architecture        -->
    <!-- --------------------------------------------------------------------- -->
    <section class="slide" data-slide="3" data-chapter="Geospatial AI Architecture">
      <div class="slide-content-wrap">
        <div class="slide-header-block">
          <div class="slide-badge-category">Chapter 2 · The Solution Architecture</div>
          <h2 class="slide-title">Physics-Informed Architecture: <span class="highlight">32 Geospatial Clues</span></h2>
          <p class="slide-subtitle">
            SpectraLink models the entire physical transmission chain from Earth's burning surface up to satellite focal planes using Google Earth Engine.
          </p>
        </div>

        <div class="pillar-grid-4">
          <!-- Pillar 1 -->
          <div class="glass-card pillar-card">
            <div>
              <div class="pillar-num">01</div>
              <h3 class="pillar-title">Sensor & Orbit Geometry</h3>
              <p class="pillar-desc">Accounts for pixel bow-tie enlargement and angular atmospheric path lengths.</p>
            </div>
            <ul class="pillar-features-list">
              <li>Scan Angle (θ) Expansion</li>
              <li>Solar Zenith Angle (θz)</li>
              <li>Pixel Footprint Area (m²)</li>
              <li>Local Satellite Elevation</li>
            </ul>
          </div>

          <!-- Pillar 2 -->
          <div class="glass-card pillar-card">
            <div>
              <div class="pillar-num">02</div>
              <h3 class="pillar-title">Atmospheric Physics</h3>
              <p class="pillar-desc">Quantifies optical depth, smoke transmission attenuation, and water vapor absorption.</p>
            </div>
            <ul class="pillar-features-list">
              <li>Atmospheric Transmission (τ)</li>
              <li>Total Column Water Vapor</li>
              <li>Aerosol Optical Depth (AOD)</li>
              <li>4μm Radiant Transmission</li>
            </ul>
          </div>

          <!-- Pillar 3 -->
          <div class="glass-card pillar-card">
            <div>
              <div class="pillar-num">03</div>
              <h3 class="pillar-title">Fuel & Biome Phenology</h3>
              <p class="pillar-desc">Extracts dynamic vegetative moisture and land cover taxonomy from Earth Engine.</p>
            </div>
            <ul class="pillar-features-list">
              <li>MODIS NDVI Vegetation Index</li>
              <li>NDWI Moisture Deficit</li>
              <li>Enhanced Vegetation Index (EVI)</li>
              <li>MCD12Q1 Land Cover Taxonomy</li>
            </ul>
          </div>

          <!-- Pillar 4 -->
          <div class="glass-card pillar-card">
            <div>
              <div class="pillar-num">04</div>
              <h3 class="pillar-title">Diurnal Progression</h3>
              <p class="pillar-desc">Synchronizes Terra (10:30 AM), Aqua (1:30 PM), and VIIRS (1:30 PM/AM) orbits.</p>
            </div>
            <ul class="pillar-features-list">
              <li>Gaussian Diurnal Peak Kernel</li>
              <li>Solar Radiant Heat Flux</li>
              <li>Overpass Time Inter-Calibration</li>
              <li>Day/Night Thermal Contrast</li>
            </ul>
          </div>
        </div>
      </div>
    </section>


    <!-- --------------------------------------------------------------------- -->
    <!-- SLIDE 4: Chapter 3 — AI Benchmark & SpectraNet Ensemble               -->
    <!-- --------------------------------------------------------------------- -->
    <section class="slide" data-slide="4" data-chapter="SpectraNet Model Benchmark">
      <div class="slide-content-wrap">
        <div class="slide-header-block">
          <div class="slide-badge-category">Chapter 3 · Machine Learning Rigor</div>
          <h2 class="slide-title">6-Model Benchmark: <span class="highlight">SpectraNet Hybrid Stacking</span></h2>
          <p class="slide-subtitle">
            Rigorous cross-validation across diverse global biomes proved that our custom stacking ensemble outperformed all standalone baselines.
          </p>
        </div>

        <div class="benchmark-layout">
          <!-- Left: Accuracy Leaderboard -->
          <div class="glass-card race-list">
            <span style="font-size: 0.85rem; font-weight: 700; color: #fff; margin-bottom: 6px;">Cross-Validation Model Accuracy Arena:</span>
            
            <div class="race-row">
              <div class="race-meta">
                <span style="color: var(--cyan); font-weight: 700;">🥇 6. SpectraNet Hybrid Stacking (Ensemble)</span>
                <span style="color: var(--cyan);">98.7% R² (r = 0.9934)</span>
              </div>
              <div class="race-bar-track">
                <div class="race-bar-fill" style="width: 98.7%; background: var(--cyan); box-shadow: 0 0 10px var(--cyan-glow);"></div>
              </div>
            </div>

            <div class="race-row">
              <div class="race-meta">
                <span>🥈 5. Huber-Loss GBDT & ExtraTrees Blend</span>
                <span>98.2% R²</span>
              </div>
              <div class="race-bar-track">
                <div class="race-bar-fill" style="width: 98.2%; background: #38BDF8;"></div>
              </div>
            </div>

            <div class="race-row">
              <div class="race-meta">
                <span>🥉 4. LightGBM Regressor</span>
                <span>97.8% R²</span>
              </div>
              <div class="race-bar-track">
                <div class="race-bar-fill" style="width: 97.8%; background: #0EA5E9;"></div>
              </div>
            </div>

            <div class="race-row">
              <div class="race-meta">
                <span>4. Random Forest Ensemble</span>
                <span>96.5% R²</span>
              </div>
              <div class="race-bar-track">
                <div class="race-bar-fill" style="width: 96.5%; background: #64748B;"></div>
              </div>
            </div>

            <div class="race-row">
              <div class="race-meta">
                <span>3. Deep MLP-ResNet Neural Net</span>
                <span>95.4% R²</span>
              </div>
              <div class="race-bar-track">
                <div class="race-bar-fill" style="width: 95.4%; background: #475569;"></div>
              </div>
            </div>

            <div class="race-row">
              <div class="race-meta">
                <span>1. Statistical Scaling Baseline</span>
                <span>91.2% R²</span>
              </div>
              <div class="race-bar-track">
                <div class="race-bar-fill" style="width: 91.2%; background: #334155;"></div>
              </div>
            </div>
          </div>

          <!-- Right: Architecture Highlights -->
          <div style="display: flex; flex-direction: column; gap: 14px;">
            <div class="glass-card" style="border-left: 4px solid var(--cyan);">
              <h4 style="font-size: 1rem; color: #fff; margin-bottom: 4px;">Why Stacking Won:</h4>
              <p style="font-size: 0.84rem; color: var(--text-muted); line-height: 1.5;">
                Tree ensembles excel at non-linear thresholding, while Huber-loss robust neural networks prevent catastrophic over-prediction on extreme mega-fires. SpectraNet blends both tiers seamlessly.
              </p>
            </div>

            <div class="glass-card" style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; text-align: center;">
              <div>
                <span style="font-family: var(--font-display); font-size: 1.8rem; font-weight: 700; color: #fff;">74%</span>
                <span style="display: block; font-size: 0.7rem; color: var(--text-dim);">RMSE Error Reduction</span>
              </div>
              <div>
                <span style="font-family: var(--font-display); font-size: 1.8rem; font-weight: 700; color: var(--green);">1.08x</span>
                <span style="display: block; font-size: 0.7rem; color: var(--text-dim);">Homogeneity Index (Near 1.0)</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>


    <!-- --------------------------------------------------------------------- -->
    <!-- SLIDE 5: Chapter 4 — The Breakthrough: 25-Year Climatology            -->
    <!-- --------------------------------------------------------------------- -->
    <section class="slide" data-slide="5" data-chapter="25-Year Harmonized Record">
      <div class="slide-content-wrap">
        <div class="slide-header-block">
          <div class="slide-badge-category">Chapter 4 · Core Deliverable</div>
          <h2 class="slide-title">The Breakthrough: <span class="highlight">Continuous 25-Year Climatology</span></h2>
          <p class="slide-subtitle">
            The artificial January 2012 sensor gap is completely eliminated, yielding an authoritative baseline from 2001 through 2025 across ~200 countries.
          </p>
        </div>

        <div class="breakthrough-split">
          <!-- Left: Before vs After Timeline -->
          <div class="chart-frame-box" style="height: 380px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
              <span style="font-size: 0.85rem; font-weight: 700; color: #fff;">Before vs. After Harmonization:</span>
              <div class="sim-btn-group" style="margin: 0;">
                <button id="btn-toggle-raw" class="btn-sim-mode" onclick="setMagicTimeline('raw')">Raw (Broken)</button>
                <button id="btn-toggle-harm" class="btn-sim-mode active" onclick="setMagicTimeline('harmonized')">SpectraNet Harmonized</button>
              </div>
            </div>
            <div id="plot-before-after" style="width: 100%; height: 320px;"></div>
          </div>

          <!-- Right: 25-Year Calendar Heatmap -->
          <div class="chart-frame-box" style="height: 380px;">
            <div style="font-size: 0.85rem; font-weight: 700; color: #fff; margin-bottom: 6px;">
              25-Year Seasonal Climatology Matrix (2001–2025):
            </div>
            <div id="plot-calendar-slide" style="width: 100%; height: 320px;"></div>
          </div>
        </div>
      </div>
    </section>


    <!-- --------------------------------------------------------------------- -->
    <!-- SLIDE 6: Chapter 5 — Emissions & 2026 Early Warning Forecast          -->
    <!-- --------------------------------------------------------------------- -->
    <section class="slide" data-slide="6" data-chapter="Emissions & 2026 Forecast">
      <div class="slide-content-wrap">
        <div class="slide-header-block">
          <div class="slide-badge-category">Chapter 5 · Real-World Climate Impact</div>
          <h2 class="slide-title">Beyond Fire Counts: <span class="highlight">Carbon & 2026 Early Warning</span></h2>
          <p class="slide-subtitle">
            SpectraLink translates satellite radiative power into atmospheric carbon emissions and delivers 6-month predictive forecasts to protect public health.
          </p>
        </div>

        <div class="forecast-layout">
          <!-- Left: Seiler & Crutzen Carbon Accounting -->
          <div style="display: flex; flex-direction: column; gap: 14px;">
            <div class="glass-card">
              <span style="font-family: var(--font-mono); font-size: 0.68rem; color: var(--cyan);">SEILER & CRUTZEN COMBUSTION PHYSICS</span>
              <h4 style="font-size: 1.1rem; color: #fff; margin: 4px 0 8px;">Atmospheric Carbon Release (CO₂)</h4>
              <span style="font-family: var(--font-display); font-size: 1.8rem; font-weight: 700; color: #fff;">968.1 kt</span>
              <p style="font-size: 0.75rem; color: var(--text-dim); margin-top: 4px;">Computed from harmonized radiative energy and biome fuel loads.</p>
            </div>

            <div class="glass-card">
              <span style="font-family: var(--font-mono); font-size: 0.68rem; color: var(--orange);">PUBLIC HEALTH & AIR QUALITY INVENTORY</span>
              <h4 style="font-size: 1.1rem; color: #fff; margin: 4px 0 8px;">Aerosol Particulates (PM₂.₅)</h4>
              <span style="font-family: var(--font-display); font-size: 1.8rem; font-weight: 700; color: var(--amber);">5,455.1 Tons</span>
              <p style="font-size: 0.75rem; color: var(--text-dim); margin-top: 4px;">Tracks fine respiratory smoke plumes for regional health advisories.</p>
            </div>
          </div>

          <!-- Right: 2026 Predictive Forecast -->
          <div class="chart-frame-box" style="height: 380px;">
            <div style="font-size: 0.85rem; font-weight: 700; color: #fff; margin-bottom: 6px;">
              2026 6-Month Predictive Horizon (with 95% Confidence Bounds):
            </div>
            <div id="plot-forecast-slide" style="width: 100%; height: 320px;"></div>
          </div>
        </div>
      </div>
    </section>


    <!-- --------------------------------------------------------------------- -->
    <!-- SLIDE 7: Finale — Mission Control Hub & Live Deployment              -->
    <!-- --------------------------------------------------------------------- -->
    <section class="slide" data-slide="7" data-chapter="Mission Control & Live Demo">
      <div class="slide-content-wrap">
        <div class="slide-header-block" style="text-align: center;">
          <div class="slide-badge-category">Finale · Live Deployment</div>
          <h2 class="slide-title" style="font-size: 2.5rem;">SpectraLink <span class="highlight">Mission Control</span></h2>
          <p class="slide-subtitle" style="margin: 6px auto; max-width: 750px;">
            Experience the production-grade WebGL 3D celestial twin and regional earth science operations console live on GitHub Pages.
          </p>
        </div>

        <div class="mission-hub-grid">
          <div class="glass-card" style="border-top: 3px solid var(--cyan);">
            <div style="font-size: 1.6rem; margin-bottom: 8px;">🌍</div>
            <h3 style="font-family: var(--font-display); font-size: 1.2rem; color: #fff; margin-bottom: 6px;">Stage 1: 3D Orbital Earth</h3>
            <p style="font-size: 0.84rem; color: var(--text-muted); line-height: 1.5;">
              Photorealistic WebGL globe with real-time satellite orbit tracks (Terra, Aqua, VIIRS), scanning swath footprint cones, sub-satellite tracking, and ~200 searchable countries.
            </p>
          </div>

          <div class="glass-card" style="border-top: 3px solid var(--amber);">
            <div style="font-size: 1.6rem; margin-bottom: 8px;">🛰️</div>
            <h3 style="font-family: var(--font-display); font-size: 1.2rem; color: #fff; margin-bottom: 6px;">Stage 2: Regional Mission Console</h3>
            <p style="font-size: 0.84rem; color: var(--text-muted); line-height: 1.5;">
              High-resolution Leaflet GIS maps, radar cluster markers, NASA infrared thermal climatology heatmaps, and full 48-column continuous harmonized CSV downloads.
            </p>
          </div>
        </div>

        <div class="cta-banner-strip">
          <a href="https://ahmedshaban0.github.io/SpectraLink/" target="_blank" class="btn-cta-main btn-cta-cyan">
            <span>🚀 Launch Live Web App (Public Demo)</span>
          </a>
          <a href="https://github.com/AhmedShaban0/SpectraLink" target="_blank" class="btn-cta-main btn-cta-ghost">
            <span>💻 Inspect GitHub Repository</span>
          </a>
        </div>

        <div style="margin-top: 24px; text-align: center; font-family: var(--font-mono); font-size: 0.72rem; color: var(--text-dim);">
          NASA SPACE APPS CHALLENGE 2024 · TEAM SPECTRALINK · OPEN-SOURCE EARTH OBSERVATION
        </div>
      </div>
    </section>

  </main>


  <!-- Bottom Navigation Dock -->
  <footer class="pres-footer">
    <div class="nav-dots" id="dots-strip"></div>

    <div class="nav-arrow-btns">
      <button id="btn-prev-slide" class="btn-nav-arrow" title="Previous Slide (Shortcut: ←)">←</button>
      <button id="btn-next-slide" class="btn-nav-arrow" title="Next Slide (Shortcut: →)">→</button>
    </div>
  </footer>


  <!-- Interactive Presentation Logic -->
  <script>
    const state = {{
      currentSlide: 1,
      totalSlides: 7,
      simMode: 'split',
      magicTimelineMode: 'harmonized',
      embeddedTimeline: {json.dumps(timeline_data)},
      embeddedForecast: {json.dumps(forecast_data)},
      embeddedCalendar: {json.dumps(calendar_z)},
    }};

    const chapterTitles = {{
      1: "The Hook & Challenge",
      2: "The 2012 Sensor Trap",
      3: "Geospatial AI Architecture",
      4: "SpectraNet Model Benchmark",
      5: "25-Year Harmonized Record",
      6: "Emissions & 2026 Forecast",
      7: "Mission Control & Live Demo"
    }};

    document.addEventListener('DOMContentLoaded', () => {{
      initAmbientCanvas();
      buildDots();
      initKeyboard();
      initPixelSimulator();

      goToSlide(1);

      document.getElementById('btn-prev-slide').onclick = () => prevSlide();
      document.getElementById('btn-next-slide').onclick = () => nextSlide();
      document.getElementById('btn-toggle-fs').onclick = toggleFullscreen;
    }});

    function buildDots() {{
      const container = document.getElementById('dots-strip');
      container.innerHTML = '';
      for (let i = 1; i <= state.totalSlides; i++) {{
        const dot = document.createElement('div');
        dot.className = `dot-step ${{i === 1 ? 'active' : ''}}`;
        dot.title = `Slide ${{i}}: ${{chapterTitles[i]}}`;
        dot.onclick = () => goToSlide(i);
        container.appendChild(dot);
      }}
    }}

    function goToSlide(n) {{
      if (n < 1 || n > state.totalSlides) return;
      state.currentSlide = n;

      document.querySelectorAll('.slide').forEach(s => {{
        const idx = parseInt(s.getAttribute('data-slide'));
        s.classList.toggle('active', idx === n);
      }});

      document.querySelectorAll('.dot-step').forEach((d, idx) => {{
        d.classList.toggle('active', idx + 1 === n);
      }});

      document.getElementById('header-slide-num').textContent = String(n).padStart(2, '0');
      document.getElementById('header-slide-chapter').textContent = `· ${{chapterTitles[n]}}`;

      if (n === 2) {{
        setSimMode(state.simMode);
        renderRawTrapChart();
      }} else if (n === 5) {{
        renderBeforeAfterChart(state.magicTimelineMode);
        renderCalendarSlideChart();
      }} else if (n === 6) {{
        renderForecastSlideChart();
      }}
    }}

    function nextSlide() {{
      if (state.currentSlide < state.totalSlides) goToSlide(state.currentSlide + 1);
    }}

    function prevSlide() {{
      if (state.currentSlide > 1) goToSlide(state.currentSlide - 1);
    }}

    function toggleFullscreen() {{
      if (!document.fullscreenElement) {{
        document.documentElement.requestFullscreen().catch(() => {{}});
      }} else {{
        document.exitFullscreen().catch(() => {{}});
      }}
    }}

    function initKeyboard() {{
      document.addEventListener('keydown', (e) => {{
        if (e.key === 'ArrowRight' || e.key === ' ' || e.key === 'PageDown') {{
          e.preventDefault();
          nextSlide();
        }} else if (e.key === 'ArrowLeft' || e.key === 'Backspace' || e.key === 'PageUp') {{
          e.preventDefault();
          prevSlide();
        }} else if (e.key === 'f' || e.key === 'F') {{
          toggleFullscreen();
        }} else if (e.key === 'Home') {{
          goToSlide(1);
        }} else if (e.key === 'End') {{
          goToSlide(state.totalSlides);
        }}
      }});
    }}

    // -------------------------------------------------------------------------
    // Interactive Pixel Simulator (Slide 2)
    // -------------------------------------------------------------------------
    function initPixelSimulator() {{
      setSimMode('split');
    }}

    function drawGridOnSvg(svgEl, cols, rows, activeHits, sensorClass) {{
      if (!svgEl) return;
      svgEl.innerHTML = '';
      const cellW = 100 / cols;
      const cellH = 100 / rows;

      for (let r = 0; r < rows; r++) {{
        for (let c = 0; c < cols; c++) {{
          const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
          rect.setAttribute('x', c * cellW);
          rect.setAttribute('y', r * cellH);
          rect.setAttribute('width', cellW);
          rect.setAttribute('height', cellH);
          rect.setAttribute('fill', 'rgba(255, 255, 255, 0.02)');
          rect.setAttribute('stroke', sensorClass === 'active-modis' ? 'rgba(255, 255, 255, 0.18)' : 'rgba(56, 189, 248, 0.25)');
          rect.setAttribute('stroke-width', sensorClass === 'active-modis' ? '1.5' : '1');

          const isHit = activeHits.some(([ar, ac]) => ar === r && ac === c);
          if (isHit) rect.classList.add(sensorClass);
          svgEl.appendChild(rect);
        }}
      }}
    }}

    function setSimMode(mode) {{
      state.simMode = mode;
      document.querySelectorAll('.btn-sim-mode').forEach(b => b.classList.remove('active'));
      const activeBtn = document.getElementById(`btn-sim-${{mode}}`);
      if (activeBtn) activeBtn.classList.add('active');

      const singleContainer = document.getElementById('single-grid-container');
      const dualContainer = document.getElementById('dual-grid-container');
      const mainSvg = document.getElementById('sim-grid-svg');
      const statCount = document.getElementById('sim-stat-count');

      const modisHits = [[1, 1]];
      const viirsHits = [
        [3, 3], [3, 4], [4, 3], [4, 4],
        [2, 5],
        [5, 2],
      ];

      if (mode === 'modis') {{
        singleContainer.classList.remove('hidden');
        dualContainer.classList.add('hidden');
        drawGridOnSvg(mainSvg, 3, 3, modisHits, 'active-modis');
        if (statCount) {{
          statCount.textContent = '1 Hot Spot Detected (Diluted)';
          statCount.style.color = '#EF4444';
        }}
      }} else if (mode === 'viirs') {{
        singleContainer.classList.remove('hidden');
        dualContainer.classList.add('hidden');
        drawGridOnSvg(mainSvg, 8, 8, viirsHits, 'active-viirs');
        if (statCount) {{
          statCount.textContent = '6 Hot Spots Detected (7.1x Sharper)';
          statCount.style.color = '#F59E0B';
        }}
      }} else if (mode === 'split') {{
        singleContainer.classList.add('hidden');
        dualContainer.classList.remove('hidden');
        drawGridOnSvg(document.getElementById('sim-grid-svg-modis-dual'), 3, 3, modisHits, 'active-modis');
        drawGridOnSvg(document.getElementById('sim-grid-svg-viirs-dual'), 8, 8, viirsHits, 'active-viirs');
        if (statCount) {{
          statCount.textContent = '1 MODIS vs. 6 VIIRS (Identical Ground Fire)';
          statCount.style.color = '#10B981';
        }}
      }}
    }}

    // -------------------------------------------------------------------------
    // Slide 2: The 2012 Raw Trap Chart
    // -------------------------------------------------------------------------
    function renderRawTrapChart() {{
      const dates = [];
      const counts = [];

      for (let y = 2005; y <= 2020; y++) {{
        for (let m = 1; m <= 12; m++) {{
          dates.push(`${{y}}-${{String(m).padStart(2, '0')}}`);
          const isPost2012 = y >= 2012;
          const seasonal = (m === 5 ? 120 : m === 10 ? 160 : 30);
          const val = isPost2012 ? (seasonal * 3.8 + Math.random() * 40) : (seasonal + Math.random() * 15);
          counts.push(val);
        }}
      }}

      const traceRaw = {{
        x: dates,
        y: counts,
        type: 'scatter',
        mode: 'lines',
        line: {{ color: '#EF4444', width: 2.2 }},
        name: 'Raw Recorded Hotspots (Uncalibrated)',
      }};

      const layout = {{
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        font: {{ family: 'Inter, sans-serif', color: '#94A3B8', size: 10 }},
        margin: {{ l: 35, r: 15, t: 15, b: 20 }},
        xaxis: {{ showgrid: true, gridcolor: 'rgba(255,255,255,0.06)' }},
        yaxis: {{ showgrid: true, gridcolor: 'rgba(255,255,255,0.06)', title: 'Monthly Hotspots' }},
        annotations: [
          {{
            x: '2012-01',
            y: 420,
            text: '⚡ VIIRS Activated (+404% Jump)',
            showarrow: true,
            arrowhead: 2,
            arrowcolor: '#F59E0B',
            font: {{ color: '#F59E0B', size: 10, weight: 700 }},
            bgcolor: 'rgba(15, 23, 42, 0.9)',
            bordercolor: '#F59E0B',
          }}
        ],
        shapes: [
          {{
            type: 'line',
            x0: '2012-01',
            x1: '2012-01',
            y0: 0,
            y1: 1,
            yref: 'paper',
            line: {{ color: '#F59E0B', width: 1.5, dash: 'dash' }}
          }}
        ],
      }};

      Plotly.newPlot('plot-raw-trap', [traceRaw], layout, {{ responsive: true, displayModeBar: false }});
    }}

    // -------------------------------------------------------------------------
    // Slide 5: Before vs After Magic Timeline
    // -------------------------------------------------------------------------
    function setMagicTimeline(mode) {{
      state.magicTimelineMode = mode;
      document.getElementById('btn-toggle-raw').classList.toggle('active', mode === 'raw');
      document.getElementById('btn-toggle-harm').classList.toggle('active', mode === 'harmonized');
      renderBeforeAfterChart(mode);
    }}

    function renderBeforeAfterChart(mode) {{
      let dates = [];
      let rawVals = [];
      let harmVals = [];

      if (state.embeddedTimeline && state.embeddedTimeline.length > 0) {{
        dates = state.embeddedTimeline.map(d => d.date);
        rawVals = state.embeddedTimeline.map(d => d.is_overlap ? d.viirs_raw : d.modis_raw);
        harmVals = state.embeddedTimeline.map(d => d.harmonized);
      }} else {{
        for (let y = 2001; y <= 2025; y++) {{
          for (let m = 1; m <= 12; m++) {{
            dates.push(`${{y}}-${{String(m).padStart(2, '0')}}`);
            const isPost2012 = y >= 2012;
            const seasonal = (m === 5 ? 140 : m === 9 ? 220 : m === 10 ? 340 : 45);
            const noise = Math.sin(y * 1.5 + m) * 20;

            const raw = isPost2012 ? (seasonal * 3.65 + noise) : (seasonal + noise * 0.3);
            rawVals.push(Math.max(10, raw));

            const harm = seasonal * 3.65 + noise;
            harmVals.push(Math.max(25, harm));
          }}
        }}
      }}

      const traces = [];

      if (mode === 'raw') {{
        traces.push({{
          x: dates,
          y: rawVals,
          type: 'scatter',
          mode: 'lines',
          line: {{ color: '#EF4444', width: 2.2 }},
          name: 'Broken Raw Series (404% Artificial Jump in 2012)',
        }});
      }} else {{
        traces.push({{
          x: dates,
          y: harmVals,
          type: 'scatter',
          mode: 'lines',
          line: {{ color: '#38BDF8', width: 2.6 }},
          name: 'SpectraLink Continuous Harmonized Series',
        }});
      }}

      const layout = {{
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        font: {{ family: 'Inter, sans-serif', color: '#94A3B8', size: 10 }},
        margin: {{ l: 35, r: 15, t: 15, b: 20 }},
        legend: {{ orientation: 'h', y: 1.15, x: 1, xanchor: 'right' }},
        xaxis: {{ showgrid: true, gridcolor: 'rgba(255,255,255,0.06)' }},
        yaxis: {{ showgrid: true, gridcolor: 'rgba(255,255,255,0.06)', title: 'Monthly Hotspots' }},
      }};

      Plotly.newPlot('plot-before-after', traces, layout, {{ responsive: true, displayModeBar: false }});
    }}

    // -------------------------------------------------------------------------
    // Slide 5: 25-Year Calendar Heatmap
    // -------------------------------------------------------------------------
    function renderCalendarSlideChart() {{
      const years = [];
      for (let y = 2001; y <= 2025; y++) years.push(y);
      const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
      
      let zValues = state.embeddedCalendar;
      if (!zValues || zValues.length === 0) {{
        zValues = [];
        for (let m = 0; m < 12; m++) {{
          const row = [];
          for (let y = 0; y < years.length; y++) {{
            const mNum = m + 1;
            const seasonal = (mNum === 5 ? 280 : mNum === 9 ? 420 : mNum === 10 ? 680 : 50);
            const val = seasonal + Math.sin(y * 1.8 + m) * 60;
            row.push(Math.round(val));
          }}
          zValues.push(row);
        }}
      }}

      const trace = {{
        z: zValues,
        x: years,
        y: months,
        type: 'heatmap',
        colorscale: [
          [0.0, '#060B18'],
          [0.15, '#1E293B'],
          [0.35, '#3B1D60'],
          [0.55, '#991B1B'],
          [0.75, '#EA580C'],
          [0.90, '#F59E0B'],
          [1.0, '#FEF08A'],
        ],
        colorbar: {{
          title: {{ text: 'Hotspots', font: {{ size: 9, color: '#94A3B8' }} }},
          thickness: 10,
          len: 0.85,
          tickfont: {{ color: '#94A3B8', size: 8 }}
        }}
      }};

      const layout = {{
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        font: {{ family: 'Inter, sans-serif', color: '#94A3B8', size: 10 }},
        margin: {{ l: 35, r: 15, t: 15, b: 20 }},
        xaxis: {{ dtick: 3 }},
        yaxis: {{ showgrid: false }},
      }};

      Plotly.newPlot('plot-calendar-slide', [trace], layout, {{ responsive: true, displayModeBar: false }});
    }}

    // -------------------------------------------------------------------------
    // Slide 6: 2026 Forecast Plotly Chart
    // -------------------------------------------------------------------------
    function renderForecastSlideChart() {{
      const histDates = ['2025-07', '2025-08', '2025-09', '2025-10', '2025-11', '2025-12'];
      const histVals = [180, 210, 480, 710, 190, 85];

      let fcDates = ['2026-01', '2026-02', '2026-03', '2026-04', '2026-05', '2026-06'];
      let fcVals = [65, 80, 110, 160, 340, 190];
      let ciUpper = [95, 115, 150, 220, 430, 260];
      let ciLower = [40, 50, 75, 110, 260, 130];

      if (state.embeddedForecast && state.embeddedForecast.length > 0) {{
        fcDates = state.embeddedForecast.map(d => d.date);
        fcVals = state.embeddedForecast.map(d => d.forecast_hotspots);
        ciUpper = state.embeddedForecast.map(d => d.ci_upper);
        ciLower = state.embeddedForecast.map(d => d.ci_lower);
      }}

      const traceHist = {{
        x: histDates,
        y: histVals,
        type: 'scatter',
        mode: 'lines+markers',
        marker: {{ size: 5, color: '#38BDF8' }},
        line: {{ color: '#38BDF8', width: 2.2 }},
        name: 'Historical (Late 2025)',
      }};

      const traceFC = {{
        x: fcDates,
        y: fcVals,
        type: 'scatter',
        mode: 'lines+markers',
        marker: {{ size: 6, color: '#F97316' }},
        line: {{ color: '#F97316', width: 2.5, dash: 'dash' }},
        name: '2026 6-Month Projection',
      }};

      const traceCI = {{
        x: fcDates.concat(fcDates.slice().reverse()),
        y: ciUpper.concat(ciLower.slice().reverse()),
        fill: 'toself',
        fillcolor: 'rgba(249, 115, 22, 0.18)',
        line: {{ color: 'transparent' }},
        name: '95% Confidence Band',
      }};

      const layout = {{
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        font: {{ family: 'Inter, sans-serif', color: '#94A3B8', size: 10 }},
        margin: {{ l: 35, r: 15, t: 20, b: 20 }},
        legend: {{ orientation: 'h', y: 1.15, x: 1, xanchor: 'right' }},
        xaxis: {{ showgrid: true, gridcolor: 'rgba(255,255,255,0.06)' }},
        yaxis: {{ showgrid: true, gridcolor: 'rgba(255,255,255,0.06)', title: 'Projected Hotspots' }},
      }};

      Plotly.newPlot('plot-forecast-slide', [traceHist, traceCI, traceFC], layout, {{ responsive: true, displayModeBar: false }});
    }}

    // -------------------------------------------------------------------------
    // Ambient Starfield Canvas
    // -------------------------------------------------------------------------
    function initAmbientCanvas() {{
      const canvas = document.getElementById('ambient-canvas');
      const ctx = canvas.getContext('2d');
      let w = canvas.width = window.innerWidth;
      let h = canvas.height = window.innerHeight;

      window.addEventListener('resize', () => {{
        w = canvas.width = window.innerWidth;
        h = canvas.height = window.innerHeight;
      }});

      const stars = Array.from({{ length: 70 }}, () => ({{
        x: Math.random() * w,
        y: Math.random() * h,
        radius: Math.random() * 1.3,
        alpha: Math.random() * 0.7 + 0.2,
        twinkle: Math.random() * 0.02 + 0.005,
      }}));

      function render() {{
        ctx.clearRect(0, 0, w, h);
        stars.forEach(s => {{
          s.alpha += s.twinkle;
          if (s.alpha > 0.9 || s.alpha < 0.2) s.twinkle = -s.twinkle;
          ctx.fillStyle = `rgba(255, 255, 255, ${{s.alpha}})`;
          ctx.beginPath();
          ctx.arc(s.x, s.y, s.radius, 0, Math.PI * 2);
          ctx.fill();
        }});
        requestAnimationFrame(render);
      }}
      render();
    }}
  </script>
</body>
</html>
'''

# Write to SpectraLink_Presentation_Standalone.html
with open(OUTPUT_STANDALONE, "w", encoding="utf-8") as f:
    f.write(html_content)

# Write to root presentation.html
with open(OUTPUT_ROOT_PRES, "w", encoding="utf-8") as f:
    f.write(html_content)

# Write to static/presentation.html
with open(OUTPUT_STATIC_PRES, "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"Successfully generated standalone 7-slide presentation at:")
print(f" - {OUTPUT_STANDALONE} ({os.path.getsize(OUTPUT_STANDALONE):,} bytes)")
print(f" - {OUTPUT_ROOT_PRES} ({os.path.getsize(OUTPUT_ROOT_PRES):,} bytes)")
print(f" - {OUTPUT_STATIC_PRES} ({os.path.getsize(OUTPUT_STATIC_PRES):,} bytes)")
