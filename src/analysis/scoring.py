from __future__ import annotations
import pandas as pd
import numpy as np

def zscore(s: pd.Series) -> pd.Series:
    """
    Compute standard score (z-score).

    Returns 0-vector if standard deviation is zero or undefined,
    preventing division-by-zero and NaN propagation.
    """
    mu = s.mean(skipna=True)
    sd = s.std(skipna=True)

    # Avoid division by zero or NaN std
    if sd == 0 or np.isnan(sd):
        return s * 0
    return (s - mu) / sd

def compute_risk_score(feats: pd.DataFrame) -> pd.DataFrame:
    """
    Simple interpretable score:
    risk = w1*vol + w2*max(0, -12m_return) + w3*price_z (optional “bubble” proxy)
    """
    df = feats.copy()

    # Volatility
    df["vol_z"] = zscore(df["vol_6m"].fillna(0))

    # Downside risk: only penalize negative returns
    df["downside"] = (-df["ret_12m"].fillna(0)).clip(lower=0)
    df["downside_z"] = zscore(df["downside"])

    # Price level proxy (valuation signal)
    df["price_z"] = zscore(df["last_price"].fillna(df["last_price"].median()))

    # Fixed interpretable weights
    w1, w2, w3 = 0.5, 0.35, 0.15 # Baseline, do the adjutment later
    df["risk_score"] = w1 * df["vol_z"] + w2 * df["downside_z"] + w3 * df["price_z"]

    # Normalize to 0–100 scale for visualization / dashboard usage
    mn, mx = df["risk_score"].min(), df["risk_score"].max()
    if mx > mn:
        df["risk_0_100"] = 100 * (df["risk_score"] - mn) / (mx - mn)
    else:
        df["risk_0_100"] = 50.0
    return df