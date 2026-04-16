import streamlit as st

st.title("Assets")

if 'df' in st.session_state:
    df = st.session_state['df']
    
    st.write("File caricato")
else:
    st.error("Nessun dato trovato. Torna alla Home e carica un file.")