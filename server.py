"""
server.py
=========
SpectraLink v3.0: Global 3D Mission Control Server
NASA Space Apps Challenge — "Harmonization of MODIS and VIIRS Hot Spots"

FastAPI Backend exposing:
- GET /api/presets: Showcase preset regions with 3D camera coordinates & biomes.
- GET /api/countries: ~200 world countries with coordinates for global autocomplete.
- POST /api/analyze: Full-pipeline harmonization, emissions, 6-model benchmark, calendar, and spatial points.
- GET /api/export/{region_id}: 48-column continuous harmonized CSV download.
- Static files: Serves 3D Orbital Earth & High-Res Satellite Mission Control web interface.
"""

from __future__ import annotations

import io
import json
import os
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import gee_global_engine as gge
import ml_engine_v3 as mle

app = FastAPI(
    title="SpectraLink Global 3D Mission Control",
    description="Cross-Sensor Earth Observation Harmonization Engine (NASA Space Apps Challenge)",
    version="3.0",
)

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
DATA_CACHE_DIR = os.path.join(BASE_DIR, "data_cache")
os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(DATA_CACHE_DIR, exist_ok=True)

# In-memory storage for CSV export of active analyzed datasets
ACTIVE_HARMONIZED_DATAFRAMES: Dict[str, Any] = {}


class AnalyzeRequest(BaseModel):
    region_id: str
    name: Optional[str] = None
    bbox: Optional[List[float]] = None
    model: Optional[str] = "6. SpectraNet Hybrid Stacking"


@app.get("/api/presets")
def get_presets():
    """Returns curated showcase mission targets."""
    return {"presets": gge.get_all_presets()}


@app.get("/api/countries")
def get_countries():
    """Returns ~200 world countries for the 3D globe search bar."""
    return {"countries": gge.get_all_countries()}


@app.get("/api/global-fires")
def get_global_fires():
    """Returns global active fire clusters for the 3D Earth Globe view."""
    return {"clusters": gge.get_global_3d_fire_clusters()}


@app.post("/api/analyze")
def analyze_region(req: AnalyzeRequest):
    """
    Main orchestration endpoint:
    1. Loads satellite records from cache or GEE.
    2. Runs 32-feature extraction.
    3. Runs 6-model benchmark & generates 2001-2025 continuous harmonized series.
    4. Computes burning calendar matrix, NASA emissions, and 6-month forecast.
    5. Generates spatial active fire hotspots for the 2D Leaflet satellite map.
    """
    clean_id = req.region_id.lower().replace(" ", "_")
    analysis_cache_file = os.path.join(DATA_CACHE_DIR, f"{clean_id}_analysis.json")

    # 1. Fetch or load raw satellite data
    df_raw, profile = gge.load_or_fetch_satellite_dataset(
        region_id=req.region_id,
        bbox=req.bbox,
        name=req.name,
    )

    # 2. Check disk cache for pre-computed analysis
    if os.path.exists(analysis_cache_file):
        try:
            with open(analysis_cache_file, "r", encoding="utf-8") as f:
                cached_data = json.load(f)
            # Generate spatial hotspots on the fly based on profile
            cached_data["profile"] = profile
            spatial_data = gge.generate_spatial_hotspots(profile, df_raw, 240)
            cached_data["spatial_hotspots"] = spatial_data["points"]
            cached_data["fire_clusters"] = spatial_data["clusters"]
            return cached_data
        except Exception:
            pass

    # 3. Compute 32 features
    feat_df, feature_cols = mle.engineer_advanced_fire_features_v3(df_raw)

    # 4. Benchmark all 6 models & generate continuous timeline
    analysis = mle.benchmark_and_harmonize(
        df_feat=feat_df,
        feature_cols=feature_cols,
        selected_model_key=req.model or "6. SpectraNet Hybrid Stacking",
        cache_key=clean_id,
    )

    # Cache harmonized DataFrame for CSV export
    ACTIVE_HARMONIZED_DATAFRAMES[clean_id] = analysis["df_harm"]

    # 5. Generate spatial hotspot points for Leaflet map
    spatial_data = gge.generate_spatial_hotspots(profile, analysis["df_harm"], 240)

    # Remove non-serializable DataFrame before returning JSON
    payload = dict(analysis)
    payload.pop("df_harm", None)
    payload["profile"] = profile
    payload["spatial_hotspots"] = spatial_data["points"]
    payload["fire_clusters"] = spatial_data["clusters"]

    # Save to disk cache for fast future retrieval
    try:
        with open(analysis_cache_file, "w", encoding="utf-8") as f:
            json.dump(payload, f)
    except Exception:
        pass

    return payload


@app.get("/api/export/{region_id}")
def export_csv(region_id: str):
    """Generates and downloads the full 48-column continuous harmonized dataset."""
    clean_id = region_id.lower().replace(" ", "_")
    
    # Check memory cache
    df = ACTIVE_HARMONIZED_DATAFRAMES.get(clean_id)
    if df is None:
        # Load raw dataset and run fast harmonization
        df_raw, profile = gge.load_or_fetch_satellite_dataset(region_id=region_id)
        feat_df, feature_cols = mle.engineer_advanced_fire_features_v3(df_raw)
        res = mle.benchmark_and_harmonize(feat_df, feature_cols, cache_key=clean_id)
        df = res["df_harm"]

    stream = io.StringIO()
    df.to_csv(stream, index=False)
    stream.seek(0)

    filename = f"SpectraLink_Harmonized_2001_2025_{clean_id}.csv"
    response = StreamingResponse(iter([stream.getvalue()]), media_type="text/csv")
    response.headers["Content-Disposition"] = f"attachment; filename={filename}"
    return response


# Mount static assets
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def serve_index():
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return HTMLResponse("<h1>SpectraLink Mission Control</h1><p>Building frontend assets...</p>")


@app.get("/presentation")
@app.get("/presentation.html")
def serve_presentation():
    standalone_path = os.path.join(BASE_DIR, "presentation.html")
    if not os.path.exists(standalone_path):
        standalone_path = os.path.join(BASE_DIR, "SpectraLink_Presentation_Standalone.html")
    if os.path.exists(standalone_path):
        return FileResponse(standalone_path)
    return HTMLResponse("<h1>SpectraLink Presentation</h1><p>Building presentation assets...</p>")


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return Response(content=b"", media_type="image/x-icon")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)

