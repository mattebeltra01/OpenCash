import streamlit as st

st.title("Mappa delle Spese")

if 'df' in st.session_state:
    df = st.session_state['df']
    
    st.write("File caricato")

    if st.button("Vai alla Home"):
        st.switch_page("app.py")
else:
    st.error("⚠️ Nessun dato trovato. Torna alla Home e carica un file CSV per visualizzare le analisi.")
    if st.button("Vai alla Home"):
        st.switch_page("app.py") # Cambia con il nome del tuo file principale se diverso