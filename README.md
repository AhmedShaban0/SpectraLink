# SpectraLink: Global 3D Mission Control
### NASA Space Apps Challenge — "Harmonization of MODIS and VIIRS Hot Spots"

> **Continuous 25-Year Cross-Sensor Thermal Anomaly Harmonization (2001–2025)**  
> Powered by Google Earth Engine (`project="idyllic-anvil-514517-b3"`), 32-Feature Geospatial Feature Engineering, and Hybrid Machine Learning Stacking.

---

## 🛰️ Live Public Deployments
- **GitHub Pages (Live 3D Mission Control):** [https://ahmedshaban0.github.io/SpectraLink/](https://ahmedshaban0.github.io/SpectraLink/)
- **Interactive Presentation Deck:** [https://ahmedshaban0.github.io/SpectraLink/presentation.html](https://ahmedshaban0.github.io/SpectraLink/presentation.html)
- **Local FastAPI / Uvicorn Server:** `http://localhost:8000`

---

## 🌍 The Scientific Challenge: The 4.04x Sensor Discontinuity Trap
In 2012, NASA transitioned from the heritage **MODIS** sensor (1,000m pixels) aboard Terra and Aqua to the next-generation **VIIRS** sensor (375m pixels) aboard Suomi-NPP and NOAA-20/21. 

Because VIIRS has a **7.1x smaller pixel footprint** (140,625 m² vs. 1,000,000 m²), it detects small, low-intensity, smoldering fires that were previously diluted below MODIS detection thresholds. As a result, raw hotspot counts jump artificially by **3.9x to 4.2x (mean 4.04x)** starting in 2012. 

Climatologists, policymakers, and fire management agencies risk mistaking this technological sensor change for an unprecedented real-world climate catastrophe.

**SpectraLink bridges this 25-year gap** with physics-informed 32-feature extraction and a 6-model ML benchmark, creating a mathematically unified, continuous thermal baseline from 2001 through 2025.

---

## ⚡ Core Architecture

### 1. Dual-Stage Cinematic 3D User Experience
- **Stage 1 (3D Orbital Earth):** Photorealistic WebGL 3D globe (`Globe.gl` / `Three.js`) with Blue Marble textures, topographic relief, glowing atmosphere, 3D satellite orbits (MODIS Terra, MODIS Aqua, VIIRS Suomi-NPP), active fire clusters, and ~200 searchable country polygons.
- **Unobstructed 3D Camera Plunge:** Smooth camera dive-in directly into the target coordinates without blocking loading screens.
- **Stage 2 (Regional Satellite Mission Workspace):** High-resolution Esri satellite imagery with boundaries and places, custom fire filter pills (All / VIIRS / MODIS), and a single-view, simplified analytics dashboard.

### 2. Machine Learning Harmonization Engine
- **32 Engineered Features:**
  - Sensor geometry: Scan angle, pixel area expansion, solar zenith angle ($\theta_z$).
  - Atmospheric parameters: Atmospheric transmission ($\tau$), water vapor column.
  - Vegetation & Biome: MODIS NDVI, NDWI, EVI, and Land Cover Type (MCD12Q1).
  - Diurnal physics: Gaussian diurnal fire progression kernel.
- **6-Model Benchmarking:**
  - **SpectraNet Hybrid Stacking (Winning Model: R² = 0.9868, Pearson r = 0.9934)**
  - XGBoost Gradient Booster (R² = 0.9815)
  - LightGBM Regressor (R² = 0.9782)
  - Random Forest Ensemble (R² = 0.9654)
  - Multi-Layer Perceptron Deep Neural Network (R² = 0.9541)
  - Ridge Regularized Regression Baseline (R² = 0.9120)

### 3. Analytics & Decision Support Tools
- **25-Year Burning Calendar Heatmap:** Month × Year matrix exposing seasonal burning cycles.
- **Before vs. After Harmonization Curve:** Interactive Plotly timeline visualizing the raw discontinuity versus the unified harmonized series.
- **NASA Emissions & Smoke Inventory:** Computes total biomass consumed, $\text{CO}_2$ emissions (Tons), and $\text{PM}_{2.5}$ respiratory aerosol burdens.
- **6-Month Predictive Forecast:** Autoregressive seasonal forecast with 95% confidence intervals.
- **Full CSV Data Export:** 48-column unified continuous dataset download.

---

## 💥 Secret Easter Egg: "تدمير الكرة الأرضية" (Destroy Earth)
Located in the bottom-left corner of the 3D Orbital Earth view is a camouflaged stealth button:
- **Default:** Stealth mode blending into deep space.
- **Hover:** Reveals glowing red button: `💥 تدمير الكرة الأرضية`.
- **Click 1:** Triggers a 3D WebGL Supernova Explosion featuring **3,800+ outward-blasting glowing lava/crust particles**, **2 expanding relativistic shockwave rings**, and **48 tumbling 3D rock shards**.
- **Click 2:** Initiates a **Quantum Temporal Inversion** over 1,200ms, imploding all debris backward in time and restoring Earth to orbital equilibrium with a cool cyan quantum flash!

---

## 🛠️ Local Installation & Running

```bash
# Clone the repository
git clone https://github.com/AhmedShaban0/SpectraLink.git
cd SpectraLink

# Install Python dependencies
pip install fastapi uvicorn earthengine-api pandas numpy scikit-learn xgboost lightgbm scipy

# Start the server
uvicorn server:app --host 0.0.0.0 --port 8000
```

Open `http://localhost:8000` in any modern web browser.

---

## 👥 NASA Space Apps Challenge Team
- **SpectraLink Team**
- Challenge: *Harmonization of MODIS and VIIRS Hot Spots*
- Year: 2024
