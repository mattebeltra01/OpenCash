import streamlit as st
import pandas as pd

# Funzione per caricare i dati (usiamo la cache per la velocità)
@st.cache_data
def load_data(uploaded_file):
    df = pd.read_csv(uploaded_file)
    # Mettere qui se c'è da fare una pulizia iniziale dei dati
    return df

st.set_page_config(
    page_icon="💰",
    page_title="OpenCash",
    layout="wide"
)

# 1. Inizializzazione Sessione
if 'df' not in st.session_state:
    st.session_state['df'] = None
if 'utente' not in st.session_state:
    st.session_state['utente'] = "Ospite"

st.title("OpenCash - NetWorth Tracker")

uploaded_file = st.file_uploader("Carica il tuo file CSV", type="csv")

if uploaded_file is not None:
    #1. Carichiamo i Dati
    st.session_state['df'] = pd.read_csv(uploaded_file)

    #2. Logica di riconoscimento dal Nome del file
    nome_file = uploaded_file.name.lower()

    if "matteo" in nome_file:
        st.session_state['utente'] = "Matteo"
        st.success(f"Bentornato **Matteo**! File riconosciuto correttamente.")
    elif "tea" in nome_file:
        st.session_state['utente'] = "Tea"
        st.success(f"Bentornato **Tea**! File riconosciuto correttamente.")
    else:
        st.session_state['utente'] = "Ospite"
        st.warning("File caricato, ma non ho riconosciuto il nome dell'utente nel file.")

    st.write("Anteprima dati della sessione")
    st.dataframe(st.session_state['df'].head())
    st.write("Hai caricato un file con", len(st.session_state['df']), "righe")

st.sidebar.info(f"Profilo Rilevato: **{st.session_state['utente']}**")
