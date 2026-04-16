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

# Inizializziamo l'utente se non esiste
if 'utente' not in st.session_state:
    st.session_state['utente'] = "Matteo" # Default

# Creiamo il selettore nella sidebar
st.sidebar.markdown("---")
st.sidebar.subheader("👤 Profilo Attivo")

utente_scelto = st.sidebar.radio(
    "Seleziona Utente:",
    ["Matteo", "Tea"],
    key = "utente",
    horizontal=True
)

# Aggiorniamo lo stato se l'utente cambia
if utente_scelto != st.session_state['utente']:
    st.session_state['utente'] = utente_scelto
    st.rerun() # Ricarica per aggiornare i testi in tutta la pagina

st.title("OpenCash - NetWorth Tracker")
st.write("Welcome to OpenCash. Use the sidebar to navigate.")
st.write(f"Stai visualizzando i dati di: **{st.session_state['utente']}**")

uploaded_file = st.file_uploader("Carica il tuo file CSV", type="csv")

if uploaded_file is not None:
    # Se il file è caricato e non è ancora nello stato, lo salviamo
    if 'df' not in st.session_state:
        st.session_state['df'] = load_data(uploaded_file)
        st.success("File caricato con successo!")

# Controllo se il df esiste prima di procedere
if 'df' in st.session_state:
    st.write("Anteprima dati della sessione")
    st.dataframe(st.session_state['df'].head())
    st.write("Hai caricato un file con", len(st.session_state['df']), "righe")
else:
    st.info("Carica un file CSV prima di iniziare")
