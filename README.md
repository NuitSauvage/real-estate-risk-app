M2 Software Engineering Project – 2025/2026
Real Estate Market Risk Analyzer
Project Overview
This application is a professional data-driven tool built to compute a Market Risk Score for cities. Il transforme des données brutes en indicateurs stratégiques grâce à un pipeline de traitement automatisé et une interface décisionnelle.
The application:
Ingests real-time financial data via REST APIs (Requests).
Cleans and processes historical real estate datasets (Pandas, NumPy).
Analyzes market sentiment using Artificial Intelligence (LLM - NLP).
Computes a transparent risk score (High/Medium/Low) based on market volatility.
Provides a high-end interactive Streamlit dashboard with dual-currency auditing.
Is fully reproducible with Docker.
Group Members
HUANG Eric
LIU Yiyi
MHADJOU Samirdine
Main Features
Live Currency Conversion: Intégration d'une API de change pour convertir dynamiquement les prix USD en EUR.
AI Sentiment Analysis: Utilisation d'un modèle de Deep Learning pour évaluer l'impact des actualités sur le marché.
Dual-Currency Audit: Graphiques comparatifs Dollar vs Euro pour valider la précision des calculs.
Andover Focus: Configuration par défaut sur la municipalité d'Andover pour la démonstration.
White-Label UI: Design blanc pour expérience utilisateur professionnelle.
Project Architecture
Plaintext
real-estate-risk-app/
├── Dockerfile              # Application containerization
├── requirements.txt        # Python dependency manifest
├── app/
│   └── streamlit_app.py    # Main Streamlit dashboard (Enterprise UI)
├── src/                    # Source Code (Modular Logic)
│   ├── external_api.py     # REST API integration
│   ├── llm_utils.py        # AI / NLP Sentiment logic
│   ├── scraper.py          # News scraping logic
│   └── __init__.py         # Package initialization
├── data/
│   └── processed/          # Sanitized data (housing_risk.csv)
└── README.md               # Project documentation

Technologies Used
Python 3.11
Streamlit (User Interface)
Pandas & NumPy (Data Engineering)
Plotly (Dynamic Graphics)
Transformers (Hugging Face) (AI/LLM)
Requests (API Communications)
Docker (DevOps & Deployment)


How to run:
1. Prerequisites
Ensure you have Docker installed on your system.
2. Launching the Application
Execute the following commands in the project root:
Bash
# 1. Build the image
docker build -t real-estate-app .

# 2. Run the container
docker run -p 8501:8501 real-estate-app

Dashboard: Open your browser at http://localhost:8501.
Default View: The dashboard is pre-configured for Andover with automatic USD to EUR conversion.[README.md](https://github.com/user-attachments/files/25473915/README.md)
