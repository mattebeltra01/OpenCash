import streamlit as st
import pandas as pd
import plotly.express as px
import json # <-- AGGIUNTO per leggere il config

st.set_page_config(page_title="Dashboard Patrimonio", layout="wide")

# --- CODICE DI SICUREZZA ---
if 'utente' not in st.session_state:
    st.session_state['utente'] = "Ospite" 

if 'df' not in st.session_state or st.session_state['df'] is None:
    st.warning("⚠️ Nessun dato caricato. Torna alla Home per caricare il tuo file CSV.")
    if st.button("Vai alla Home"):
        st.switch_page("app.py")
    st.stop()
# ---------------------------

# --- CARICAMENTO CONFIGURAZIONE ---
# Leggiamo i saldi iniziali dal JSON
try:
    with open("models/config.json", "r") as f:
        config_data = json.load(f)
        
    utente_corrente = st.session_state['utente']
    # Recupera i saldi iniziali in modo sicuro, se non ci sono restituisce un dizionario vuoto
    saldi_iniziali = config_data.get(utente_corrente, {}).get("saldi iniziali", {})
except FileNotFoundError:
    st.error("⚠️ File models/config.json non trovato.")
    saldi_iniziali = {}
# ----------------------------------

st.title(f"📊 Dashboard di {st.session_state['utente']}")

if 'df' in st.session_state:
    df = st.session_state['df'].copy()
    df['Valore'] = pd.to_numeric(df['Valore'], errors='coerce').fillna(0)
    
    # --- LOGICA DI FILTRAGGIO ---
    df_entrate = df[(df['Conto Uscita'] == '-') & (df['Conto Entrata'] != '-')]
    df_uscite = df[(df['Conto Uscita'] != '-') & (df['Conto Entrata'] == '-')]
    
    # --- CALCOLO KPI ---
    tot_entrate = df_entrate['Valore'].sum()
    tot_uscite = df_uscite['Valore'].sum()
    flusso_netto = tot_entrate - tot_uscite
    
    # EXTRA: Calcoliamo il patrimonio totale (Saldi Iniziali + Flusso Netto)
    totale_saldi_iniziali = sum(saldi_iniziali.values())
    patrimonio_totale = totale_saldi_iniziali + flusso_netto
    
    # --- SEZIONE KPI (Metriche) ---
    col1, col2, col3, col4 = st.columns(4) # <-- Passato a 4 colonne per mostrare il Patrimonio
    
    with col1:
        st.metric(label="📈 Entrate Totali", value=f"€ {tot_entrate:,.2f}")
    with col2:
        st.metric(label="📉 Uscite Totali", value=f"€ {tot_uscite:,.2f}")
    with col3:
        st.metric(
            label="⚖️ Flusso Netto", 
            value=f"€ {flusso_netto:,.2f}", 
            delta=f"{flusso_netto:,.2f} €",
            delta_color="normal"
        )
    with col4:
        st.metric(label="💰 Patrimonio Totale", value=f"€ {patrimonio_totale:,.2f}")
    
    st.divider()
    
    # --- SEZIONE GRAFICI ---
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.subheader("Distribuzione Spese per Categoria")
        if not df_uscite.empty:
            fig_spese = px.pie(
                df_uscite, 
                values='Valore', 
                names='Categoria', 
                hole=0.4,
                color_discrete_sequence=px.colors.sequential.RdBu
            )
            st.plotly_chart(fig_spese, use_container_width=True)
        else:
            st.info("Nessuna spesa registrata.")

    with col_right:
        st.subheader("Utilizzo dei Conti (Uscite)")
        if not df_uscite.empty:
            spese_conti = df_uscite.groupby('Conto Uscita')['Valore'].sum().reset_index()
            fig_conti = px.bar(
                spese_conti, 
                x='Conto Uscita', 
                y='Valore',
                text_auto='.2s',
                color='Conto Uscita',
                color_discrete_sequence=px.colors.qualitative.Safe
            )
            st.plotly_chart(fig_conti, use_container_width=True)
        else:
            st.info("Dati insufficienti per i conti.")

    # --- SEZIONE ANDAMENTO CONTI NEL TEMPO ---
    st.subheader("📈 Andamento dei Conti")
    
    df['Data'] = pd.to_datetime(df['Data'], utc=True)
    
    # Movimenti in USCITA
    df_out = df[df['Conto Uscita'] != '-'][['Data', 'Conto Uscita', 'Valore']].copy()
    df_out = df_out.rename(columns={'Conto Uscita': 'Conto'})
    df_out['Variazione'] = -df_out['Valore'] 
    
    # Movimenti in ENTRATA
    df_in = df[df['Conto Entrata'] != '-'][['Data', 'Conto Entrata', 'Valore']].copy()
    df_in = df_in.rename(columns={'Conto Entrata': 'Conto'})
    df_in['Variazione'] = df_in['Valore'] 
    
    df_movimenti = pd.concat([df_out, df_in]).sort_values('Data')
    
    # 5. Calcoliamo il saldo progressivo per ogni conto (SOLO VARIAZIONI)
    df_movimenti['Saldo Progressivo'] = df_movimenti.groupby('Conto')['Variazione'].cumsum()
    
    # AGGIUNTA: Mappiamo i saldi iniziali e li sommiamo al saldo progressivo
    # .map() cerca il nome del conto nel dizionario e restituisce il valore iniziale. 
    # .fillna(0) gestisce i conti che magari non sono presenti nel file config.
    df_movimenti['Saldo Progressivo'] += df_movimenti['Conto'].map(saldi_iniziali).fillna(0)
    
    if not df_movimenti.empty:
        fig_andamento = px.line(
            df_movimenti, 
            x='Data', 
            y='Saldo Progressivo', 
            color='Conto',
            markers=True, 
            labels={'Saldo Progressivo': 'Saldo Progressivo (€)', 'Data': 'Data Operazione'},
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        st.plotly_chart(fig_andamento, use_container_width=True)
    else:
        st.info("Nessun movimento temporale da mostrare.")
        
    st.divider()

    # --- TABELLA ULTIME TRANSAZIONI ---
    st.subheader("📝 Ultime operazioni registrate")
    st.dataframe(df.head(10), use_container_width=True)

else:
    st.error("⚠️ Nessun dato trovato. Torna alla Home e carica un file CSV per visualizzare le analisi.")
    if st.button("Vai alla Home"):
        st.switch_page("app.py")