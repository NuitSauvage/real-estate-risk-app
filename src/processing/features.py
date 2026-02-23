from __future__ import annotations
import pandas as pd

def make_city_features(prices: pd.DataFrame) -> pd.DataFrame:
    """
    Build city-level features:
    - last_price
    - 12m_return
    - rolling_vol (monthly)
    """

    # Sort to ensure groupby time operations (pct_change, rolling, shift) are computed chronologically
    df = prices.sort_values(["city", "date"]).copy()

    # Convert to month start timestamps to standardize the time index
    df["month"] = df["date"].dt.to_period("M").dt.to_timestamp()

    # Monthly average price per sqm per city
    m = df.groupby(["city", "month"], as_index=False)["price_per_sqm"].mean()

    # Monthly returns per city
    m["ret"] = m.groupby("city")["price_per_sqm"].pct_change()

    # Volatility proxy rolling 6-month standard deviation of monthly returns (per city)
    m["vol_6m"] = (
        m.groupby("city")["ret"]
        .rolling(6)
        .std()
        .reset_index(level=0, drop=True) # aligns the rolling output back to the original rows
    )

    # Latest available month per city
    last = m.sort_values(["city", "month"]).groupby("city").tail(1)[
        ["city", 
         "price_per_sqm", 
         "vol_6m"
    ]
    ].rename(columns={"price_per_sqm": "last_price"})

    # 12-month return: compare the latest monthly price to the price 12 months earlier
    # ret_12m will be NaN for cities with < 13 months of data
    m["price_12m_ago"] = m.groupby("city")["price_per_sqm"].shift(12)
    m["ret_12m"] = (m["price_per_sqm"] / m["price_12m_ago"]) - 1.0

    ret12 = m.sort_values(["city", 
                           "month"
                        ]
                    ).groupby("city").tail(1)[["city", 
                                               "ret_12m"
                                            ]
                                        ]
    
    # Final feature table (one row per city)
    feats = last.merge(ret12, on="city", how="left")
    return feats