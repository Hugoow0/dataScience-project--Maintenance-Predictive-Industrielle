import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from sklearn.metrics import confusion_matrix, accuracy_score
import joblib

# 1. UNIQUE CONFIGURATION DE LA PAGE
st.set_page_config(page_title="Dashboard Décisionnel Machine", layout="wide")
st.title("Dashboard Décisionnel & Analyse Prédictive")

# --- CHARGEMENT DES DONNÉES ET MODÈLES ---

@st.cache_data
def load_data():
    return pd.read_csv("donnees_machine.csv") 

@st.cache_resource
def load_models():
    lr = joblib.load("model_lr.pkl")
    svm = joblib.load("model_svm.pkl")
    return lr, svm

# Chargement du CSV
try:
    df = load_data()
    st.session_state["df"] = df 
    st.success("Données 'donnees_machine.csv' chargées avec succès !")
except Exception as e:
    st.error(f"Erreur lors du chargement des données : {e}")

# Chargement des modèles
try:
    model_lr, model_svm = load_models()
    st.session_state["model_lr"] = model_lr
    st.session_state["model_svm"] = model_svm
    st.session_state["X_features"] = df.drop(columns=['Panne'])
except Exception as e:
    st.error(f"Erreur lors du chargement des modèles : {e}")


# --- BARRE DE NAVIGATION ---
st.sidebar.header("Navigation")
page = st.sidebar.radio("Aller vers :", [
    "Analyse des Capteurs & Corrélations", 
    "Performance des Modèles", 
    "Simulation & Prédiction Temps Réel"
])

# --- LOGIQUE DE ROUTAGE (Le lien manquant) ---
# On lit et exécute le script correspondant selon le choix de l'utilisateur
if page == "Analyse des Capteurs & Corrélations":
    exec(open("onglet/analyse_Capteur.py", encoding="utf-8").read())

elif page == "Performance des Modèles":
    exec(open("onglet/performance_Modeles.py", encoding="utf-8").read())

elif page == "Simulation & Prédiction Temps Réel":
    exec(open("onglet/simulation.py", encoding="utf-8").read())