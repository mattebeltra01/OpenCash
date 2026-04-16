import streamlit as st
import pandas as pd

st.set_page_config(page_title="Ricerca Transazioni", layout="wide")

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

st.title(f"📊 Ricerca e Correzione di {st.session_state['utente']}")

if 'df' in st.session_state:
    df = st.session_state['df'].copy()
    
    st.title("🔍 Ricerca e Controllo Dati")
    st.write("Usa i filtri per trovare transazioni specifiche o controllare le note.")

    # --- FILTRI ---
    col1, col2, col3 = st.columns(3)
    
    with col1:
        search_query = st.text_input("Cerca nelle Note:", placeholder="Es: spesa, benzina...")
    
    with col2:
        filtro_conto = st.selectbox("Filtra per Conto:", ["Tutti"] + list(set(df['Conto Uscita'].unique()) | set(df['Conto Entrata'].unique())))

    with col3:
        min_val, max_val = st.slider("Intervallo di Importo (€):", 
                                     float(df['Valore'].min()), 
                                     float(df['Valore'].max()), 
                                     (0.0, float(df['Valore'].max())))

    # --- LOGICA DI FILTRAGGIO ---
    df_filtered = df.copy()
    
    if search_query:
        df_filtered = df_filtered[df_filtered['Note'].str.contains(search_query, case=False, na=False)]
    
    if filtro_conto != "Tutti":
        df_filtered = df_filtered[(df_filtered['Conto Uscita'] == filtro_conto) | (df_filtered['Conto Entrata'] == filtro_conto)]
    
    df_filtered = df_filtered[(df_filtered['Valore'] >= min_val) & (df_filtered['Valore'] <= max_val)]

    # --- DISPLAY ---
    st.metric("Risultati trovati", len(df_filtered))
    
    # Mostriamo la tabella con possibilità di ordinamento
    st.dataframe(df_filtered.sort_values(by='Data', ascending=False), use_container_width=True)

    # --- ESPORTAZIONE ---
    st.divider()
    csv_search = df_filtered.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Scarica i risultati filtrati in CSV",
        data=csv_search,
        file_name="ricerca_patrimonio.csv",
        mime="text/csv",
    )

else:
    st.error("Carica i dati nella Home!")
    if st.button("Vai alla Home"):
        st.switch_page("app.py") # Cambia con il nome del tuo file principale se diverso