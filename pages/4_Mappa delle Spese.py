import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Mappa Spese", layout="wide")

# --- CODICE DI SICUREZZA ---
# Se l'utente apre direttamente questa pagina, inizializziamo 'utente' 
# per evitare il KeyError
if 'utente' not in st.session_state:
    st.session_state['utente'] = "Ospite" 

if 'df' not in st.session_state or st.session_state['df'] is None:
    # Se i dati mancano, mostriamo un messaggio e fermiamo l'esecuzione
    st.warning("⚠️ Nessun dato caricato. Torna alla Home per caricare il tuo file CSV.")
    if st.button("Vai alla Home"):
        st.switch_page("app.py") # Assicurati che il nome del file principale sia corretto
    
    st.stop()
# ---------------------------

st.title(f"📊 Mappa delle Spese di {st.session_state['utente']}")

if 'df' in st.session_state:
    df = st.session_state['df'].copy()
    
    # 1. Pulizia coordinate: separiamo la stringa "lat lon" in due colonne numeriche
    # La tua colonna Posizione è tipo: "44.9104 10.6516"
    df[['lat', 'lon']] = df['Posizione'].str.split(' ', expand=True).astype(float)
    df['Valore'] = pd.to_numeric(df['Valore'])

    st.title("📍 Mappa Geografica delle Spese")
    st.write("Visualizza dove effettui i tuoi acquisti più frequenti.")

    # Filtro per categoria sulla mappa
    cat_map = st.multiselect("Filtra per Categoria:", options=df['Categoria'].unique(), default=df['Categoria'].unique())
    df_map = df[df['Categoria'].isin(cat_map)]

    # Creazione della mappa con Plotly
    # NB: Richiede connessione internet per caricare i tile della mappa
    fig_map = px.scatter_mapbox(
        df_map, 
        lat="lat", 
        lon="lon", 
        size="Valore", 
        color="Categoria",
        hover_name="Note",
        hover_data={"Valore": True, "Sottocategoria": True, "lat": False, "lon": False},
        zoom=12, 
        height=600,
        mapbox_style="carto-positron" # Stile pulito e chiaro
    )

    st.plotly_chart(fig_map, use_container_width=True)

else:
    st.error("Carica i dati nella Home!")
    if st.button("Vai alla Home"):
        st.switch_page("app.py")