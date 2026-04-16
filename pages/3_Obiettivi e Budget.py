import streamlit as st
import pandas as pd
import json
import os

st.set_page_config(page_title="Budgeting", layout="wide")

# --- 1. CODICE DI SICUREZZA ---
if 'utente' not in st.session_state:
    st.session_state['utente'] = "Ospite" 

if 'df' not in st.session_state or st.session_state['df'] is None:
    st.warning("⚠️ Nessun dato caricato. Torna alla Home per caricare il tuo file CSV.")
    if st.button("Vai alla Home"):
        st.switch_page("app.py") # Assicurati che il nome del file principale sia corretto
    st.stop()

# --- 2. CARICAMENTO CONFIGURAZIONE DA JSON ---
def load_user_config(utente):
    if os.path.exists('settings.json'):
        with open('settings.json', 'r') as f:
            config = json.load(f)
            return config.get(utente, {})
    return {}

user_conf = load_user_config(st.session_state['utente'])
budget_impostati = user_conf.get("budget", {})
extra_conf = user_conf.get("extra", {})
soglia_allerta = extra_conf.get("soglia_allerta_budget", 0.85) # Default 85%

st.title(f"🎯 Obiettivi e Budget di {st.session_state['utente']}")

# --- 3. PREPARAZIONE DATI E FILTRO MESI ---
df = st.session_state['df'].copy()
df_uscite = df[(df['Conto Uscita'] != '-') & (df['Conto Entrata'] == '-')].copy()
df_uscite['Valore'] = pd.to_numeric(df_uscite['Valore'], errors='coerce').fillna(0)

# Convertiamo la colonna Data in formato datetime comprensibile da pandas
df_uscite['Data'] = pd.to_datetime(df_uscite['Data'], utc=True, errors='coerce')

# Creiamo una colonna con Anno e Mese (es: "2026-04")
df_uscite['Mese_Anno'] = df_uscite['Data'].dt.strftime('%Y-%m')

# Troviamo tutti i mesi unici presenti nel file, ordinati dal più recente al più vecchio
mesi_disponibili = sorted(df_uscite['Mese_Anno'].dropna().unique(), reverse=True)

if not mesi_disponibili:
    st.info("Nessuna spesa trovata nel file.")
    st.stop()

# Creiamo il selettore del mese (di default prende l'indice 0, ovvero il mese più recente)
mese_selezionato = st.selectbox("📅 Seleziona il mese da analizzare:", mesi_disponibili, index=0)

st.divider()

# --- 4. CALCOLO E VISUALIZZAZIONE BUDGET ---
st.subheader(f"Stato del Budget - {mese_selezionato}")

# Filtriamo i dati solo per il mese selezionato
df_mese = df_uscite[df_uscite['Mese_Anno'] == mese_selezionato]
spesa_reale = df_mese.groupby('Categoria')['Valore'].sum()

# Se l'utente non ha impostato nessun budget nel JSON
if not budget_impostati:
    st.warning("Non hai ancora impostato nessun budget! Vai nella pagina Impostazioni per configurarli.")
else:
    # Mostriamo le barre di progresso per ogni categoria configurata nel JSON
    for cat, limite in budget_impostati.items():
        reale = spesa_reale.get(cat, 0.0)
        percentuale = min(reale / limite, 1.0) if limite > 0 else 0
        
        col_testo, col_bar = st.columns([1, 3])
        with col_testo:
            st.write(f"**{cat}**")
            st.caption(f"Speso: € {reale:,.2f} / € {limite:,.2f}")
        
        with col_bar:
            # Calcolo dinamico del colore in base alla soglia impostata in settings.json
            if percentuale >= 1.0:
                color = "red"
            elif percentuale >= soglia_allerta:
                color = "orange"
            else:
                color = "green"
            
            st.progress(percentuale)
            
            # Notifica in tempo reale se hai sforato (solo se stai guardando il mese corrente/ultimo mese)
            if reale > limite and mese_selezionato == mesi_disponibili[0]:
                st.toast(f"Hai superato il budget mensile per {cat}!", icon="⚠️")

# Opzionale: Mostriamo le spese fuori budget (categorie in cui hai speso ma che non sono nel JSON)
categorie_spese_non_a_budget = [c for c in spesa_reale.index if c not in budget_impostati.keys()]
if categorie_spese_non_a_budget:
    st.markdown("---")
    st.caption("Spese in categorie senza un budget predefinito:")
    for cat in categorie_spese_non_a_budget:
        st.write(f"- {cat}: € {spesa_reale[cat]:,.2f}")