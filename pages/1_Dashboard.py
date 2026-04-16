import streamlit as st

st.title("Dashboard")

if 'df' in st.session_state:
    df = st.session_state['df']
else:
    st.error("Nessun dato trovato. Torna alla Home e carica un file.")