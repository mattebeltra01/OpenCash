import streamlit as st
import pandas as pd
import plotly.express as px
import json

from components.config_loader import get_valuta, get_colore_tema, get_saldi_iniziali, load_user_config

st.set_page_config(page_title="Dashboard Patrimonio", layout="wide")

if 'utente' not in st.session_state:
    st.session_state['utente'] = "Ospite"

if 'df' not in st.session_state or st.session_state['df'] is None:
    st.warning("⚠️ Nessun dato caricato. Torna alla Home per caricare il tuo file CSV.")
    if st.button("Vai alla Home"):
        st.switch_page("app.py")
    st.stop()

utente_corrente = st.session_state['utente']
saldi_iniziali = get_saldi_iniziali(utente_corrente)
valuta = get_valuta(utente_corrente)
colore_tema = get_colore_tema(utente_corrente)

st.title(f"📊 Dashboard di {utente_corrente}")

if 'df' in st.session_state:
    df = st.session_state['df'].copy()
    df['Valore'] = pd.to_numeric(df['Valore'], errors='coerce').fillna(0)

    df_entrate = df[(df['Conto Uscita'] == '-') & (df['Conto Entrata'] != '-')]
    df_uscite = df[(df['Conto Uscita'] != '-') & (df['Conto Entrata'] == '-')]
    df_trasferimenti = df[(df['Conto Uscita'] != '-') & (df['Conto Entrata'] != '-')]

    tot_entrate = df_entrate['Valore'].sum()
    tot_uscite = df_uscite['Valore'].sum()
    flusso_netto = tot_entrate - tot_uscite

    totale_saldi_iniziali = sum(saldi_iniziali.values())
    patrimonio_totale = totale_saldi_iniziali + flusso_netto

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(label="📈 Entrate Totali", value=f"{valuta} {tot_entrate:,.2f}")
    with col2:
        st.metric(label="📉 Uscite Totali", value=f"{valuta} {tot_uscite:,.2f}")
    with col3:
        st.metric(
            label="⚖️ Flusso Netto",
            value=f"{valuta} {flusso_netto:,.2f}",
            delta=f"{flusso_netto:,.2f} {valuta}",
            delta_color="normal"
        )
    with col4:
        st.metric(label="💰 Patrimonio Totale", value=f"{valuta} {patrimonio_totale:,.2f}")

    st.divider()

    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("Distribuzione Spese per Categoria")
        if not df_uscite.empty:
            fig_spese = px.pie(
                df_uscite,
                values='Valore',
                names='Categoria',
                hole=0.4,
                color_discrete_sequence=[colore_tema] + px.colors.qualitative.Set2
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
                color_discrete_sequence=[colore_tema]
            )
            st.plotly_chart(fig_conti, use_container_width=True)
        else:
            st.info("Dati insufficienti per i conti.")

    st.subheader("📈 Andamento dei Conti")

    df['Data'] = pd.to_datetime(df['Data'], utc=True, errors='coerce')

    df_out = df[df['Conto Uscita'] != '-'][['Data', 'Conto Uscita', 'Valore']].copy()
    df_out = df_out.rename(columns={'Conto Uscita': 'Conto'})
    df_out['Variazione'] = -df_out['Valore']

    df_in = df[df['Conto Entrata'] != '-'][['Data', 'Conto Entrata', 'Valore']].copy()
    df_in = df_in.rename(columns={'Conto Entrata': 'Conto'})
    df_in['Variazione'] = df_in['Valore']

    df_movimenti = pd.concat([df_out, df_in]).sort_values('Data')
    df_movimenti['Saldo Progressivo'] = df_movimenti.groupby('Conto')['Variazione'].cumsum()
    df_movimenti['Saldo Progressivo'] += df_movimenti['Conto'].map(saldi_iniziali).fillna(0)

    if not df_movimenti.empty:
        fig_andamento = px.line(
            df_movimenti,
            x='Data',
            y='Saldo Progressivo',
            color='Conto',
            markers=True,
            labels={'Saldo Progressivo': f'Saldo Progressivo ({valuta})', 'Data': 'Data Operazione'},
            color_discrete_sequence=[colore_tema] + px.colors.qualitative.Pastel
        )
        st.plotly_chart(fig_andamento, use_container_width=True)
    else:
        st.info("Nessun movimento temporale da mostrare.")

    if not df_trasferimenti.empty:
        st.divider()
        st.subheader("🔄 Trasferimenti tra Conti")
        st.write("Movimenti di denaro tra i tuoi conti (non sono entrate né uscite).")
        df_tf_display = df_trasferimenti[['Data', 'Conto Uscita', 'Conto Entrata', 'Valore', 'Note']].copy()
        df_tf_display['Data'] = pd.to_datetime(df_tf_display['Data'], utc=True, errors='coerce').dt.strftime('%d/%m/%Y')
        tot_trasferimenti = df_trasferimenti['Valore'].sum()
        st.metric("Totale Transferiti", value=f"{valuta} {tot_trasferimenti:,.2f}")
        st.dataframe(df_tf_display.sort_values('Data', ascending=False), use_container_width=True)

    st.divider()

    st.subheader("📝 Ultime operazioni registrate")
    st.dataframe(df.head(10), use_container_width=True)

    user_conf = load_user_config(utente_corrente)
    ricorrenti = user_conf.get("transazioni_ricorrenti", [])
    if ricorrenti:
        st.divider()
        st.subheader("🔄 Transazioni Ricorrenti Programmate")
        st.write("Queste transazioni si ripetono ogni mese. Non sono ancora registrate nei dati.")
        df_ric = pd.DataFrame(ricorrenti)
        if 'valore' in df_ric.columns:
            df_ric['tipo'] = df_ric.apply(
                lambda r: 'Entrata' if r.get('conto_uscita', '-') == '-' and r.get('conto_entrata', '-') != '-' else 'Uscita',
                axis=1
            )
        st.dataframe(df_ric, use_container_width=True, hide_index=True)

else:
    st.error("⚠️ Nessun dato trovato. Torna alla Home e carica un file CSV per visualizzare le analisi.")
    if st.button("Vai alla Home"):
        st.switch_page("app.py")
