"""
harmonizer_ml.py
================
SpectraLink v3.0: Machine Learning Harmonization & Analytics Engine
NASA Space Apps Challenge — "Harmonization of MODIS and VIIRS Hot Spots"

Provides:
1. Feature Engineering v3.0 (32 physical, diurnal, radiative, Fourier, temporal lag/rolling,
   and seasonal target-encoded features).
2. Model Architectures & Benchmark Suite:
   - SpectraNet Hybrid Super-Learner (Stacking Ensemble)
   - Huber-Loss GBDT & ExtraTrees Blend
   - Deep Multi-Layer Neural Network (MLP-ResNet)
   - Temporal Sequence Neural Network (1D-MLP)
   - Huber Robust Linear Regressor
   - Statistical Scaling Baseline
3. Burning Activity Calendar Matrix & Climatology Analytics.
4. NASA Biomass Burning, Carbon (CO2), and PM2.5 Smoke Aerosol Calculations.
5. 6-Month Forward Forecasting Engine with 95% Confidence Intervals.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy.optimize import minimize

from sklearn.base import BaseEstimator, RegressorMixin, clone
from sklearn.ensemble import (
    ExtraTreesRegressor,
    GradientBoostingRegressor,
    RandomForestRegressor,
)
from sklearn.linear_model import HuberRegressor, Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import TimeSeriesSplit
from sklearn.neural_network import MLPRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import RobustScaler, StandardScaler

MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


# ---------------------------------------------------------------------------
# 1. Feature Engineering Engine (32 Features)
# ---------------------------------------------------------------------------
def engineer_advanced_fire_features_v3(df_in: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    d = df_in.copy().sort_values(["Year", "Month"]).reset_index(drop=True)

    # Core Sensor & Diurnal Radiative
    d["MODIS_Total_Count"] = d["MODIS_Terra_Count"] + d["MODIS_Aqua_Count"]
    d["Aqua_to_Terra_Ratio"] = d["MODIS_Aqua_Count"] / (d["MODIS_Terra_Count"] + 1.0)
    d["High_Confidence_Ratio"] = np.clip(
        d["MODIS_HighConf_Count"] / (d["MODIS_Total_Count"] + 1.0), 0.0, 1.0
    )
    d["frp_per_hotspot"] = d["MODIS_FRP_Sum"] / (d["MODIS_Total_Count"] + 1.0)
    d["frp_density_index"] = d["MODIS_Max_Peak_FRP"] / (d["frp_per_hotspot"] + 1.0)

    # Cross-Sensor Physical & Radiative
    d["Terra_Aqua_Harmonic_Mean"] = (2.0 * d["MODIS_Terra_Count"] * d["MODIS_Aqua_Count"]) / (d["MODIS_Total_Count"] + 1.0)
    d["FRP_to_Count_Power"] = np.sqrt(np.maximum(0.0, d["MODIS_FRP_Sum"])) / (d["MODIS_Total_Count"] + 1.0)

    # Log Transforms & Non-linear Interaction
    d["log_MODIS_Count"] = np.log1p(d["MODIS_Total_Count"])
    d["log_MODIS_FRP"] = np.log1p(d["MODIS_FRP_Sum"])
    d["count_x_high_conf"] = d["MODIS_Total_Count"] * d["High_Confidence_Ratio"]

    # Multi-Order Fourier Seasonality
    d["sin_month_1"] = np.sin(2.0 * np.pi * d["Month"] / 12.0)
    d["cos_month_1"] = np.cos(2.0 * np.pi * d["Month"] / 12.0)
    d["sin_month_2"] = np.sin(4.0 * np.pi * d["Month"] / 12.0)
    d["cos_month_2"] = np.cos(4.0 * np.pi * d["Month"] / 12.0)

    # Autoregressive Lag & Rolling Statistics
    d["MODIS_Count_Lag1"] = d["MODIS_Total_Count"].shift(1).bfill()
    d["MODIS_Count_Lag2"] = d["MODIS_Total_Count"].shift(2).bfill()
    d["MODIS_Count_Lag12"] = d["MODIS_Total_Count"].shift(12).bfill()
    d["Rolling_Mean_3M"] = d["MODIS_Total_Count"].rolling(window=3, min_periods=1).mean()
    d["Rolling_Std_3M"] = d["MODIS_Total_Count"].rolling(window=3, min_periods=1).std().fillna(0.0)
    d["Rolling_Max_6M"] = d["MODIS_Total_Count"].rolling(window=6, min_periods=1).max()
    d["MoM_Momentum"] = d["MODIS_Total_Count"] - d["MODIS_Count_Lag1"]
    d["Centered_Window_Momentum"] = d["MODIS_Total_Count"] - d["Rolling_Mean_3M"]

    monthly_clim = d.groupby("Month")["MODIS_Total_Count"].transform("mean")
    d["Seasonal_Climatology_Baseline"] = monthly_clim
    d["Seasonal_Expected_MODIS_Ratio"] = d["MODIS_Total_Count"] / (d["Seasonal_Climatology_Baseline"] + 1.0)

    # Expanding Seasonal Target Encoding (Zero Data Leakage)
    exp_ratios = np.full(len(d), 0.55, dtype=float)
    for i in range(len(d)):
        cur_month = d.loc[i, "Month"]
        past_hist = d.loc[:max(0, i - 1)]
        past_overlap = past_hist[past_hist["Year"] >= 2012].dropna(subset=["VIIRS_Count"])
        if len(past_overlap) >= 12:
            m_sub = past_overlap[past_overlap["Month"] == cur_month]
            if len(m_sub) >= 2 and m_sub["MODIS_Total_Count"].sum() > 0:
                exp_ratios[i] = m_sub["VIIRS_Count"].sum() / m_sub["MODIS_Total_Count"].sum()
            else:
                exp_ratios[i] = past_overlap["VIIRS_Count"].sum() / max(1.0, past_overlap["MODIS_Total_Count"].sum())
        else:
            exp_ratios[i] = 0.55

    d["Expanding_Monthly_Ratio"] = np.clip(exp_ratios, 0.15, 2.50)
    d["Target_Encoded_Expected_VIIRS"] = d["MODIS_Total_Count"] * d["Expanding_Monthly_Ratio"]

    # Environmental Context
    d["NDVI_Fuel_Index"] = d["NDVI_Proxy"] if "NDVI_Proxy" in d else 0.50

    feature_cols = [
        "MODIS_Total_Count", "MODIS_Terra_Count", "MODIS_Aqua_Count", "Aqua_to_Terra_Ratio",
        "MODIS_FRP_Sum", "MODIS_Max_Peak_FRP", "High_Confidence_Ratio", "frp_per_hotspot",
        "frp_density_index", "Terra_Aqua_Harmonic_Mean", "FRP_to_Count_Power", "log_MODIS_Count",
        "log_MODIS_FRP", "count_x_high_conf", "sin_month_1", "cos_month_1", "sin_month_2",
        "cos_month_2", "MODIS_Count_Lag1", "MODIS_Count_Lag2", "MODIS_Count_Lag12",
        "Rolling_Mean_3M", "Rolling_Std_3M", "Rolling_Max_6M", "MoM_Momentum",
        "Centered_Window_Momentum", "Seasonal_Climatology_Baseline", "Seasonal_Expected_MODIS_Ratio",
        "Expanding_Monthly_Ratio", "Target_Encoded_Expected_VIIRS",
        "Surface_Temp_K", "NDVI_Fuel_Index",
    ]
    return d, feature_cols


# ---------------------------------------------------------------------------
# 2. Model Architectures & Deep Learning Pipelines
# ---------------------------------------------------------------------------
class StatisticalScalingBaseline(BaseEstimator, RegressorMixin):
    def __init__(self, col_idx: int = 0):
        self.col_idx = col_idx
        self.scaling_ratio_ = 1.0

    def fit(self, X: Any, y: Any):
        X_arr = np.asarray(X, dtype=float)
        y_arr = np.asarray(y, dtype=float)
        self.scaling_ratio_ = float(np.sum(y_arr) / max(1e-6, np.sum(X_arr[:, self.col_idx])))
        return self

    def predict(self, X: Any) -> np.ndarray:
        X_arr = np.asarray(X, dtype=float)
        return np.clip(X_arr[:, self.col_idx] * self.scaling_ratio_, 0.0, None)


class PhysicsInformedDeepMLP(BaseEstimator, RegressorMixin):
    def __init__(self, hidden_layer_sizes: Tuple[int, ...] = (128, 64, 32), alpha: float = 0.5, random_state: int = 42):
        self.hidden_layer_sizes = hidden_layer_sizes
        self.alpha = alpha
        self.random_state = random_state
        self.scaler = StandardScaler()
        self.mlp = MLPRegressor(
            hidden_layer_sizes=self.hidden_layer_sizes,
            activation="relu",
            solver="adam",
            alpha=self.alpha,
            learning_rate="adaptive",
            max_iter=2000,
            random_state=self.random_state,
            early_stopping=True,
            n_iter_no_change=25,
            validation_fraction=0.15,
        )
        self.ratio_ = 1.0

    def fit(self, X: Any, y: Any):
        X_arr = np.asarray(X, dtype=float)
        y_arr = np.asarray(y, dtype=float)
        self.ratio_ = float(np.sum(y_arr) / max(1.0, np.sum(X_arr[:, 0])))
        base_pred = X_arr[:, 0] * self.ratio_
        target_mult = np.clip(y_arr / (base_pred + 1.0), 0.1, 4.0)
        X_sc = self.scaler.fit_transform(X_arr)
        self.mlp.fit(X_sc, target_mult)
        return self

    def predict(self, X: Any) -> np.ndarray:
        X_arr = np.asarray(X, dtype=float)
        base_pred = X_arr[:, 0] * self.ratio_
        X_sc = self.scaler.transform(X_arr)
        mult = np.clip(self.mlp.predict(X_sc), 0.1, 4.0)
        return np.clip(base_pred * mult, 0.0, None)


class TemporalSequenceMLP(BaseEstimator, RegressorMixin):
    def __init__(self, hidden_layer_sizes: Tuple[int, ...] = (64, 32, 16), alpha: float = 1.0, random_state: int = 42):
        self.hidden_layer_sizes = hidden_layer_sizes
        self.alpha = alpha
        self.random_state = random_state
        self.scaler = StandardScaler()
        self.mlp = MLPRegressor(
            hidden_layer_sizes=self.hidden_layer_sizes,
            activation="relu",
            solver="adam",
            alpha=self.alpha,
            learning_rate="adaptive",
            max_iter=2000,
            random_state=self.random_state,
            early_stopping=True,
            n_iter_no_change=25,
            validation_fraction=0.15,
        )
        self.indices = [0, 18, 19, 20, 21, 24, 29, 14, 15, 16, 17]

    def fit(self, X: Any, y: Any):
        X_sub = np.asarray(X, dtype=float)[:, self.indices]
        X_sc = self.scaler.fit_transform(X_sub)
        self.mlp.fit(X_sc, y)
        return self

    def predict(self, X: Any) -> np.ndarray:
        X_sub = np.asarray(X, dtype=float)[:, self.indices]
        X_sc = self.scaler.transform(X_sub)
        return np.clip(self.mlp.predict(X_sc), 0.0, None)


class HuberTreeBlend(BaseEstimator, RegressorMixin):
    def __init__(self, random_state: int = 42):
        self.random_state = random_state
        self.gbr = GradientBoostingRegressor(
            loss="huber", alpha=0.9, n_estimators=250, max_depth=3,
            learning_rate=0.035, subsample=0.85, random_state=random_state
        )
        self.etr = ExtraTreesRegressor(
            n_estimators=250, max_depth=7, min_samples_leaf=2,
            random_state=random_state, n_jobs=-1
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
        self.weights_ = np.array([0.05, 0.10, 0.10, 0.75])

    def fit(self, X: Any, y: Any):
        tscv_in = TimeSeriesSplit(n_splits=4)
        oof_meta = np.zeros((len(y), 4), dtype=float)
        oof_mask = np.zeros(len(y), dtype=bool)
        estimators = [self.m_huber, self.m_deep, self.m_seq, self.m_tree]

        for tr_i, val_i in tscv_in.split(X):
            for k, est in enumerate(estimators):
                c_est = clone(est)
                c_est.fit(X[tr_i], y[tr_i])
                oof_meta[val_i, k] = c_est.predict(X[val_i])
            oof_mask[val_i] = True

        P = oof_meta[oof_mask]
        y_m = np.asarray(y)[oof_mask]

        def loss_fn(w: np.ndarray) -> float:
            return float(mean_squared_error(y_m, P @ w))

        res = minimize(
            loss_fn,
            [0.05, 0.10, 0.10, 0.75],
            bounds=[(0, 1)] * 4,
            constraints={"type": "eq", "fun": lambda w: np.sum(w) - 1.0},
        )
        self.weights_ = res.x

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


def get_model_by_name(model_name: str) -> BaseEstimator:
    m_dict = {
        "SpectraNet Hybrid Super-Learner (Stacking)": SpectraNetHybridStacking(random_state=42),
        "Huber-Loss GBDT & ExtraTrees Blend": HuberTreeBlend(random_state=42),
        "Deep Multi-Layer Neural Network (MLP-ResNet)": PhysicsInformedDeepMLP(random_state=42),
        "Temporal Sequence Neural Network (1D-MLP)": TemporalSequenceMLP(random_state=42),
        "Huber Robust Linear Regressor": Pipeline([("scaler", RobustScaler()), ("huber", HuberRegressor(max_iter=1500, alpha=1.35))]),
        "Statistical Scaling Baseline": StatisticalScalingBaseline(col_idx=0),
    }
    return m_dict.get(model_name, HuberTreeBlend(random_state=42))


# ---------------------------------------------------------------------------
# 3. Time-Series Cross-Validation Benchmark Suite
# ---------------------------------------------------------------------------
def run_model_benchmark(
    df_feat: pd.DataFrame,
    feature_cols: List[str],
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    df_train = df_feat[df_feat["Year"] >= 2012].dropna(subset=["VIIRS_Count", "VIIRS_FRP_Sum"]).copy().reset_index(drop=True)
    X = df_train[feature_cols].values
    y_cnt = df_train["VIIRS_Count"].values
    y_frp = df_train["VIIRS_FRP_Sum"].values

    models = {
        "1. Statistical Scaling Baseline": StatisticalScalingBaseline(col_idx=0),
        "2. Huber Robust Linear Regressor": Pipeline([("scaler", RobustScaler()), ("huber", HuberRegressor(max_iter=1500, alpha=1.35))]),
        "3. Deep Multi-Layer Neural Network (MLP-ResNet)": PhysicsInformedDeepMLP(random_state=42),
        "4. Temporal Sequence Neural Network (1D-MLP)": TemporalSequenceMLP(random_state=42),
        "5. Huber-Loss GBDT & ExtraTrees Blend": HuberTreeBlend(random_state=42),
        "6. SpectraNet Hybrid Super-Learner (Stacking)": SpectraNetHybridStacking(random_state=42),
    }

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
        yt_f, yp_f = y_frp[mask], oof_f[mask]

        cv_r2 = r2_score(yt_c, yp_c)
        cv_mae = mean_absolute_error(yt_c, yp_c)
        cv_rmse = float(np.sqrt(mean_squared_error(yt_c, yp_c)))
        valid_m = yt_c >= 5.0
        cv_mape = float(
            np.mean(np.abs((yt_c[valid_m] - yp_c[valid_m]) / yt_c[valid_m])) * 100.0
            if np.any(valid_m)
            else np.mean(np.abs(yt_c - yp_c) / np.maximum(1.0, yt_c)) * 100.0
        )
        cv_r2_frp = r2_score(yt_f, yp_f)

        final_c = clone(base_model)
        final_f = clone(base_model) if not isinstance(base_model, StatisticalScalingBaseline) else StatisticalScalingBaseline(col_idx=frp_col_idx)
        final_c.fit(X, y_cnt)
        final_f.fit(X, y_frp)

        full_r2 = r2_score(y_cnt, final_c.predict(X))

        fitted_cnt[name] = final_c
        fitted_frp[name] = final_f

        rows.append({
            "Model": name,
            "CV_R2_Score": round(cv_r2, 4),
            "Full_Overlap_R2": round(full_r2, 4),
            "CV_MAE": round(cv_mae, 2),
            "CV_RMSE": round(cv_rmse, 2),
            "CV_MAPE_%": round(cv_mape, 2),
            "FRP_CV_R2": round(cv_r2_frp, 4),
        })

    leaderboard = pd.DataFrame(rows).sort_values(by="CV_RMSE", ascending=True).reset_index(drop=True)
    return leaderboard, {"fitted_count": fitted_cnt, "fitted_frp": fitted_frp}


# ---------------------------------------------------------------------------
# 4. Harmonization & Emissions Execution Engine
# ---------------------------------------------------------------------------
def apply_harmonization(
    df_feat: pd.DataFrame,
    feature_cols: List[str],
    selected_model_name: str,
    fitted_dict: Optional[Dict[str, Any]] = None,
) -> pd.DataFrame:
    d = df_feat.copy()
    X_all = d[feature_cols].values

    if fitted_dict and selected_model_name in fitted_dict["fitted_count"]:
        model_cnt = fitted_dict["fitted_count"][selected_model_name]
        model_frp = fitted_dict["fitted_frp"][selected_model_name]
    else:
        df_train = d[d["Year"] >= 2012].dropna(subset=["VIIRS_Count", "VIIRS_FRP_Sum"]).copy()
        X_train = df_train[feature_cols].values
        y_train_c = df_train["VIIRS_Count"].values
        y_train_f = df_train["VIIRS_FRP_Sum"].values

        clean_name = selected_model_name.split(". ")[-1] if ". " in selected_model_name else selected_model_name
        model_cnt = get_model_by_name(clean_name)
        frp_col_idx = feature_cols.index("MODIS_FRP_Sum")
        model_frp = get_model_by_name(clean_name) if not isinstance(model_cnt, StatisticalScalingBaseline) else StatisticalScalingBaseline(col_idx=frp_col_idx)

        model_cnt.fit(X_train, y_train_c)
        model_frp.fit(X_train, y_train_f)

    d["ML_Predicted_VIIRS_Count"] = np.round(np.clip(model_cnt.predict(X_all), 0.0, None), 1)
    d["ML_Predicted_VIIRS_FRP"] = np.round(np.clip(model_frp.predict(X_all), 0.0, None), 2)

    # 50/50 fusion during overlap (2012-2025) to avoid double-counting
    d["Harmonized_Hotspots"] = np.where(
        d["Year"] < 2012,
        d["ML_Predicted_VIIRS_Count"],
        np.round(0.50 * d["ML_Predicted_VIIRS_Count"] + 0.50 * d["VIIRS_Count"], 1),
    )
    d["Harmonized_FRP_MW"] = np.where(
        d["Year"] < 2012,
        d["ML_Predicted_VIIRS_FRP"],
        np.round(0.50 * d["ML_Predicted_VIIRS_FRP"] + 0.50 * d["VIIRS_FRP_Sum"], 2),
    )

    # NASA Biomass & Carbon / Aerosol Emissions Physics
    effective_burn_s = 3600.0
    biomass_conv_kg_mj = 0.368
    ef_co2 = 1.615
    ef_pm25 = 0.0091

    d["FRE_Energy_MJ"] = np.round(d["Harmonized_FRP_MW"] * effective_burn_s, 1)
    d["Burned_Biomass_Tons"] = np.round((d["FRE_Energy_MJ"] * biomass_conv_kg_mj) / 1000.0, 2)
    d["CO2_Emissions_Tons"] = np.round(d["Burned_Biomass_Tons"] * ef_co2, 2)
    d["PM25_Smoke_Tons"] = np.round(d["Burned_Biomass_Tons"] * ef_pm25, 3)

    return d


# ---------------------------------------------------------------------------
# 5. Burning Activity Calendar Matrix & Climatology
# ---------------------------------------------------------------------------
def build_burning_activity_calendar_matrix(df: pd.DataFrame) -> pd.DataFrame:
    pivot = (
        df.pivot(index="Year", columns="Month", values="Harmonized_Hotspots")
        .reindex(columns=range(1, 13))
    )
    pivot.columns = MONTH_NAMES
    return pivot


def compute_monthly_climatology(df: pd.DataFrame) -> Tuple[pd.DataFrame, float, float]:
    clim = (
        df.groupby("Month", as_index=False)
        .agg(
            Mean_Hotspots=("Harmonized_Hotspots", "mean"),
            Std_Hotspots=("Harmonized_Hotspots", "std"),
            Median_Hotspots=("Harmonized_Hotspots", "median"),
            Max_Hotspots=("Harmonized_Hotspots", "max"),
            Mean_CO2_Tons=("CO2_Emissions_Tons", "mean"),
        )
    )
    clim["Month_Name"] = MONTH_NAMES

    q25 = float(np.percentile(clim["Mean_Hotspots"], 25))
    q75 = float(np.percentile(clim["Mean_Hotspots"], 75))

    def classify(v: float) -> str:
        if v >= q75:
            return "Peak Burning Season"
        elif v <= q25:
            return "Quiet Season"
        return "Moderate Activity"

    clim["Season_Class"] = clim["Mean_Hotspots"].apply(classify)
    return clim, q25, q75


def compute_annual_anomalies(df: pd.DataFrame) -> pd.DataFrame:
    annual = (
        df.groupby("Year", as_index=False)
        .agg(Annual_Harmonized_Total=("Harmonized_Hotspots", "sum"))
    )
    base_mean = float(annual["Annual_Harmonized_Total"].mean())
    base_std = float(max(1e-6, annual["Annual_Harmonized_Total"].std()))
    annual["Z_Score_Anomaly"] = (annual["Annual_Harmonized_Total"] - base_mean) / base_std
    return annual


# ---------------------------------------------------------------------------
# 6. 6-Month Forward Predictive Forecaster
# ---------------------------------------------------------------------------
def generate_6month_forecast(
    df_hist: pd.DataFrame,
    clim_df: pd.DataFrame,
    q25: float,
    q75: float,
    horizon: int = 6,
) -> pd.DataFrame:
    h = df_hist.copy().sort_values(["Year", "Month"]).reset_index(drop=True)
    clim_map = dict(zip(clim_df["Month"], clim_df["Mean_Hotspots"]))
    clim_std_map = dict(zip(clim_df["Month"], clim_df["Std_Hotspots"]))
    month_to_class = dict(zip(clim_df["Month"], clim_df["Season_Class"]))

    y_series = list(h["Harmonized_Hotspots"].values)
    years_list = list(h["Year"].values)
    months_list = list(h["Month"].values)

    def make_ar_features(idx: int, series: List[float], yr: int, mo: int) -> List[float]:
        lag1 = series[idx - 1] if idx >= 1 else series[0]
        lag2 = series[idx - 2] if idx >= 2 else lag1
        lag3 = series[idx - 3] if idx >= 3 else lag2
        lag12 = series[idx - 12] if idx >= 12 else clim_map[mo]
        lag24 = series[idx - 24] if idx >= 24 else lag12
        roll_mean_3 = float(np.mean(series[max(0, idx - 3):idx])) if idx >= 1 else lag1
        roll_max_6 = float(np.max(series[max(0, idx - 6):idx])) if idx >= 1 else lag1
        sin1 = float(np.sin(2.0 * np.pi * mo / 12.0))
        cos1 = float(np.cos(2.0 * np.pi * mo / 12.0))
        sin2 = float(np.sin(4.0 * np.pi * mo / 12.0))
        cos2 = float(np.cos(4.0 * np.pi * mo / 12.0))
        clim_base = float(clim_map[mo])
        trend_idx = float(yr - 2001)
        return [lag1, lag2, lag3, lag12, lag24, roll_mean_3, roll_max_6, sin1, cos1, sin2, cos2, clim_base, trend_idx]

    X_ar, y_ar = [], []
    for i in range(12, len(y_series)):
        X_ar.append(make_ar_features(i, y_series, years_list[i], months_list[i]))
        y_ar.append(y_series[i])

    rf_forecaster = RandomForestRegressor(n_estimators=250, max_depth=8, min_samples_leaf=2, random_state=42, n_jobs=-1)
    rf_forecaster.fit(np.asarray(X_ar, dtype=float), np.asarray(y_ar, dtype=float))

    last_date = h["Date"].max()
    forecast_rows = []

    for step in range(1, horizon + 1):
        next_date = last_date + pd.DateOffset(months=step)
        f_yr = int(next_date.year)
        f_mo = int(next_date.month)
        cur_idx = len(y_series)

        feat_vec = np.asarray(make_ar_features(cur_idx, y_series, f_yr, f_mo), dtype=float).reshape(1, -1)
        tree_preds = np.array([tree.predict(feat_vec)[0] for tree in rf_forecaster.estimators_])
        mean_pred = float(np.clip(np.mean(tree_preds), 0.0, None))

        tree_std = float(np.std(tree_preds))
        seasonal_std = float(clim_std_map[f_mo]) * 0.35
        combined_se = float(np.sqrt(tree_std**2 + seasonal_std**2) * (1.0 + 0.05 * (step - 1)))

        ci_lower = float(np.clip(mean_pred - 1.96 * combined_se, 0.0, None))
        ci_upper = float(mean_pred + 1.96 * combined_se)

        y_series.append(mean_pred)
        years_list.append(f_yr)
        months_list.append(f_mo)

        season_status = month_to_class.get(f_mo, "Moderate Activity")
        forecast_rows.append({
            "Date": next_date,
            "Year": f_yr,
            "Month": f_mo,
            "Month_Name": MONTH_NAMES[f_mo - 1],
            "Forecast_Hotspots": round(mean_pred, 1),
            "CI_95_Lower": round(ci_lower, 1),
            "CI_95_Upper": round(ci_upper, 1),
            "Projected_Season_Class": season_status,
            "Early_Warning_Alert": (
                "🚨 HIGH ALERT: Peak Fire Season"
                if mean_pred >= q75 or season_status == "Peak Burning Season"
                else ("⚠️ WATCH: Moderate Burning" if mean_pred > q25 else "✅ Quiet Season")
            ),
        })

    return pd.DataFrame(forecast_rows)

