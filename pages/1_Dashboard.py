import streamlit as st
import pandas as pd
import plotly.express as px

# PRIMA istruzione della pagina
st.set_page_config(page_title="Dashboard Patrimonio", layout="wide")

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

st.title(f"📊 Dashboard di {st.session_state['utente']}")

if 'df' in st.session_state:
    # Recuperiamo il dataframe e assicuriamoci che i tipi siano corretti
    df = st.session_state['df'].copy()
    df['Valore'] = pd.to_numeric(df['Valore'], errors='coerce').fillna(0)
    
    # --- LOGICA DI FILTRAGGIO ---
    # Definiamo entrate e uscite basandoci sui conti
    df_entrate = df[(df['Conto Uscita'] == '-') & (df['Conto Entrata'] != '-')]
    df_uscite = df[(df['Conto Uscita'] != '-') & (df['Conto Entrata'] == '-')]
    
    # --- CALCOLO KPI ---
    tot_entrate = df_entrate['Valore'].sum()
    tot_uscite = df_uscite['Valore'].sum()
    flusso_netto = tot_entrate - tot_uscite
    
    # --- SEZIONE KPI (Metriche) ---
    col1, col2, col3 = st.columns(3)
    
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
    
    st.divider()
    
    # --- SEZIONE GRAFICI ---
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.subheader("Distribuzione Spese per Categoria")
        if not df_uscite.empty:
            # Grafico a torta delle spese
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
            # Grafico a barre dei conti di uscita
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
    
    # 1. Assicuriamoci che la colonna 'Data' sia un formato data comprensibile a Pandas
    df['Data'] = pd.to_datetime(df['Data'], utc=True)
    
    # 2. Creiamo una tabella con tutti i movimenti in USCITA (valori negativi)
    df_out = df[df['Conto Uscita'] != '-'][['Data', 'Conto Uscita', 'Valore']].copy()
    df_out = df_out.rename(columns={'Conto Uscita': 'Conto'})
    df_out['Variazione'] = -df_out['Valore'] # Mettiamo il meno perché i soldi escono
    
    # 3. Creiamo una tabella con tutti i movimenti in ENTRATA (valori positivi)
    df_in = df[df['Conto Entrata'] != '-'][['Data', 'Conto Entrata', 'Valore']].copy()
    df_in = df_in.rename(columns={'Conto Entrata': 'Conto'})
    df_in['Variazione'] = df_in['Valore'] # Positivo perché i soldi entrano
    
    # 4. Uniamo entrate e uscite e ordiniamo cronologicamente
    df_movimenti = pd.concat([df_out, df_in]).sort_values('Data')
    
    # 5. Calcoliamo il saldo progressivo per ogni conto
    df_movimenti['Saldo Progressivo'] = df_movimenti.groupby('Conto')['Variazione'].cumsum()
    
    # 6. Creiamo il grafico a linee con Plotly
    if not df_movimenti.empty:
        fig_andamento = px.line(
            df_movimenti, 
            x='Data', 
            y='Saldo Progressivo', 
            color='Conto',
            markers=True, # Aggiunge i puntini su ogni transazione
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
        st.switch_page("app.py") # Cambia con il nome del tuo file principale se diverso