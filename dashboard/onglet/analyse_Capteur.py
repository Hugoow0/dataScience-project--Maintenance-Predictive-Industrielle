import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np  

st.set_page_config(page_title="Analyse des Capteurs", layout="wide")
st.header("Analyse Exploration des Données")

if "df" in st.session_state:
    df = st.session_state["df"]
    
    st.subheader("Distribution d'un capteur")
 
    numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
    if numeric_cols:
        capteur_choisi = st.selectbox("Sélectionnez un capteur :", numeric_cols)
        fig_hist = px.histogram(df, x=capteur_choisi, marginal="box", title=f"Distribution de {capteur_choisi}")
        st.plotly_chart(fig_hist, use_container_width=True)
    else:
        st.info("Aucune colonne numérique trouvée pour l'analyse de distribution.")
    
    st.subheader("Matrice de corrélation")
    corr = df.corr(numeric_only=True)
    if not corr.empty:

        fig_heatmap = px.imshow(corr, text_auto=True, aspect="auto", color_continuous_scale='RdBu_r', title="Corrélation entre les capteurs")
        st.plotly_chart(fig_heatmap, use_container_width=True)
    else:
        st.info("Impossible de calculer la matrice de corrélation avec les données actuelles.")
else:
    st.warning("Veuillez charger les données sur la page d'accueil (app.py).")