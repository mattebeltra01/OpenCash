import streamlit as st
import pandas as pd
import json
import os
import plotly.graph_objects as go

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
    if os.path.exists('models/config.json'):
        with open('models/config.json', 'r') as f:
            config = json.load(f)
            return config.get(utente, {})
    return {}

user_conf = load_user_config(st.session_state['utente'])
budget_impostati = user_conf.get("budget", {})
extra_conf = user_conf.get("extra", {})

soglia_allerta = extra_conf.get("soglia_allerta_budget", 0.85)
target_risparmio = extra_conf.get("obiettivo_risparmio", 0.0) 

st.title(f"🎯 Obiettivi e Budget di {st.session_state['utente']}")

# --- 3. ANALISI SAVING RATE (ULTIMI 12 MESI) ---
st.subheader("📈 Analisi Risparmio Mensile")

# Creiamo una copia per non sporcare il dataframe originale
df_full = st.session_state['df'].copy()

# 1. PARSING DELLE DATE (Forziamo il formato europeo giorno/mese/anno)
df_full['Data'] = pd.to_datetime(df_full['Data'], dayfirst=True, errors='coerce')

df_full['Valore'] = pd.to_numeric(df_full['Valore'], errors='coerce').fillna(0)

# Creiamo la colonna Mese_Anno saltando le date invalide (NaT)
df_full = df_full.dropna(subset=['Data'])
df_full['Mese_Anno'] = df_full['Data'].dt.strftime('%Y-%m')

# 2. Raggruppamento Entrate e Uscite
entrate_m = df_full[(df_full['Conto Uscita'] == '-') & (df_full['Conto Entrata'] != '-')].groupby('Mese_Anno')['Valore'].sum()
uscite_m = df_full[(df_full['Conto Uscita'] != '-') & (df_full['Conto Entrata'] == '-')].groupby('Mese_Anno')['Valore'].sum()

# 3. Creazione DataFrame Risparmio
df_risparmio = pd.DataFrame({
    'Entrate': entrate_m,
    'Uscite': uscite_m
}).fillna(0)

# ---> OPZIONE NUCLEARE: Filtriamo via tutto ciò che viene prima del 2010 testualmente <---
df_risparmio = df_risparmio[df_risparmio.index >= '2010-01']

df_risparmio['Risparmio_Reale'] = df_risparmio['Entrate'] - df_risparmio['Uscite']

# 4. FILTRO ULTIMI 12 MESI
df_risparmio = df_risparmio.sort_index(ascending=True)
df_risparmio = df_risparmio.tail(12)

# DEBUG: Se vedi ancora problemi, de-commenta la riga qui sotto per vedere cosa c'è davvero nei dati
# st.write(df_risparmio)

# 5. VISUALIZZAZIONE GRAFICA
if not df_risparmio.empty:
    fig_saving = go.Figure()

    colori = [
        '#28A745' if val >= target_risparmio else '#FF4B4B' 
        for val in df_risparmio['Risparmio_Reale']
    ]

    fig_saving.add_trace(go.Bar(
        x=df_risparmio.index,
        y=df_risparmio['Risparmio_Reale'],
        marker_color=colori,
        name="Risparmio Effettivo"
    ))

    fig_saving.add_shape(
        type="line",
        x0=-0.5, x1=len(df_risparmio)-0.5,
        y0=target_risparmio, y1=target_risparmio,
        line=dict(color="rgba(0,0,0,0.5)", width=2, dash="dash"),
    )

    fig_saving.update_layout(
        height=350,
        margin=dict(l=20, r=20, t=30, b=20),
        xaxis_title="Mese",
        yaxis_title="Risparmio Netto (€)",
        showlegend=False,
        xaxis=dict(type='category') # <--- LA MAGIA È QUI: forza le etichette testuali senza creare spazi vuoti
    )

    st.plotly_chart(fig_saving, use_container_width=True)
    
    c1, c2, c3 = st.columns(3)
    media_risp = df_risparmio['Risparmio_Reale'].mean()
    mesi_ok = sum(1 for v in df_risparmio['Risparmio_Reale'] if v >= target_risparmio)
    
    c1.metric("Media Risparmio (12m)", f"€ {media_risp:,.2f}")
    c2.metric("Mesi Target Raggiunto", f"{mesi_ok} / {len(df_risparmio)}")
    c3.metric("Obiettivo Mensile", f"€ {target_risparmio:,.0f}")
else:
    st.info("📊 Non ci sono abbastanza dati validi per mostrare lo storico del risparmio.")

# --- 4. PREPARAZIONE DATI E FILTRO MESI ---
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

# --- 5. CALCOLO E VISUALIZZAZIONE BUDGET ---
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
            # 1. Calcolo percentuale per il CSS (max 100%)
            percent_css = min(reale / limite * 100, 100) if limite > 0 else 0
            
            # 2. Logica colori dinamici
            if reale >= limite:
                color_hex = "#FF4B4B" # Rosso Streamlit
            elif reale >= (limite * soglia_allerta):
                color_hex = "#FFA500" # Arancione
            else:
                color_hex = "#28A745" # Verde
            
            # 3. Creazione della barra HTML personalizzata
            st.markdown(
                f"""
                <div style="
                    background-color: #e0e0e0;
                    border-radius: 10px;
                    height: 20px;
                    width: 100%;
                    margin-top: 10px;
                ">
                    <div style="
                        background-color: {color_hex};
                        width: {percent_css}%;
                        height: 20px;
                        border-radius: 10px;
                        transition: width 0.5s ease-in-out;
                    ">
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
            
            # Messaggio di avviso sotto la barra se necessario
            if reale > limite and mese_selezionato == mesi_disponibili[0]:
                st.caption(f"⚠️ Hai sforato di € {(reale - limite):,.2f}!")

# Opzionale: Mostriamo le spese fuori budget (categorie in cui hai speso ma che non sono nel JSON)
categorie_spese_non_a_budget = [c for c in spesa_reale.index if c not in budget_impostati.keys()]
if categorie_spese_non_a_budget:
    st.markdown("---")
    st.caption("Spese in categorie senza un budget predefinito:")
    for cat in categorie_spese_non_a_budget:
        st.write(f"- {cat}: € {spesa_reale[cat]:,.2f}")