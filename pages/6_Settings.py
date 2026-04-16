import streamlit as st

st.set_page_config(page_title="Impostazioni", layout="wide")

st.title("⚙️ Impostazioni Progetto")

# --- 1. GESTIONE CONTI ---
st.header("🏦 Gestione Conti e Portafogli")
st.write("Configura i nomi dei conti che utilizzi abitualmente.")

# Inizializziamo la lista conti se non esiste nello stato
if 'lista_conti' not in st.session_state:
    st.session_state['lista_conti'] = ["Banca1", "Banca2", "Banca3", "Contanti"]

# Layout per aggiungere nuovi conti
col_add, col_list = st.columns(2)

with col_add:
    nuovo_conto = st.text_input("Aggiungi un nuovo conto:", placeholder="Es: PayPal, Satispay...")
    if st.button("Aggiungi"):
        if nuovo_conto and nuovo_conto not in st.session_state['lista_conti']:
            st.session_state['lista_conti'].append(nuovo_conto)
            st.success(f"Conto '{nuovo_conto}' aggiunto!")
        else:
            st.warning("Nome non valido o già esistente.")

with col_list:
    st.write("**Conti attivi:**")
    for c in st.session_state['lista_conti']:
        st.code(c)

st.divider()

# --- 2. PRIVACY & VISUALIZZAZIONE ---
st.header("🕶️ Privacy e Visualizzazione")
col_p1, col_p2 = st.columns(2)

with col_p1:
    privacy_mode = st.toggle("Modalità Privacy", help="Nasconde gli importi totali nelle dashboard sostituendoli con asterischi.")
    if privacy_mode:
        st.info("La modalità privacy è attiva (Logica da implementare nelle altre pagine).")
        # Questa variabile può essere usata nelle altre pagine per fare: 
        # st.metric("Totale", "*** €" if st.session_state.get('privacy', False) else f"{valore} €")
        st.session_state['privacy'] = True
    else:
        st.session_state['privacy'] = False

with col_p2:
    st.write("Scegli il tema dei grafici:")
    tema_scelto = st.selectbox("Palette colori:", ["Pastel", "Safe", "Vivid", "Spectral"])
    st.session_state['tema_grafici'] = tema_scelto

st.divider()

# --- 3. MANUTENZIONE DATI ---
st.header("⚠️ Manutenzione Dati")
st.write("Attenzione: queste azioni sono irreversibili.")

col_del1, col_del2 = st.columns(2)

with col_del1:
    if st.button("🗑️ Svuota Sessione (Reset File)", use_container_width=True):
        if 'df' in st.session_state:
            del st.session_state['df']
            st.rerun()
        else:
            st.info("Nessun file caricato da eliminare.")

with col_del2:
    if st.button("🔄 Reset Impostazioni Budget", use_container_width=True):
        if 'budget' in st.session_state:
            del st.session_state['budget']
            st.success("Budget resettati ai valori di default.")
        else:
            st.info("Nessun budget personalizzato trovato.")

st.divider()
st.caption("Versione App: 1.0.0 | Sviluppato con Streamlit & Pandas")