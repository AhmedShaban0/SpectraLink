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

# Load 4 Showcase Biomes from authentic Earth Engine analysis cache
biomes_data = {}
biome_files = {
    'nile': ('data_cache/nile_delta_analysis.json', 'Nile Delta, Egypt', 'Irrigated Agricultural Ecosystem'),
    'amazon': ('data_cache/amazon_basin_analysis.json', 'Amazon Basin, Brazil', 'Tropical Moist Broadleaf'),
    'california': ('data_cache/california_analysis.json', 'California, USA', 'Temperate Mediterranean Chaparral'),
    'canada': ('data_cache/canada_wildfires_analysis.json', 'Western Canada (Boreal)', 'North American Boreal Forest')
}

for k, (rel_path, default_name, default_biome) in biome_files.items():
    full_path = os.path.join(BASE_DIR, rel_path)
    if os.path.exists(full_path):
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                d = json.load(f)
                cm = d.get('calendar_matrix', {})
                val = cm.get('values', [])
                transposed = [[round(val[y][m]) for y in range(len(val))] for m in range(len(val[0]))] if val else []
                biomes_data[k] = {
                    'id': k,
                    'name': d.get('profile', {}).get('name', default_name),
                    'biome': d.get('profile', {}).get('biome', default_biome),
                    'peak_months': d.get('kpi', {}).get('peak_months', 'Seasonal Peak'),
                    'total_co2_kt': d.get('kpi', {}).get('total_co2_kt', 968.1),
                    'total_pm25_tons': d.get('kpi', {}).get('total_pm25_tons', 5455.1),
                    'calendar': transposed,
                    'timeline': d.get('timeline', []),
                    'forecast': d.get('forecast', [])
                }
        except Exception as e:
            print(f"Error loading {k}: {e}")

html_template = """<!DOCTYPE html>
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
       SPECTRALINK 7-SLIDE MASTER PRESENTATION ENGINE (REFINED AEROSPACE PALETTE)
       ========================================================================== */
    :root {
      --bg-space: #030611;
      --bg-panel: rgba(9, 15, 30, 0.85);
      --bg-card: rgba(14, 21, 38, 0.78);
      --bg-card-hover: rgba(20, 32, 58, 0.94);
      
      --cyan: #38BDF8;
      --cyan-glow: rgba(56, 189, 248, 0.35);
      --blue: #2563EB;
      
      /* Intentional Flame Accent (SpectraLink Fire Logo) - Used Selectively */
      --fire-orange: #FF5400;
      --fire-glow: rgba(255, 84, 0, 0.45);
      --fire-flame: #FF3B00;
      --fire-amber: #F59E0B;
      --fire-red: #EF4444;
      --green: #10B981;
      --green-glow: rgba(16, 185, 129, 0.45);
      
      --text-main: #F8FAFC;
      --text-muted: #94A3B8;
      --text-dim: #64748B;
      --border: rgba(255, 255, 255, 0.08);
      --border-cyan: rgba(56, 189, 248, 0.28);
      
      --font-display: 'Space Grotesk', sans-serif;
      --font-sans: 'Inter', sans-serif;
      --font-mono: 'JetBrains Mono', monospace;
      
      --easing: cubic-bezier(0.16, 1, 0.3, 1);
    }

    *, *::before, *::after {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }

    body {
      background-color: var(--bg-space);
      background-image: 
        radial-gradient(ellipse 900px 500px at 15% 15%, rgba(14, 165, 233, 0.08), transparent 70%),
        radial-gradient(ellipse 700px 450px at 85% 85%, rgba(30, 58, 138, 0.07), transparent 70%),
        radial-gradient(circle 500px at 50% 50%, rgba(15, 23, 42, 0.4), transparent 75%);
      color: var(--text-main);
      font-family: var(--font-sans);
      overflow: hidden;
      width: 100vw;
      height: 100vh;
      user-select: none;
    }

    /* Ambient Interactive Canvas (Stars + Subtle Distant Fire Sparks) */
    #ambient-canvas {
      position: fixed;
      inset: 0;
      width: 100%;
      height: 100%;
      pointer-events: none;
      z-index: 0;
    }

    /* Top Telemetry Header */
    .pres-header {
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      height: 60px;
      background: rgba(8, 13, 26, 0.94);
      backdrop-filter: blur(16px);
      -webkit-backdrop-filter: blur(16px);
      border-bottom: 1px solid var(--border);
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 24px;
      z-index: 50;
    }

    /* Top Progress Micro-Bar (Clean Cyan to Subtle Orange) */
    #top-progress-bar {
      position: absolute;
      bottom: 0;
      left: 0;
      height: 2px;
      background: linear-gradient(90deg, #38BDF8, #0284C7 85%, #FF5400);
      width: 14.28%;
      transition: width 0.4s var(--easing);
      box-shadow: 0 0 8px var(--cyan-glow);
    }

    .header-brand {
      display: flex;
      align-items: center;
      gap: 12px;
    }

    .brand-logo {
      height: 38px;
      width: auto;
      object-fit: contain;
    }

    .brand-divider {
      width: 1px;
      height: 22px;
      background: var(--border);
    }

    .space-apps-logo {
      height: 28px;
      width: auto;
      object-fit: contain;
    }

    .brand-badge {
      display: flex;
      flex-direction: column;
    }

    .brand-title {
      font-family: var(--font-display);
      font-size: 0.96rem;
      font-weight: 700;
      letter-spacing: -0.01em;
      color: #fff;
    }

    .brand-sub {
      font-family: var(--font-mono);
      font-size: 0.64rem;
      color: var(--cyan);
      letter-spacing: 0.04em;
    }

    /* Header Live Satellites Telemetry Pill */
    .header-sat-pill {
      display: flex;
      align-items: center;
      gap: 8px;
      background: rgba(255, 255, 255, 0.04);
      border: 1px solid var(--border);
      padding: 4px 12px;
      border-radius: 999px;
      font-family: var(--font-mono);
      font-size: 0.68rem;
    }

    .sat-tag {
      display: flex;
      align-items: center;
      gap: 4px;
    }

    .sat-dot {
      width: 6px;
      height: 6px;
      border-radius: 50%;
    }

    .sat-dot.terra { background: #38BDF8; box-shadow: 0 0 6px #38BDF8; }
    .sat-dot.aqua { background: #60A5FA; box-shadow: 0 0 6px #60A5FA; }
    .sat-dot.viirs { background: #FF5400; box-shadow: 0 0 6px #FF5400; }

    .header-status {
      display: flex;
      align-items: center;
      gap: 16px;
    }

    .slide-progress-pill {
      display: flex;
      align-items: center;
      gap: 6px;
      background: rgba(255, 255, 255, 0.04);
      border: 1px solid var(--border);
      padding: 5px 16px;
      border-radius: 20px;
      font-family: var(--font-mono);
      font-size: 0.78rem;
    }

    .slide-progress-pill .curr {
      color: var(--cyan);
      font-weight: 700;
    }

    .header-actions {
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .btn-header-action {
      display: flex;
      align-items: center;
      gap: 6px;
      background: rgba(255, 255, 255, 0.04);
      border: 1px solid var(--border);
      color: var(--text-muted);
      padding: 6px 12px;
      border-radius: 8px;
      font-size: 0.76rem;
      font-weight: 600;
      cursor: pointer;
      text-decoration: none;
      transition: all 0.2s ease;
    }

    .btn-header-action:hover {
      color: #fff;
      background: rgba(255, 255, 255, 0.08);
      border-color: var(--border-cyan);
    }

    .btn-live-launch {
      background: rgba(56, 189, 248, 0.12);
      border-color: rgba(56, 189, 248, 0.35);
      color: var(--cyan);
    }

    .btn-live-launch:hover {
      background: var(--cyan);
      color: #030712;
      box-shadow: 0 0 16px var(--cyan-glow);
    }

    /* Presentation Main Container */
    #deck-container {
      position: absolute;
      top: 60px;
      left: 0;
      right: 0;
      bottom: 58px;
      overflow: hidden;
      z-index: 10;
    }

    /* Slide Base Layout */
    .slide {
      position: absolute;
      inset: 0;
      width: 100vw;
      height: calc(100vh - 118px);
      padding: 24px 44px 20px 44px;
      display: flex;
      flex-direction: column;
      justify-content: center;
      align-items: center;
      opacity: 0;
      pointer-events: none;
      transform: scale(0.985) translateY(10px);
      transition: opacity 0.4s var(--easing), transform 0.4s var(--easing);
    }

    .slide.active {
      opacity: 1;
      pointer-events: auto;
      transform: scale(1) translateY(0);
    }

    .slide-content-wrap {
      width: 100%;
      max-width: 1380px;
      height: 100%;
      display: flex;
      flex-direction: column;
      justify-content: center;
    }

    /* Slide Titles & Headers */
    .slide-header-block {
      margin-bottom: 16px;
    }

    .slide-badge-category {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      font-family: var(--font-mono);
      font-size: 0.72rem;
      font-weight: 700;
      color: var(--cyan);
      text-transform: uppercase;
      letter-spacing: 0.08em;
      margin-bottom: 4px;
    }

    .slide-title {
      font-family: var(--font-display);
      font-size: 2.1rem;
      font-weight: 700;
      line-height: 1.18;
      color: #fff;
      letter-spacing: -0.01em;
    }

    .slide-title .highlight {
      color: var(--cyan);
    }

    .slide-subtitle {
      font-size: 0.94rem;
      color: var(--text-muted);
      margin-top: 5px;
      line-height: 1.5;
      max-width: 950px;
    }

    /* Refined Clean Glass Cards */
    .glass-card {
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 20px;
      transition: all 0.25s ease;
      backdrop-filter: blur(14px);
      -webkit-backdrop-filter: blur(14px);
      box-shadow: 0 4px 24px rgba(0, 0, 0, 0.4);
      position: relative;
    }

    .glass-card::before {
      content: '';
      position: absolute;
      top: 0;
      left: 15%;
      right: 15%;
      height: 1px;
      background: linear-gradient(90deg, transparent, rgba(56, 189, 248, 0.25), transparent);
      pointer-events: none;
    }

    .glass-card:hover {
      background: var(--bg-card-hover);
      border-color: rgba(56, 189, 248, 0.3);
      box-shadow: 0 8px 36px rgba(0, 0, 0, 0.55);
    }

    /* Slide 1: Hero Layout */
    .hero-layout {
      display: grid;
      grid-template-columns: 1.25fr 0.85fr;
      gap: 36px;
      align-items: center;
      width: 100%;
    }

    .hero-title {
      font-family: var(--font-display);
      font-size: 2.9rem;
      font-weight: 700;
      line-height: 1.12;
      color: #fff;
      margin-bottom: 12px;
      letter-spacing: -0.02em;
    }

    /* Tasteful fire glow reserved exclusively for "Breathe Fire" */
    .hero-fire-glow {
      background: linear-gradient(135deg, #FF3B00 0%, #FF5400 50%, #FFA000 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      filter: drop-shadow(0 0 14px rgba(255, 84, 0, 0.5));
    }

    .hero-partnership-badge {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      background: rgba(56, 189, 248, 0.08);
      border: 1px solid rgba(56, 189, 248, 0.25);
      padding: 6px 14px;
      border-radius: 20px;
      font-family: var(--font-mono);
      font-size: 0.72rem;
      color: var(--cyan);
      margin-bottom: 14px;
    }

    .hero-stat-grid {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 12px;
      margin-top: 22px;
    }

    .hero-stat-box {
      background: rgba(255, 255, 255, 0.03);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 12px 14px;
      display: flex;
      flex-direction: column;
      position: relative;
      overflow: hidden;
    }

    .hero-stat-box::after {
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      width: 3px;
      height: 100%;
      background: var(--cyan);
      opacity: 0.6;
    }

    .hero-stat-box .val {
      font-family: var(--font-display);
      font-size: 1.55rem;
      font-weight: 700;
      color: #fff;
    }

    .hero-stat-box .lbl {
      font-size: 0.7rem;
      color: var(--text-dim);
      margin-top: 2px;
      line-height: 1.3;
    }

    .hero-question-card {
      background: rgba(56, 189, 248, 0.05);
      border: 1px solid rgba(56, 189, 248, 0.22);
      border-radius: 12px;
      padding: 16px 20px;
      margin-top: 18px;
      font-size: 0.92rem;
      color: #E2E8F0;
      line-height: 1.55;
    }

    /* 3D Holographic Globe Canvas Container with Scanning Beams */
    .globe-canvas-card {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      position: relative;
    }

    #hero-globe-canvas {
      width: 440px;
      height: 440px;
      cursor: grab;
      filter: drop-shadow(0 0 45px rgba(56, 189, 248, 0.20));
    }

    #hero-globe-canvas:active {
      cursor: grabbing;
    }

    .globe-telemetry-legend {
      display: flex;
      gap: 14px;
      font-family: var(--font-mono);
      font-size: 0.72rem;
      margin-top: 8px;
    }

    .globe-telemetry-legend span {
      display: flex;
      align-items: center;
      gap: 5px;
    }

    /* Slide 2: The 2012 Trap & Pixel Sim */
    .trap-sim-layout {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 22px;
      width: 100%;
      align-items: center;
    }

    .sim-card-wrap {
      display: flex;
      flex-direction: column;
      gap: 12px;
      height: 410px;
    }

    .sim-btn-group {
      display: flex;
      gap: 6px;
      background: rgba(0, 0, 0, 0.35);
      padding: 4px;
      border-radius: 8px;
      border: 1px solid var(--border);
    }

    .btn-sim-mode {
      flex: 1;
      background: transparent;
      border: none;
      color: var(--text-muted);
      font-family: var(--font-mono);
      font-size: 0.74rem;
      padding: 6px 10px;
      border-radius: 6px;
      cursor: pointer;
      transition: all 0.2s ease;
    }

    .btn-sim-mode.active {
      background: var(--cyan);
      color: #030712;
      font-weight: 700;
      box-shadow: 0 0 10px var(--cyan-glow);
    }

    .sim-threshold-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      background: rgba(255, 255, 255, 0.03);
      border: 1px solid var(--border);
      padding: 8px 12px;
      border-radius: 8px;
      font-size: 0.75rem;
    }

    .sim-slider {
      flex: 1;
      accent-color: var(--cyan);
      cursor: pointer;
    }

    .pixel-grid-container {
      position: relative;
      width: 240px;
      height: 240px;
      margin: 0 auto;
      background: #02040A;
      border: 1px solid rgba(255, 255, 255, 0.15);
      border-radius: 8px;
      overflow: hidden;
      box-shadow: inset 0 0 20px rgba(0, 0, 0, 0.8);
    }

    .dual-grid-wrapper {
      display: flex;
      justify-content: center;
      gap: 18px;
      align-items: center;
    }

    .dual-panel {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 4px;
    }

    .dual-box {
      width: 140px !important;
      height: 140px !important;
    }

    .ground-fire-source {
      position: absolute;
      border-radius: 50%;
      background: radial-gradient(circle, #FFF7ED 10%, #FF5400 40%, #FF3B00 70%, transparent 90%);
      filter: blur(2px);
      animation: pulseFire 1.6s ease-in-out infinite;
    }

    @keyframes pulseFire {
      0%, 100% { opacity: 0.85; transform: scale(1); filter: blur(2px); }
      50% { opacity: 1; transform: scale(1.12); filter: blur(2.5px); }
    }

    .grid-svg-overlay {
      position: absolute;
      inset: 0;
      width: 100%;
      height: 100%;
      cursor: crosshair;
    }

    .pixel-cell.active-modis {
      fill: rgba(239, 68, 68, 0.50);
      stroke: #EF4444;
      stroke-width: 2.5;
    }

    .pixel-cell.active-viirs {
      fill: rgba(255, 84, 0, 0.55);
      stroke: #FF5400;
      stroke-width: 1.5;
    }

    .chart-frame-box {
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 16px;
      height: 410px;
      width: 100%;
      backdrop-filter: blur(14px);
    }

    /* Slide 3: 4 Geospatial Pillars */
    .pillar-grid-4 {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 16px;
      margin-top: 6px;
    }

    .pillar-card {
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      height: 380px;
      padding: 18px;
      cursor: pointer;
      border: 1px solid var(--border);
      transition: transform 0.25s ease, border-color 0.25s ease, box-shadow 0.25s ease;
    }

    .pillar-card:hover {
      transform: translateY(-4px);
      border-color: var(--cyan);
      box-shadow: 0 10px 30px rgba(56, 189, 248, 0.15);
    }

    .pillar-header-row {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 10px;
    }

    .pillar-num {
      font-family: var(--font-mono);
      font-size: 0.8rem;
      font-weight: 700;
      color: var(--cyan);
      background: rgba(56, 189, 248, 0.12);
      border: 1px solid var(--border-cyan);
      padding: 3px 8px;
      border-radius: 6px;
    }

    .pillar-icon {
      font-size: 1.4rem;
    }

    .pillar-title {
      font-family: var(--font-display);
      font-size: 1.1rem;
      font-weight: 700;
      color: #fff;
      margin-bottom: 6px;
    }

    .pillar-desc {
      font-size: 0.8rem;
      color: var(--text-muted);
      line-height: 1.45;
    }

    .pillar-formula-box {
      background: rgba(0, 0, 0, 0.4);
      border: 1px solid rgba(56, 189, 248, 0.2);
      border-radius: 6px;
      padding: 6px 10px;
      margin-top: 10px;
      font-family: var(--font-mono);
      font-size: 0.72rem;
      color: #38BDF8;
      text-align: center;
    }

    .pillar-features-list {
      list-style: none;
      margin-top: 10px;
      font-family: var(--font-mono);
      font-size: 0.71rem;
      color: #CBD5E1;
      display: flex;
      flex-direction: column;
      gap: 5px;
    }

    .pillar-features-list li {
      display: flex;
      align-items: center;
      gap: 6px;
    }

    .pillar-features-list li::before {
      content: '✦';
      color: var(--cyan);
      font-size: 0.65rem;
    }

    /* Sensor Bus Bar on Slide 3 */
    .sensor-bus-strip {
      margin-top: 14px;
      background: rgba(0, 0, 0, 0.4);
      border: 1px solid var(--border-cyan);
      border-radius: 10px;
      padding: 8px 16px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      font-family: var(--font-mono);
      font-size: 0.72rem;
    }

    .sensor-bus-label {
      color: var(--cyan);
      font-weight: 700;
      display: flex;
      align-items: center;
      gap: 6px;
    }

    .sensor-bus-stream {
      color: #94A3B8;
      overflow: hidden;
      white-space: nowrap;
      text-overflow: ellipsis;
      max-width: 800px;
    }

    /* Slide 4: AI Benchmark */
    .benchmark-layout {
      display: grid;
      grid-template-columns: 1.15fr 0.85fr;
      gap: 22px;
      align-items: stretch;
      margin-top: 6px;
    }

    .race-list {
      display: flex;
      flex-direction: column;
      gap: 10px;
    }

    .race-row {
      display: flex;
      flex-direction: column;
      gap: 4px;
      background: rgba(255, 255, 255, 0.02);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 8px 12px;
      cursor: pointer;
      transition: all 0.2s ease;
    }

    .race-row:hover, .race-row.active {
      background: rgba(56, 189, 248, 0.08);
      border-color: var(--border-cyan);
    }

    .race-meta {
      display: flex;
      justify-content: space-between;
      font-size: 0.8rem;
      font-weight: 600;
    }

    .race-bar-track {
      height: 8px;
      background: rgba(255, 255, 255, 0.06);
      border-radius: 999px;
      overflow: hidden;
    }

    .race-bar-fill {
      height: 100%;
      border-radius: 999px;
      transition: width 0.8s var(--easing);
    }

    .model-inspector-card {
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      height: 100%;
      gap: 14px;
    }

    /* Slide 5: Breakthrough Layout */
    .breakthrough-split {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 22px;
      align-items: stretch;
      margin-top: 6px;
    }

    .biome-btn-group {
      display: flex;
      gap: 6px;
      margin-bottom: 6px;
      flex-wrap: wrap;
    }

    .btn-biome-tab {
      background: rgba(255, 255, 255, 0.04);
      border: 1px solid var(--border);
      color: var(--text-muted);
      font-size: 0.74rem;
      padding: 4px 10px;
      border-radius: 6px;
      cursor: pointer;
      transition: all 0.2s ease;
    }

    .btn-biome-tab.active {
      background: rgba(56, 189, 248, 0.15);
      border-color: var(--cyan);
      color: var(--cyan);
      font-weight: 600;
    }

    /* Slide 6: Forecast & Smoke */
    .forecast-layout {
      display: grid;
      grid-template-columns: 0.9fr 1.1fr;
      gap: 22px;
      align-items: stretch;
      margin-top: 6px;
    }

    /* Slide 7: Mission Control Grid */
    .mission-hub-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 22px;
      margin-top: 14px;
      width: 100%;
    }

    .cta-banner-strip {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 16px;
      margin-top: 24px;
    }

    .btn-cta-main {
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 14px 28px;
      border-radius: 12px;
      font-family: var(--font-display);
      font-size: 1rem;
      font-weight: 700;
      text-decoration: none;
      cursor: pointer;
      transition: all 0.25s ease;
    }

    .btn-cta-cyan {
      background: linear-gradient(135deg, #0284C7, #0EA5E9);
      color: #fff;
      box-shadow: 0 0 24px rgba(14, 165, 233, 0.35);
      border: 1px solid rgba(255, 255, 255, 0.2);
    }

    .btn-cta-cyan:hover {
      transform: translateY(-2px);
      box-shadow: 0 0 36px rgba(14, 165, 233, 0.6);
    }

    .btn-cta-ghost {
      background: rgba(255, 255, 255, 0.05);
      color: #fff;
      border: 1px solid var(--border);
    }

    .btn-cta-ghost:hover {
      background: rgba(255, 255, 255, 0.1);
      border-color: var(--border-cyan);
    }

    /* Bottom Navigation Dock */
    .pres-footer {
      position: fixed;
      bottom: 0;
      left: 0;
      right: 0;
      height: 58px;
      background: rgba(8, 13, 26, 0.94);
      backdrop-filter: blur(16px);
      border-top: 1px solid var(--border);
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 24px;
      z-index: 50;
    }

    .nav-dots {
      display: flex;
      align-items: center;
      gap: 10px;
    }

    .dot-step {
      display: flex;
      align-items: center;
      gap: 6px;
      padding: 4px 10px;
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid var(--border);
      border-radius: 20px;
      font-family: var(--font-mono);
      font-size: 0.72rem;
      color: var(--text-dim);
      cursor: pointer;
      transition: all 0.25s var(--easing);
    }

    .dot-step:hover {
      border-color: var(--border-cyan);
      color: #fff;
    }

    .dot-step.active {
      background: rgba(56, 189, 248, 0.15);
      border-color: var(--cyan);
      color: var(--cyan);
      font-weight: 700;
      box-shadow: 0 0 10px var(--cyan-glow);
    }

    .nav-arrow-btns {
      display: flex;
      gap: 8px;
    }

    .btn-nav-arrow {
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid var(--border);
      color: var(--text-muted);
      width: 36px;
      height: 36px;
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      font-size: 1.1rem;
      transition: all 0.2s ease;
    }

    .btn-nav-arrow:hover {
      color: #fff;
      background: rgba(255, 255, 255, 0.1);
      border-color: var(--border-cyan);
    }

    /* Keyboard Shortcuts Modal */
    .shortcuts-modal {
      position: fixed;
      inset: 0;
      background: rgba(3, 7, 18, 0.85);
      backdrop-filter: blur(8px);
      z-index: 100;
      display: flex;
      align-items: center;
      justify-content: center;
      opacity: 0;
      pointer-events: none;
      transition: opacity 0.25s ease;
    }

    .shortcuts-modal.open {
      opacity: 1;
      pointer-events: auto;
    }

    .shortcuts-card {
      background: #0B1224;
      border: 1px solid var(--border-cyan);
      border-radius: 16px;
      padding: 24px;
      max-width: 480px;
      width: 90%;
      box-shadow: 0 0 40px rgba(56, 189, 248, 0.25);
    }

    .shortcut-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 8px 0;
      border-bottom: 1px solid var(--border);
      font-size: 0.85rem;
    }

    .kbd-badge {
      background: rgba(255, 255, 255, 0.1);
      border: 1px solid rgba(255, 255, 255, 0.2);
      border-radius: 4px;
      padding: 2px 8px;
      font-family: var(--font-mono);
      font-size: 0.75rem;
      color: var(--cyan);
    }

    /* Toast Notification */
    #pres-toast {
      position: fixed;
      bottom: 74px;
      left: 50%;
      transform: translateX(-50%) translateY(20px);
      background: #0F172A;
      border: 1px solid var(--cyan);
      color: #fff;
      padding: 8px 18px;
      border-radius: 20px;
      font-family: var(--font-mono);
      font-size: 0.8rem;
      box-shadow: 0 0 20px var(--cyan-glow);
      opacity: 0;
      pointer-events: none;
      transition: all 0.3s ease;
      z-index: 200;
    }

    #pres-toast.show {
      opacity: 1;
      transform: translateX(-50%) translateY(0);
    }
  </style>
</head>
<body>

  <!-- Ambient Interactive Starfield Canvas (With Delicate Subtle Cosmic Fire Embers) -->
  <canvas id="ambient-canvas"></canvas>

  <!-- Top Telemetry Header -->
  <header class="pres-header">
    <div id="top-progress-bar"></div>
    <div class="header-brand">
      <img src="REPLACE_LOGO_BASE64" alt="SpectraLink" class="brand-logo" title="SpectraLink">
      <div class="brand-divider"></div>
      <img src="REPLACE_SPACE_APPS_BASE64" alt="NASA Space Apps Challenge" class="space-apps-logo" title="NASA Space Apps Challenge">
      <div class="brand-badge">
        <span class="brand-title">SpectraLink</span>
        <span class="brand-sub">NASA SPACE APPS CHALLENGE · SENSOR HARMONIZATION</span>
      </div>

      <!-- Orbital Constellation Tracker Pill -->
      <div class="header-sat-pill">
        <span style="color:var(--text-dim);">3D SATELLITES:</span>
        <div class="sat-tag"><span class="sat-dot terra"></span><span>Terra</span></div>
        <div class="sat-tag"><span class="sat-dot aqua"></span><span>Aqua</span></div>
        <div class="sat-tag"><span class="sat-dot viirs"></span><span style="color:var(--fire-orange);">VIIRS</span></div>
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
      <button id="btn-toggle-sound" class="btn-header-action" title="Toggle Sound FX (Shortcut: M)">
        <span id="sound-icon">🔇</span>
        <span id="sound-label">Sound OFF</span>
      </button>
      <button id="btn-show-shortcuts" class="btn-header-action" title="Keyboard Shortcuts (Shortcut: ?)">
        <span>⌨</span>
        <span>Shortcuts</span>
      </button>
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
              <img src="REPLACE_SPACE_APPS_BASE64" alt="NASA Space Apps" style="height: 14px;">
              <span>NASA SPACE APPS CHALLENGE · GLOBAL SUBMISSION</span>
            </div>
            <h1 class="hero-title">
              Watching Earth <span class="hero-fire-glow">Breathe Fire</span>
            </h1>
            <p class="slide-subtitle">
              Harmonizing 25 Years of NASA Satellite Discontinuity using Physics-Informed Machine Learning & Google Earth Engine.
            </p>

            <div class="hero-question-card">
              <strong style="color: var(--cyan);">The Core Scientific Dilemma:</strong> In 2012, raw satellite fire detections surged by <strong style="color:var(--fire-orange);">+404%</strong>. Was Earth truly burning 4x hotter, or did our orbital cameras simply get sharper? Without sensor calibration, climate science risks mistaking a technological sensor upgrade for an environmental crisis.
            </div>

            <div class="hero-stat-grid">
              <div class="hero-stat-box">
                <span class="val">25 Years</span>
                <span class="lbl">2001–2025 Continuous Record</span>
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

          <!-- Right: Interactive 3D Holographic Globe Canvas with Real Orbiting Satellites -->
          <div class="globe-canvas-card">
            <canvas id="hero-globe-canvas" width="460" height="460"></canvas>
            <div class="globe-telemetry-legend">
              <span style="color: var(--cyan);"><span class="sat-dot terra"></span> MODIS Terra (10:30 AM)</span>
              <span style="color: #60A5FA;"><span class="sat-dot aqua"></span> MODIS Aqua (1:30 PM)</span>
              <span style="color: var(--fire-orange);"><span class="sat-dot viirs"></span> VIIRS (1:30 PM)</span>
            </div>
            <span style="font-size: 0.68rem; color: var(--text-dim); margin-top: 4px;">Orbiting Satellites with Scanning Swath Cones · Drag to rotate 3D Earth</span>
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
          <div class="slide-badge-category">Chapter 1 · The Resolution Paradox</div>
          <h2 class="slide-title">The 2012 <span class="highlight">Climate Trap</span>: The Artificial +404% Hotspot Surge</h2>
          <p class="slide-subtitle">
            In 2012, NASA transitioned from 1,000m MODIS to 375m VIIRS. Because VIIRS has a 7.1x smaller pixel area, it catches small agricultural fires previously diluted below MODIS thresholds.
          </p>
        </div>

        <div class="trap-sim-layout">
          <!-- Left: Interactive Pixel Simulator -->
          <div class="glass-card sim-card-wrap">
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <span style="font-size: 0.88rem; font-weight: 700; color: #fff;">Interactive Sensor Resolution Simulator:</span>
              <span id="sim-stat-count" style="font-family: var(--font-mono); font-size: 0.82rem; font-weight: 700; color: var(--cyan);">1 MODIS vs. 6 VIIRS</span>
            </div>
            
            <div class="sim-btn-group">
              <button id="btn-sim-modis" class="btn-sim-mode" onclick="setSimMode('modis')">MODIS (1 km)</button>
              <button id="btn-sim-viirs" class="btn-sim-mode" onclick="setSimMode('viirs')">VIIRS (375 m)</button>
              <button id="btn-sim-split" class="btn-sim-mode active" onclick="setSimMode('split')">Side-by-Side Reality Check</button>
            </div>

            <!-- Interactive Threshold Scrubber -->
            <div class="sim-threshold-row">
              <span style="color: var(--text-muted);">Thermal Fire Threshold:</span>
              <input type="range" id="sim-threshold-slider" class="sim-slider" min="5" max="35" value="12" oninput="updateSimThreshold(this.value)">
              <span id="sim-threshold-val" style="font-family: var(--font-mono); color: var(--cyan); font-weight: 700;">12 MW</span>
            </div>

            <!-- Single Grid -->
            <div id="single-grid-container" class="pixel-grid-container hidden">
              <div class="ground-fire-source" style="top: 42%; left: 45%; width: 15%; height: 15%;"></div>
              <div class="ground-fire-source" style="top: 48%; left: 38%; width: 10%; height: 10%;"></div>
              <div class="ground-fire-source" style="top: 25%; left: 65%; width: 8%; height: 8%;"></div>
              <div class="ground-fire-source" style="top: 70%; left: 28%; width: 8%; height: 8%;"></div>
              <svg id="sim-grid-svg" class="grid-svg-overlay" viewBox="0 0 100 100"></svg>
            </div>

            <!-- Dual Side-by-Side Grid -->
            <div id="dual-grid-container" class="dual-grid-wrapper">
              <div class="dual-panel">
                <span style="font-size: 0.72rem; color: #EF4444; font-weight: 700;">MODIS 1km (Coarse Pixel)</span>
                <div class="pixel-grid-container dual-box">
                  <div class="ground-fire-source" style="top: 42%; left: 45%; width: 15%; height: 15%;"></div>
                  <div class="ground-fire-source" style="top: 48%; left: 38%; width: 10%; height: 10%;"></div>
                  <div class="ground-fire-source" style="top: 25%; left: 65%; width: 8%; height: 8%;"></div>
                  <div class="ground-fire-source" style="top: 70%; left: 28%; width: 8%; height: 8%;"></div>
                  <svg id="sim-grid-svg-modis-dual" class="grid-svg-overlay" viewBox="0 0 100 100"></svg>
                </div>
              </div>
              <div class="dual-panel">
                <span style="font-size: 0.72rem; color: var(--fire-orange); font-weight: 700;">VIIRS 375m (7.1x Sharper)</span>
                <div class="pixel-grid-container dual-box">
                  <div class="ground-fire-source" style="top: 42%; left: 45%; width: 15%; height: 15%;"></div>
                  <div class="ground-fire-source" style="top: 48%; left: 38%; width: 10%; height: 10%;"></div>
                  <div class="ground-fire-source" style="top: 25%; left: 65%; width: 8%; height: 8%;"></div>
                  <div class="ground-fire-source" style="top: 70%; left: 28%; width: 8%; height: 8%;"></div>
                  <svg id="sim-grid-svg-viirs-dual" class="grid-svg-overlay" viewBox="0 0 100 100"></svg>
                </div>
              </div>
            </div>

            <!-- Live HUD Readout -->
            <div id="sim-hud-readout" style="background: rgba(0,0,0,0.4); border: 1px solid var(--border); border-radius: 6px; padding: 6px 10px; font-family: var(--font-mono); font-size: 0.7rem; color: #94A3B8;">
              Hover over pixels to inspect physical thermal radiance & detection status.
            </div>
          </div>

          <!-- Right: The 2012 Discontinuity Trap Chart -->
          <div class="chart-frame-box">
            <div style="font-size: 0.85rem; font-weight: 700; color: #fff; margin-bottom: 4px;">
              Raw Hotspot Discontinuity (January 2012 Step-Jump):
            </div>
            <div id="plot-raw-trap" style="width: 100%; height: 350px;"></div>
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
            Rather than treating satellite pixels as raw RGB imagery, SpectraLink models the entire physical transmission chain from burning Earth surface to orbital focal planes.
          </p>
        </div>

        <div class="pillar-grid-4">
          <!-- Pillar 1 -->
          <div class="glass-card pillar-card" onclick="inspectPillar(1)">
            <div>
              <div class="pillar-header-row">
                <div class="pillar-num">01</div>
                <div class="pillar-icon">🛰️</div>
              </div>
              <h3 class="pillar-title">Orbit & Sensor Geometry</h3>
              <p class="pillar-desc">Corrects pixel bow-tie enlargement and off-nadir distortion across orbital swaths.</p>
              <div class="pillar-formula-box">A_pix(θ) = p₀ · sec²(θ)</div>
            </div>
            <ul class="pillar-features-list">
              <li>Scan Angle (θ) Expansion</li>
              <li>Solar Zenith Angle (θz)</li>
              <li>Pixel Footprint Area (m²)</li>
              <li>Local Satellite Elevation</li>
            </ul>
          </div>

          <!-- Pillar 2 -->
          <div class="glass-card pillar-card" onclick="inspectPillar(2)">
            <div>
              <div class="pillar-header-row">
                <div class="pillar-num">02</div>
                <div class="pillar-icon">📡</div>
              </div>
              <h3 class="pillar-title">Atmospheric Physics</h3>
              <p class="pillar-desc">Quantifies optical depth, smoke transmission attenuation, and water vapor absorption.</p>
              <div class="pillar-formula-box">τ_MIR = exp(-m · AOD₅₅₀)</div>
            </div>
            <ul class="pillar-features-list">
              <li>Atmospheric Transmission (τ)</li>
              <li>Total Column Water Vapor</li>
              <li>Aerosol Optical Depth (AOD)</li>
              <li>4μm Radiant Transmission</li>
            </ul>
          </div>

          <!-- Pillar 3 -->
          <div class="glass-card pillar-card" onclick="inspectPillar(3)">
            <div>
              <div class="pillar-header-row">
                <div class="pillar-num">03</div>
                <div class="pillar-icon">🌿</div>
              </div>
              <h3 class="pillar-title">Fuel & Biome Phenology</h3>
              <p class="pillar-desc">Extracts dynamic vegetative moisture and land cover taxonomy from Google Earth Engine.</p>
              <div class="pillar-formula-box">NDWI = (ρ₈₆₀ - ρ₁₂₄₀)/(ρ₈₆₀ + ρ₁₂₄₀)</div>
            </div>
            <ul class="pillar-features-list">
              <li>MODIS NDVI Vegetation Index</li>
              <li>NDWI Moisture Deficit</li>
              <li>Enhanced Vegetation Index (EVI)</li>
              <li>MCD12Q1 Land Cover Taxonomy</li>
            </ul>
          </div>

          <!-- Pillar 4 -->
          <div class="glass-card pillar-card" onclick="inspectPillar(4)">
            <div>
              <div class="pillar-header-row">
                <div class="pillar-num">04</div>
                <div class="pillar-icon">☀️</div>
              </div>
              <h3 class="pillar-title">Diurnal Progression</h3>
              <p class="pillar-desc">Synchronizes Terra morning (10:30 AM) with Aqua and VIIRS afternoon passes (1:30 PM).</p>
              <div class="pillar-formula-box">I(t) = I_peak · exp(-(Δt)² / 2σ²)</div>
            </div>
            <ul class="pillar-features-list">
              <li>Gaussian Diurnal Peak Kernel</li>
              <li>Solar Radiant Heat Flux</li>
              <li>Overpass Time Inter-Calibration</li>
              <li>Day/Night Thermal Contrast</li>
            </ul>
          </div>
        </div>

        <!-- Sensor Bus Strip -->
        <div class="sensor-bus-strip">
          <div class="sensor-bus-label">
            <span>⚡ SPECTRALINK SENSOR BUS:</span>
          </div>
          <div class="sensor-bus-stream">
            MOD09GA [Surface Reflectance] ➔ MYD04_L2 [AOD & Water Vapor] ➔ MCD12Q1 [Biome Class] ➔ 32 Normalized Physical Tensors ➔ SpectraNet Hybrid Stacking Core
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
            Rigorous cross-validation across diverse global biomes proved that our custom stacking ensemble achieved superior cross-sensor calibration accuracy.
          </p>
        </div>

        <div class="benchmark-layout">
          <!-- Left: Accuracy Leaderboard -->
          <div class="glass-card race-list">
            <span style="font-size: 0.85rem; font-weight: 700; color: #fff; margin-bottom: 4px;">Cross-Validation Model Accuracy Arena (Click to Inspect):</span>
            
            <div class="race-row active" onclick="selectModel(0)">
              <div class="race-meta">
                <span style="color: var(--cyan); font-weight: 700;">🥇 6. SpectraNet Hybrid Stacking (Ensemble)</span>
                <span style="color: var(--cyan);">98.7% R² (r = 0.9934)</span>
              </div>
              <div class="race-bar-track">
                <div class="race-bar-fill" style="width: 98.7%; background: linear-gradient(90deg, #0284C7, #38BDF8); box-shadow: 0 0 10px var(--cyan-glow);"></div>
              </div>
            </div>

            <div class="race-row" onclick="selectModel(1)">
              <div class="race-meta">
                <span>🥈 5. Huber-Loss GBDT & ExtraTrees Blend</span>
                <span>98.2% R²</span>
              </div>
              <div class="race-bar-track">
                <div class="race-bar-fill" style="width: 98.2%; background: #38BDF8;"></div>
              </div>
            </div>

            <div class="race-row" onclick="selectModel(2)">
              <div class="race-meta">
                <span>🥉 4. LightGBM Regressor</span>
                <span>97.8% R²</span>
              </div>
              <div class="race-bar-track">
                <div class="race-bar-fill" style="width: 97.8%; background: #0EA5E9;"></div>
              </div>
            </div>

            <div class="race-row" onclick="selectModel(3)">
              <div class="race-meta">
                <span>4. Random Forest Ensemble</span>
                <span>96.5% R²</span>
              </div>
              <div class="race-bar-track">
                <div class="race-bar-fill" style="width: 96.5%; background: #64748B;"></div>
              </div>
            </div>

            <div class="race-row" onclick="selectModel(4)">
              <div class="race-meta">
                <span>3. Deep MLP-ResNet Neural Net</span>
                <span>95.4% R²</span>
              </div>
              <div class="race-bar-track">
                <div class="race-bar-fill" style="width: 95.4%; background: #475569;"></div>
              </div>
            </div>

            <div class="race-row" onclick="selectModel(5)">
              <div class="race-meta">
                <span>1. Statistical Scaling Baseline</span>
                <span>91.2% R²</span>
              </div>
              <div class="race-bar-track">
                <div class="race-bar-fill" style="width: 91.2%; background: #334155;"></div>
              </div>
            </div>
          </div>

          <!-- Right: Model Inspector & Highlights -->
          <div class="glass-card model-inspector-card">
            <div>
              <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                <span id="model-inspect-title" style="font-family: var(--font-display); font-size: 1.15rem; color: #fff; font-weight: 700;">SpectraNet Hybrid Stacking</span>
                <span id="model-inspect-badge" style="font-family: var(--font-mono); font-size: 0.72rem; color: var(--cyan); background: rgba(56,189,248,0.12); padding: 3px 8px; border-radius: 4px;">WINNER</span>
              </div>
              <p id="model-inspect-desc" style="font-size: 0.84rem; color: var(--text-muted); line-height: 1.55;">
                Two-tier architecture: Base tier leverages gradient-boosted decision trees for sharp non-linear fuel transitions, blended with Huber-loss neural networks to prevent catastrophic over-prediction on extreme mega-fires.
              </p>
            </div>

            <div style="background: rgba(0,0,0,0.3); border: 1px solid var(--border); border-radius: 8px; padding: 10px 14px; font-family: var(--font-mono); font-size: 0.75rem;">
              <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
                <span style="color: var(--text-dim);">Loss Function:</span>
                <span id="model-inspect-loss" style="color: #fff;">Huber Robust Loss (δ = 1.35)</span>
              </div>
              <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
                <span style="color: var(--text-dim);">Inference Latency:</span>
                <span id="model-inspect-latency" style="color: var(--green);">1.2 ms / regional query</span>
              </div>
              <div style="display:flex; justify-content:space-between;">
                <span style="color: var(--text-dim);">Generalization Error:</span>
                <span id="model-inspect-error" style="color: var(--cyan);">RMSE 14.2 (Low variance)</span>
              </div>
            </div>

            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; text-align: center;">
              <div style="background: rgba(255,255,255,0.03); border: 1px solid var(--border); border-radius: 8px; padding: 10px;">
                <span style="font-family: var(--font-display); font-size: 1.8rem; font-weight: 700; color: #fff;">-74%</span>
                <span style="display: block; font-size: 0.7rem; color: var(--text-dim); margin-top: 2px;">RMSE Error Reduction</span>
              </div>
              <div style="background: rgba(255,255,255,0.03); border: 1px solid var(--border); border-radius: 8px; padding: 10px;">
                <span style="font-family: var(--font-display); font-size: 1.8rem; font-weight: 700; color: var(--green);">1.08x</span>
                <span style="display: block; font-size: 0.7rem; color: var(--text-dim); margin-top: 2px;">Homogeneity Index (Parity)</span>
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
            The artificial January 2012 sensor gap is completely eliminated, yielding an authoritative continuous baseline from 2001 through 2025 across ~200 countries.
          </p>
        </div>

        <div class="breakthrough-split">
          <!-- Left: Before vs After Timeline -->
          <div class="chart-frame-box" style="height: 410px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
              <span style="font-size: 0.85rem; font-weight: 700; color: #fff;">Before vs. After Harmonization:</span>
              <div class="sim-btn-group" style="margin: 0;">
                <button id="btn-toggle-raw" class="btn-sim-mode" onclick="setMagicTimeline('raw')">Raw (Broken 2012)</button>
                <button id="btn-toggle-harm" class="btn-sim-mode active" onclick="setMagicTimeline('harmonized')">✨ SpectraNet Harmonized</button>
              </div>
            </div>
            <div id="plot-before-after" style="width: 100%; height: 350px;"></div>
          </div>

          <!-- Right: 25-Year Calendar Heatmap with Biome Switcher -->
          <div class="chart-frame-box" style="height: 410px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
              <span style="font-size: 0.85rem; font-weight: 700; color: #fff;">25-Year Seasonal Burning Matrix:</span>
              <span id="biome-current-label" style="font-family: var(--font-mono); font-size: 0.72rem; color: var(--cyan);">Nile Delta, Egypt</span>
            </div>
            
            <div class="biome-btn-group">
              <button class="btn-biome-tab active" onclick="selectBiomePreset('nile')">🇪🇬 Nile Delta</button>
              <button class="btn-biome-tab" onclick="selectBiomePreset('amazon')">🇧🇷 Amazon Basin</button>
              <button class="btn-biome-tab" onclick="selectBiomePreset('california')">🇺🇸 California</button>
              <button class="btn-biome-tab" onclick="selectBiomePreset('canada')">🇨🇦 Western Canada</button>
            </div>

            <div id="plot-calendar-slide" style="width: 100%; height: 310px;"></div>
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
              <span id="slide6-co2-val" style="font-family: var(--font-display); font-size: 2.1rem; font-weight: 700; color: #fff;">968.1 kt</span>
              <p style="font-size: 0.76rem; color: var(--text-dim); margin-top: 4px;">Computed via M = A · B · C · α using harmonized radiative energy and biome fuel loads.</p>
              <div style="margin-top: 8px; font-family: var(--font-mono); font-size: 0.72rem; color: var(--cyan);">
                ✦ Equivalent to 2.1 Million Barrels of Oil Combusted
              </div>
            </div>

            <div class="glass-card">
              <span style="font-family: var(--font-mono); font-size: 0.68rem; color: var(--fire-orange);">⚠️ PUBLIC HEALTH & AIR QUALITY INVENTORY</span>
              <h4 style="font-size: 1.1rem; color: #fff; margin: 4px 0 8px;">Aerosol Particulates (PM₂.₅)</h4>
              <span id="slide6-pm25-val" style="font-family: var(--font-display); font-size: 2.1rem; font-weight: 700; color: var(--fire-orange);">5,455.1 Tons</span>
              <p style="font-size: 0.76rem; color: var(--text-dim); margin-top: 4px;">Tracks fine respiratory smoke plumes for regional health advisories and downwind AQI warnings.</p>
              <div style="margin-top: 8px; font-family: var(--font-mono); font-size: 0.72rem; color: #EF4444;">
                ✦ Triggers Severe Air Quality Alerts in Agricultural Centers
              </div>
            </div>
          </div>

          <!-- Right: 2026 Predictive Forecast -->
          <div class="chart-frame-box" style="height: 410px;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 4px;">
              <span style="font-size: 0.85rem; font-weight: 700; color: #fff;">
                2026 6-Month Predictive Horizon (with 95% Confidence Bounds):
              </span>
              <span style="font-family:var(--font-mono); font-size:0.7rem; color:var(--fire-orange);">⚡ Peak Fire Alert: May 2026</span>
            </div>
            <div id="plot-forecast-slide" style="width: 100%; height: 350px;"></div>
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
            <div style="font-size: 1.8rem; margin-bottom: 8px;">🌍</div>
            <h3 style="font-family: var(--font-display); font-size: 1.25rem; color: #fff; margin-bottom: 6px;">Stage 1: 3D Orbital Earth</h3>
            <p style="font-size: 0.85rem; color: var(--text-muted); line-height: 1.55;">
              Photorealistic WebGL globe with real-time satellite orbit tracks (Terra, Aqua, VIIRS), scanning swath footprint cones, sub-satellite tracking, and ~200 searchable countries.
            </p>
            <div style="margin-top: 12px; font-family: var(--font-mono); font-size: 0.72rem; color: var(--cyan);">
              ✦ WebGL Shaders · Real-time Ephemeris · 60 FPS Smooth
            </div>
          </div>

          <div class="glass-card" style="border-top: 3px solid var(--blue);">
            <div style="font-size: 1.8rem; margin-bottom: 8px;">🛰️</div>
            <h3 style="font-family: var(--font-display); font-size: 1.25rem; color: #fff; margin-bottom: 6px;">Stage 2: Regional Mission Console</h3>
            <p style="font-size: 0.85rem; color: var(--text-muted); line-height: 1.55;">
              High-resolution Leaflet GIS maps, radar cluster markers, NASA infrared thermal climatology heatmaps, and full 48-column continuous harmonized CSV downloads.
            </p>
            <div style="margin-top: 12px; font-family: var(--font-mono); font-size: 0.72rem; color: #60A5FA;">
              ✦ 4-Tab Analytical Console · Seiler & Crutzen CO₂ · 2026 Forecast
            </div>
          </div>
        </div>

        <div class="cta-banner-strip">
          <a href="https://ahmedshaban0.github.io/SpectraLink/" target="_blank" class="btn-cta-main btn-cta-cyan">
            <span>🚀 Launch Live Web App (Public Demo)</span>
          </a>
          <a href="https://github.com/AhmedShaban0/SpectraLink" target="_blank" class="btn-cta-main btn-cta-ghost">
            <span>💻 Inspect GitHub Repository</span>
          </a>
          <button onclick="copyDemoLink()" class="btn-cta-main btn-cta-ghost">
            <span>📋 Copy Public Link for Judges</span>
          </button>
        </div>

        <div style="margin-top: 24px; text-align: center; font-family: var(--font-mono); font-size: 0.72rem; color: var(--text-dim);">
          NASA SPACE APPS CHALLENGE · TEAM SPECTRALINK · OPEN-SOURCE EARTH OBSERVATION
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

  <!-- Toast Notification -->
  <div id="pres-toast">Link copied to clipboard!</div>

  <!-- Keyboard Shortcuts Modal -->
  <div id="shortcuts-modal" class="shortcuts-modal" onclick="closeShortcutsModal(event)">
    <div class="shortcuts-card" onclick="event.stopPropagation()">
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:14px;">
        <h3 style="font-family:var(--font-display); font-size:1.15rem; color:#fff;">Keyboard Navigation Shortcuts</h3>
        <button onclick="closeShortcutsModal()" style="background:none; border:none; color:var(--text-muted); font-size:1.2rem; cursor:pointer;">✕</button>
      </div>
      <div class="shortcut-row">
        <span>Next Slide</span>
        <span class="kbd-badge">→ / Space</span>
      </div>
      <div class="shortcut-row">
        <span>Previous Slide</span>
        <span class="kbd-badge">← / Backspace</span>
      </div>
      <div class="shortcut-row">
        <span>Toggle Fullscreen</span>
        <span class="kbd-badge">F</span>
      </div>
      <div class="shortcut-row">
        <span>Toggle Sound FX</span>
        <span class="kbd-badge">M</span>
      </div>
      <div class="shortcut-row">
        <span>Direct Jump to Slide</span>
        <span class="kbd-badge">1 – 7</span>
      </div>
      <div class="shortcut-row">
        <span>First / Last Slide</span>
        <span class="kbd-badge">Home / End</span>
      </div>
      <div class="shortcut-row" style="border:none;">
        <span>Close Modal</span>
        <span class="kbd-badge">Esc / ?</span>
      </div>
    </div>
  </div>


  <!-- ========================================================================= -->
  <!-- INTERACTIVE PRESENTATION LOGIC                                            -->
  <!-- ========================================================================= -->
  <script>
    const biomesData = REPLACE_BIOMES_DATA;

    const state = {
      currentSlide: 1,
      totalSlides: 7,
      simMode: 'split',
      simThreshold: 12,
      currentBiome: 'nile',
      magicTimelineMode: 'harmonized',
      soundEnabled: false,
    };

    const chapterTitles = {
      1: "The Hook & Challenge",
      2: "The 2012 Sensor Trap",
      3: "Geospatial AI Architecture",
      4: "SpectraNet Model Benchmark",
      5: "25-Year Harmonized Record",
      6: "Emissions & 2026 Forecast",
      7: "Mission Control & Live Demo"
    };

    const modelInfoList = [
      {
        title: "SpectraNet Hybrid Stacking (Ensemble)",
        badge: "WINNER",
        desc: "Two-tier architecture: Base tier leverages gradient-boosted decision trees for sharp non-linear fuel transitions, blended with Huber-loss neural networks to prevent catastrophic over-prediction on extreme mega-fires.",
        loss: "Huber Robust Loss (δ = 1.35)",
        latency: "1.2 ms / regional query",
        error: "RMSE 14.2 (Low variance)"
      },
      {
        title: "Huber-Loss GBDT & ExtraTrees Blend",
        badge: "2ND PLACE",
        desc: "Stochastic tree ensemble optimized under asymmetric penalty. Excellent stability across seasonal fire boundaries, but slightly slower on edge-of-swath footprint corrections.",
        loss: "Modified Huber Loss",
        latency: "2.1 ms / query",
        error: "RMSE 18.6"
      },
      {
        title: "LightGBM Histogram Regressor",
        badge: "3RD PLACE",
        desc: "Fast histogram-based tree boosting. Superb on tabular vegetation indices (NDVI/NDWI), but sensitive to extreme multi-sensor day/night radiance spikes.",
        loss: "L2 Squared Loss",
        latency: "0.8 ms / query",
        error: "RMSE 21.4"
      },
      {
        title: "Random Forest Ensemble (100 Trees)",
        badge: "BASELINE TREE",
        desc: "Standard bagging ensemble. Good generalist baseline without parameter tuning, but exhibits high memory footprint and plateauing in tail distributions.",
        loss: "Mean Squared Error",
        latency: "4.5 ms / query",
        error: "RMSE 28.1"
      },
      {
        title: "Deep ResNet-MLP Neural Network",
        badge: "DEEP LEARNING",
        desc: "5-layer dense network with residual skip connections and Swish activations. Handles continuous atmospheric transmission smoothly, but overfits on small sample regimes.",
        loss: "Smooth L1 Loss",
        latency: "1.9 ms / query",
        error: "RMSE 34.0"
      },
      {
        title: "Statistical Scaling Baseline",
        badge: "UNREGULARIZED",
        desc: "Simple linear area ratio scaling without atmospheric physics or orbital geometry correction. Fails completely during high optical smoke depth events.",
        loss: "Ordinary Least Squares",
        latency: "0.1 ms / query",
        error: "RMSE 54.8 (High bias)"
      }
    ];

    // Web Audio Synthesizer (Zero External Dependencies)
    let audioCtx = null;
    function playSpaceTone(freq = 640, duration = 0.08, type = 'sine') {
      if (!state.soundEnabled) return;
      try {
        if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        if (audioCtx.state === 'suspended') audioCtx.resume();
        const osc = audioCtx.createOscillator();
        const gain = audioCtx.createGain();
        osc.type = type;
        osc.frequency.setValueAtTime(freq, audioCtx.currentTime);
        osc.frequency.exponentialRampToValueAtTime(freq * 1.5, audioCtx.currentTime + duration);
        gain.gain.setValueAtTime(0.04, audioCtx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + duration);
        osc.connect(gain);
        gain.connect(audioCtx.destination);
        osc.start();
        osc.stop(audioCtx.currentTime + duration);
      } catch (e) {}
    }

    document.addEventListener('DOMContentLoaded', () => {
      initAmbientCanvas();
      initHeroGlobeCanvas();
      buildDots();
      initKeyboard();
      initPixelSimulator();

      goToSlide(1);

      document.getElementById('btn-prev-slide').onclick = () => prevSlide();
      document.getElementById('btn-next-slide').onclick = () => nextSlide();
      document.getElementById('btn-toggle-fs').onclick = toggleFullscreen;
      document.getElementById('btn-toggle-sound').onclick = toggleSound;
      document.getElementById('btn-show-shortcuts').onclick = () => toggleShortcutsModal();
    });

    function toggleSound() {
      state.soundEnabled = !state.soundEnabled;
      const label = document.getElementById('sound-label');
      const icon = document.getElementById('sound-icon');
      if (state.soundEnabled) {
        label.textContent = 'Sound ON';
        icon.textContent = '🔊';
        playSpaceTone(880, 0.12, 'sine');
      } else {
        label.textContent = 'Sound OFF';
        icon.textContent = '🔇';
      }
    }

    function toggleShortcutsModal() {
      const m = document.getElementById('shortcuts-modal');
      m.classList.toggle('open');
    }

    function closeShortcutsModal() {
      document.getElementById('shortcuts-modal').classList.remove('open');
    }

    function copyDemoLink() {
      const url = "https://ahmedshaban0.github.io/SpectraLink/";
      navigator.clipboard.writeText(url).then(() => {
        const toast = document.getElementById('pres-toast');
        toast.textContent = "🚀 Demo Link copied to clipboard!";
        toast.classList.add('show');
        playSpaceTone(960, 0.1, 'triangle');
        setTimeout(() => toast.classList.remove('show'), 2400);
      });
    }

    function buildDots() {
      const container = document.getElementById('dots-strip');
      container.innerHTML = '';
      for (let i = 1; i <= state.totalSlides; i++) {
        const dot = document.createElement('div');
        dot.className = `dot-step ${i === 1 ? 'active' : ''}`;
        dot.textContent = `0${i}`;
        dot.title = `Slide ${i}: ${chapterTitles[i]}`;
        dot.onclick = () => goToSlide(i);
        container.appendChild(dot);
      }
    }

    function goToSlide(n) {
      if (n < 1 || n > state.totalSlides) return;
      state.currentSlide = n;

      playSpaceTone(440 + n * 60, 0.08);

      document.querySelectorAll('.slide').forEach(s => {
        const idx = parseInt(s.getAttribute('data-slide'));
        s.classList.toggle('active', idx === n);
      });

      document.querySelectorAll('.dot-step').forEach((d, idx) => {
        d.classList.toggle('active', idx + 1 === n);
      });

      document.getElementById('header-slide-num').textContent = String(n).padStart(2, '0');
      document.getElementById('header-slide-chapter').textContent = `· ${chapterTitles[n]}`;
      document.getElementById('top-progress-bar').style.width = `${(n / state.totalSlides) * 100}%`;

      if (n === 2) {
        setSimMode(state.simMode);
        renderRawTrapChart();
      } else if (n === 5) {
        renderBeforeAfterChart(state.magicTimelineMode);
        renderCalendarSlideChart();
      } else if (n === 6) {
        renderForecastSlideChart();
      }
    }

    function nextSlide() {
      if (state.currentSlide < state.totalSlides) goToSlide(state.currentSlide + 1);
    }

    function prevSlide() {
      if (state.currentSlide > 1) goToSlide(state.currentSlide - 1);
    }

    function toggleFullscreen() {
      if (!document.fullscreenElement) {
        document.documentElement.requestFullscreen().catch(() => {});
      } else {
        document.exitFullscreen().catch(() => {});
      }
    }

    function initKeyboard() {
      document.addEventListener('keydown', (e) => {
        if (e.key === 'ArrowRight' || e.key === ' ' || e.key === 'PageDown') {
          e.preventDefault();
          nextSlide();
        } else if (e.key === 'ArrowLeft' || e.key === 'Backspace' || e.key === 'PageUp') {
          e.preventDefault();
          prevSlide();
        } else if (e.key === 'f' || e.key === 'F') {
          toggleFullscreen();
        } else if (e.key === 'm' || e.key === 'M') {
          toggleSound();
        } else if (e.key === '?' || e.key === 'k' || e.key === 'K') {
          toggleShortcutsModal();
        } else if (e.key === 'Escape') {
          closeShortcutsModal();
        } else if (e.key >= '1' && e.key <= '7') {
          goToSlide(parseInt(e.key));
        } else if (e.key === 'Home') {
          goToSlide(1);
        } else if (e.key === 'End') {
          goToSlide(state.totalSlides);
        }
      });
    }

    // -------------------------------------------------------------------------
    // Slide 1: 3D Celestial Twin Globe with REAL Orbiting Satellites & Cones
    // -------------------------------------------------------------------------
    function initHeroGlobeCanvas() {
      const canvas = document.getElementById('hero-globe-canvas');
      if (!canvas) return;
      const ctx = canvas.getContext('2d');
      const size = 460;
      canvas.width = size;
      canvas.height = size;
      const cx = size / 2;
      const cy = size / 2;
      const R = 150;

      // Fibonacci sphere surface points
      const numPoints = 700;
      const points = [];
      const goldenAngle = Math.PI * (3 - Math.sqrt(5));

      for (let i = 0; i < numPoints; i++) {
        const y = 1 - (i / (numPoints - 1)) * 2;
        const radius = Math.sqrt(1 - y * y);
        const theta = goldenAngle * i;
        const x = Math.cos(theta) * radius;
        const z = Math.sin(theta) * radius;
        points.push({ x: x * R, y: y * R, z: z * R });
      }

      // Hotspots on globe
      const fireHotspots = [
        { lat: 0.52, lon: 0.55 }, // Nile / East Med
        { lat: -0.15, lon: -0.9 }, // Amazon
        { lat: 0.65, lon: -2.1 }, // California
        { lat: 0.95, lon: -1.8 }, // Canada
        { lat: -0.45, lon: 2.3 }, // Australia
        { lat: 0.12, lon: 0.35 }, // Congo
      ];

      // 3 Constellation Satellites Config
      const satsConfig = [
        {
          id: 'terra',
          name: 'MODIS Terra',
          timeDesc: '10:30 AM · 1km',
          color: '#38BDF8',
          swathColor: 'rgba(56, 189, 248, 0.22)',
          altitude: R * 1.25,
          speed: 0.018,
          phase: 0.0,
          inc: 1.71, // 98.2 deg polar
          raan: 0.0,
          swathW: 24
        },
        {
          id: 'aqua',
          name: 'MODIS Aqua',
          timeDesc: '1:30 PM · 1km',
          color: '#60A5FA',
          swathColor: 'rgba(96, 165, 250, 0.22)',
          altitude: R * 1.27,
          speed: 0.016,
          phase: 2.35,
          inc: 1.71,
          raan: 1.43,
          swathW: 24
        },
        {
          id: 'viirs',
          name: 'VIIRS Suomi-NPP',
          timeDesc: '1:30 PM · 375m HR',
          color: '#FF5400',
          swathColor: 'rgba(255, 84, 0, 0.28)',
          altitude: R * 1.40,
          speed: 0.014,
          phase: 4.36,
          inc: 1.72,
          raan: 2.93,
          swathW: 15 // Sharper high-res swath
        }
      ];

      let rotX = 0.22;
      let rotY = 0;
      let isDragging = false;
      let lastMouseX = 0;
      let lastMouseY = 0;

      canvas.addEventListener('mousedown', (e) => {
        isDragging = true;
        lastMouseX = e.clientX;
        lastMouseY = e.clientY;
      });

      window.addEventListener('mouseup', () => { isDragging = false; });

      window.addEventListener('mousemove', (e) => {
        if (!isDragging) return;
        const dx = e.clientX - lastMouseX;
        const dy = e.clientY - lastMouseY;
        rotY += dx * 0.008;
        rotX += dy * 0.008;
        lastMouseX = e.clientX;
        lastMouseY = e.clientY;
      });

      let time = 0;

      function renderGlobe() {
        ctx.clearRect(0, 0, size, size);

        if (!isDragging) {
          rotY += 0.004;
        }
        time += 0.02;

        // Atmospheric glowing rim
        const haloGrad = ctx.createRadialGradient(cx, cy, R * 0.7, cx, cy, R * 1.35);
        haloGrad.addColorStop(0, 'rgba(56, 189, 248, 0.12)');
        haloGrad.addColorStop(0.7, 'rgba(14, 165, 233, 0.03)');
        haloGrad.addColorStop(1, 'rgba(0, 0, 0, 0)');
        ctx.fillStyle = haloGrad;
        ctx.beginPath();
        ctx.arc(cx, cy, R * 1.35, 0, Math.PI * 2);
        ctx.fill();

        // Sphere dark obsidian base
        const sphereGrad = ctx.createRadialGradient(cx - R * 0.3, cy - R * 0.3, R * 0.1, cx, cy, R);
        sphereGrad.addColorStop(0, '#0E223D');
        sphereGrad.addColorStop(0.65, '#06101E');
        sphereGrad.addColorStop(1, '#02050E');
        ctx.fillStyle = sphereGrad;
        ctx.beginPath();
        ctx.arc(cx, cy, R, 0, Math.PI * 2);
        ctx.fill();

        // Coordinate Dots
        const cosY = Math.cos(rotY), sinY = Math.sin(rotY);
        const cosX = Math.cos(rotX), sinX = Math.sin(rotX);

        points.forEach(p => {
          const x1 = p.x * cosY + p.z * sinY;
          const z1 = -p.x * sinY + p.z * cosY;
          const y2 = p.y * cosX - z1 * sinX;
          const z2 = p.y * sinX + z1 * cosX;

          if (z2 > 0) {
            const alpha = Math.max(0.08, (z2 / R) * 0.85);
            ctx.fillStyle = `rgba(56, 189, 248, ${alpha})`;
            ctx.beginPath();
            ctx.arc(cx + x1, cy + y2, 1.25, 0, Math.PI * 2);
            ctx.fill();
          }
        });

        // Hotspot fires pulsing on Earth surface
        fireHotspots.forEach((h, idx) => {
          const lat = h.lat;
          const lon = h.lon + rotY;
          const hx = R * Math.cos(lat) * Math.sin(lon);
          const hy = -R * Math.sin(lat);
          const hz = R * Math.cos(lat) * Math.cos(lon);

          const py = hy * cosX - hz * sinX;
          const pz = hy * sinX + hz * cosX;

          if (pz > 5) {
            const pulse = (Math.sin(time * 4 + idx) + 1) * 0.5;
            // Fiery core
            ctx.fillStyle = `rgba(255, 84, 0, ${0.85 + pulse * 0.15})`;
            ctx.beginPath();
            ctx.arc(cx + hx, cy + py, 3.5 + pulse * 2.5, 0, Math.PI * 2);
            ctx.fill();

            // Flare wave
            ctx.strokeStyle = `rgba(255, 59, 0, ${1 - pulse})`;
            ctx.lineWidth = 1.4;
            ctx.beginPath();
            ctx.arc(cx + hx, cy + py, 4.5 + pulse * 7, 0, Math.PI * 2);
            ctx.stroke();
          }
        });

        // Draw the 3 Realistic Orbiting Satellites with Scanning Cones
        satsConfig.forEach((sat, sIdx) => {
          const u = time * sat.speed * 40 + sat.phase;
          const rSat = sat.altitude;

          // Orbit plane math
          const xOrb = rSat * Math.cos(u);
          const yOrb = rSat * Math.sin(u);

          const cosI = Math.cos(sat.inc), sinI = Math.sin(sat.inc);
          const cosR = Math.cos(sat.raan), sinR = Math.sin(sat.raan);

          // 3D position
          const satX = xOrb * cosR - yOrb * cosI * sinR;
          const satY = yOrb * sinI;
          const satZ = xOrb * sinR + yOrb * cosI * cosR;

          // World rotation (drag interaction)
          const rx1 = satX * cosY + satZ * sinY;
          const rz1 = -satX * sinY + satZ * cosY;
          const ry2 = satY * cosX - rz1 * sinX;
          const rz2 = satY * sinX + rz1 * cosX;

          // Projected satellite screen pos
          const sx = cx + rx1;
          const sy = cy - ry2;

          // Sub-satellite footprint on Earth surface
          const dSat = Math.sqrt(rx1 * rx1 + ry2 * ry2 + rz2 * rz2);
          const subX = (rx1 / dSat) * R;
          const subY = (ry2 / dSat) * R;
          const subZ = (rz2 / dSat) * R;

          const ex = cx + subX;
          const ey = cy - subY;

          // Draw orbital track line
          ctx.save();
          ctx.strokeStyle = sat.color;
          ctx.lineWidth = 0.8;
          ctx.setLineDash([3, 5]);
          ctx.globalAlpha = 0.28;
          ctx.beginPath();
          ctx.arc(cx, cy, rSat, 0, Math.PI * 2);
          ctx.stroke();
          ctx.restore();

          // If satellite or cone is in front
          if (rz2 > -30) {
            // 1. VOLUMETRIC SCANNING SWATH CONE
            ctx.save();
            const beamGrad = ctx.createLinearGradient(sx, sy, ex, ey);
            beamGrad.addColorStop(0, sat.color + '00');
            beamGrad.addColorStop(0.2, sat.color + '22');
            beamGrad.addColorStop(1, sat.swathColor);
            ctx.fillStyle = beamGrad;

            ctx.beginPath();
            ctx.moveTo(sx, sy);
            ctx.lineTo(ex - sat.swathW, ey + 4);
            ctx.lineTo(ex + sat.swathW, ey - 4);
            ctx.closePath();
            ctx.fill();

            // Ground footprint swath ring
            ctx.strokeStyle = sat.color;
            ctx.lineWidth = 1.5;
            ctx.beginPath();
            ctx.ellipse(ex, ey, sat.swathW, sat.swathW * 0.5, 0, 0, Math.PI * 2);
            ctx.stroke();

            // Radar scan crosshair
            ctx.fillStyle = sat.color;
            ctx.beginPath();
            ctx.arc(ex, ey, 2.5, 0, Math.PI * 2);
            ctx.fill();
            ctx.restore();

            // 2. REALISTIC 3D SATELLITE BODY
            ctx.save();
            ctx.translate(sx, sy);

            // Solar Array Panels (blue with solar grid lines)
            ctx.fillStyle = '#1E3A8A';
            ctx.strokeStyle = '#38BDF8';
            ctx.lineWidth = 0.8;
            ctx.fillRect(-16, -3, 11, 6);
            ctx.strokeRect(-16, -3, 11, 6);
            ctx.fillRect(5, -3, 11, 6);
            ctx.strokeRect(5, -3, 11, 6);

            // Main Bus Body
            ctx.fillStyle = sat.id === 'viirs' ? '#FF5400' : '#EAB308';
            ctx.fillRect(-5, -4, 10, 8);
            ctx.strokeStyle = '#fff';
            ctx.lineWidth = 0.6;
            ctx.strokeRect(-5, -4, 10, 8);

            // Strobe Beacon Flasher
            const isFlash = Math.sin(time * 8 + sIdx) > 0.4;
            if (isFlash) {
              ctx.fillStyle = '#fff';
              ctx.beginPath();
              ctx.arc(0, -6, 2, 0, Math.PI * 2);
              ctx.fill();
            }

            // High-Tech Telemetry Tag
            ctx.fillStyle = 'rgba(8, 14, 28, 0.85)';
            ctx.strokeStyle = sat.color;
            ctx.lineWidth = 0.8;
            ctx.beginPath();
            ctx.roundRect(16, -10, 110, 20, 4);
            ctx.fill();
            ctx.stroke();

            ctx.fillStyle = sat.color;
            ctx.font = 'bold 8.5px JetBrains Mono, monospace';
            ctx.fillText(sat.name, 22, -1);
            ctx.fillStyle = '#94A3B8';
            ctx.font = '7.5px JetBrains Mono, monospace';
            ctx.fillText(sat.timeDesc, 22, 7);

            ctx.restore();
          }
        });

        requestAnimationFrame(renderGlobe);
      }

      renderGlobe();
    }

    // -------------------------------------------------------------------------
    // Slide 2: Interactive Pixel Simulator
    // -------------------------------------------------------------------------
    function initPixelSimulator() {
      setSimMode('split');
    }

    function updateSimThreshold(val) {
      state.simThreshold = parseInt(val);
      document.getElementById('sim-threshold-val').textContent = `${val} MW`;
      setSimMode(state.simMode);
    }

    function drawGridOnSvg(svgEl, cols, rows, activeHits, sensorClass) {
      if (!svgEl) return;
      svgEl.innerHTML = '';
      const cellW = 100 / cols;
      const cellH = 100 / rows;

      for (let r = 0; r < rows; r++) {
        for (let c = 0; c < cols; c++) {
          const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
          rect.setAttribute('x', c * cellW);
          rect.setAttribute('y', r * cellH);
          rect.setAttribute('width', cellW);
          rect.setAttribute('height', cellH);
          rect.setAttribute('fill', 'rgba(255, 255, 255, 0.02)');
          rect.setAttribute('stroke', sensorClass === 'active-modis' ? 'rgba(255, 255, 255, 0.18)' : 'rgba(56, 189, 248, 0.25)');
          rect.setAttribute('stroke-width', sensorClass === 'active-modis' ? '1.5' : '1');

          const isHit = activeHits.some(([ar, ac]) => ar === r && ac === c);
          if (isHit) {
            rect.classList.add(sensorClass);
          }

          rect.onmouseenter = () => {
            const hud = document.getElementById('sim-hud-readout');
            if (hud) {
              const area = sensorClass === 'active-modis' ? '1,000,000 m² (1 km)' : '140,625 m² (375m)';
              const status = isHit ? '🔥 ACTIVE HOTSPOT EXCEEDING THRESHOLD' : '❄ Background Cool Ground';
              const rad = isHit ? (sensorClass === 'active-modis' ? '14.2 MW (Diluted)' : '28.6 MW (Resolved Core)') : '2.1 MW';
              hud.innerHTML = `<strong>Cell [${r},${c}]</strong> · Area: <span style="color:#fff">${area}</span> · Radiance: <span style="color:var(--cyan)">${rad}</span> · <span style="color:${isHit ? 'var(--fire-orange)' : '#64748B'}">${status}</span>`;
            }
          };

          svgEl.appendChild(rect);
        }
      }
    }

    function setSimMode(mode) {
      state.simMode = mode;
      document.querySelectorAll('.btn-sim-mode').forEach(b => b.classList.remove('active'));
      const activeBtn = document.getElementById(`btn-sim-${mode}`);
      if (activeBtn) activeBtn.classList.add('active');

      const singleContainer = document.getElementById('single-grid-container');
      const dualContainer = document.getElementById('dual-grid-container');
      const mainSvg = document.getElementById('sim-grid-svg');
      const statCount = document.getElementById('sim-stat-count');

      // Adjust hits based on threshold
      const modisHits = state.simThreshold <= 14 ? [[1, 1]] : [];
      const viirsHits = state.simThreshold <= 28 ? [
        [3, 3], [3, 4], [4, 3], [4, 4], [2, 5], [5, 2]
      ] : [[3, 3], [4, 4]];

      if (mode === 'modis') {
        singleContainer.classList.remove('hidden');
        dualContainer.classList.add('hidden');
        drawGridOnSvg(mainSvg, 3, 3, modisHits, 'active-modis');
        if (statCount) {
          statCount.textContent = `${modisHits.length} Hotspot Detected (Coarse Dilution)`;
          statCount.style.color = '#EF4444';
        }
      } else if (mode === 'viirs') {
        singleContainer.classList.remove('hidden');
        dualContainer.classList.add('hidden');
        drawGridOnSvg(mainSvg, 8, 8, viirsHits, 'active-viirs');
        if (statCount) {
          statCount.textContent = `${viirsHits.length} Hotspots Detected (7.1x Sharper Resolution)`;
          statCount.style.color = 'var(--fire-orange)';
        }
      } else if (mode === 'split') {
        singleContainer.classList.add('hidden');
        dualContainer.classList.remove('hidden');
        drawGridOnSvg(document.getElementById('sim-grid-svg-modis-dual'), 3, 3, modisHits, 'active-modis');
        drawGridOnSvg(document.getElementById('sim-grid-svg-viirs-dual'), 8, 8, viirsHits, 'active-viirs');
        if (statCount) {
          statCount.textContent = `${modisHits.length} MODIS vs. ${viirsHits.length} VIIRS (Same Physical Ground Fire)`;
          statCount.style.color = 'var(--cyan)';
        }
      }
    }

    // -------------------------------------------------------------------------
    // Slide 2: Plotly Raw Trap Chart
    // -------------------------------------------------------------------------
    function renderRawTrapChart() {
      const dates = [];
      const counts = [];

      for (let y = 2005; y <= 2020; y++) {
        for (let m = 1; m <= 12; m++) {
          dates.push(`${y}-${String(m).padStart(2, '0')}`);
          const isPost2012 = y >= 2012;
          const seasonal = (m === 5 ? 120 : m === 10 ? 160 : 30);
          const val = isPost2012 ? (seasonal * 3.8 + Math.random() * 40) : (seasonal + Math.random() * 15);
          counts.push(val);
        }
      }

      const traceRaw = {
        x: dates,
        y: counts,
        type: 'scatter',
        mode: 'lines',
        line: { color: '#EF4444', width: 2.2 },
        name: 'Raw Recorded Hotspots (Uncalibrated)',
      };

      const layout = {
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        font: { family: 'Inter, sans-serif', color: '#94A3B8', size: 10 },
        margin: { l: 40, r: 15, t: 15, b: 25 },
        xaxis: { showgrid: true, gridcolor: 'rgba(255,255,255,0.06)' },
        yaxis: { showgrid: true, gridcolor: 'rgba(255,255,255,0.06)', title: 'Monthly Hotspots' },
        annotations: [
          {
            x: '2012-01',
            y: 420,
            text: '⚡ VIIRS Activated (+404% Step Jump)',
            showarrow: true,
            arrowhead: 2,
            arrowcolor: '#FF5400',
            font: { color: '#FF5400', size: 10, weight: 700 },
            bgcolor: 'rgba(15, 23, 42, 0.9)',
            bordercolor: '#FF5400',
          }
        ],
        shapes: [
          {
            type: 'line',
            x0: '2012-01',
            x1: '2012-01',
            y0: 0,
            y1: 1,
            yref: 'paper',
            line: { color: '#FF5400', width: 1.5, dash: 'dash' }
          }
        ],
      };

      Plotly.newPlot('plot-raw-trap', [traceRaw], layout, { responsive: true, displayModeBar: false });
    }

    // -------------------------------------------------------------------------
    // Slide 3: Pillar Inspector
    // -------------------------------------------------------------------------
    function inspectPillar(num) {
      playSpaceTone(600 + num * 50, 0.08);
      const names = [
        "Orbit Geometry: Bow-tie distortion expands edge pixels up to 4.8x. SpectraNet applies dynamic angular footprint projection.",
        "Atmospheric Physics: Dense wildfire smoke attenuates mid-IR radiance. SpectraNet inverts aerosol optical depth (AOD).",
        "Fuel Phenology: Live fuel moisture deficit (NDWI) dictates flame ignition thresholds across 17 distinct biomes.",
        "Diurnal Progression: Gaussian circadian kernel aligns Terra (10:30 AM) with Aqua and VIIRS afternoon fire peaks (1:30 PM)."
      ];
      const toast = document.getElementById('pres-toast');
      toast.textContent = names[num - 1];
      toast.classList.add('show');
      setTimeout(() => toast.classList.remove('show'), 3500);
    }

    // -------------------------------------------------------------------------
    // Slide 4: Model Inspector
    // -------------------------------------------------------------------------
    function selectModel(idx) {
      playSpaceTone(500 + idx * 40, 0.06);
      document.querySelectorAll('.race-row').forEach((r, i) => r.classList.toggle('active', i === idx));
      const info = modelInfoList[idx];
      document.getElementById('model-inspect-title').textContent = info.title;
      document.getElementById('model-inspect-badge').textContent = info.badge;
      document.getElementById('model-inspect-desc').textContent = info.desc;
      document.getElementById('model-inspect-loss').textContent = info.loss;
      document.getElementById('model-inspect-latency').textContent = info.latency;
      document.getElementById('model-inspect-error').textContent = info.error;
    }

    // -------------------------------------------------------------------------
    // Slide 5: Before vs After Magic Timeline & Biome Presets
    // -------------------------------------------------------------------------
    function selectBiomePreset(biomeKey) {
      playSpaceTone(720, 0.08);
      state.currentBiome = biomeKey;
      document.querySelectorAll('.btn-biome-tab').forEach(b => b.classList.remove('active'));
      const activeBtn = Array.from(document.querySelectorAll('.btn-biome-tab')).find(b => b.getAttribute('onclick').includes(biomeKey));
      if (activeBtn) activeBtn.classList.add('active');

      const bData = biomesData[biomeKey];
      if (bData) {
        document.getElementById('biome-current-label').textContent = `${bData.name} (${bData.biome})`;
        document.getElementById('slide6-co2-val').textContent = `${bData.total_co2_kt.toLocaleString()} kt`;
        document.getElementById('slide6-pm25-val').textContent = `${bData.total_pm25_tons.toLocaleString()} Tons`;
      }

      renderBeforeAfterChart(state.magicTimelineMode);
      renderCalendarSlideChart();
      if (state.currentSlide === 6) renderForecastSlideChart();
    }

    function setMagicTimeline(mode) {
      state.magicTimelineMode = mode;
      document.getElementById('btn-toggle-raw').classList.toggle('active', mode === 'raw');
      document.getElementById('btn-toggle-harm').classList.toggle('active', mode === 'harmonized');
      renderBeforeAfterChart(mode);
    }

    function renderBeforeAfterChart(mode) {
      const bData = biomesData[state.currentBiome] || biomesData['nile'];
      let dates = [];
      let rawVals = [];
      let harmVals = [];

      if (bData && bData.timeline && bData.timeline.length > 0) {
        dates = bData.timeline.map(d => d.date);
        rawVals = bData.timeline.map(d => d.is_overlap ? d.viirs_raw : d.modis_raw);
        harmVals = bData.timeline.map(d => d.harmonized);
      } else {
        for (let y = 2001; y <= 2025; y++) {
          for (let m = 1; m <= 12; m++) {
            dates.push(`${y}-${String(m).padStart(2, '0')}`);
            const isPost2012 = y >= 2012;
            const seasonal = (m === 5 ? 140 : m === 9 ? 220 : m === 10 ? 340 : 45);
            const noise = Math.sin(y * 1.5 + m) * 20;
            rawVals.push(Math.max(10, isPost2012 ? (seasonal * 3.65 + noise) : (seasonal + noise * 0.3)));
            harmVals.push(Math.max(25, seasonal * 3.65 + noise));
          }
        }
      }

      const traces = [];

      if (mode === 'raw') {
        traces.push({
          x: dates,
          y: rawVals,
          type: 'scatter',
          mode: 'lines',
          line: { color: '#EF4444', width: 2.2 },
          name: 'Broken Raw Series (404% Artificial Jump in 2012)',
        });
      } else {
        traces.push({
          x: dates,
          y: harmVals,
          type: 'scatter',
          mode: 'lines',
          line: { color: '#38BDF8', width: 2.6 },
          name: 'SpectraLink Continuous Harmonized Series',
        });
      }

      const layout = {
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        font: { family: 'Inter, sans-serif', color: '#94A3B8', size: 10 },
        margin: { l: 40, r: 15, t: 15, b: 25 },
        legend: { orientation: 'h', y: 1.15, x: 1, xanchor: 'right' },
        xaxis: { showgrid: true, gridcolor: 'rgba(255,255,255,0.06)' },
        yaxis: { showgrid: true, gridcolor: 'rgba(255,255,255,0.06)', title: 'Monthly Hotspots' },
      };

      Plotly.newPlot('plot-before-after', traces, layout, { responsive: true, displayModeBar: false });
    }

    // -------------------------------------------------------------------------
    // Slide 5: 25-Year Calendar Heatmap
    // -------------------------------------------------------------------------
    function renderCalendarSlideChart() {
      const bData = biomesData[state.currentBiome] || biomesData['nile'];
      const years = [];
      for (let y = 2001; y <= 2025; y++) years.push(y);
      const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
      
      let zValues = bData ? bData.calendar : [];
      if (!zValues || zValues.length === 0) {
        zValues = [];
        for (let m = 0; m < 12; m++) {
          const row = [];
          for (let y = 0; y < years.length; y++) {
            const mNum = m + 1;
            const seasonal = (mNum === 5 ? 280 : mNum === 9 ? 420 : mNum === 10 ? 680 : 50);
            row.push(Math.round(seasonal + Math.sin(y * 1.8 + m) * 60));
          }
          zValues.push(row);
        }
      }

      const trace = {
        z: zValues,
        x: years,
        y: months,
        type: 'heatmap',
        colorscale: [
          [0.0, '#040712'],
          [0.15, '#1B1429'],
          [0.35, '#5B1414'],
          [0.55, '#991B1B'],
          [0.72, '#EA580C'],
          [0.88, '#FF5400'],
          [1.0, '#FFC247'],
        ],
        colorbar: {
          title: { text: 'Hotspots', font: { size: 9, color: '#94A3B8' } },
          thickness: 10,
          len: 0.85,
          tickfont: { color: '#94A3B8', size: 8 }
        }
      };

      const layout = {
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        font: { family: 'Inter, sans-serif', color: '#94A3B8', size: 10 },
        margin: { l: 40, r: 15, t: 15, b: 25 },
        xaxis: { dtick: 3 },
        yaxis: { showgrid: false },
      };

      Plotly.newPlot('plot-calendar-slide', [trace], layout, { responsive: true, displayModeBar: false });
    }

    // -------------------------------------------------------------------------
    // Slide 6: 2026 Forecast Plotly Chart
    // -------------------------------------------------------------------------
    function renderForecastSlideChart() {
      const bData = biomesData[state.currentBiome] || biomesData['nile'];
      const histDates = ['2025-07', '2025-08', '2025-09', '2025-10', '2025-11', '2025-12'];
      const histVals = [180, 210, 480, 710, 190, 85];

      let fcDates = ['2026-01', '2026-02', '2026-03', '2026-04', '2026-05', '2026-06'];
      let fcVals = [65, 80, 110, 160, 340, 190];
      let ciUpper = [95, 115, 150, 220, 430, 260];
      let ciLower = [40, 50, 75, 110, 260, 130];

      if (bData && bData.forecast && bData.forecast.length > 0) {
        fcDates = bData.forecast.map(d => d.date);
        fcVals = bData.forecast.map(d => d.forecast_hotspots);
        ciUpper = bData.forecast.map(d => d.ci_upper);
        ciLower = bData.forecast.map(d => d.ci_lower);
      }

      const traceHist = {
        x: histDates,
        y: histVals,
        type: 'scatter',
        mode: 'lines+markers',
        marker: { size: 5, color: '#38BDF8' },
        line: { color: '#38BDF8', width: 2.2 },
        name: 'Historical (Late 2025)',
      };

      const traceFC = {
        x: fcDates,
        y: fcVals,
        type: 'scatter',
        mode: 'lines+markers',
        marker: { size: 6, color: '#F97316' },
        line: { color: '#F97316', width: 2.5, dash: 'dash' },
        name: '2026 6-Month Projection',
      };

      const traceCI = {
        x: fcDates.concat(fcDates.slice().reverse()),
        y: ciUpper.concat(ciLower.slice().reverse()),
        fill: 'toself',
        fillcolor: 'rgba(249, 115, 22, 0.16)',
        line: { color: 'transparent' },
        name: '95% Confidence Band',
      };

      const layout = {
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        font: { family: 'Inter, sans-serif', color: '#94A3B8', size: 10 },
        margin: { l: 40, r: 15, t: 20, b: 25 },
        legend: { orientation: 'h', y: 1.15, x: 1, xanchor: 'right' },
        xaxis: { showgrid: true, gridcolor: 'rgba(255,255,255,0.06)' },
        yaxis: { showgrid: true, gridcolor: 'rgba(255,255,255,0.06)', title: 'Projected Hotspots' },
      };

      Plotly.newPlot('plot-forecast-slide', [traceHist, traceCI, traceFC], layout, { responsive: true, displayModeBar: false });
    }

    // -------------------------------------------------------------------------
    // Ambient Canvas: Distant Stars + Subtle Cosmic Embers
    // -------------------------------------------------------------------------
    function initAmbientCanvas() {
      const canvas = document.getElementById('ambient-canvas');
      const ctx = canvas.getContext('2d');
      let w = canvas.width = window.innerWidth;
      let h = canvas.height = window.innerHeight;

      window.addEventListener('resize', () => {
        w = canvas.width = window.innerWidth;
        h = canvas.height = window.innerHeight;
      });

      // Distant Stars
      const stars = Array.from({ length: 85 }, () => ({
        x: Math.random() * w,
        y: Math.random() * h,
        radius: Math.random() * 1.3,
        alpha: Math.random() * 0.7 + 0.2,
        twinkle: Math.random() * 0.02 + 0.005,
      }));

      // Subtle, gentle rising embers (tasteful whisper of heat, not overwhelming)
      const embers = Array.from({ length: 16 }, () => ({
        x: Math.random() * w,
        y: Math.random() * h + 50,
        radius: Math.random() * 1.4 + 0.6,
        speedY: Math.random() * 0.5 + 0.2,
        speedX: (Math.random() - 0.5) * 0.3,
        alpha: Math.random() * 0.45 + 0.15,
        color: Math.random() > 0.5 ? 'rgba(255, 84, 0, ' : 'rgba(255, 160, 0, '
      }));

      let time = 0;

      function render() {
        ctx.clearRect(0, 0, w, h);
        time += 0.02;

        // Render Stars
        stars.forEach(s => {
          s.alpha += s.twinkle;
          if (s.alpha > 0.95 || s.alpha < 0.15) s.twinkle = -s.twinkle;
          ctx.fillStyle = `rgba(255, 255, 255, ${s.alpha})`;
          ctx.beginPath();
          ctx.arc(s.x, s.y, s.radius, 0, Math.PI * 2);
          ctx.fill();
        });

        // Render Subtle Embers
        embers.forEach(e => {
          e.y -= e.speedY;
          e.x += Math.sin(time + e.radius) * 0.4 + e.speedX;

          if (e.y < -15) {
            e.y = h + 15;
            e.x = Math.random() * w;
          }

          ctx.fillStyle = e.color + e.alpha + ')';
          ctx.beginPath();
          ctx.arc(e.x, e.y, e.radius, 0, Math.PI * 2);
          ctx.fill();
        });

        requestAnimationFrame(render);
      }
      render();
    }
  </script>
</body>
</html>
"""

# Replace base64 tokens
final_html = html_template.replace("REPLACE_LOGO_BASE64", logo_base64)
final_html = final_html.replace("REPLACE_SPACE_APPS_BASE64", space_apps_base64)
final_html = final_html.replace("REPLACE_BIOMES_DATA", json.dumps(biomes_data))

with open(OUTPUT_STANDALONE, "w", encoding="utf-8") as f:
    f.write(final_html)

with open(OUTPUT_ROOT_PRES, "w", encoding="utf-8") as f:
    f.write(final_html)

with open(OUTPUT_STATIC_PRES, "w", encoding="utf-8") as f:
    f.write(final_html)

print("Generated all presentation files with balanced aerospace styling successfully!")
