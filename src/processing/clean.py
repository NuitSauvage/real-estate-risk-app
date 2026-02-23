from __future__ import annotations
import pandas as pd

def standardize_city_name(s: pd.Series) -> pd.Series:
    """Basic text standardization for city names."""

    return (
    s.astype(str) # Ensure string dtype
    .str.strip() # Remove leading/trailing whitespace
    .str.replace(r"\s+", " ", regex=True) # Collapse multiple internal spaces
    .str.upper() # Convert to uppercase for consistency
)

def clean_prices(df: pd.DataFrame) -> pd.DataFrame:
    """
    Expected columns (example): city, date, price_per_sqm
    """
    out = df.copy()

    # Normalize city identifiers to avoid duplicates caused by formatting inconsistencies
    out["city"] = standardize_city_name(out["city"])

    # Parse date
    out["date"] = pd.to_datetime(out["date"], errors="coerce")

    # Ensure numeric price column
    out["price_per_sqm"] = pd.to_numeric(out["price_per_sqm"], errors="coerce")

    # Remove incomplete observations (required for time-series features)
    out = out.dropna(subset=["city", "date", "price_per_sqm"])
    return out