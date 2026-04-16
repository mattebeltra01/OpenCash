import streamlit as st
import pandas as pd
import plotly.express as px

from components.config_loader import get_valuta, get_colore_tema

st.set_page_config(page_title="Analisi Entrate", layout="wide")

if 'utente' not in st.session_state:
    st.session_state['utente'] = "Ospite"

if 'df' not in st.session_state or st.session_state['df'] is None:
    st.warning("⚠️ Nessun dato caricato. Torna alla Home per caricare il tuo file CSV.")
    if st.button("Vai alla Home"):
        st.switch_page("app.py")
    st.stop()

utente_corrente = st.session_state['utente']
valuta = get_valuta(utente_corrente)
colore_tema = get_colore_tema(utente_corrente)

st.title(f"💵 Analisi Entrate di {utente_corrente}")

if 'df' in st.session_state:
    df = st.session_state['df'].copy()

    df_entrate = df[(df['Conto Uscita'] == '-') & (df['Conto Entrata'] != '-')].copy()
    df_entrate['Valore'] = pd.to_numeric(df_entrate['Valore'], errors='coerce').fillna(0)
    df_entrate['Data'] = pd.to_datetime(df_entrate['Data'], utc=True, errors='coerce')

    st.subheader("📅 Filtro Temporale")

    tipo_periodo = st.radio(
        "Scegli il periodo di analisi:",
        ["Tutto il periodo", "Annuale", "Mensile", "Periodo Personalizzato"],
        horizontal=True
    )

    df_filtrato = df_entrate.copy()
    totale_precedente = 0.0
    etichetta_delta = ""

    if not df_entrate.empty:
        if tipo_periodo == "Annuale":
            anni = sorted(df_entrate['Data'].dt.year.dropna().unique(), reverse=True)
            if len(anni) > 0:
                anno_selezionato = st.selectbox("Seleziona l'anno:", anni)
                df_filtrato = df_entrate[df_entrate['Data'].dt.year == anno_selezionato]
                anno_prec = anno_selezionato - 1
                totale_precedente = df_entrate[df_entrate['Data'].dt.year == anno_prec]['Valore'].sum()
                etichetta_delta = f"vs {anno_prec}"

        elif tipo_periodo == "Mensile":
            mesi = sorted(df_entrate['Data'].dt.to_period('M').dropna().unique(), reverse=True)
            if len(mesi) > 0:
                mesi_str = [str(m) for m in mesi]
                mese_selezionato_str = st.selectbox("Seleziona il mese:", mesi_str)
                df_filtrato = df_entrate[df_entrate['Data'].dt.to_period('M').astype(str) == mese_selezionato_str]
                mese_corrente_pd = pd.Period(mese_selezionato_str, freq='M')
                mese_prec_pd = mese_corrente_pd - 1
                totale_precedente = df_entrate[df_entrate['Data'].dt.to_period('M') == mese_prec_pd]['Valore'].sum()
                etichetta_delta = f"vs {mese_prec_pd}"

        elif tipo_periodo == "Periodo Personalizzato":
            df_valid = df_entrate.dropna(subset=['Data'])
            if not df_valid.empty:
                min_data = df_valid['Data'].min().date()
                max_data = df_valid['Data'].max().date()
                date_selezionate = st.date_input(
                    "Seleziona il range di date:",
                    value=(min_data, max_data),
                    min_value=min_data,
                    max_value=max_data
                )
                if len(date_selezionate) == 2:
                    data_inizio, data_fine = date_selezionate
                    data_inizio = pd.to_datetime(data_inizio).tz_localize('UTC')
                    data_fine = pd.to_datetime(data_fine).tz_localize('UTC')
                    df_filtrato = df_entrate[(df_entrate['Data'] >= data_inizio) & (df_entrate['Data'] <= data_fine)]
                    giorni_intervallo = (data_fine - data_inizio).days
                    data_fine_prec = data_inizio - pd.Timedelta(days=1)
                    data_inizio_prec = data_fine_prec - pd.Timedelta(days=giorni_intervallo)
                    df_prec = df_entrate[(df_entrate['Data'] >= data_inizio_prec) & (df_entrate['Data'] <= data_fine_prec)]
                    totale_precedente = df_prec['Valore'].sum()
                    etichetta_delta = "vs periodo equivalente prec."
                else:
                    st.info("Seleziona anche la data di fine per applicare il filtro.")

    st.divider()

    if df_filtrato.empty:
        st.warning("Nessuna entrata registrata nel periodo selezionato.")
    else:
        totale_corrente = df_filtrato['Valore'].sum()

        col_metric, _ = st.columns([1, 2])
        with col_metric:
            if tipo_periodo == "Tutto il periodo":
                st.metric(label="Totale Entrate", value=f"{valuta} {totale_corrente:,.2f}")
            else:
                differenza = totale_corrente - totale_precedente
                st.metric(
                    label=f"Totale Entrate ({tipo_periodo})",
                    value=f"{valuta} {totale_corrente:,.2f}",
                    delta=f"{valuta} {differenza:,.2f} {etichetta_delta}",
                    delta_color="normal"
                )

        col_left, col_right = st.columns(2)

        with col_left:
            st.subheader("Distribuzione Entrate per Categoria")
            if not df_filtrato.empty:
                fig_entrate = px.pie(
                    df_filtrato,
                    values='Valore',
                    names='Categoria',
                    hole=0.4,
                    color_discrete_sequence=[colore_tema] + px.colors.qualitative.Set2
                )
                st.plotly_chart(fig_entrate, use_container_width=True)
            else:
                st.info("Nessuna entrata registrata.")

        with col_right:
            st.subheader("Entrate per Conto")
            if not df_filtrato.empty:
                entrate_conti = df_filtrato.groupby('Conto Entrata')['Valore'].sum().reset_index()
                fig_conti = px.bar(
                    entrate_conti,
                    x='Conto Entrata',
                    y='Valore',
                    text_auto='.2s',
                    color='Conto Entrata',
                    color_discrete_sequence=[colore_tema]
                )
                st.plotly_chart(fig_conti, use_container_width=True)
            else:
                st.info("Dati insufficienti.")

        st.divider()

        categorie = ["Tutte"] + list(df_filtrato['Categoria'].dropna().unique())
        cat_selezionata = st.selectbox("Seleziona una categoria per il dettaglio:", categorie)

        if cat_selezionata != "Tutte":
            df_plot = df_filtrato[df_filtrato['Categoria'] == cat_selezionata]
        else:
            df_plot = df_filtrato

        col1, col2 = st.columns([2, 1])

        with col1:
            st.subheader(f"Dettaglio: {cat_selezionata}")
            dati_barre = df_plot.groupby('Sottocategoria')['Valore'].sum().reset_index()
            if not dati_barre.empty:
                fig_sub = px.bar(
                    dati_barre,
                    x='Sottocategoria', y='Valore',
                    color='Sottocategoria',
                    text_auto='.2s',
                    color_discrete_sequence=[colore_tema]
                )
                st.plotly_chart(fig_sub, use_container_width=True)
            else:
                st.info("Nessun dato per questa categoria nel periodo scelto.")

        with col2:
            st.subheader("Top 5 Entrate Singole")
            top_5 = df_plot.sort_values(by='Valore', ascending=False).head(5)
            for _, row in top_5.iterrows():
                data_str = row['Data'].strftime('%d/%m/%Y') if pd.notna(row['Data']) else "N/A"
                st.success(f"**{valuta} {row['Valore']:.2f}** - {row['Note']} ({row['Categoria']})\n\n📅 {data_str}")

        st.divider()

        st.subheader("📊 Andamento Entrate nel Tempo")
        df_mensile = df_entrate.dropna(subset=['Data']).copy()
        df_mensile['Mese_Anno'] = df_mensile['Data'].dt.to_period('M').astype(str)
        entrate_mensili = df_mensile.groupby('Mese_Anno')['Valore'].sum().reset_index()
        entrate_mensili = entrate_mensili.sort_values('Mese_Anno')

        if len(entrate_mensili) >= 2:
            fig_trend = px.line(
                entrate_mensili,
                x='Mese_Anno', y='Valore',
                markers=True,
                labels={'Mese_Anno': 'Mese', 'Valore': f'Entrate ({valuta})'},
                color_discrete_sequence=[colore_tema]
            )
            st.plotly_chart(fig_trend, use_container_width=True)
        else:
            st.info("Servono almeno 2 mesi di dati per il trend.")

        st.subheader("📊 Analisi di Incidenza Entrate")
        incidenza_df = df_filtrato.groupby('Categoria')['Valore'].sum().sort_values(ascending=False).reset_index()
        incidenza_df['Percentuale'] = (incidenza_df['Valore'] / incidenza_df['Valore'].sum()) * 100
        st.dataframe(incidenza_df.style.format({'Valore': f'{valuta} {{:.2f}}', 'Percentuale': '{:.1f}%'}), use_container_width=True)

else:
    st.error("Carica i dati nella Home!")
    if st.button("Vai alla Home"):
        st.switch_page("app.py")
