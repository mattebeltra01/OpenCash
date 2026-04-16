import streamlit as st
import pandas as pd

st.set_page_config(page_title="Budgeting", layout="wide")

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

st.title(f"📊 Obiettivi e Budget di {st.session_state['utente']}")

if 'df' in st.session_state:
    df = st.session_state['df'].copy()
    df_uscite = df[(df['Conto Uscita'] != '-') & (df['Conto Entrata'] == '-')]
    df_uscite['Valore'] = pd.to_numeric(df_uscite['Valore'])

    st.title("🎯 Obiettivi di Spesa")

    # Inizializziamo un budget di default se non esiste
    if 'budget' not in st.session_state:
        st.session_state['budget'] = {cat: 500.0 for cat in df_uscite['Categoria'].unique()}

    st.sidebar.header("Imposta i tuoi limiti")
    for cat in st.session_state['budget'].keys():
        st.session_state['budget'][cat] = st.sidebar.number_input(
            f"Budget mensile {cat}", 
            value=float(st.session_state['budget'][cat]),
            step=50.0
        )

    st.subheader("Stato del Budget Attuale")
    
    # Calcolo spesa reale vs budget
    spesa_reale = df_uscite.groupby('Categoria')['Valore'].sum()
    
    for cat, limite in st.session_state['budget'].items():
        reale = spesa_reale.get(cat, 0)
        percentuale = min(reale / limite, 1.0) if limite > 0 else 0
        
        col_testo, col_bar = st.columns([1, 3])
        with col_testo:
            st.write(f"**{cat}**")
            st.caption(f"Speso: € {reale:,.2f} / Limite: € {limite:,.2f}")
        
        with col_bar:
            # Colore barra: verde se < 80%, giallo se < 100%, rosso se oltre
            color = "green" if percentuale < 0.8 else "orange" if percentuale < 1.0 else "red"
            st.progress(percentuale)
            if reale > limite:
                st.toast(f"Hai superato il budget per {cat}!", icon="⚠️")

else:
    st.error("Carica i dati nella Home!")
    if st.button("Vai alla Home"):
        st.switch_page("app.py")