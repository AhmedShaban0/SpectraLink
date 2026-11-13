import json
import os
import gee_global_engine as gge
import ml_engine_v3 as mle

presets = ["nile_delta", "california", "amazon_basin", "australia", "portugal"]
cache_dir = os.path.join(os.path.dirname(__file__), "data_cache")

print("Pre-warming analysis cache for showcase presets...")
for pid in presets:
    cache_file = os.path.join(cache_dir, f"{pid}_analysis.json")
    if os.path.exists(cache_file):
        print(f"Preset {pid} already cached on disk.")
        continue
    
    print(f"Generating cache for preset: {pid}...")
    df_raw, profile = gge.load_or_fetch_satellite_dataset(pid)
    feat_df, cols = mle.engineer_advanced_fire_features_v3(df_raw)
    res = mle.benchmark_and_harmonize(feat_df, cols, cache_key=pid)
    
    payload = dict(res)
    payload.pop("df_harm", None)
    payload["profile"] = profile
    payload["spatial_hotspots"] = gge.generate_spatial_hotspots(profile, df_raw, 160)
    
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(payload, f)
    print(f"Successfully cached {pid}!")

print("All showcase presets are pre-warmed!")

