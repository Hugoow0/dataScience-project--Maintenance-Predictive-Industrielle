Voici ce que Gemini m’a proposé je sais pas si c’est en adéquation avec ce qu on doit faire ou si c’est ce qui est deja dans performances\_Modeles ou simulation

#### **Utiliser les modèles pour faire des prédictions en temps réel**

Dans la page **"Simulation & Prédiction Temps Réel"** de ton menu Streamlit, tu vas récupérer les valeurs saisies par l'utilisateur (via des st.slider ou st.number\_input) et les passer dans le modèle choisi.  
Voici l'exemple de code à mettre dans ta page de prédiction pour voir comment traiter la donnée selon le modèle :

Python  
\# \--- DANS TA PAGE DE SIMULATION \---  
st.header("Simulation de panne sur une machine")

\# 1\. Collecte des données utilisateur (Exemple de features)  
vibration \= st.slider("Vibrations (RMS)", 0.0, 10.0, 2.5)  
temperature \= st.slider("Température Moteur (°C)", 20.0, 120.0, 65.0)  
type\_machine \= st.selectbox("Type de Machine", \["Type A", "Type B", "Type C"\])  
\# ... (ajoute toutes les 9 variables requises par tes modèles)

\# 2\. Création du DataFrame avec exactement les mêmes noms de colonnes que ton dataset  
input\_data \= pd.DataFrame(\[{  
    'vibration\_rms': vibration,  
    'temperature\_motor': temperature,  
    'machine\_type': type\_machine,  
    \# ... ajoute le reste des variables ici  
}\])

\# 3\. Choix du modèle par l'utilisateur  
choix\_modele \= st.selectbox("Choisir le modèle de prédiction", \["Random Forest (Pipeline)", "Ensemble (XGB/LGBM)", "Régression Logistique"\])

if st.button("Prédire l'état de la machine"):  
    if choix\_modele \== "Random Forest (Pipeline)":  
        \# Très simple : le pipeline gère le préprocessing (StandardScaler/OneHotEncoder) tout seul \!  
        prediction \= st.session\_state\["rf\_pipe"\].predict(input\_data)  
        probabilite \= st.session\_state\["rf\_pipe"\].predict\_proba(input\_data)\[0\]\[1\]

    elif choix\_modele \== "Régression Logistique":  
        \# Il faut d'abord transformer les données avec le préprocesseur dédié, puis prédire  
        data\_scaled \= st.session\_state\["lr\_prep"\].transform(input\_data)  
        prediction \= st.session\_state\["lr\_mdl"\].predict(data\_scaled)  
        probabilite \= st.session\_state\["lr\_mdl"\].predict\_proba(data\_scaled)\[0\]\[1\]  
          
    elif choix\_modele \== "Ensemble (XGB/LGBM)":  
        \# Attention : Assure-toi si ce modèle requiert les données brutes ou pré-traitées.  
        \# Si c'est un VotingClassifier Scikit-Learn sans pipeline intégré, passe-lui les données pré-traitées :  
        data\_scaled \= st.session\_state\["lr\_prep"\].transform(input\_data)   
        prediction \= st.session\_state\["ensemble\_mdl"\].predict(data\_scaled)  
        probabilite \= st.session\_state\["ensemble\_mdl"\].predict\_proba(data\_scaled)\[0\]\[1\]

    \# 4\. Affichage du résultat  
    if prediction\[0\] \== 1:  
        st.error(f"🚨 Risque élevé de Panne détecté \! (Probabilité : {probabilite:.2%})")  
    else:  
        st.success(f"✅ Machine stable. (Risque de panne : {probabilite:.2%})")

