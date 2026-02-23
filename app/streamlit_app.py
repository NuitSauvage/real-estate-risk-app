import sys
import os
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import importlib.util

# --- CRITICAL PATH SETUP (M2 VALIDATION) ---
current_file = Path(__file__).resolve()
root_dir = current_file.parents[1] 
src_dir = root_dir / "src"

# --- SMART IMPORT FOR API (Safe Loading) ---
def manual_import(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

try:
    # Mandatory API import for EUR conversion
    api_mod = manual_import("external_api", src_dir / "external_api.py")
    get_euro_conversion_rates = api_mod.get_euro_conversion_rates
except Exception as e:
    st.error(f"Critical Error: Could not load 'src/external_api.py'. Details: {e}")
    st.stop()

# --- APP SETTINGS ---
st.set_page_config(
    page_title="RE-Analytics Pro | Enterprise BI",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- WHITE LABEL PREMIUM DESIGN (CSS) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #ffffff; color: #1a1a1a; }
    section[data-testid="stSidebar"] { background-color: #f8f9fa !important; border-right: 1px solid #e0e0e0; }
    [data-testid="stMetric"] { 
        background: #f1f3f7; 
        border-left: 5px solid #007bff; 
        padding: 20px; 
        border-radius: 8px; 
    }
    .stTabs [data-baseweb="tab"] { font-weight: 600; padding: 10px 20px; }
    .stTabs [data-baseweb="tab--active"] { border-top: 3px solid #007bff !important; color: #007bff !important; }
    </style>
    """, unsafe_allow_html=True)

# --- EXTERNAL API & DATA ENGINE ---
conv_data = get_euro_conversion_rates()
usd_to_eur = conv_data["USD_TO_EUR"]

@st.cache_data
def load_and_transform(path):
    if not os.path.exists(path): return None
    data = pd.read_csv(path, low_memory=False)
    data["Transaction Date"] = pd.to_datetime(data["Transaction Date"], errors="coerce")
    data["Year"] = data["Transaction Date"].dt.year
    # Dynamic EUR conversion via API
    data["Sale Amount EUR"] = data["Sale Amount"] * usd_to_eur
    return data

DATA_PATH = root_dir / "data" / "processed" / "housing_risk.csv"
df = load_and_transform(DATA_PATH)

if df is None:
    st.error("Dataset 'housing_risk.csv' not found. Please check your data folder.")
    st.stop()

# --- SIDEBAR NAVIGATION (DOUBLE WINDOW LOGIC) ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3592/3592103.png", width=65)
    st.title("RE-Analytics BI")
    st.markdown("---")
    
    # Main Navigation
    page = st.radio("Navigation", 
                    ["🏠 Dashboard Principal", "🔍 Analyse Détaillée", "📈 Tendances Marché", "🗄️ Base de Données"])
    
    st.markdown("---")
    st.subheader("Filtres Globaux")
    towns = sorted(df["Town"].dropna().unique().tolist())
    selected_town = st.selectbox("Municipalité Target", towns, index=towns.index("Andover") if "Andover" in towns else 0)
    
    prop_types = sorted(df["Property Type"].dropna().unique().tolist())
    selected_props = st.multiselect("Segments Actifs", prop_types, default=prop_types)
    
    year_range = st.slider("Période Analyse", int(df["Year"].min()), int(df["Year"].max()), (2015, 2026))

# --- GLOBAL FILTERING ---
mask = (df["Town"] == selected_town) & \
       (df["Property Type"].isin(selected_props)) & \
       (df["Year"].between(year_range[0], year_range[1]))
f_df = df[mask].copy().sort_values("Transaction Date")

# --- UI WINDOWS RENDERING ---

if page == "🏠 Dashboard Principal":
    st.header(f"Executive Summary: {selected_town}")
    st.caption(f"Conversion EUR via API (Taux: 1 USD = {usd_to_eur:.4f} EUR)")
    
    # KPI Row
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Score Risque Moyen", f"{f_df['risk_score_scaled'].mean():.3f}")
    c2.metric("Prix Médian (€)", f"{f_df['Sale Amount EUR'].median():,.0f} €")
    c3.metric("Ratio Ventes", f"{f_df['Sales Ratio'].mean():.2f}")
    c4.metric("Volume Transac.", f"{len(f_df):,}")
    
    st.markdown("---")
    
    # Main Combined Chart
    st.subheader("Évolution du Risque et Liquidité")
    fig_main = go.Figure()
    fig_main.add_trace(go.Scatter(x=f_df["Transaction Date"], y=f_df["risk_score_scaled"], name="Risque Index", line=dict(color="#007bff")))
    fig_main.add_trace(go.Bar(x=f_df["Transaction Date"], y=f_df["Sale Amount EUR"], name="Volume (€)", yaxis="y2", opacity=0.3, marker_color="#28a745"))
    fig_main.update_layout(template="plotly_white", yaxis2=dict(overlaying="y", side="right"), legend=dict(orientation="h", y=1.1, x=1))
    st.plotly_chart(fig_main, use_container_width=True)

elif page == "🔍 Analyse Détaillée":
    st.header(f"Exploration de Données : {selected_town}")
    t1, t2 = st.tabs(["📊 Distribution", "⚖️ Corrélations"])
    
    with t1:
        st.subheader("Répartition par Catégorie de Risque")
        fig_pie = px.pie(f_df, names='risk_category', hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
        st.plotly_chart(fig_pie, use_container_width=True)
        
        st.subheader("Distribution des Prix par Type de Bien")
        fig_hist = px.histogram(f_df, x="Sale Amount EUR", color="Property Type", marginal="box", nbins=50, template="plotly_white")
        st.plotly_chart(fig_hist, use_container_width=True)
        
    with t2:
        st.subheader("Corrélation Prix vs Risque")
        fig_scatter = px.scatter(f_df, x="Sale Amount EUR", y="risk_score_scaled", color="risk_category", size="Sales Ratio", hover_name="Address", template="plotly_white")
        st.plotly_chart(fig_scatter, use_container_width=True)

elif page == "📈 Tendances Marché":
    st.header(f"Volatilité & Dynamique Immobilière : {selected_town}")
    v1, v2 = st.tabs(["📉 Volatilité Annuelle", "💰 Momentum des Prix"])
    
    with v1:
        st.subheader("Indice de Volatilité du Marché")
        # Protection contre colonne manquante
        v_col = 'volatility_scaled' if 'volatility_scaled' in f_df.columns else 'risk_score_scaled'
        vol_data = f_df.groupby('Year')[v_col].std().reset_index()
        fig_vol = px.line(vol_data, x="Year", y=v_col, markers=True, title="Volatilité Moyenne par An")
        st.plotly_chart(fig_vol, use_container_width=True)
        
    with v2:
        st.subheader("Progression des Prix Médian (€)")
        price_trend = f_df.groupby("Year")["Sale Amount EUR"].median().reset_index()
        fig_area = px.area(price_trend, x="Year", y="Sale Amount EUR", title="Évolution du Prix Médian")
        st.plotly_chart(fig_area, use_container_width=True)

elif page == "🗄️ Base de Données":
    st.header("Registre Propriétaire des Transactions")
    st.markdown(f"Affichage de **{len(f_df)}** entrées filtrées.")
    st.dataframe(f_df.head(1000), use_container_width=True)
    
    # Export Button
    csv = f_df.to_csv(index=False).encode('utf-8')
    st.download_button(label="📥 Télécharger l'Audit complet (CSV)", data=csv, file_name=f"audit_{selected_town}.csv", mime='text/csv')