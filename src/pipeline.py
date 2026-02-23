import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from .config import RAW_DIR, PROCESSED_DIR

def load_raw_data():
    """
    Load raw datasets from the /data/raw directory.
    """

    # Main dataset
    df = pd.read_csv(RAW_DIR / "RES.csv", low_memory=False)

    # External macro indicators
    unemp = pd.read_csv(RAW_DIR / "Unemployment Connecticut.csv", delimiter=";")
    mort = pd.read_csv(RAW_DIR / "nmdb-new-mortgage-statistics-state-annual.csv")

    return df, unemp, mort

def clean_base(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean the housing transactions dataset:
    """
    # Drop irrelevant/high-missing text fields (safe drop with errors="ignore")
    df = df.drop(columns=["OPM remarks", "Assessor Remarks", "Non Use Code", "Location"], errors="ignore")

    # Keep only valid transactions with a sale amount and a location
    df = df[(df["Sale Amount"].notna()) & (df["Town"].notna())].copy()

    # Parse transaction date; invalid formats become NaT
    df["Date Recorded"] = pd.to_datetime(
        df["Date Recorded"], 
        errors="coerce",
        format="%m/%d/%Y"
    )

    # Create the year feature to join with yearly macro data
    df["Year"] = df["Date Recorded"].dt.year.fillna(0).astype(int)

    # Standardize missing categorical values to avoid NaNs later in modeling/EDA
    df["Property Type"] = df["Property Type"].fillna("No Information")
    df["Residential Type"] = df["Residential Type"].fillna("No Information")
    df["Address"] = df["Address"].fillna("No Information")

    # Rename for downstream readability
    df = df.rename(columns={"Date Recorded": "Transaction Date"})
    return df

def prep_unemployment(unemp: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare the unemployment dataset:
    """

    # Filter for selecting only the unemployment rate in Connecticut after 2000 to merge with the main data
    unemp = unemp[
        (unemp["State name"] == "Connecticut")
        & (unemp["Metric name"] == "unemployment rate")
        & (unemp["Year"] >= 2001)
    ].copy()

    # Remove id not needed for the model
    unemp = unemp.drop(
        columns=["State FIPS code",
                 "State abbreviation ", 
                 "State name", 
                 "Metric code", 
                 "Series ID", 
                 "Update date"
        ],
        errors="ignore"
    )
    
    # Rename and enforce numeric type
    unemp = unemp.rename(columns={"Value": "Unemployment Rate"})
    unemp["Unemployment Rate"] = unemp["Unemployment Rate"].astype(str).str.replace(",", ".").astype(float)

    # Aggregate by mean yearly (in case multiple entries exist per year)
    unemp = unemp.groupby("Year", as_index=False)[["Unemployment Rate"]].mean()
    return unemp

def prep_mortgage(mort: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare mortgage dataset:
    - 
    - Keep only (Year, Mortgage Value)
    - Impute missing values using the column mean
    - Aggregate to yearly mean
    """

    # Filter by All Mortgages in Connecticut after 2000
    mort = mort[
        (mort["GEONAME"] == "Connecticut")
        & (mort["MARKET"] == "All Mortgages")
        & (mort["YEAR"] >= 2001)
    ].copy()

    # Rename and keep only the relevant columns
    mort = mort.rename(columns={"YEAR": "Year", "VALUE1": "Mortgage Value"})
    mort = mort[["Year", "Mortgage Value"]].copy()

    # Aggregate by mean yearly (in case multiple entries exist per year)
    mort["Mortgage Value"] = mort["Mortgage Value"].fillna(mort["Mortgage Value"].mean())
    mort = mort.groupby("Year", as_index=False)[["Mortgage Value"]].mean()
    return mort

def feature_engineering(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create engineered features for risk scoring.
    """

    # Core ratio feature (beware division by zero if Assessed Value can be 0)
    df["Sales Ratio"] = df["Sale Amount"] / df["Assessed Value"]

    # Ensure Transaction Date is datetime and recompute Year from it when possible
    df["Transaction Date"] = pd.to_datetime(df["Transaction Date"], errors="coerce")
    df["Year"] = df["Transaction Date"].dt.year.fillna(df["Year"]).astype(int)

    # Volatility proxy computed from transaction prices
    yearly_std = df.groupby(["Town", "Year"])["Sale Amount"].std().reset_index()
    avg_vol = yearly_std.groupby("Town")["Sale Amount"].mean().reset_index()
    avg_vol.columns = ["Town", "avg_volatility_by_town"]

    # Town-level feature merged back to each transaction
    df = df.merge(avg_vol, on="Town", how="left")
    return df

def risk_scoring(df: pd.DataFrame) -> pd.DataFrame:
    """
    Build a simple composite risk score from:
    - Unemployment Rate (macro stress)
    - Mortgage Value (credit/mortgage market proxy)
    - avg_volatility_by_town (local price volatility proxy)
    """
    
    cols = ["Unemployment Rate", "Mortgage Value", "avg_volatility_by_town"]
    
    # Safety: avoid inf breaking scaler
    df[cols] = df[cols].replace([np.inf, -np.inf], np.nan)

    # Standardize
    scaler = StandardScaler()
    scaled = scaler.fit_transform(df[cols].fillna(df[cols].mean(numeric_only=True)))

    df["Unemployment_scaled"] = scaled[:, 0]
    df["Mortgage_scaled"] = scaled[:, 1]
    df["Volatility_scaled"] = scaled[:, 2]

    # Weighted risk score (baseline weights to have 1) 
    # Tune later with Regression, PCA or Convex combination of standardized risk drivers
    df["risk_score_scaled"] = (
        0.3 * df["Unemployment_scaled"] +
        0.3 * df["Mortgage_scaled"] +
        0.4 * df["Volatility_scaled"]
    )

    # Coarse risk tiers based on z-score thresholds
    df["risk_category"] = pd.cut(
        df["risk_score_scaled"],
        bins=[-np.inf, -0.5, 0.5, np.inf],
        labels=["Safe", "Neutral", "Risky"]
    )
    return df

def run_pipeline() -> pd.DataFrame:
    """
    Punpeline
    """
    # Load raw data
    df, unemp, mort = load_raw_data()

    # Cleaning
    df = clean_base(df)

    # Prepare macro datasets
    unemp = prep_unemployment(unemp)
    mort = prep_mortgage(mort)

    # Merge yearly macro indicators into each transaction
    df = df.merge(unemp, on="Year", how="left").merge(mort, on="Year", how="left")

    # Features Engineering
    df = feature_engineering(df)

    # Compute risk score + category
    df = risk_scoring(df)

    # Processed dataset for Downstream Modeling and Exploratory Analysis
    out = PROCESSED_DIR / "housing_risk.csv"

    # Save without index to keep a clean tabular structure
    df.to_csv(out, index=False)
    return df