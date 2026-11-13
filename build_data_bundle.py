"""
build_data_bundle.py
====================
Compiles a self-contained, pre-cached static dataset bundle into static/data_bundle.json.
Allows SpectraLink to run 100% autonomously in static CDN environments (GitHub Pages, Vercel)
without needing a live Python / GEE backend running!
"""

import os
import glob
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

import gee_global_engine as gge

OUTPUT_PATH = os.path.join(BASE_DIR, "static", "data_bundle.json")

print("📦 Building SpectraLink Offline & CDN Data Bundle...")

# 1. Fetch presets, countries, and global fires
presets = gge.get_all_presets()
countries = gge.get_all_countries()
global_fires = gge.get_global_3d_fire_clusters()

# 2. Collect all cached analyses
cached_analyses = {}
cache_files = glob.glob(os.path.join(BASE_DIR, "data_cache", "*_analysis.json"))

for cf in cache_files:
    fname = os.path.basename(cf)
    key = fname.replace("_analysis.json", "").lower()
    try:
        with open(cf, "r", encoding="utf-8") as f:
            data = json.load(f)
            cached_analyses[key] = data
            # Also store with aliases (e.g. nile_delta_egypt -> nile_delta)
            if key == "nile_delta":
                cached_analyses["nile_delta_egypt"] = data
            elif key == "california":
                cached_analyses["california_usa"] = data
            elif key == "amazon_basin":
                cached_analyses["amazon_basin_brazil"] = data
            elif key == "australia":
                cached_analyses["australia_southeast"] = data
            elif key == "canada_wildfires":
                cached_analyses["canada_boreal_fires"] = data
            elif key == "portugal":
                cached_analyses["portugal_mediterranean"] = data
    except Exception as e:
        print(f"⚠️ Error reading {fname}: {e}")

bundle = {
    "version": "3.0",
    "presets": presets,
    "countries": countries,
    "global_fires": global_fires,
    "cached_analyses": cached_analyses,
    "total_cached_regions": len(cached_analyses),
}

with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    json.dump(bundle, f, ensure_ascii=False)

file_size_mb = os.path.getsize(OUTPUT_PATH) / (1024 * 1024)
print(f"✅ Successfully generated {OUTPUT_PATH} ({file_size_mb:.2f} MB)")
print(f"📊 Bundled {len(presets)} presets, {len(countries)} countries, {len(global_fires)} fire clusters, and {len(cached_analyses)} pre-computed regional analyses.")
