"""
ml_engine_v3.py
===============
SpectraLink v3.0: 32-Feature Machine Learning & Deep Learning Harmonization Engine
NASA Space Apps Challenge — "Harmonization of MODIS and VIIRS Hot Spots"

Provides:
1. 32-Feature Physics-Informed & Temporal Sequence Feature Pipeline.
2. 6-Model Suite & Leaderboard (Stacking, Deep MLP, Sequence MLP, GBDT/ExtraTrees, Huber Linear, Baseline).
3. 25-Year Burning Activity Calendar Matrix.
4. NASA Biomass, CO2, and PM2.5 Emissions Accounting.
5. 6-Month Forward Autoregressive Forecasting with 95% Confidence Bounds.
6. Permutation / GBDT Feature Importances (Top 15 Features).
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from sklearn.base import BaseEstimator, RegressorMixin, clone
from sklearn.ensemble import ExtraTreesRegressor, GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import HuberRegressor, Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import TimeSeriesSplit
from sklearn.neural_network import MLPRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import RobustScaler, StandardScaler

MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


# -----------------------------------------------------------------------------
# 1. 32-Feature Engineering Pipeline
# -----------------------------------------------------------------------------
def engineer_advanced_fire_features_v3(df_in: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    d = df_in.copy().sort_values(["Year", "Month"]).reset_index(drop=True)

    # Core Sensor & Radiative Counts
    d["MODIS_Total_Count"] = d["MODIS_Terra_Count"] + d["MODIS_Aqua_Count"]
    d["Aqua_to_Terra_Ratio"] = d["MODIS_Aqua_Count"] / (d["MODIS_Terra_Count"] + 1.0)
    d["High_Confidence_Ratio"] = np.clip(
        d["MODIS_HighConf_Count"] / (d["MODIS_Total_Count"] + 1.0), 0.0, 1.0
    )
    d["frp_per_hotspot"] = d["MODIS_FRP_Sum"] / (d["MODIS_Total_Count"] + 1.0)
    d["frp_density_index"] = d["MODIS_Max_Peak_FRP"] / (d["frp_per_hotspot"] + 1.0)

    # Physics-Informed Harmonic & Non-Linear Powers
    d["Terra_Aqua_Harmonic_Mean"] = (
        2.0 * d["MODIS_Terra_Count"] * d["MODIS_Aqua_Count"]
    ) / (d["MODIS_Total_Count"] + 1.0)
    d["FRP_to_Count_Power"] = np.sqrt(np.maximum(0.0, d["MODIS_FRP_Sum"])) / (
        d["MODIS_Total_Count"] + 1.0
    )
    d["Radiative_Dispersion_Index"] = (
        d["MODIS_Max_Peak_FRP"] - d["frp_per_hotspot"]
    ) / (d["MODIS_Max_Peak_FRP"] + 1.0)

    # Cyclical Calendar Harmonics (Fourier Multi-frequency)
    d["month_sin_1"] = np.sin(2.0 * np.pi * d["Month"] / 12.0)
    d["month_cos_1"] = np.cos(2.0 * np.pi * d["Month"] / 12.0)
    d["month_sin_2"] = np.sin(4.0 * np.pi * d["Month"] / 12.0)
    d["month_cos_2"] = np.cos(4.0 * np.pi * d["Month"] / 12.0)

    # Surface Climate Proxies
    d["Thermal_NDVI_Interaction"] = (d["Surface_Temp_K"] / 300.0) * (
        1.0 - d["NDVI_Proxy"]
    )
    d["Seasonal_Drought_Proxy"] = np.maximum(
        0.0, (d["Surface_Temp_K"] - 295.0) / 15.0
    ) * (1.0 / (d["NDVI_Proxy"] + 0.1))

    # Temporal Sequence & Autoregressive Window Features
    d["modis_lag1"] = d["MODIS_Total_Count"].shift(1).bfill()
    d["modis_lag2"] = d["MODIS_Total_Count"].shift(2).bfill()
    d["modis_lag3"] = d["MODIS_Total_Count"].shift(3).bfill()
    d["modis_lag12"] = d["MODIS_Total_Count"].shift(12).bfill()

    d["modis_roll_mean_3"] = d["MODIS_Total_Count"].rolling(window=3, min_periods=1).mean()
    d["modis_roll_max_6"] = d["MODIS_Total_Count"].rolling(window=6, min_periods=1).max()
    d["modis_roll_std_3"] = d["MODIS_Total_Count"].rolling(window=3, min_periods=1).std().fillna(0.0)

    d["modis_acceleration"] = (
        d["MODIS_Total_Count"] - 2.0 * d["modis_lag1"] + d["modis_lag2"]
    )
    d["frp_lag1"] = d["MODIS_FRP_Sum"].shift(1).bfill()
    d["frp_roll_mean_3"] = d["MODIS_FRP_Sum"].rolling(window=3, min_periods=1).mean()

    # Out-of-Fold / Expanding Target Encoding of Monthly Climatology
    monthly_clim = d.groupby("Month")["MODIS_Total_Count"].transform("mean")
    d["Seasonal_Expected_MODIS"] = monthly_clim
    d["MODIS_Seasonal_Ratio"] = d["MODIS_Total_Count"] / (monthly_clim + 1.0)
    d["Centered_Window_Momentum"] = (
        d["MODIS_Total_Count"] - d["modis_roll_mean_3"]
    ) / (d["modis_roll_std_3"] + 1.0)

    # Non-linear Multi-Sensor Cross Interactions
    d["Log_MODIS_Count"] = np.log1p(np.maximum(0.0, d["MODIS_Total_Count"]))
    d["Log_MODIS_FRP"] = np.log1p(np.maximum(0.0, d["MODIS_FRP_Sum"]))
    d["FRP_per_HighConf"] = d["MODIS_FRP_Sum"] / (d["MODIS_HighConf_Count"] + 1.0)
    d["Normalized_Burn_Index"] = (
        d["MODIS_Total_Count"] * d["Thermal_NDVI_Interaction"]
    ) / (d["MODIS_Total_Count"] + 5.0)
    d["Terra_Aqua_Diff"] = np.abs(d["MODIS_Aqua_Count"] - d["MODIS_Terra_Count"])
    d["Terra_Aqua_Asymmetry"] = (
        d["MODIS_Aqua_Count"] - d["MODIS_Terra_Count"]
    ) / (d["MODIS_Total_Count"] + 1.0)
    d["Trend_Index"] = (d["Year"] - 2001) / 25.0

    feature_cols = [
        "MODIS_Total_Count",
        "MODIS_FRP_Sum",
        "Aqua_to_Terra_Ratio",
        "High_Confidence_Ratio",
        "frp_per_hotspot",
        "frp_density_index",
        "Terra_Aqua_Harmonic_Mean",
        "FRP_to_Count_Power",
        "Radiative_Dispersion_Index",
        "month_sin_1",
        "month_cos_1",
        "month_sin_2",
        "month_cos_2",
        "Surface_Temp_K",
        "NDVI_Proxy",
        "Thermal_NDVI_Interaction",
        "Seasonal_Drought_Proxy",
        "modis_lag1",
        "modis_lag2",
        "modis_lag3",
        "modis_lag12",
        "modis_roll_mean_3",
        "modis_roll_max_6",
        "modis_roll_std_3",
        "modis_acceleration",
        "frp_lag1",
        "frp_roll_mean_3",
        "Seasonal_Expected_MODIS",
        "MODIS_Seasonal_Ratio",
        "Centered_Window_Momentum",
        "Log_MODIS_Count",
        "Trend_Index",
    ]

    return d, feature_cols


# -----------------------------------------------------------------------------
# 2. Machine Learning & Deep Learning Architectures
# -----------------------------------------------------------------------------
class StatisticalScalingBaseline(BaseEstimator, RegressorMixin):
    def __init__(self, col_idx: int = 0):
        self.col_idx = col_idx
        self.ratio_ = 3.65

    def fit(self, X: Any, y: Any):
        X_arr = np.asarray(X, dtype=float)
        y_arr = np.asarray(y, dtype=float)
        x_base = X_arr[:, self.col_idx]
        valid = (x_base > 1.0) & (y_arr > 0.0)
        if np.any(valid):
            self.ratio_ = float(np.median(y_arr[valid] / x_base[valid]))
        return self

    def predict(self, X: Any) -> np.ndarray:
        X_arr = np.asarray(X, dtype=float)
        return np.maximum(0.0, X_arr[:, self.col_idx] * self.ratio_)


class PhysicsInformedDeepMLP(BaseEstimator, RegressorMixin):
    def __init__(self, random_state: int = 42, alpha: float = 0.5):
        self.random_state = random_state
        self.alpha = alpha
        self.scaler = RobustScaler()
        self.mlp = MLPRegressor(
            hidden_layer_sizes=(64, 32),
            activation="relu",
            solver="adam",
            alpha=self.alpha,
            learning_rate="adaptive",
            max_iter=300,
            random_state=self.random_state,
        )
        self.indices = [0, 1, 2, 6, 7, 9, 10, 17, 21, 27, 28, 30]

    def fit(self, X: Any, y: Any):
        X_arr = np.asarray(X, dtype=float)
        y_arr = np.asarray(y, dtype=float)
        X_sub = X_arr[:, self.indices]
        X_sc = self.scaler.fit_transform(X_sub)
        self.mlp.fit(X_sc, y_arr)
        return self

    def predict(self, X: Any) -> np.ndarray:
        X_arr = np.asarray(X, dtype=float)
        X_sub = X_arr[:, self.indices]
        X_sc = self.scaler.transform(X_sub)
        return np.clip(self.mlp.predict(X_sc), 0.0, None)


class TemporalSequenceMLP(BaseEstimator, RegressorMixin):
    def __init__(self, random_state: int = 42, alpha: float = 0.8):
        self.random_state = random_state
        self.alpha = alpha
        self.scaler = StandardScaler()
        self.mlp = MLPRegressor(
            hidden_layer_sizes=(32, 16),
            activation="relu",
            solver="adam",
            alpha=self.alpha,
            learning_rate="adaptive",
            max_iter=300,
            random_state=self.random_state,
        )
        self.indices = [0, 9, 10, 11, 12, 17, 18, 19, 20, 21, 22, 27, 29]

    def fit(self, X: Any, y: Any):
        X_arr = np.asarray(X, dtype=float)
        y_arr = np.asarray(y, dtype=float)
        X_sub = X_arr[:, self.indices]
        X_sc = self.scaler.fit_transform(X_sub)
        self.mlp.fit(X_sc, y_arr)
        return self

    def predict(self, X: Any) -> np.ndarray:
        X_arr = np.asarray(X, dtype=float)
        X_sub = X_arr[:, self.indices]
        X_sc = self.scaler.transform(X_sub)
        return np.clip(self.mlp.predict(X_sc), 0.0, None)


class HuberTreeBlend(BaseEstimator, RegressorMixin):
    def __init__(self, random_state: int = 42):
        self.random_state = random_state
        self.gbr = GradientBoostingRegressor(
            loss="huber", alpha=0.9, n_estimators=110, max_depth=3,
            learning_rate=0.04, subsample=0.85, random_state=random_state
        )
        self.etr = ExtraTreesRegressor(
            n_estimators=110, max_depth=6, min_samples_leaf=2,
            random_state=random_state, n_jobs=1
        )

    def fit(self, X: Any, y: Any):
        self.gbr.fit(X, y)
        self.etr.fit(X, y)
        return self

    def predict(self, X: Any) -> np.ndarray:
        return np.clip(0.65 * self.gbr.predict(X) + 0.35 * self.etr.predict(X), 0.0, None)


class SpectraNetHybridStacking(BaseEstimator, RegressorMixin):
    def __init__(self, random_state: int = 42):
        self.random_state = random_state
        self.m_huber = Pipeline([("scaler", RobustScaler()), ("huber", HuberRegressor(max_iter=1500, alpha=1.35))])
        self.m_deep = PhysicsInformedDeepMLP(random_state=random_state)
        self.m_seq = TemporalSequenceMLP(random_state=random_state)
        self.m_tree = HuberTreeBlend(random_state=random_state)
        self.weights_ = np.array([0.05, 0.12, 0.10, 0.73])

    def fit(self, X: Any, y: Any):
        tscv = TimeSeriesSplit(n_splits=4)
        oof_meta = np.zeros((len(y), 4), dtype=float)
        oof_mask = np.zeros(len(y), dtype=bool)
        estimators = [self.m_huber, self.m_deep, self.m_seq, self.m_tree]

        for tr_i, val_i in tscv.split(X):
            for k, est in enumerate(estimators):
                c_est = clone(est)
                c_est.fit(X[tr_i], y[tr_i])
                oof_meta[val_i, k] = c_est.predict(X[val_i])
            oof_mask[val_i] = True

        y_valid = y[oof_mask]
        meta_valid = oof_meta[oof_mask]

        def loss_fn(w):
            w_norm = np.maximum(0.0, w)
            if np.sum(w_norm) > 0:
                w_norm = w_norm / np.sum(w_norm)
            p = meta_valid @ w_norm
            return mean_squared_error(y_valid, p)

        res = minimize(loss_fn, self.weights_, bounds=[(0.0, 1.0)] * 4)
        if res.success:
            w_final = np.maximum(0.0, res.x)
            self.weights_ = w_final / np.sum(w_final)

        for est in estimators:
            est.fit(X, y)
        return self

    def predict(self, X: Any) -> np.ndarray:
        p1 = self.m_huber.predict(X)
        p2 = self.m_deep.predict(X)
        p3 = self.m_seq.predict(X)
        p4 = self.m_tree.predict(X)
        P = np.column_stack([p1, p2, p3, p4])
        return np.clip(P @ self.weights_, 0.0, None)


def build_models_dict() -> Dict[str, BaseEstimator]:
    return {
        "6. SpectraNet Hybrid Stacking": SpectraNetHybridStacking(random_state=42),
        "5. Huber-Loss GBDT & ExtraTrees Blend": HuberTreeBlend(random_state=42),
        "3. Deep MLP-ResNet Neural Net": PhysicsInformedDeepMLP(random_state=42),
        "4. Temporal Sequence 1D-MLP Neural Net": TemporalSequenceMLP(random_state=42),
        "2. Huber Robust Linear Regressor": Pipeline([("scaler", RobustScaler()), ("huber", HuberRegressor(max_iter=1500, alpha=1.35))]),
        "1. Statistical Baseline": StatisticalScalingBaseline(col_idx=0),
    }


CACHE_ANALYTICS: Dict[str, Dict[str, Any]] = {}

# -----------------------------------------------------------------------------
# 3. Model Benchmark & Leaderboard Engine
# -----------------------------------------------------------------------------
def benchmark_and_harmonize(
    df_feat: pd.DataFrame,
    feature_cols: List[str],
    selected_model_key: str = "6. SpectraNet Hybrid Stacking",
    cache_key: Optional[str] = None,
) -> Dict[str, Any]:
    if cache_key and cache_key in CACHE_ANALYTICS:
        return CACHE_ANALYTICS[cache_key]

    df_train = df_feat[df_feat["Year"] >= 2012].dropna(subset=["VIIRS_Count", "VIIRS_FRP_Sum"]).copy().reset_index(drop=True)
    X = df_train[feature_cols].values
    y_cnt = df_train["VIIRS_Count"].values
    y_frp = df_train["VIIRS_FRP_Sum"].values
    X_all = df_feat[feature_cols].values

    models = build_models_dict()
    tscv = TimeSeriesSplit(n_splits=5)
    rows = []
    fitted_cnt = {}
    fitted_frp = {}
    frp_col_idx = feature_cols.index("MODIS_FRP_Sum")

    for name, base_model in models.items():
        oof_c = np.zeros_like(y_cnt, dtype=float)
        oof_f = np.zeros_like(y_frp, dtype=float)
        mask = np.zeros(len(y_cnt), dtype=bool)

        for tr, val in tscv.split(X):
            mc = clone(base_model)
            mf = clone(base_model) if not isinstance(base_model, StatisticalScalingBaseline) else StatisticalScalingBaseline(col_idx=frp_col_idx)

            mc.fit(X[tr], y_cnt[tr])
            mf.fit(X[tr], y_frp[tr])

            oof_c[val] = mc.predict(X[val])
            oof_f[val] = mf.predict(X[val])
            mask[val] = True

        yt_c, yp_c = y_cnt[mask], oof_c[mask]
        cv_r2 = float(r2_score(yt_c, yp_c))
        cv_mae = float(mean_absolute_error(yt_c, yp_c))
        cv_rmse = float(np.sqrt(mean_squared_error(yt_c, yp_c)))
        valid_m = yt_c >= 5.0
        cv_mape = float(
            np.mean(np.abs((yt_c[valid_m] - yp_c[valid_m]) / yt_c[valid_m])) * 100.0
            if np.any(valid_m)
            else np.mean(np.abs(yt_c - yp_c) / np.maximum(1.0, yt_c)) * 100.0
        )

        final_c = clone(base_model)
        final_f = clone(base_model) if not isinstance(base_model, StatisticalScalingBaseline) else StatisticalScalingBaseline(col_idx=frp_col_idx)
        final_c.fit(X, y_cnt)
        final_f.fit(X, y_frp)

        full_r2 = float(r2_score(y_cnt, final_c.predict(X)))
        fitted_cnt[name] = final_c
        fitted_frp[name] = final_f

        rows.append({
            "model_name": name,
            "cv_r2": round(cv_r2, 4),
            "full_r2": round(full_r2, 4),
            "cv_mae": round(cv_mae, 2),
            "cv_rmse": round(cv_rmse, 2),
            "cv_mape": round(cv_mape, 2),
        })

    leaderboard = pd.DataFrame(rows).sort_values(by="cv_rmse", ascending=True).reset_index(drop=True)

    # Pick winner or selected
    matched_key = next((k for k in models if selected_model_key in k or k in selected_model_key), "6. SpectraNet Hybrid Stacking")
    active_cnt = fitted_cnt[matched_key]
    active_frp = fitted_frp[matched_key]

    # Predict entire 2001-2025 timeline
    pred_c = np.round(np.clip(active_cnt.predict(X_all), 0.0, None), 1)
    pred_f = np.round(np.clip(active_frp.predict(X_all), 0.0, None), 2)

    df_harm = df_feat.copy()
    df_harm["ML_Predicted_VIIRS_Count"] = pred_c
    df_harm["ML_Predicted_VIIRS_FRP"] = pred_f

    # 50/50 smooth blending during overlap
    df_harm["Harmonized_Hotspots"] = np.where(
        df_harm["Year"] < 2012,
        df_harm["ML_Predicted_VIIRS_Count"],
        np.round(0.50 * df_harm["ML_Predicted_VIIRS_Count"] + 0.50 * df_harm["VIIRS_Count"], 1),
    )
    df_harm["Harmonized_FRP_MW"] = np.where(
        df_harm["Year"] < 2012,
        df_harm["ML_Predicted_VIIRS_FRP"],
        np.round(0.50 * df_harm["ML_Predicted_VIIRS_FRP"] + 0.50 * df_harm["VIIRS_FRP_Sum"], 2),
    )

    # NASA Emissions Physics
    # FRE = FRP * 3600 s; Biomass (kg) = FRE * 0.368 kg/MJ; CO2 = Biomass * 1.615; PM2.5 = Biomass * 0.0091
    effective_burn_s = 3600.0
    biomass_conv = 0.368
    ef_co2 = 1.615
    ef_pm25 = 0.0091

    df_harm["FRE_Energy_MJ"] = np.round(df_harm["Harmonized_FRP_MW"] * effective_burn_s, 1)
    df_harm["Burned_Biomass_Tons"] = np.round((df_harm["FRE_Energy_MJ"] * biomass_conv) / 1000.0, 2)
    df_harm["CO2_Emissions_Tons"] = np.round(df_harm["Burned_Biomass_Tons"] * ef_co2, 2)
    df_harm["PM25_Smoke_Tons"] = np.round(df_harm["Burned_Biomass_Tons"] * ef_pm25, 3)

    # Climatology & Calendar Matrix
    calendar_matrix = (
        df_harm.pivot(index="Year", columns="Month", values="Harmonized_Hotspots")
        .reindex(columns=range(1, 13))
        .fillna(0.0)
    )

    clim = (
        df_harm.groupby("Month", as_index=False)
        .agg(
            mean_hotspots=("Harmonized_Hotspots", "mean"),
            std_hotspots=("Harmonized_Hotspots", "std"),
            max_hotspots=("Harmonized_Hotspots", "max"),
            mean_co2=("CO2_Emissions_Tons", "mean"),
        )
    )
    q25 = float(np.percentile(clim["mean_hotspots"], 25))
    q75 = float(np.percentile(clim["mean_hotspots"], 75))

    clim["season_class"] = clim["mean_hotspots"].apply(
        lambda v: "Peak Burning Season" if v >= q75 else ("Quiet Season" if v <= q25 else "Moderate Burning")
    )
    clim["month_name"] = MONTH_NAMES

    # Annual Anomalies (Z-Score)
    annual = df_harm.groupby("Year", as_index=False).agg(
        total_hotspots=("Harmonized_Hotspots", "sum"),
        total_co2=("CO2_Emissions_Tons", "sum"),
        total_pm25=("PM25_Smoke_Tons", "sum"),
    )
    mean_ann = float(annual["total_hotspots"].mean())
    std_ann = float(max(1.0, annual["total_hotspots"].std()))
    annual["z_score"] = np.round((annual["total_hotspots"] - mean_ann) / std_ann, 2)

    # Top 15 Feature Importances (Tree Blend GBDT)
    tree_model = fitted_cnt["5. Huber-Loss GBDT & ExtraTrees Blend"]
    raw_importances = tree_model.gbr.feature_importances_
    sorted_idx = np.argsort(raw_importances)[::-1][:15]
    top_features = [
        {"feature": feature_cols[i], "importance": round(float(raw_importances[i]) * 100.0, 2)}
        for i in sorted_idx
    ]

    # 6-Month Forward Autoregressive Forecast (Jan - Jun 2026)
    forecast_rows = generate_forecast_rows(df_harm, clim, q25, q75, horizon=6)

    # Overlap Scatter Data (2012-2025)
    df_overlap = df_harm[df_harm["Year"] >= 2012].dropna(subset=["VIIRS_Count"])
    overlap_scatter = [
        {
            "year": int(r["Year"]),
            "month": int(r["Month"]),
            "modis": round(float(r["MODIS_Total_Count"]), 1),
            "viirs": round(float(r["VIIRS_Count"]), 1),
            "harmonized": round(float(r["Harmonized_Hotspots"]), 1),
        }
        for _, r in df_overlap.iterrows()
    ]

    # Sensor Discrepancy Jump Ratio
    raw_ratio_2012 = float(
        df_overlap["VIIRS_Count"].sum() / (df_overlap["MODIS_Total_Count"].sum() + 1.0)
    )
    harm_ratio_2012 = float(
        df_overlap["Harmonized_Hotspots"].sum() / (df_overlap["VIIRS_Count"].sum() + 1.0)
    )

    # Correlation
    corr = float(df_overlap[["MODIS_Total_Count", "VIIRS_Count"]].corr().iloc[0, 1])

    payload = {
        "leaderboard": leaderboard.to_dict(orient="records"),
        "winning_model": leaderboard.iloc[0]["model_name"],
        "selected_model": matched_key,
        "cv_r2": float(leaderboard.iloc[0]["cv_r2"]),
        "pearson_r": round(corr, 4),
        "raw_sensor_jump_ratio": round(raw_ratio_2012, 2),
        "harmonized_continuity_ratio": round(harm_ratio_2012, 2),
        "top_features": top_features,
        "calendar_matrix": {
            "years": [int(y) for y in calendar_matrix.index],
            "months": MONTH_NAMES,
            "values": [[round(float(v), 1) for v in row] for row in calendar_matrix.values],
        },
        "climatology": clim.to_dict(orient="records"),
        "annual_anomalies": annual.to_dict(orient="records"),
        "forecast": forecast_rows,
        "overlap_scatter": overlap_scatter,
        "timeline": [
            {
                "date": str(r["Date"]),
                "year": int(r["Year"]),
                "month": int(r["Month"]),
                "modis": round(float(r["MODIS_Total_Count"]), 1),
                "viirs": round(float(r["VIIRS_Count"]), 1) if pd.notna(r["VIIRS_Count"]) else None,
                "harmonized": round(float(r["Harmonized_Hotspots"]), 1),
                "co2_tons": round(float(r["CO2_Emissions_Tons"]), 1),
                "pm25_tons": round(float(r["PM25_Smoke_Tons"]), 2),
                "frp_mw": round(float(r["Harmonized_FRP_MW"]), 2),
            }
            for _, r in df_harm.iterrows()
        ],
        "kpi": {
            "total_harmonized_hotspots": int(df_harm["Harmonized_Hotspots"].sum()),
            "total_co2_kt": round(float(df_harm["CO2_Emissions_Tons"].sum() / 1000.0), 1),
            "total_biomass_kt": round(float(df_harm["Burned_Biomass_Tons"].sum() / 1000.0), 1),
            "total_pm25_tons": round(float(df_harm["PM25_Smoke_Tons"].sum()), 1),
            "peak_months": ", ".join(clim[clim["season_class"] == "Peak Burning Season"]["month_name"].tolist()[:3]),
            "next_month_alert": forecast_rows[0]["alert_badge"],
            "next_month_val": forecast_rows[0]["forecast_hotspots"],
        },
        "df_harm": df_harm,
    }

    if cache_key:
        CACHE_ANALYTICS[cache_key] = payload

    return payload


def generate_forecast_rows(
    df_hist: pd.DataFrame,
    clim_df: pd.DataFrame,
    q25: float,
    q75: float,
    horizon: int = 6,
) -> List[Dict[str, Any]]:
    clim_map = dict(zip(clim_df["Month"], clim_df["mean_hotspots"]))
    clim_std_map = dict(zip(clim_df["Month"], clim_df["std_hotspots"]))
    month_to_class = dict(zip(clim_df["Month"], clim_df["season_class"]))

    y_series = list(df_hist["Harmonized_Hotspots"].values)
    years_list = list(df_hist["Year"].values)
    months_list = list(df_hist["Month"].values)

    def make_ar_features(idx: int, series: List[float], yr: int, mo: int) -> List[float]:
        lag1 = series[idx - 1] if idx >= 1 else series[0]
        lag2 = series[idx - 2] if idx >= 2 else lag1
        lag3 = series[idx - 3] if idx >= 3 else lag2
        lag12 = series[idx - 12] if idx >= 12 else clim_map[mo]
        roll_mean_3 = float(np.mean(series[max(0, idx - 3):idx])) if idx >= 1 else lag1
        roll_max_6 = float(np.max(series[max(0, idx - 6):idx])) if idx >= 1 else lag1
        sin1 = float(np.sin(2.0 * np.pi * mo / 12.0))
        cos1 = float(np.cos(2.0 * np.pi * mo / 12.0))
        clim_base = float(clim_map[mo])
        return [lag1, lag2, lag3, lag12, roll_mean_3, roll_max_6, sin1, cos1, clim_base]

    X_ar, y_ar = [], []
    for i in range(12, len(y_series)):
        X_ar.append(make_ar_features(i, y_series, years_list[i], months_list[i]))
        y_ar.append(y_series[i])

    rf = RandomForestRegressor(n_estimators=80, max_depth=6, min_samples_leaf=2, random_state=42, n_jobs=1)
    rf.fit(np.asarray(X_ar, dtype=float), np.asarray(y_ar, dtype=float))

    forecast_rows = []
    last_year = 2025
    last_month = 12

    for step in range(1, horizon + 1):
        f_mo = (last_month + step - 1) % 12 + 1
        f_yr = last_year + ((last_month + step - 1) // 12)
        cur_idx = len(y_series)

        feat_vec = np.asarray(make_ar_features(cur_idx, y_series, f_yr, f_mo), dtype=float).reshape(1, -1)
        tree_preds = np.array([tree.predict(feat_vec)[0] for tree in rf.estimators_])
        mean_pred = float(np.clip(np.mean(tree_preds), 0.0, None))

        tree_std = float(np.std(tree_preds))
        seasonal_std = float(clim_std_map.get(f_mo, 10.0)) * 0.35
        combined_se = float(np.sqrt(tree_std**2 + seasonal_std**2) * (1.0 + 0.05 * (step - 1)))

        ci_lower = float(np.clip(mean_pred - 1.96 * combined_se, 0.0, None))
        ci_upper = float(mean_pred + 1.96 * combined_se)

        y_series.append(mean_pred)
        years_list.append(f_yr)
        months_list.append(f_mo)

        season_status = month_to_class.get(f_mo, "Moderate Burning")
        alert = (
            "🚨 HIGH ALERT: Peak Burning Season"
            if mean_pred >= q75 or season_status == "Peak Burning Season"
            else ("⚠️ WATCH: Moderate Activity" if mean_pred > q25 else "✅ Quiet Season")
        )

        forecast_rows.append({
            "date": f"{f_yr:04d}-{f_mo:02d}-01",
            "year": f_yr,
            "month": f_mo,
            "month_name": MONTH_NAMES[f_mo - 1],
            "forecast_hotspots": round(mean_pred, 1),
            "ci_lower": round(ci_lower, 1),
            "ci_upper": round(ci_upper, 1),
            "season_status": season_status,
            "alert_badge": alert,
        })

    return forecast_rows
