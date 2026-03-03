from __future__ import annotations

from typing import Dict, Any

import numpy as np
import pandas as pd


def compute_gst_anomalies(gst_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Simple, non-ML anomaly scoring for GST data using z-scores
    over monthly taxable values.
    """
    if gst_df is None or gst_df.empty or "period" not in gst_df.columns or "taxable_value" not in gst_df.columns:
        return {"gst_anomaly_score": 0.0}

    monthly = gst_df.groupby("period")["taxable_value"].sum().sort_index()
    if len(monthly) < 3:
        return {"gst_anomaly_score": 0.0}

    mean = monthly.mean()
    std = monthly.std(ddof=0) or 1.0
    z_scores = (monthly - mean) / std

    max_abs_z = float(np.abs(z_scores).max())

    # Rolling window anomaly proxy
    rolling_mean = monthly.rolling(window=3, min_periods=2).mean()
    rolling_std = monthly.rolling(window=3, min_periods=2).std(ddof=0).replace(0, np.nan).fillna(1.0)
    rolling_z = (monthly - rolling_mean) / rolling_std
    max_abs_rolling_z = float(np.abs(rolling_z.dropna()).max()) if not rolling_z.dropna().empty else 0.0

    anomaly_score = max(0.0, min(1.0, max(max_abs_z, max_abs_rolling_z) / 5.0))

    return {
        "gst_anomaly_score": anomaly_score,
        "gst_max_abs_zscore": max_abs_z,
        "gst_max_abs_rolling_zscore": max_abs_rolling_z,
    }


def compute_bank_anomalies(bank_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Simple anomaly scoring for bank flows using monthly net flow
    volatility and extreme deviations.
    """
    if (
        bank_df is None
        or bank_df.empty
        or "date" not in bank_df.columns
        or "amount" not in bank_df.columns
    ):
        return {"bank_anomaly_score": 0.0}

    monthly = bank_df.copy()
    monthly["month"] = monthly["date"].dt.to_period("M")
    series = monthly.groupby("month")["amount"].sum().sort_index()
    if len(series) < 3:
        return {"bank_anomaly_score": 0.0}

    mean = series.mean()
    std = series.std(ddof=0) or 1.0
    z_scores = (series - mean) / std
    max_abs_z = float(np.abs(z_scores).max())

    rolling_mean = series.rolling(window=3, min_periods=2).mean()
    rolling_std = series.rolling(window=3, min_periods=2).std(ddof=0).replace(0, np.nan).fillna(1.0)
    rolling_z = (series - rolling_mean) / rolling_std
    max_abs_rolling_z = float(np.abs(rolling_z.dropna()).max()) if not rolling_z.dropna().empty else 0.0

    anomaly_score = max(0.0, min(1.0, max(max_abs_z, max_abs_rolling_z) / 5.0))

    return {
        "bank_anomaly_score": anomaly_score,
        "bank_max_abs_zscore": max_abs_z,
        "bank_max_abs_rolling_zscore": max_abs_rolling_z,
    }

