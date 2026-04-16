import streamlit as st
import pandas as pd
from datetime import datetime

COLONNE_RICHIESTE = ["Data", "Posizione", "Valore", "Categoria", "Sottocategoria", "Note", "Conto Uscita", "Conto Entrata"]

@st.cache_data
def load_data(uploaded_file):
    df = pd.read_csv(uploaded_file)
    return df

st.set_page_config(
    page_icon="💰",
    page_title="OpenCash",
    layout="wide"
)

if 'df' not in st.session_state:
    st.session_state['df'] = None
if 'utente' not in st.session_state:
    st.session_state['utente'] = "Ospite"

st.title("OpenCash - NetWorth Tracker")

uploaded_file = st.file_uploader("Carica il tuo file CSV", type="csv")

if uploaded_file is not None:
    df_temp = pd.read_csv(uploaded_file)
    colonne_mancanti = [c for c in COLONNE_RICHIESTE if c not in df_temp.columns]
    if colonne_mancanti:
        st.error(f"Il file CSV non contiene le colonne richieste: **{', '.join(colonne_mancanti)}**")
        st.info(f"Colonne attese: {', '.join(COLONNE_RICHIESTE)}")
        st.stop()

    st.session_state['df'] = df_temp

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

    df_kpi = st.session_state['df'].copy()
    df_kpi['Valore'] = pd.to_numeric(df_kpi['Valore'], errors='coerce').fillna(0)
    df_kpi['Data'] = pd.to_datetime(df_kpi['Data'], utc=True, errors='coerce')
    oggi = datetime.now()
    inizio_mese = pd.Timestamp(oggi.year, oggi.month, 1, tz='UTC')
    spese_mese = df_kpi[(df_kpi['Conto Uscita'] != '-') & (df_kpi['Conto Entrata'] == '-') & (df_kpi['Data'] >= inizio_mese)]
    totale_spese_mese = spese_mese['Valore'].sum()
    st.metric(label=f"📉 Spese dal 1° {oggi.strftime('%B %Y')}", value=f"€ {totale_spese_mese:,.2f}")

    st.write("Anteprima dati della sessione")
    st.dataframe(st.session_state['df'].head())
    st.write("Hai caricato un file con", len(st.session_state['df']), "righe")

st.sidebar.info(f"Profilo Rilevato: **{st.session_state['utente']}**")
