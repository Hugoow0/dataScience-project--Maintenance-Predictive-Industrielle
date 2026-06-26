import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import joblib

st.set_page_config(page_title="Performance des Modèles", layout="wide")
st.header("🏆 Comparaison des Performances & Feature Importance")

# --- CHARGEMENT DU MODÈLE POUR L'IMPORTANCE ---
# Assurez-vous que le chemin vers votre modèle est correct.
# Le modèle doit être un pipeline sklearn ou un modèle avec .coef_ ou .feature_importances_.
@st.cache_resource
def load_model():
    try:
        # Chemin relatif depuis dashboard/pages/ vers models/
        model_path = "../../models/best_model.joblib" 
        model_pipeline = joblib.load(model_path)
        return model_pipeline
    except FileNotFoundError:
        st.error(f"Modèle non trouvé à l'emplacement : {model_path}")
        return None
    except Exception as e:
        st.error(f"Erreur lors du chargement du modèle : {e}")
        return None

model_pipeline = load_model()

col1, col2 = st.columns(2)

with col1:
    st.subheader("Métriques globales")
    # Exemple de tableau comparatif - Remplacez par vos vrais scores générés par Dev 2 dans reports/
    data_perf = {
        "Modèle": ["Régression Logistique", "Random Forest", "XGBoost"],
        "Accuracy": [0.8523, 0.9145, 0.9310], 
        "Précision": [0.83, 0.90, 0.91],
        "Recall": [0.78, 0.88, 0.89],
        "F1-Score": [0.80, 0.89, 0.90]
    }
    st.table(pd.DataFrame(data_perf))
    
with col2:
    st.subheader("Analyse des variables influentes")
    if model_pipeline and "df" in st.session_state:
        try:
            df = st.session_state["df"]
            # Extraire le modèle et les noms de colonnes du pipeline
            # Ceci est un exemple, adaptez-le à la structure réelle de votre pipeline
            model = model_pipeline.named_steps.get("model", model_pipeline) # Tente d'obtenir 'model' ou utilise le pipeline entier
            
            # Tente d'obtenir les noms de caractéristiques après prétraitement
            try:
                # Si le préprocesseur est un ColumnTransformer, get_feature_names_out() est utile
                features = model_pipeline.named_steps["prep"].get_feature_names_out()
            except AttributeError:
                # Fallback si pas de get_feature_names_out ou pas de 'prep' step
                features = df.drop(columns=['failure_within_24h', 'timestamp', 'machine_id'], errors='ignore').columns.tolist()

            if hasattr(model, 'feature_importances_'):
                importances = model.feature_importances_
            elif hasattr(model, 'coef_'):
                importances = np.abs(model.coef_[0])
            else:
                st.info("Le modèle ne supporte pas l'extraction directe de l'importance des variables (feature_importances_ ou coef_).")
                importances = None

            if importances is not None and len(features) == len(importances):
                df_importance = pd.DataFrame({
                    'Capteur': features,
                    'Importance': importances
                }).sort_values(by='Importance', ascending=True)
                
                fig_imp = px.bar(df_importance, x='Importance', y='Capteur', orientation='h', title="Importance des variables")
                st.plotly_chart(fig_imp, use_container_width=True)
            else:
                st.info("Impossible d'afficher l'importance des variables. Vérifiez la correspondance entre les caractéristiques et les importances.")

        except Exception as e:
            st.error(f"Erreur lors de l'affichage de l'importance des variables : {e}")
    else:
        st.info("Le graphique d'importance s'affichera une fois le modèle entraîné et sauvegardé, et les données chargées.")
