import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Simulation & Prédiction", layout="wide")
st.header("🔮 Simulation & Prédiction Temps Réel")

# --- CONFIGURATION DE L'API ---
# L'URL de l'API doit être accessible depuis le dashboard.
# Si l'API tourne localement, assurez-vous que le port est exposé ou utilisez l'IP locale.
API_URL = "http://localhost:8000" # À adapter si l'API est déployée ailleurs

st.subheader("Saisissez les paramètres du scénario machine")

# Création des champs de saisie pour les capteurs
# Ces champs doivent correspondre aux schémas Pydantic de votre API (api/schemas.py)
with st.form("prediction_form"):
    machine_type = st.selectbox("Type de machine", ["CNC", "Robot", "Presse"])
    vibration_rms = st.slider("Vibration RMS", 0.0, 20.0, 5.0, step=0.1)
    temperature_motor = st.slider("Température Moteur (°C)", 0.0, 200.0, 60.0, step=0.5)
    current_phase_avg = st.slider("Courant Phase Moyen (A)", 0.0, 100.0, 20.0, step=0.1)
    pressure_level = st.slider("Niveau de Pression (bar)", 0.0, 50.0, 10.0, step=0.1)
    rpm = st.slider("RPM", 0, 10000, 1500)
    operating_mode = st.selectbox("Mode Opérationnel", ["idle", "normal", "high_load"])
    hours_since_maintenance = st.slider("Heures depuis Maintenance", 0.0, 5000.0, 100.0, step=10.0)
    ambient_temp = st.slider("Température Ambiante (°C)", 0.0, 50.0, 25.0, step=0.1)

    submitted = st.form_submit_button("Obtenir la Prédiction")

    if submitted:
        # Préparation des données pour l'API
        input_data = {
            "machine_type": machine_type,
            "vibration_rms": vibration_rms,
            "temperature_motor": temperature_motor,
            "current_phase_avg": current_phase_avg,
            "pressure_level": pressure_level,
            "rpm": rpm,
            "operating_mode": operating_mode,
            "hours_since_maintenance": hours_since_maintenance,
            "ambient_temp": ambient_temp,
        }

        try:
            response = requests.post(f"{API_URL}/predict", json=input_data)
            if response.status_code == 200:
                prediction_result = response.json()
                st.subheader("Résultat de la Prédiction")
                
                risk_level = prediction_result.get("risk_level", "UNKNOWN")
                probability = prediction_result.get("probability", 0.0)

                if risk_level == "HIGH":
                    st.error(f"**RISQUE ÉLEVÉ** de panne dans les 24h ! Probabilité : {probability:.1%}")
                elif risk_level == "MEDIUM":
                    st.warning(f"**RISQUE MOYEN** de panne dans les 24h. Probabilité : {probability:.1%}")
                else:
                    st.success(f" **RISQUE FAIBLE** de panne dans les 24h. Probabilité : {probability:.1%}")
                
                st.write(f"Version du modèle : {prediction_result.get("model_version", "N/A")}")

            else:
                st.error(f"Erreur de l'API : {response.status_code} - {response.json().get('detail', 'Erreur inconnue')}")
        except requests.exceptions.ConnectionError:
            st.error(f"Impossible de se connecter à l'API à l'adresse {API_URL}. Assurez-vous qu'elle est en cours d'exécution.")
        except Exception as e:
            st.error(f"Une erreur inattendue est survenue : {e}")


