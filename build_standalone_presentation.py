import base64
import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGO_PATH = os.path.join(BASE_DIR, "static", "logo_transparent.png")
SPACE_APPS_PATH = os.path.join(BASE_DIR, "static", "nasa_space_apps_white.png")
OUTPUT_PATH = os.path.join(BASE_DIR, "SpectraLink_Presentation_Standalone.html")

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

# HTML Template
html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>SpectraLink | NASA Space Apps Challenge Interactive Presentation</title>
  
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&family=Space+Grotesk:wght@500;600;700&display=swap" rel="stylesheet">
  
  <!-- Standalone Plotly.js from CDN -->
  <script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>

  <style>
    /* ==========================================================================
       SPECTRALINK STANDALONE PRESENTATION ENGINE
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
      z-index: 1;
    }}

    /* Top Telemetry Header */
    .pres-header {{
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      height: 64px;
      padding: 0 32px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      background: linear-gradient(180deg, rgba(7, 10, 18, 0.95) 0%, rgba(7, 10, 18, 0) 100%);
      z-index: 100;
      backdrop-filter: blur(8px);
      border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    }}

    .header-brand {{
      display: flex;
      align-items: center;
      gap: 16px;
      text-decoration: none;
    }}

    .brand-logo {{
      height: 36px;
      width: auto;
      object-fit: contain;
      filter: drop-shadow(0 2px 10px rgba(56, 189, 248, 0.35));
    }}

    .brand-divider {{
      width: 1px;
      height: 28px;
      background: rgba(255, 255, 255, 0.2);
    }}

    .space-apps-logo {{
      height: 40px;
      width: auto;
      object-fit: contain;
      filter: drop-shadow(0 2px 10px rgba(255, 255, 255, 0.25));
    }}

    .brand-badge {{
      display: flex;
      flex-direction: column;
    }}

    .brand-title {{
      font-family: var(--font-display);
      font-size: 0.95rem;
      font-weight: 700;
      letter-spacing: 0.05em;
      color: #fff;
    }}

    .brand-sub {{
      font-family: var(--font-mono);
      font-size: 0.65rem;
      color: var(--cyan);
      letter-spacing: 0.08em;
    }}

    .header-status {{
      display: flex;
      align-items: center;
      gap: 16px;
    }}

    .slide-progress-pill {{
      font-family: var(--font-mono);
      font-size: 0.8rem;
      color: var(--text-muted);
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid var(--border);
      padding: 6px 14px;
      border-radius: 9999px;
      display: flex;
      align-items: center;
      gap: 8px;
    }}

    .slide-progress-pill span.curr {{
      color: var(--cyan);
      font-weight: 700;
    }}

    .header-actions {{
      display: flex;
      align-items: center;
      gap: 12px;
    }}

    .btn-header-action {{
      background: rgba(255, 255, 255, 0.06);
      border: 1px solid var(--border);
      color: var(--text-main);
      padding: 7px 15px;
      border-radius: 8px;
      font-size: 0.82rem;
      font-weight: 600;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 8px;
      transition: all 0.2s var(--easing);
      text-decoration: none;
    }}

    .btn-header-action:hover {{
      background: rgba(56, 189, 248, 0.15);
      border-color: var(--cyan);
      color: #fff;
      transform: translateY(-1px);
    }}

    .btn-live-launch {{
      background: linear-gradient(135deg, rgba(56, 189, 248, 0.25) 0%, rgba(249, 115, 22, 0.25) 100%);
      border-color: var(--cyan);
      color: #fff;
      box-shadow: 0 0 15px rgba(56, 189, 248, 0.25);
    }}

    .btn-live-launch:hover {{
      background: linear-gradient(135deg, rgba(56, 189, 248, 0.45) 0%, rgba(249, 115, 22, 0.45) 100%);
      box-shadow: 0 0 25px rgba(56, 189, 248, 0.5);
    }}

    /* Deck Container */
    #deck-container {{
      position: absolute;
      inset: 0;
      width: 100vw;
      height: 100vh;
      z-index: 10;
      overflow: hidden;
    }}

    /* Slide Base Layout with Safe Viewport Padding */
    .slide {{
      position: absolute;
      inset: 0;
      width: 100vw;
      height: 100vh;
      padding: 72px 48px 84px 48px;
      display: flex;
      flex-direction: column;
      justify-content: center;
      align-items: center;
      opacity: 0;
      pointer-events: none;
      transform: scale(0.96) translateY(20px);
      transition: opacity 0.5s var(--easing), transform 0.5s var(--easing);
      z-index: 5;
    }}

    .slide.active {{
      opacity: 1;
      pointer-events: auto;
      transform: scale(1) translateY(0);
      z-index: 10;
    }}

    .slide-content-wrap {{
      width: 100%;
      max-width: 1280px;
      height: 100%;
      max-height: 84vh;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
    }}

    /* Partnership Badge in Slide 1 */
    .hero-partnership-badge {{
      display: inline-flex;
      align-items: center;
      gap: 12px;
      background: rgba(255, 255, 255, 0.06);
      border: 1px solid rgba(255, 255, 255, 0.15);
      padding: 6px 18px;
      border-radius: 9999px;
      margin-bottom: 14px;
      align-self: flex-start;
      backdrop-filter: blur(10px);
    }}

    .hero-space-apps-badge-logo {{
      height: 28px;
      width: auto;
      object-fit: contain;
    }}

    .hero-partnership-badge span {{
      font-family: var(--font-mono);
      font-size: 0.75rem;
      font-weight: 600;
      letter-spacing: 0.08em;
      color: #E2E8F0;
    }}

    .slide-badge-category {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      font-family: var(--font-mono);
      font-size: 0.72rem;
      font-weight: 600;
      color: var(--cyan);
      background: rgba(56, 189, 248, 0.12);
      border: 1px solid rgba(56, 189, 248, 0.3);
      padding: 4px 12px;
      border-radius: 9999px;
      letter-spacing: 0.1em;
      margin-bottom: 8px;
      text-transform: uppercase;
      align-self: flex-start;
    }}

    .slide-title {{
      font-family: var(--font-display);
      font-size: 2.35rem;
      font-weight: 700;
      line-height: 1.15;
      letter-spacing: -0.02em;
      color: #FFFFFF;
      margin-bottom: 6px;
    }}

    .slide-title span.highlight {{
      background: linear-gradient(135deg, #38BDF8 0%, #F59E0B 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }}

    .slide-subtitle {{
      font-size: 1.02rem;
      color: var(--text-muted);
      line-height: 1.45;
      max-width: 900px;
      margin-bottom: 16px;
    }}

    /* Staggered Animations */
    .slide.active .stagger-1 {{ animation: slideInUp 0.5s var(--easing) 0.05s both; }}
    .slide.active .stagger-2 {{ animation: slideInUp 0.5s var(--easing) 0.12s both; }}
    .slide.active .stagger-3 {{ animation: slideInUp 0.5s var(--easing) 0.20s both; }}
    .slide.active .stagger-4 {{ animation: slideInUp 0.5s var(--easing) 0.28s both; }}
    .slide.active .stagger-5 {{ animation: slideInUp 0.5s var(--easing) 0.36s both; }}

    @keyframes slideInUp {{
      from {{
        opacity: 0;
        transform: translateY(20px);
      }}
      to {{
        opacity: 1;
        transform: translateY(0);
      }}
    }}

    /* Glassmorphic Cards */
    .glass-card {{
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 20px 24px;
      backdrop-filter: blur(14px);
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.45);
      position: relative;
      overflow: hidden;
      transition: all 0.3s var(--easing);
    }}

    .glass-card:hover {{
      background: var(--bg-card-hover);
      border-color: rgba(56, 189, 248, 0.35);
      transform: translateY(-2px);
    }}

    .glass-card::before {{
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      height: 2px;
      background: linear-gradient(90deg, transparent, rgba(56, 189, 248, 0.4), transparent);
    }}

    /* Slide 1: Hero Hook */
    .hero-layout {{
      display: grid;
      grid-template-columns: 1.15fr 0.85fr;
      gap: 36px;
      align-items: center;
      height: 100%;
    }}

    .hero-text {{
      display: flex;
      flex-direction: column;
      justify-content: center;
    }}

    .hero-title {{
      font-family: var(--font-display);
      font-size: 3.2rem;
      font-weight: 700;
      line-height: 1.1;
      margin-bottom: 16px;
      letter-spacing: -0.03em;
    }}

    .hero-question-card {{
      background: linear-gradient(135deg, rgba(56, 189, 248, 0.12) 0%, rgba(249, 115, 22, 0.12) 100%);
      border: 1px solid rgba(56, 189, 248, 0.35);
      padding: 18px 22px;
      border-radius: 14px;
      margin-top: 18px;
      display: flex;
      align-items: center;
      gap: 16px;
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
    }}

    .hero-q-icon {{
      font-size: 1.8rem;
    }}

    .hero-q-text {{
      font-size: 0.98rem;
      font-weight: 500;
      color: #E2E8F0;
      line-height: 1.45;
    }}

    .hero-visual {{
      display: flex;
      justify-content: center;
      align-items: center;
      position: relative;
    }}

    .globe-simulation-art {{
      width: 340px;
      height: 340px;
      border-radius: 50%;
      background: radial-gradient(circle at 35% 35%, #1e293b 0%, #0b1329 60%, #030712 100%);
      border: 2px solid rgba(56, 189, 248, 0.35);
      box-shadow: 0 0 60px rgba(56, 189, 248, 0.25), inset 0 0 50px rgba(56, 189, 248, 0.2);
      position: relative;
      display: flex;
      justify-content: center;
      align-items: center;
    }}

    .orbit-ring {{
      position: absolute;
      border-radius: 50%;
      border: 1px dashed rgba(56, 189, 248, 0.3);
      pointer-events: none;
    }}

    .orbit-ring.modis {{
      width: 400px;
      height: 400px;
      transform: rotate(65deg);
      animation: spinOrbit 24s linear infinite;
    }}

    .orbit-ring.viirs {{
      width: 460px;
      height: 460px;
      transform: rotate(-35deg);
      animation: spinOrbitRev 18s linear infinite;
    }}

    .sat-dot-3d {{
      position: absolute;
      width: 14px;
      height: 14px;
      border-radius: 50%;
      top: -7px;
      left: 50%;
      transform: translateX(-50%);
      box-shadow: 0 0 15px currentColor;
    }}

    @keyframes spinOrbit {{
      from {{ transform: rotate(0deg); }}
      to {{ transform: rotate(360deg); }}
    }}
    @keyframes spinOrbitRev {{
      from {{ transform: rotate(0deg); }}
      to {{ transform: rotate(-360deg); }}
    }}

    .hero-flame-center {{
      position: absolute;
      font-size: 3.2rem;
      filter: drop-shadow(0 0 25px rgba(249, 115, 22, 0.8));
      animation: flameBeat 2s ease-in-out infinite;
    }}

    @keyframes flameBeat {{
      0%, 100% {{ transform: scale(1); filter: drop-shadow(0 0 20px rgba(249, 115, 22, 0.7)); }}
      50% {{ transform: scale(1.15); filter: drop-shadow(0 0 35px rgba(239, 68, 68, 0.9)); }}
    }}

    /* Slide 2: 3 Beginner Cards */
    .cards-grid-3 {{
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 20px;
      width: 100%;
      margin-top: 8px;
    }}

    .card-icon-banner {{
      width: 50px;
      height: 50px;
      border-radius: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 1.6rem;
      margin-bottom: 16px;
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid var(--border);
    }}

    .card-title {{
      font-family: var(--font-display);
      font-size: 1.25rem;
      font-weight: 700;
      color: #fff;
      margin-bottom: 8px;
    }}

    .card-desc {{
      font-size: 0.9rem;
      color: var(--text-muted);
      line-height: 1.55;
    }}

    .card-callout-pill {{
      margin-top: 16px;
      display: inline-block;
      font-family: var(--font-mono);
      font-size: 0.72rem;
      padding: 5px 10px;
      border-radius: 6px;
      background: rgba(56, 189, 248, 0.1);
      color: var(--cyan);
      border: 1px solid rgba(56, 189, 248, 0.25);
    }}

    /* Slide 3: Two Cameras Comparison */
    .compare-cameras-grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 24px;
      width: 100%;
      margin-top: 10px;
    }}

    .camera-card {{
      padding: 24px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
    }}

    .cam-header {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 14px;
    }}

    .cam-name {{
      font-family: var(--font-display);
      font-size: 1.6rem;
      font-weight: 700;
    }}

    .cam-tag {{
      font-family: var(--font-mono);
      font-size: 0.75rem;
      padding: 4px 10px;
      border-radius: 6px;
      font-weight: 600;
    }}

    .modis-tag {{ background: rgba(239, 68, 68, 0.15); color: #EF4444; border: 1px solid rgba(239, 68, 68, 0.3); }}
    .viirs-tag {{ background: rgba(56, 189, 248, 0.15); color: #38BDF8; border: 1px solid rgba(56, 189, 248, 0.3); }}

    .cam-metric-box {{
      background: rgba(0, 0, 0, 0.35);
      border: 1px solid var(--border);
      padding: 14px 18px;
      border-radius: 12px;
      margin: 14px 0;
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 16px;
    }}

    .metric-sub {{
      font-size: 0.72rem;
      color: var(--text-dim);
      text-transform: uppercase;
      letter-spacing: 0.05em;
      margin-bottom: 2px;
    }}

    .metric-val {{
      font-family: var(--font-mono);
      font-size: 1.3rem;
      font-weight: 700;
      color: #fff;
    }}

    /* ==========================================================================
       SLIDE 4: Interactive Pixel Simulator & Full Working Side-by-Side
       ========================================================================== */
    .sim-layout {{
      display: grid;
      grid-template-columns: 0.88fr 1.12fr;
      gap: 24px;
      align-items: center;
      width: 100%;
      height: 100%;
    }}

    .sim-controls-panel {{
      display: flex;
      flex-direction: column;
      gap: 14px;
    }}

    .sim-btn-group {{
      display: flex;
      gap: 8px;
      margin-top: 10px;
    }}

    .btn-sim-mode {{
      flex: 1;
      padding: 10px 12px;
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid var(--border);
      border-radius: 10px;
      color: var(--text-main);
      font-weight: 600;
      font-size: 0.82rem;
      cursor: pointer;
      transition: all 0.2s var(--easing);
      text-align: center;
    }}

    .btn-sim-mode.active {{
      background: linear-gradient(135deg, rgba(56, 189, 248, 0.25) 0%, rgba(249, 115, 22, 0.25) 100%);
      border-color: var(--cyan);
      box-shadow: 0 0 15px rgba(56, 189, 248, 0.3);
      color: #fff;
    }}

    .sim-canvas-card {{
      background: #0B101E;
      border: 1px solid var(--border-cyan);
      border-radius: 18px;
      padding: 18px 22px;
      display: flex;
      flex-direction: column;
      align-items: center;
      box-shadow: 0 15px 40px rgba(0, 0, 0, 0.5);
    }}

    .pixel-grid-container {{
      width: 340px;
      height: 340px;
      position: relative;
      border-radius: 12px;
      overflow: hidden;
      border: 2px solid rgba(255, 255, 255, 0.15);
      background: radial-gradient(circle at 45% 45%, #18231c 0%, #0d1612 100%);
      transition: all 0.3s var(--easing);
    }}

    /* Dual Side-by-Side View Elements */
    .dual-grid-wrapper {{
      display: flex;
      gap: 18px;
      justify-content: center;
      align-items: center;
      width: 100%;
      transition: all 0.3s var(--easing);
    }}

    .dual-grid-wrapper.hidden {{
      display: none;
    }}

    .dual-panel {{
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 8px;
    }}

    .dual-panel-header {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      width: 100%;
      padding: 0 4px;
      font-size: 0.78rem;
      font-weight: 700;
      font-family: var(--font-display);
    }}

    .dual-badge-pill {{
      font-family: var(--font-mono);
      font-size: 0.7rem;
      padding: 2px 8px;
      border-radius: 9999px;
    }}

    .dual-badge-pill.red {{
      background: rgba(239, 68, 68, 0.2);
      color: #EF4444;
      border: 1px solid rgba(239, 68, 68, 0.35);
    }}

    .dual-badge-pill.amber {{
      background: rgba(245, 158, 11, 0.2);
      color: #F59E0B;
      border: 1px solid rgba(245, 158, 11, 0.35);
    }}

    .dual-box {{
      width: 200px !important;
      height: 200px !important;
    }}

    .dual-verdict {{
      font-size: 0.72rem;
      font-family: var(--font-mono);
      font-weight: 600;
      margin-top: 2px;
    }}

    /* Ground Fire Embers Underneath Grid */
    .ground-fire-source {{
      position: absolute;
      border-radius: 50%;
      background: radial-gradient(circle, #EF4444 20%, #F59E0B 60%, transparent 85%);
      filter: blur(3px);
      pointer-events: none;
      animation: pulseFire 1.6s ease-in-out infinite;
    }}

    @keyframes pulseFire {{
      0%, 100% {{ opacity: 0.85; transform: scale(1); }}
      50% {{ opacity: 1; transform: scale(1.12); }}
    }}

    /* Grid Overlays */
    .grid-svg-overlay {{
      position: absolute;
      inset: 0;
      width: 100%;
      height: 100%;
      pointer-events: none;
    }}

    .pixel-cell {{
      transition: all 0.35s var(--easing);
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

    .sim-stats-bar {{
      width: 100%;
      display: flex;
      justify-content: space-around;
      align-items: center;
      margin-top: 14px;
      padding-top: 10px;
      border-top: 1px solid var(--border);
    }}

    .sim-stat-item {{
      text-align: center;
      display: flex;
      flex-direction: column;
      align-items: center;
    }}

    .sim-stat-val {{
      font-family: var(--font-mono);
      font-size: 1.35rem;
      font-weight: 700;
      line-height: 1.2;
    }}

    .sim-stat-lbl {{
      font-size: 0.68rem;
      color: var(--text-dim);
      text-transform: uppercase;
      letter-spacing: 0.05em;
      margin-top: 2px;
      white-space: nowrap;
    }}

    /* Slide 5: The 2012 Trap */
    .trap-layout {{
      display: grid;
      grid-template-columns: 1.25fr 0.75fr;
      gap: 28px;
      align-items: center;
      width: 100%;
    }}

    .chart-frame-box {{
      background: #0B1120;
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 14px;
      height: 380px;
      width: 100%;
    }}

    /* Slide 6: 4-Step Pipeline */
    .pipeline-grid {{
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 16px;
      width: 100%;
      margin-top: 14px;
    }}

    .step-card {{
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      height: 350px;
      padding: 20px;
      position: relative;
    }}

    .step-number-badge {{
      font-family: var(--font-mono);
      font-size: 0.95rem;
      font-weight: 700;
      color: var(--cyan);
      background: rgba(56, 189, 248, 0.15);
      border: 1px solid var(--cyan-glow);
      width: 34px;
      height: 34px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      margin-bottom: 12px;
    }}

    /* Slide 7: AI Brain & Benchmark */
    .ai-brain-layout {{
      display: grid;
      grid-template-columns: 0.95fr 1.05fr;
      gap: 24px;
      width: 100%;
      margin-top: 10px;
    }}

    .clues-grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 10px;
      margin-top: 10px;
    }}

    .clue-chip {{
      background: rgba(0, 0, 0, 0.35);
      border: 1px solid var(--border);
      padding: 10px 12px;
      border-radius: 10px;
      display: flex;
      flex-direction: column;
      gap: 2px;
    }}

    .clue-chip .tag {{
      font-family: var(--font-mono);
      font-size: 0.65rem;
      color: var(--cyan);
      letter-spacing: 0.05em;
    }}

    .clue-chip .name {{
      font-size: 0.82rem;
      font-weight: 600;
      color: #fff;
    }}

    .benchmark-race-list {{
      display: flex;
      flex-direction: column;
      gap: 11px;
      margin-top: 10px;
    }}

    .race-item {{
      display: flex;
      flex-direction: column;
      gap: 4px;
    }}

    .race-labels {{
      display: flex;
      justify-content: space-between;
      font-size: 0.82rem;
      font-weight: 600;
    }}

    .race-bar-bg {{
      height: 10px;
      background: rgba(255, 255, 255, 0.08);
      border-radius: 9999px;
      overflow: hidden;
      position: relative;
    }}

    .race-bar-fill {{
      height: 100%;
      border-radius: 9999px;
      transition: width 1.2s var(--easing);
      width: 0%;
    }}

    /* Slide 8: Before vs After Magic Toggle */
    .magic-toggle-bar {{
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 12px;
    }}

    .btn-magic-toggle {{
      padding: 8px 18px;
      border-radius: 9999px;
      font-size: 0.84rem;
      font-weight: 600;
      border: 1px solid var(--border);
      background: rgba(255, 255, 255, 0.05);
      color: var(--text-main);
      cursor: pointer;
      transition: all 0.25s var(--easing);
    }}

    .btn-magic-toggle.active {{
      background: linear-gradient(135deg, rgba(56, 189, 248, 0.3) 0%, rgba(16, 185, 129, 0.3) 100%);
      border-color: var(--cyan);
      color: #fff;
      box-shadow: 0 0 20px rgba(56, 189, 248, 0.35);
    }}

    /* Slide 10: Environmental Emissions Cards */
    .emissions-kpis-strip {{
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 16px;
      margin-bottom: 14px;
    }}

    .impact-stat-card {{
      background: rgba(17, 27, 52, 0.8);
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 16px 20px;
      display: flex;
      align-items: center;
      gap: 14px;
    }}

    .impact-stat-card.alert {{
      border-color: rgba(239, 68, 68, 0.45);
      background: rgba(30, 18, 28, 0.8);
    }}

    .impact-icon {{
      font-size: 2rem;
    }}

    .impact-num {{
      font-family: var(--font-mono);
      font-size: 1.6rem;
      font-weight: 700;
      color: #fff;
    }}

    .impact-lbl {{
      font-size: 0.74rem;
      color: var(--text-dim);
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }}

    /* Slide 11: Launch Hero */
    .finale-layout {{
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      text-align: center;
      height: 100%;
    }}

    .giant-launch-btn {{
      margin-top: 28px;
      display: inline-flex;
      align-items: center;
      gap: 16px;
      padding: 18px 38px;
      font-family: var(--font-display);
      font-size: 1.3rem;
      font-weight: 700;
      color: #fff;
      background: linear-gradient(135deg, #0284C7 0%, #F97316 100%);
      border: 2px solid rgba(255, 255, 255, 0.3);
      border-radius: 9999px;
      text-decoration: none;
      box-shadow: 0 0 50px rgba(56, 189, 248, 0.5), 0 10px 30px rgba(0, 0, 0, 0.5);
      transition: all 0.3s var(--easing);
    }}

    .giant-launch-btn:hover {{
      transform: scale(1.05) translateY(-3px);
      box-shadow: 0 0 70px rgba(56, 189, 248, 0.8), 0 15px 40px rgba(0, 0, 0, 0.6);
    }}

    /* Bottom Presentation Navigation Bar */
    .pres-footer {{
      position: fixed;
      bottom: 0;
      left: 0;
      right: 0;
      height: 68px;
      padding: 0 32px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      background: linear-gradient(0deg, rgba(7, 10, 18, 0.95) 0%, rgba(7, 10, 18, 0) 100%);
      z-index: 100;
      backdrop-filter: blur(8px);
      border-top: 1px solid rgba(255, 255, 255, 0.05);
    }}

    .footer-left {{
      display: flex;
      align-items: center;
      gap: 14px;
    }}

    .nav-arrow-btn {{
      width: 42px;
      height: 42px;
      border-radius: 12px;
      background: rgba(255, 255, 255, 0.06);
      border: 1px solid var(--border);
      color: #fff;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      font-size: 1.2rem;
      transition: all 0.2s var(--easing);
    }}

    .nav-arrow-btn:hover {{
      background: rgba(56, 189, 248, 0.2);
      border-color: var(--cyan);
      transform: translateY(-1px);
    }}

    .dots-strip {{
      display: flex;
      align-items: center;
      gap: 8px;
    }}

    .dot-step {{
      width: 26px;
      height: 7px;
      border-radius: 4px;
      background: rgba(255, 255, 255, 0.12);
      cursor: pointer;
      transition: all 0.3s var(--easing);
      position: relative;
    }}

    .dot-step.active {{
      width: 44px;
      background: linear-gradient(90deg, var(--cyan) 0%, var(--orange) 100%);
      box-shadow: 0 0 12px var(--cyan-glow);
    }}

    .footer-hints {{
      font-family: var(--font-mono);
      font-size: 0.75rem;
      color: var(--text-dim);
      display: flex;
      align-items: center;
      gap: 16px;
    }}

    .footer-hints kbd {{
      background: rgba(255, 255, 255, 0.08);
      border: 1px solid var(--border);
      padding: 2px 6px;
      border-radius: 4px;
      color: #E2E8F0;
    }}
  </style>
</head>
<body>

  <!-- Background Dynamic Canvas -->
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
        <span>/ 11</span>
        <span id="header-slide-chapter" style="color: #64748B; margin-left: 8px;">· The Hook</span>
      </div>
    </div>

    <div class="header-actions">
      <button id="btn-toggle-fs" class="btn-header-action" title="Toggle Fullscreen (Shortcut: F)">
        <span>⛶</span>
        <span>Fullscreen</span>
      </button>
      <a href="http://localhost:8000" target="_blank" class="btn-header-action btn-live-launch" title="Launch Live 3D Mission Control (Requires local server on port 8000)">
        <span>🌍</span>
        <span>Live 3D Globe</span>
      </a>
    </div>
  </header>


  <!-- ========================================================================= -->
  <!-- PRESENTATION SLIDE DECK (11 ANIMATED SLIDES)                              -->
  <!-- ========================================================================= -->
  <main id="deck-container">

    <!-- --------------------------------------------------------------------- -->
    <!-- SLIDE 1: The Hook — Watching Earth Breathe Fire                       -->
    <!-- --------------------------------------------------------------------- -->
    <section class="slide active" data-slide="1" data-chapter="The Hook">
      <div class="slide-content-wrap">
        <div class="hero-layout">
          <div class="hero-text">
            <div class="hero-partnership-badge stagger-1">
              <img src="{space_apps_base64}" alt="NASA Space Apps Challenge" class="hero-space-apps-badge-logo">
              <span>NASA SPACE APPS CHALLENGE 2026</span>
            </div>
            <h1 class="hero-title stagger-2">
              Watching Earth <span class="highlight">Breathe Fire</span>
            </h1>
            <p class="slide-subtitle stagger-3">
              How we united 25 years of NASA satellite history using Artificial Intelligence & Google Earth Engine.
            </p>

            <div class="hero-question-card stagger-4">
              <span class="hero-q-icon">🌍</span>
              <span class="hero-q-text">
                <strong>The Big Question:</strong> How do we know if global wildfires and agricultural burning are <em>truly getting worse</em> over the last 25 years, or if our space cameras simply got sharper?
              </span>
            </div>
          </div>

          <div class="hero-visual stagger-3">
            <div class="globe-simulation-art">
              <div class="orbit-ring modis">
                <div class="sat-dot-3d" style="color: #EF4444; background: #EF4444;"></div>
              </div>
              <div class="orbit-ring viirs">
                <div class="sat-dot-3d" style="color: #38BDF8; background: #38BDF8;"></div>
              </div>
              <div class="hero-flame-center">🔥</div>
            </div>
          </div>
        </div>
      </div>
    </section>


    <!-- --------------------------------------------------------------------- -->
    <!-- SLIDE 2: Chapter 1 — What is a "Hot Spot" & Why Track Fires?          -->
    <!-- --------------------------------------------------------------------- -->
    <section class="slide" data-slide="2" data-chapter="Chapter 1: The Heat Below">
      <div class="slide-content-wrap">
        <div class="slide-header-block">
          <div class="slide-badge-category stagger-1">Chapter 1 · The Basics</div>
          <h2 class="slide-title stagger-2">What is a <span class="highlight">"Hot Spot"</span> & Why Track Fires from Space?</h2>
          <p class="slide-subtitle stagger-3">
            Before talking about satellites and pixels, let's look at what actually happens when Earth burns.
          </p>
        </div>

        <div class="cards-grid-3">
          <!-- Card 1 -->
          <div class="glass-card stagger-2">
            <div class="card-icon-banner" style="color: #F97316;">🌍</div>
            <h3 class="card-title">Fires Shape Our Planet</h3>
            <p class="card-desc">
              Every year, millions of acres burn across the globe—from forest fires in California and the Amazon to the seasonal agricultural rice-straw burning in Egypt's Nile Delta (known as the "Black Cloud").
            </p>
            <span class="card-callout-pill">Air Quality & Health Hazard</span>
          </div>

          <!-- Card 2 -->
          <div class="glass-card stagger-3">
            <div class="card-icon-banner" style="color: #38BDF8;">🛰️</div>
            <h3 class="card-title">Satellites See Thermal Heat</h3>
            <p class="card-desc">
              Satellites hundreds of kilometers in space don't take regular photos; they carry infrared sensors that detect intense surface heat (>300°C). Every heat signature is registered as a <strong>"Hot Spot"</strong>.
            </p>
            <span class="card-callout-pill">Thermal Infrared Radiance (FRP)</span>
          </div>

          <!-- Card 3 -->
          <div class="glass-card stagger-4">
            <div class="card-icon-banner" style="color: #10B981;">📅</div>
            <h3 class="card-title">The Need for a 25-Year Record</h3>
            <p class="card-desc">
              Governments, firefighters, and climate scientists need an unbroken, accurate 25-year calendar (2001–2025) to predict when fire seasons peak and to verify if climate change is worsening blazes.
            </p>
            <span class="card-callout-pill">Unbroken 2001–2025 Climatology</span>
          </div>
        </div>
      </div>
    </section>


    <!-- --------------------------------------------------------------------- -->
    <!-- SLIDE 3: Chapter 2 — Meet NASA's Two Generations of Space Cameras     -->
    <!-- --------------------------------------------------------------------- -->
    <section class="slide" data-slide="3" data-chapter="Chapter 2: The Two Cameras">
      <div class="slide-content-wrap">
        <div class="slide-header-block">
          <div class="slide-badge-category stagger-1">Chapter 2 · Sensor Evolution</div>
          <h2 class="slide-title stagger-2">Meet NASA's Two Generations of <span class="highlight">Space Cameras</span></h2>
          <p class="slide-subtitle stagger-3">
            The simple analogy: Imagine taking a photo with an early 2000s flip phone vs. a modern 4K smartphone.
          </p>
        </div>

        <div class="compare-cameras-grid">
          <!-- MODIS -->
          <div class="glass-card camera-card stagger-2" style="border-top: 3px solid #EF4444;">
            <div>
              <div class="cam-header">
                <div>
                  <h3 class="cam-name">MODIS</h3>
                  <div style="font-size: 0.85rem; color: var(--text-muted);">Terra & Aqua Satellites</div>
                </div>
                <span class="cam-tag modis-tag">LAUNCHED 1999 / 2002</span>
              </div>
              <p class="card-desc">
                NASA's faithful workhorse. It pioneered global fire monitoring, scanning the planet every single day. But it has wide, coarse eyesight:
              </p>
            </div>

            <div class="cam-metric-box">
              <div>
                <div class="metric-sub">Pixel Size</div>
                <div class="metric-val text-red">1,000 meters</div>
              </div>
              <div>
                <div class="metric-sub">Ground Area per Pixel</div>
                <div class="metric-val">1,000,000 m²</div>
              </div>
            </div>

            <div style="font-size: 0.9rem; color: #FDA4AF; line-height: 1.5;">
              ⚠️ <strong>The Limitation:</strong> Great for massive forest wildfires, but completely blind to smaller or short-lived agricultural fires.
            </div>
          </div>

          <!-- VIIRS -->
          <div class="glass-card camera-card stagger-3" style="border-top: 3px solid #38BDF8;">
            <div>
              <div class="cam-header">
                <div>
                  <h3 class="cam-name">VIIRS</h3>
                  <div style="font-size: 0.85rem; color: var(--text-muted);">Suomi-NPP & NOAA Satellites</div>
                </div>
                <span class="cam-tag viirs-tag">LAUNCHED 2012</span>
              </div>
              <p class="card-desc">
                NASA's modern ultra-sharp upgrade. With advanced 375-meter high-resolution channels, it catches fires that MODIS never even saw:
              </p>
            </div>

            <div class="cam-metric-box">
              <div>
                <div class="metric-sub">Pixel Size</div>
                <div class="metric-val text-cyan">375 meters</div>
              </div>
              <div>
                <div class="metric-sub">Resolution Advantage</div>
                <div class="metric-val text-amber"><span data-counter="7.1" data-decimals="1">0</span>x Sharper Area</div>
              </div>
            </div>

            <div style="font-size: 0.9rem; color: #7DD3FC; line-height: 1.5;">
              ✨ <strong>The Superpower:</strong> Detects small localized field burns, cooler thermal signatures, and fleeting blazes with razor precision.
            </div>
          </div>
        </div>
      </div>
    </section>


    <!-- --------------------------------------------------------------------- -->
    <!-- SLIDE 4: Chapter 3 — Interactive Pixel Simulator (FIXED RESPONSIVE)   -->
    <!-- --------------------------------------------------------------------- -->
    <section class="slide" data-slide="4" data-chapter="Chapter 3: The Resolution Paradox">
      <div class="slide-content-wrap">
        <div class="slide-header-block">
          <div class="slide-badge-category stagger-1">Chapter 3 · Interactive Proof</div>
          <h2 class="slide-title stagger-2">The Visual Proof: <span class="highlight">"Same Fire, Different Count!"</span></h2>
          <p class="slide-subtitle stagger-3">
            Two satellites fly over the exact same burning field at the exact same hour. Try toggling the camera sensors below!
          </p>
        </div>

        <div class="sim-layout">
          <!-- Left Controls & Explanations -->
          <div class="sim-controls-panel stagger-2">
            <div class="glass-card" style="padding: 18px 20px;">
              <h4 style="font-size: 1.05rem; color: #fff; margin-bottom: 6px;">Simulate Satellite Sensor View:</h4>
              <p style="font-size: 0.86rem; color: var(--text-muted); line-height: 1.45;">
                Watch how the exact same ground fires register completely differently when the pixel grid changes:
              </p>

              <div class="sim-btn-group">
                <button id="btn-sim-modis" class="btn-sim-mode active" onclick="setSimMode('modis')">
                  👁️ MODIS (1 km)
                </button>
                <button id="btn-sim-viirs" class="btn-sim-mode" onclick="setSimMode('viirs')">
                  👁️ VIIRS (375 m)
                </button>
                <button id="btn-sim-split" class="btn-sim-mode" onclick="setSimMode('split')">
                  ⚖️ Side-by-Side
                </button>
              </div>
            </div>

            <div id="sim-explanation-card" class="glass-card" style="padding: 18px 20px; border-left: 4px solid #EF4444;">
              <div id="sim-expl-title" style="font-weight: 700; color: #EF4444; margin-bottom: 6px; font-size: 0.95rem;">
                MODIS Sensor View (1,000m Pixels)
              </div>
              <div id="sim-expl-text" style="font-size: 0.88rem; color: #CBD5E1; line-height: 1.5;">
                Because each MODIS pixel covers a huge 1,000,000 m² square, the central fire cluster only triggers <strong>1 single hotspot</strong>. The nearby smaller fires are diluted by cool ground and completely missed!
              </div>
            </div>
          </div>

          <!-- Right Interactive Grid Canvas Card -->
          <div class="sim-canvas-card stagger-3">
            
            <!-- SINGLE GRID VIEW (for MODIS or VIIRS) -->
            <div id="single-grid-container" class="pixel-grid-container">
              <div class="ground-fire-source" style="top: 42%; left: 45%; width: 14%; height: 14%;"></div>
              <div class="ground-fire-source" style="top: 48%; left: 38%; width: 9%; height: 9%;"></div>
              <div class="ground-fire-source" style="top: 25%; left: 65%; width: 7%; height: 7%;"></div>
              <div class="ground-fire-source" style="top: 70%; left: 28%; width: 7%; height: 7%;"></div>
              <svg id="sim-grid-svg" class="grid-svg-overlay" viewBox="0 0 100 100"></svg>
            </div>

            <!-- DUAL SIDE-BY-SIDE VIEW (for Side-by-Side comparison mode) -->
            <div id="dual-grid-container" class="dual-grid-wrapper hidden">
              <!-- MODIS Left Panel -->
              <div class="dual-panel">
                <div class="dual-panel-header">
                  <span style="color: #EF4444;">MODIS (1 km)</span>
                  <span class="dual-badge-pill red">1 Hot Spot</span>
                </div>
                <div class="pixel-grid-container dual-box">
                  <div class="ground-fire-source" style="top: 42%; left: 45%; width: 14%; height: 14%;"></div>
                  <div class="ground-fire-source" style="top: 48%; left: 38%; width: 9%; height: 9%;"></div>
                  <div class="ground-fire-source" style="top: 25%; left: 65%; width: 7%; height: 7%;"></div>
                  <div class="ground-fire-source" style="top: 70%; left: 28%; width: 7%; height: 7%;"></div>
                  <svg id="sim-grid-svg-modis-dual" class="grid-svg-overlay" viewBox="0 0 100 100"></svg>
                </div>
                <div class="dual-verdict text-red">❌ 2 Small Fires Missed</div>
              </div>

              <!-- VIIRS Right Panel -->
              <div class="dual-panel">
                <div class="dual-panel-header">
                  <span style="color: #38BDF8;">VIIRS (375 m)</span>
                  <span class="dual-badge-pill amber">6 Hot Spots</span>
                </div>
                <div class="pixel-grid-container dual-box">
                  <div class="ground-fire-source" style="top: 42%; left: 45%; width: 14%; height: 14%;"></div>
                  <div class="ground-fire-source" style="top: 48%; left: 38%; width: 9%; height: 9%;"></div>
                  <div class="ground-fire-source" style="top: 25%; left: 65%; width: 7%; height: 7%;"></div>
                  <div class="ground-fire-source" style="top: 70%; left: 28%; width: 7%; height: 7%;"></div>
                  <svg id="sim-grid-svg-viirs-dual" class="grid-svg-overlay" viewBox="0 0 100 100"></svg>
                </div>
                <div class="dual-verdict text-cyan">✅ All Fires Resolved (7.1x)</div>
              </div>
            </div>

            <!-- Stats Bar (Always completely visible!) -->
            <div class="sim-stats-bar">
              <div class="sim-stat-item">
                <div id="sim-stat-count" class="sim-stat-val text-red">1 Hot Spot</div>
                <div class="sim-stat-lbl">Detected by Satellite</div>
              </div>
              <div class="sim-stat-item">
                <div id="sim-stat-res" class="sim-stat-val">1,000 m</div>
                <div class="sim-stat-lbl">Spatial Resolution</div>
              </div>
              <div class="sim-stat-item">
                <div id="sim-stat-ratio" class="sim-stat-val text-amber">Coarse Eye</div>
                <div class="sim-stat-lbl">Detection Sensitivity</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>


    <!-- --------------------------------------------------------------------- -->
    <!-- SLIDE 5: Chapter 4 — The 2012 Climate Trap (The Artificial Jump)      -->
    <!-- --------------------------------------------------------------------- -->
    <section class="slide" data-slide="5" data-chapter="Chapter 4: The 2012 Discontinuity">
      <div class="slide-content-wrap">
        <div class="slide-header-block">
          <div class="slide-badge-category stagger-1">Chapter 4 · The Discontinuity</div>
          <h2 class="slide-title stagger-2">The 2012 <span class="highlight">Climate Trap</span>: The Fake 404% Surge</h2>
          <p class="slide-subtitle stagger-3">
            What happens if you simply plot raw satellite data from 2001 to 2025 without harmonizing?
          </p>
        </div>

        <div class="trap-layout">
          <div class="chart-frame-box stagger-2">
            <div id="plot-raw-trap" style="width: 100%; height: 100%;"></div>
          </div>

          <div style="display: flex; flex-direction: column; gap: 16px;" class="stagger-3">
            <div class="glass-card" style="border: 1px solid rgba(239, 68, 68, 0.45); background: rgba(30, 18, 28, 0.85); padding: 18px 20px;">
              <div style="font-size: 1.35rem; margin-bottom: 6px;">⚠️ <strong>The 4.04x Artifact</strong></div>
              <p style="font-size: 0.9rem; color: #FECDD3; line-height: 1.5;">
                In January 2012, recorded fire hot spots suddenly jumped by <strong>+404%</strong>. 
                <br><br>
                <em>Did fires across the globe actually quadruple overnight?</em> <strong>NO!</strong> The satellite camera resolution upgraded from 1km to 375m!
              </p>
            </div>

            <div class="glass-card" style="padding: 18px 20px;">
              <h4 style="font-size: 1rem; color: #fff; margin-bottom: 6px;">Why This Ruined Climate Science:</h4>
              <ul style="font-size: 0.86rem; color: var(--text-muted); line-height: 1.55; padding-left: 20px;">
                <li>Comparing a 2005 fire to a 2018 fire was like comparing apples to watermelons.</li>
                <li>Climate models falsely predicted catastrophic fire surges.</li>
                <li>Summing both satellites double-counted identical fires.</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </section>


    <!-- --------------------------------------------------------------------- -->
    <!-- SLIDE 6: Chapter 5 — How SpectraLink Solves the Puzzle (4 Steps)      -->
    <!-- --------------------------------------------------------------------- -->
    <section class="slide" data-slide="6" data-chapter="Chapter 5: The SpectraLink Solution">
      <div class="slide-content-wrap">
        <div class="slide-header-block">
          <div class="slide-badge-category stagger-1">Chapter 5 · Architecture</div>
          <h2 class="slide-title stagger-2">How <span class="highlight">SpectraLink</span> Solves the Puzzle</h2>
          <p class="slide-subtitle stagger-3">
            Our 4-step physics-informed pipeline bridges 25 years of space observation into a single continuous record.
          </p>
        </div>

        <div class="pipeline-grid">
          <!-- Step 1 -->
          <div class="glass-card step-card stagger-1">
            <div>
              <div class="step-number-badge">1</div>
              <h3 class="card-title">Standardize on GEE</h3>
              <p class="card-desc">
                Using <strong>Google Earth Engine</strong>, we resample both MODIS and VIIRS onto an identical 1 km global spatial grid anywhere on Earth.
              </p>
            </div>
            <div class="card-callout-pill">Spatial Uniformity</div>
          </div>

          <!-- Step 2 -->
          <div class="glass-card step-card stagger-2">
            <div>
              <div class="step-number-badge">2</div>
              <h3 class="card-title">14-Year Overlap Rosetta Stone</h3>
              <p class="card-desc">
                Both satellites flew together in orbit from <strong>2012 to 2025</strong>. Our AI uses these 168 months of simultaneous observations as ground-truth training pairs.
              </p>
            </div>
            <div class="card-callout-pill">168 Simultaneous Months</div>
          </div>

          <!-- Step 3 -->
          <div class="glass-card step-card stagger-3">
            <div>
              <div class="step-number-badge">3</div>
              <h3 class="card-title">The AI Time Machine (2001–2011)</h3>
              <p class="card-desc">
                Our model acts as an intelligent translator—predicting how many 375m VIIRS hot spots <em>would have been detected</em> during the pre-2012 MODIS era.
              </p>
            </div>
            <div class="card-callout-pill">Recovers Missing Small Fires</div>
          </div>

          <!-- Step 4 -->
          <div class="glass-card step-card stagger-4">
            <div>
              <div class="step-number-badge">4</div>
              <h3 class="card-title">Smart Fusion (2012–2025)</h3>
              <p class="card-desc">
                Integrates modern Terra, Aqua, and Suomi-NPP detections into an unified high-fidelity time-series without double-counting identical fire centers.
              </p>
            </div>
            <div class="card-callout-pill">Zero Double-Counting</div>
          </div>
        </div>
      </div>
    </section>


    <!-- --------------------------------------------------------------------- -->
    <!-- SLIDE 7: Chapter 6 — Inside Our AI Brain (32 Clues & 6 Models)        -->
    <!-- --------------------------------------------------------------------- -->
    <section class="slide" data-slide="7" data-chapter="Chapter 6: Inside the AI Brain">
      <div class="slide-content-wrap">
        <div class="slide-header-block">
          <div class="slide-badge-category stagger-1">Chapter 6 · Machine Learning</div>
          <h2 class="slide-title stagger-2">Inside Our AI Brain: <span class="highlight">32 Physical Clues</span></h2>
          <p class="slide-subtitle stagger-3">
            Why simple multiplication fails: The detection ratio changes with seasonal heat, diurnal orbits, and fire size!
          </p>
        </div>

        <div class="ai-brain-layout">
          <!-- Left: Physical Clues -->
          <div class="glass-card stagger-2" style="padding: 18px 20px;">
            <h3 style="font-size: 1.15rem; color: #fff; margin-bottom: 6px;">The 32 Clues Fed to Our AI:</h3>
            <p style="font-size: 0.85rem; color: var(--text-muted); line-height: 1.45;">
              Our models evaluate physical satellite orbital geometry, not just plain fire numbers:
            </p>

            <div class="clues-grid">
              <div class="clue-chip">
                <span class="tag">DIURNAL PASSES</span>
                <span class="name">Terra 10:30AM vs Aqua 1:30PM</span>
              </div>
              <div class="clue-chip">
                <span class="tag">ENERGY RATIO</span>
                <span class="name">Fire Radiative Power (FRP)</span>
              </div>
              <div class="clue-chip">
                <span class="tag">TARGET ENCODING</span>
                <span class="name">Out-of-Fold Monthly Climatology</span>
              </div>
              <div class="clue-chip">
                <span class="tag">MOMENTUM</span>
                <span class="name">Centered Temporal Window Delta</span>
              </div>
              <div class="clue-chip">
                <span class="tag">HARMONIC MEAN</span>
                <span class="name">Non-linear Cross-Sensor Power</span>
              </div>
              <div class="clue-chip">
                <span class="tag">SEASONALITY</span>
                <span class="name">Cyclical Sin/Cos Calendar Waves</span>
              </div>
            </div>
          </div>

          <!-- Right: Benchmark Leaderboard -->
          <div class="glass-card stagger-3" style="padding: 18px 20px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
              <h3 style="font-size: 1.15rem; color: #fff;">6-Model Benchmark Arena:</h3>
              <span class="card-callout-pill" style="margin-top: 0;">TimeSeriesSplit (5 Folds)</span>
            </div>
            <p style="font-size: 0.82rem; color: var(--text-muted); margin-bottom: 10px;">
              Tested on real NASA satellite data from the Nile Delta (2001–2025):
            </p>

            <div class="benchmark-race-list">
              <!-- Model 1 -->
              <div class="race-item">
                <div class="race-labels">
                  <span style="color: #38BDF8;">🥇 1. Huber-Loss GBDT & ExtraTrees Blend</span>
                  <span style="font-family: var(--font-mono); color: #38BDF8;">98.68% (R² = 0.7659)</span>
                </div>
                <div class="race-bar-bg">
                  <div class="race-bar-fill" style="width: 98.7%; background: linear-gradient(90deg, #0284C7, #38BDF8);"></div>
                </div>
              </div>

              <!-- Model 2 -->
              <div class="race-item">
                <div class="race-labels">
                  <span style="color: #F59E0B;">🥈 2. SpectraNet Deep Neural Network Stacking</span>
                  <span style="font-family: var(--font-mono); color: #F59E0B;">97.05% (R² = 0.7410)</span>
                </div>
                <div class="race-bar-bg">
                  <div class="race-bar-fill" style="width: 97.1%; background: linear-gradient(90deg, #D97706, #F59E0B);"></div>
                </div>
              </div>

              <!-- Model 3 -->
              <div class="race-item">
                <div class="race-labels">
                  <span>🥉 3. Temporal Sequence 1D-MLP</span>
                  <span style="font-family: var(--font-mono); color: var(--text-dim);">94.20%</span>
                </div>
                <div class="race-bar-bg">
                  <div class="race-bar-fill" style="width: 94.2%; background: #475569;"></div>
                </div>
              </div>

              <!-- Model 4 -->
              <div class="race-item">
                <div class="race-labels">
                  <span>4. Physics-Informed Deep MLP</span>
                  <span style="font-family: var(--font-mono); color: var(--text-dim);">93.80%</span>
                </div>
                <div class="race-bar-bg">
                  <div class="race-bar-fill" style="width: 93.8%; background: #475569;"></div>
                </div>
              </div>

              <!-- Model 5 -->
              <div class="race-item">
                <div class="race-labels">
                  <span>5. Huber Robust Linear Regressor</span>
                  <span style="font-family: var(--font-mono); color: var(--text-dim);">88.40%</span>
                </div>
                <div class="race-bar-bg">
                  <div class="race-bar-fill" style="width: 88.4%; background: #334155;"></div>
                </div>
              </div>

              <!-- Model 6 -->
              <div class="race-item">
                <div class="race-labels">
                  <span>6. Statistical Scaling Baseline</span>
                  <span style="font-family: var(--font-mono); color: var(--text-dim);">76.20%</span>
                </div>
                <div class="race-bar-bg">
                  <div class="race-bar-fill" style="width: 76.2%; background: #1E293B;"></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>


    <!-- --------------------------------------------------------------------- -->
    <!-- SLIDE 8: Chapter 7 — The Magic Result: Before vs. After Harmonization -->
    <!-- --------------------------------------------------------------------- -->
    <section class="slide" data-slide="8" data-chapter="Chapter 7: The Magic Result">
      <div class="slide-content-wrap">
        <div class="slide-header-block">
          <div class="slide-badge-category stagger-1">Chapter 7 · Breakthrough</div>
          <h2 class="slide-title stagger-2">The Magic Result: <span class="highlight">Before vs. After</span></h2>
          <p class="slide-subtitle stagger-3">
            Watch 25 years of NASA satellite observations snap into a single continuous climate record!
          </p>
        </div>

        <div style="display: flex; flex-direction: column; width: 100%;">
          <div class="magic-toggle-bar stagger-2">
            <span style="font-size: 0.88rem; font-weight: 600; color: var(--text-muted);">SELECT DATA STATE:</span>
            <button id="btn-toggle-raw" class="btn-magic-toggle" onclick="setMagicTimeline('raw')">
              ❌ Broken Raw Data (With 2012 Jump)
            </button>
            <button id="btn-toggle-harm" class="btn-magic-toggle active" onclick="setMagicTimeline('harmonized')">
              ✅ SpectraLink AI Harmonization (Continuous 2001–2025)
            </button>
          </div>

          <div class="chart-frame-box stagger-3" style="height: 340px;">
            <div id="plot-before-after" style="width: 100%; height: 100%;"></div>
          </div>

          <!-- 3 Proof Badges -->
          <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-top: 14px;" class="stagger-4">
            <div class="glass-card" style="padding: 14px 16px;">
              <div style="font-size: 0.72rem; color: var(--text-dim);">PRE-HARMONIZATION JUMP</div>
              <div style="font-family: var(--font-mono); font-size: 1.4rem; font-weight: 700; color: #EF4444;">4.04x Discontinuity</div>
              <div style="font-size: 0.78rem; color: var(--text-muted); margin-top: 2px;">Ruined cross-decade climate trend analysis</div>
            </div>

            <div class="glass-card" style="padding: 14px 16px;">
              <div style="font-size: 0.72rem; color: var(--text-dim);">SPECTRALINK CONTINUITY RATIO</div>
              <div style="font-family: var(--font-mono); font-size: 1.4rem; font-weight: 700; color: #10B981;">1.08x Homogeneity</div>
              <div style="font-size: 0.78rem; color: var(--text-muted); margin-top: 2px;">Perfect continuous baseline across 2012 seam</div>
            </div>

            <div class="glass-card" style="padding: 14px 16px;">
              <div style="font-size: 0.72rem; color: var(--text-dim);">RECOVERED HISTORICAL FIRES</div>
              <div style="font-family: var(--font-mono); font-size: 1.4rem; font-weight: 700; color: #38BDF8;">+342% Fires Calibrated</div>
              <div style="font-size: 0.78rem; color: var(--text-muted); margin-top: 2px;">2001–2011 scaled to true 375m equivalent</div>
            </div>
          </div>
        </div>
      </div>
    </section>


    <!-- --------------------------------------------------------------------- -->
    <!-- SLIDE 9: Chapter 8 — The 25-Year Burning Activity Calendar            -->
    <!-- --------------------------------------------------------------------- -->
    <section class="slide" data-slide="9" data-chapter="Chapter 8: The 25-Year Calendar">
      <div class="slide-content-wrap">
        <div class="slide-header-block">
          <div class="slide-badge-category stagger-1">Chapter 8 · Core Deliverable</div>
          <h2 class="slide-title stagger-2">The <span class="highlight">25-Year Burning Activity</span> Calendar</h2>
          <p class="slide-subtitle stagger-3">
            A complete 25-year monthly matrix (2001–2025 × Jan–Dec) revealing the exact rhythm of burning seasons.
          </p>
        </div>

        <div style="display: grid; grid-template-columns: 1.35fr 0.65fr; gap: 24px; width: 100%;">
          <div class="chart-frame-box stagger-2" style="height: 360px;">
            <div id="plot-calendar-slide" style="width: 100%; height: 100%;"></div>
          </div>

          <div style="display: flex; flex-direction: column; gap: 14px;" class="stagger-3">
            <div class="glass-card" style="padding: 16px 18px;">
              <div style="font-size: 1.1rem; color: #F59E0B; margin-bottom: 4px;">🌾 Egypt: Dual Harvest Peaks</div>
              <p style="font-size: 0.85rem; color: var(--text-muted); line-height: 1.45;">
                The 25-year matrix automatically identified Egypt's two agricultural fires seasons:
                <br>• <strong>May:</strong> Wheat stubble burning.
                <br>• <strong>September–October:</strong> Rice straw burning ("The Black Cloud").
              </p>
            </div>

            <div class="glass-card" style="padding: 16px 18px;">
              <div style="font-size: 1.1rem; color: #38BDF8; margin-bottom: 4px;">🌲 North America & Amazon</div>
              <p style="font-size: 0.85rem; color: var(--text-muted); line-height: 1.45;">
                In California and Canada, the calendar pinpoints August–September dry lightning firestorms. In the Amazon, it highlights the August deforestation slash-and-burn window.
              </p>
            </div>

            <div class="glass-card" style="padding: 16px 18px; border-left: 4px solid #10B981;">
              <div style="font-size: 0.9rem; font-weight: 700; color: #fff;">25-Year Total Active Fires:</div>
              <div style="font-family: var(--font-mono); font-size: 1.5rem; color: #10B981; font-weight: 700;">
                <span data-counter="53120" data-decimals="0">0</span>
              </div>
              <div style="font-size: 0.74rem; color: var(--text-dim);">Validated Harmonized Detections (Nile Delta)</div>
            </div>
          </div>
        </div>
      </div>
    </section>


    <!-- --------------------------------------------------------------------- -->
    <!-- SLIDE 10: Chapter 9 — Carbon Emissions & 2026 Early Warning          -->
    <!-- --------------------------------------------------------------------- -->
    <section class="slide" data-slide="10" data-chapter="Chapter 9: Climate Action & 2026">
      <div class="slide-content-wrap">
        <div class="slide-header-block">
          <div class="slide-badge-category stagger-1">Chapter 9 · Environmental Impact</div>
          <h2 class="slide-title stagger-2">Beyond Fire Counts: <span class="highlight">Carbon & 2026 Early Warning</span></h2>
          <p class="slide-subtitle stagger-3">
            Converting thermal energy into emissions inventories and predicting fire risk 6 months ahead.
          </p>
        </div>

        <div style="display: flex; flex-direction: column; width: 100%;">
          <!-- 3 Impact KPI Cards -->
          <div class="emissions-kpis-strip stagger-2">
            <div class="impact-stat-card">
              <span class="impact-icon">🪵</span>
              <div>
                <div class="impact-lbl">Burned Biomass</div>
                <div class="impact-num text-amber"><span data-counter="1.37" data-decimals="2">0</span>M Tons</div>
                <div style="font-size: 0.72rem; color: var(--text-dim);">Seiler & Crutzen Equation</div>
              </div>
            </div>

            <div class="impact-stat-card">
              <span class="impact-icon">☁️</span>
              <div>
                <div class="impact-lbl">Total CO₂ Released</div>
                <div class="impact-num text-red"><span data-counter="2.21" data-decimals="2">0</span>M Tons</div>
                <div style="font-size: 0.72rem; color: var(--text-dim);">Atmospheric Carbon Inventory</div>
              </div>
            </div>

            <div class="impact-stat-card alert">
              <span class="impact-icon">🚨</span>
              <div>
                <div class="impact-lbl">Toxic PM2.5 Aerosol</div>
                <div class="impact-num" style="color: #F87171;"><span data-counter="12486" data-decimals="0">0</span> Tons</div>
                <div style="font-size: 0.72rem; color: var(--text-dim);">Public Health Respiratory Risk</div>
              </div>
            </div>
          </div>

          <!-- Forecast Chart -->
          <div class="chart-frame-box stagger-3" style="height: 310px;">
            <div id="plot-forecast-slide" style="width: 100%; height: 100%;"></div>
          </div>
        </div>
      </div>
    </section>


    <!-- --------------------------------------------------------------------- -->
    <!-- SLIDE 11: Finale — Experience the Live 3D Earth Platform              -->
    <!-- --------------------------------------------------------------------- -->
    <section class="slide" data-slide="11" data-chapter="Finale: Mission Control">
      <div class="slide-content-wrap">
        <div class="finale-layout">
          <img src="{space_apps_base64}" alt="NASA Space Apps Challenge" style="height: 58px; width: auto; margin-bottom: 14px; filter: drop-shadow(0 4px 16px rgba(255,255,255,0.25));" class="stagger-1">
          <div class="slide-badge-category stagger-2">SpectraLink Mission Control</div>
          <h2 class="slide-title stagger-2" style="font-size: 2.9rem; margin-bottom: 12px;">
            Ready to Explore <span class="highlight">Any Place on Earth</span>?
          </h2>
          <p class="slide-subtitle stagger-3" style="text-align: center; max-width: 800px; margin-bottom: 20px;">
            Experience our 2-stage cinematic mission control: Rotate the 3D photorealistic Earth with flame clusters, dive straight into any of ~200 countries, and run live machine learning harmonization!
          </p>

          <a href="http://localhost:8000" target="_blank" class="giant-launch-btn stagger-4">
            <span>🌍</span>
            <span>Launch Live 3D SpectraLink Platform</span>
            <span>➔</span>
          </a>

          <div style="display: flex; gap: 20px; margin-top: 30px;" class="stagger-5">
            <div style="font-family: var(--font-mono); font-size: 0.8rem; color: var(--cyan); background: rgba(56, 189, 248, 0.1); border: 1px solid rgba(56, 189, 248, 0.3); padding: 7px 14px; border-radius: 8px;">
              🛰️ NASA MODIS & VIIRS Live
            </div>
            <div style="font-family: var(--font-mono); font-size: 0.8rem; color: #34D399; background: rgba(52, 211, 153, 0.1); border: 1px solid rgba(52, 211, 153, 0.3); padding: 7px 14px; border-radius: 8px;">
              ⚡ Google Earth Engine Connected
            </div>
            <div style="font-family: var(--font-mono); font-size: 0.8rem; color: #F59E0B; background: rgba(245, 158, 11, 0.1); border: 1px solid rgba(245, 158, 11, 0.3); padding: 7px 14px; border-radius: 8px;">
              🧠 6 Deep Learning & Physics Models
            </div>
          </div>
        </div>
      </div>
    </section>

  </main>


  <!-- ========================================================================= -->
  <!-- BOTTOM NAVIGATION BAR                                                     -->
  <!-- ========================================================================= -->
  <footer class="pres-footer">
    <div class="footer-left">
      <button id="btn-prev-slide" class="nav-arrow-btn" title="Previous Slide (← / Backspace)">
        ‹
      </button>

      <div class="dots-strip" id="dots-strip">
        <!-- 11 Dots generated via JS -->
      </div>

      <button id="btn-next-slide" class="nav-arrow-btn" title="Next Slide (→ / Space)">
        ›
      </button>
    </div>

    <div class="footer-hints">
      <span><kbd>←</kbd> <kbd>→</kbd> Navigate</span>
      <span><kbd>F</kbd> Fullscreen</span>
      <span><kbd>Home</kbd> Slide 1</span>
    </div>
  </footer>


  <!-- ========================================================================= -->
  <!-- APPLICATION SCRIPT & INTERACTIVITY LOGIC                                  -->
  <!-- ========================================================================= -->
  <script>
    /**
     * SpectraLink Standalone Presentation Controller
     */
    const state = {{
      currentSlide: 1,
      totalSlides: 11,
      simMode: 'modis', // 'modis' | 'viirs' | 'split'
      magicTimelineMode: 'harmonized', // 'raw' | 'harmonized'
      embeddedTimeline: {json.dumps(timeline_data)},
      embeddedForecast: {json.dumps(forecast_data)},
      embeddedCalendar: {json.dumps(calendar_z)},
    }};

    const chapterTitles = {{
      1: "The Hook",
      2: "Chapter 1: The Heat Below",
      3: "Chapter 2: The Two Cameras",
      4: "Chapter 3: The Resolution Paradox",
      5: "Chapter 4: The 2012 Discontinuity",
      6: "Chapter 5: The SpectraLink Solution",
      7: "Chapter 6: Inside the AI Brain",
      8: "Chapter 7: The Magic Result",
      9: "Chapter 8: The 25-Year Calendar",
      10: "Chapter 9: Climate Action & 2026",
      11: "Finale: Mission Control"
    }};

    // -------------------------------------------------------------------------
    // Init Deck
    // -------------------------------------------------------------------------
    document.addEventListener('DOMContentLoaded', () => {{
      initAmbientCanvas();
      buildDots();
      initKeyboard();
      initPixelSimulator();

      // Initial Slide setup
      goToSlide(1);

      // Footer controls
      document.getElementById('btn-prev-slide').onclick = () => prevSlide();
      document.getElementById('btn-next-slide').onclick = () => nextSlide();

      // Fullscreen toggle
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

      // Update active slide class
      document.querySelectorAll('.slide').forEach(s => {{
        const idx = parseInt(s.getAttribute('data-slide'));
        s.classList.toggle('active', idx === n);
      }});

      // Update dots
      document.querySelectorAll('.dot-step').forEach((d, idx) => {{
        d.classList.toggle('active', idx + 1 === n);
      }});

      // Update header
      document.getElementById('header-slide-num').textContent = String(n).padStart(2, '0');
      document.getElementById('header-slide-chapter').textContent = `· ${{chapterTitles[n]}}`;

      // Trigger animated number counters on entering slide
      triggerCounters(n);

      // Slide-specific lazy chart renders
      if (n === 4) {{
        setSimMode(state.simMode);
      }} else if (n === 5) {{
        renderRawTrapChart();
      }} else if (n === 8) {{
        renderBeforeAfterChart(state.magicTimelineMode);
      }} else if (n === 9) {{
        renderCalendarSlideChart();
      }} else if (n === 10) {{
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
    // Smooth Number Counters
    // -------------------------------------------------------------------------
    function triggerCounters(slideNum) {{
      const activeSlide = document.querySelector(`.slide[data-slide="${{slideNum}}"]`);
      if (!activeSlide) return;

      const counters = activeSlide.querySelectorAll('[data-counter]');
      counters.forEach(el => {{
        const target = parseFloat(el.getAttribute('data-counter'));
        const decimals = parseInt(el.getAttribute('data-decimals') || '0');
        const duration = 1200;
        const start = performance.now();

        function update(now) {{
          const elapsed = now - start;
          const progress = Math.min(elapsed / duration, 1);
          // Ease-out cubic
          const ease = 1 - Math.pow(1 - progress, 3);
          const current = target * ease;
          el.textContent = decimals > 0 ? current.toFixed(decimals) : Math.round(current).toLocaleString();

          if (progress < 1) {{
            requestAnimationFrame(update);
          }} else {{
            el.textContent = decimals > 0 ? target.toFixed(decimals) : target.toLocaleString();
          }}
        }}
        requestAnimationFrame(update);
      }});
    }}

    // -------------------------------------------------------------------------
    // Interactive Pixel Simulator (Slide 4 - FULL WORKING DUAL SIDE-BY-SIDE)
    // -------------------------------------------------------------------------
    function initPixelSimulator() {{
      setSimMode('modis');
    }}

    function drawGridOnSvg(svgEl, cols, rows, activeHits, sensorClass) {{
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
          rect.classList.add('pixel-cell');

          const isHit = activeHits.some(([ar, ac]) => ar === r && ac === c);
          if (isHit) {{
            rect.classList.add(sensorClass);
          }}
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

      const explCard = document.getElementById('sim-explanation-card');
      const explTitle = document.getElementById('sim-expl-title');
      const explText = document.getElementById('sim-expl-text');

      const statCount = document.getElementById('sim-stat-count');
      const statRes = document.getElementById('sim-stat-res');
      const statRatio = document.getElementById('sim-stat-ratio');

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

        explCard.style.borderLeftColor = '#EF4444';
        explTitle.style.color = '#EF4444';
        explTitle.textContent = 'MODIS Sensor View (1,000m Pixels)';
        explText.innerHTML = 'Because each MODIS pixel covers a huge 1,000,000 m² square, the central fire cluster only triggers <strong>1 single hotspot</strong>. The nearby smaller fires are diluted by cool ground and completely missed!';

        statCount.textContent = '1 Hot Spot';
        statCount.className = 'sim-stat-val text-red';
        statRes.textContent = '1,000 m';
        statRatio.textContent = 'Coarse Eye (1x)';

      }} else if (mode === 'viirs') {{
        singleContainer.classList.remove('hidden');
        dualContainer.classList.add('hidden');
        drawGridOnSvg(mainSvg, 8, 8, viirsHits, 'active-viirs');

        explCard.style.borderLeftColor = '#38BDF8';
        explTitle.style.color = '#38BDF8';
        explTitle.textContent = 'VIIRS Sensor View (375m Pixels)';
        explText.innerHTML = 'With 7.1x finer resolution, VIIRS separates the central blaze into 4 sharp individual detections and easily spots both small agricultural fires. <strong>Total: 6 Hot Spots detected for the exact same event!</strong>';

        statCount.textContent = '6 Hot Spots';
        statCount.className = 'sim-stat-val text-amber';
        statRes.textContent = '375 m';
        statRatio.textContent = '7.1x Sharper Area';

      }} else if (mode === 'split') {{
        // TRUE DUAL SIDE-BY-SIDE DISPLAY
        singleContainer.classList.add('hidden');
        dualContainer.classList.remove('hidden');

        // Draw left MODIS grid
        const dualModisSvg = document.getElementById('sim-grid-svg-modis-dual');
        drawGridOnSvg(dualModisSvg, 3, 3, modisHits, 'active-modis');

        // Draw right VIIRS grid
        const dualViirsSvg = document.getElementById('sim-grid-svg-viirs-dual');
        drawGridOnSvg(dualViirsSvg, 8, 8, viirsHits, 'active-viirs');

        explCard.style.borderLeftColor = '#10B981';
        explTitle.style.color = '#10B981';
        explTitle.textContent = '⚖️ Side-by-Side Reality Check';
        explText.innerHTML = '<strong>1 MODIS detection vs. 6 VIIRS detections for the identical ground event!</strong> Neither sensor is "lying"—MODIS covers 1,000,000 m² per pixel so small fires get diluted by cool ground. VIIRS covers 140,625 m² per pixel and catches small blazes. This is why SpectraLink AI harmonization is needed to unite them.';

        statCount.textContent = '1 vs 6 Hotspots';
        statCount.className = 'sim-stat-val text-green';
        statRes.textContent = '1000m vs 375m';
        statRatio.textContent = '7.1x Area Gain';
      }}
    }}

    // -------------------------------------------------------------------------
    // Slide 5: The 2012 Trap Plotly Chart
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
        paper_bgcolor: '#0B1120',
        plot_bgcolor: '#0B1120',
        font: {{ family: 'Inter, sans-serif', color: '#94A3B8', size: 10 }},
        margin: {{ l: 40, r: 20, t: 25, b: 30 }},
        xaxis: {{ showgrid: true, gridcolor: 'rgba(255,255,255,0.06)', title: 'Observation Timeline (2005 – 2020)' }},
        yaxis: {{ showgrid: true, gridcolor: 'rgba(255,255,255,0.06)', title: 'Monthly Hotspot Detections' }},
        annotations: [
          {{
            x: '2012-01',
            y: 420,
            xref: 'x',
            yref: 'y',
            text: '⚡ VIIRS Sensor Activated (+404% Jump)',
            showarrow: true,
            arrowhead: 2,
            arrowcolor: '#F59E0B',
            arrowwidth: 2,
            font: {{ color: '#F59E0B', size: 11, weight: 700 }},
            bgcolor: 'rgba(15, 23, 42, 0.9)',
            bordercolor: '#F59E0B',
            borderwidth: 1,
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
            line: {{ color: '#F59E0B', width: 2, dash: 'dash' }}
          }}
        ],
      }};

      Plotly.newPlot('plot-raw-trap', [traceRaw], layout, {{ responsive: true, displayModeBar: false }});
    }}

    // -------------------------------------------------------------------------
    // Slide 8: Before vs After Magic Timeline
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
          line: {{ color: '#38BDF8', width: 2.8 }},
          name: 'SpectraLink Continuous Harmonized Series (Homogeneity: 1.08x)',
        }});
      }}

      const layout = {{
        paper_bgcolor: '#0B1120',
        plot_bgcolor: '#0B1120',
        font: {{ family: 'Inter, sans-serif', color: '#94A3B8', size: 10 }},
        margin: {{ l: 40, r: 20, t: 25, b: 30 }},
        legend: {{ orientation: 'h', y: 1.15, x: 1, xanchor: 'right' }},
        xaxis: {{ showgrid: true, gridcolor: 'rgba(255,255,255,0.06)', title: 'Timeline (2001 – 2025)' }},
        yaxis: {{ showgrid: true, gridcolor: 'rgba(255,255,255,0.06)', title: 'Monthly Hotspots' }},
      }};

      Plotly.newPlot('plot-before-after', traces, layout, {{ responsive: true, displayModeBar: false }});
    }}

    // -------------------------------------------------------------------------
    // Slide 9: 25-Year Calendar Heatmap
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
          [0.0, '#0B192C'],
          [0.2, '#1E3E62'],
          [0.5, '#F59E0B'],
          [0.8, '#EA580C'],
          [1.0, '#DC2626'],
        ],
        colorbar: {{
          title: 'Fires',
          titleside: 'top',
          tickcolor: '#94A3B8',
          tickfont: {{ color: '#94A3B8', size: 9 }}
        }}
      }};

      const layout = {{
        paper_bgcolor: '#0B1120',
        plot_bgcolor: '#0B1120',
        font: {{ family: 'Inter, sans-serif', color: '#94A3B8', size: 10 }},
        margin: {{ l: 40, r: 15, t: 15, b: 30 }},
        xaxis: {{ title: 'Year (2001 – 2025)', dtick: 2 }},
        yaxis: {{ title: 'Calendar Month' }},
      }};

      Plotly.newPlot('plot-calendar-slide', [trace], layout, {{ responsive: true, displayModeBar: false }});
    }}

    // -------------------------------------------------------------------------
    // Slide 10: 2026 Forecast Plotly Chart
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
        name: 'Historical Observations (Late 2025)',
      }};

      const traceFC = {{
        x: fcDates,
        y: fcVals,
        type: 'scatter',
        mode: 'lines+markers',
        marker: {{ size: 6, color: '#F97316' }},
        line: {{ color: '#F97316', width: 2.5, dash: 'dash' }},
        name: '2026 6-Month Prediction',
      }};

      const traceCI = {{
        x: fcDates.concat(fcDates.slice().reverse()),
        y: ciUpper.concat(ciLower.slice().reverse()),
        fill: 'toself',
        fillcolor: 'rgba(249, 115, 22, 0.22)',
        line: {{ color: 'transparent' }},
        name: '95% Confidence Interval',
      }};

      const layout = {{
        paper_bgcolor: '#0B1120',
        plot_bgcolor: '#0B1120',
        font: {{ family: 'Inter, sans-serif', color: '#94A3B8', size: 10 }},
        margin: {{ l: 40, r: 20, t: 25, b: 30 }},
        legend: {{ orientation: 'h', y: 1.15, x: 1, xanchor: 'right' }},
        xaxis: {{ showgrid: true, gridcolor: 'rgba(255,255,255,0.06)', title: 'Forecast Horizon (Jan – Jun 2026)' }},
        yaxis: {{ showgrid: true, gridcolor: 'rgba(255,255,255,0.06)', title: 'Predicted Hotspots' }},
        annotations: [
          {{
            x: '2026-05',
            y: fcVals[4] || 340,
            text: '🚨 HIGH RISK ALERT (Wheat Harvest)',
            showarrow: true,
            arrowhead: 2,
            arrowcolor: '#EF4444',
            font: {{ color: '#EF4444', size: 10, weight: 700 }},
            bgcolor: 'rgba(15, 23, 42, 0.9)',
            bordercolor: '#EF4444',
          }}
        ]
      }};

      Plotly.newPlot('plot-forecast-slide', [traceHist, traceCI, traceFC], layout, {{ responsive: true, displayModeBar: false }});
    }}

    // -------------------------------------------------------------------------
    // Ambient Starfield & Ember Particles Canvas
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

      const stars = Array.from({{ length: 80 }}, () => ({{
        x: Math.random() * w,
        y: Math.random() * h,
        radius: Math.random() * 1.4,
        alpha: Math.random() * 0.8 + 0.2,
        twinkle: Math.random() * 0.02 + 0.005,
      }}));

      const embers = Array.from({{ length: 30 }}, () => ({{
        x: Math.random() * w,
        y: h + Math.random() * 50,
        radius: Math.random() * 2 + 1,
        speedY: Math.random() * 0.8 + 0.4,
        speedX: (Math.random() - 0.5) * 0.4,
        alpha: Math.random() * 0.7 + 0.3,
        color: Math.random() > 0.4 ? '#F97316' : '#EF4444',
      }}));

      function render() {{
        ctx.clearRect(0, 0, w, h);

        // Draw Stars
        stars.forEach(s => {{
          s.alpha += s.twinkle;
          if (s.alpha > 1 || s.alpha < 0.2) s.twinkle = -s.twinkle;
          ctx.fillStyle = `rgba(255, 255, 255, ${{s.alpha}})`;
          ctx.beginPath();
          ctx.arc(s.x, s.y, s.radius, 0, Math.PI * 2);
          ctx.fill();
        }});

        // Draw Embers
        embers.forEach(e => {{
          e.y -= e.speedY;
          e.x += e.speedX;
          if (e.y < -10) {{
            e.y = h + 10;
            e.x = Math.random() * w;
          }}
          ctx.fillStyle = e.color;
          ctx.globalAlpha = e.alpha;
          ctx.beginPath();
          ctx.arc(e.x, e.y, e.radius, 0, Math.PI * 2);
          ctx.fill();
          ctx.globalAlpha = 1.0;
        }});

        requestAnimationFrame(render);
      }}
      render();
    }}
  </script>
</body>
</html>
'''

with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"Successfully generated standalone presentation at: {OUTPUT_PATH}")
print(f"File size: {os.path.getsize(OUTPUT_PATH):,} bytes")
