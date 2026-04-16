import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Analisi Spese", layout="wide")

# --- CODICE DI SICUREZZA ---
if 'utente' not in st.session_state:
    st.session_state['utente'] = "Ospite" 

if 'df' not in st.session_state or st.session_state['df'] is None:
    st.warning("⚠️ Nessun dato caricato. Torna alla Home per caricare il tuo file CSV.")
    if st.button("Vai alla Home"):
        st.switch_page("app.py")
    st.stop()
# ---------------------------

st.title(f"📊 Analisi Spese di {st.session_state['utente']}")

if 'df' in st.session_state:
    df = st.session_state['df'].copy()
    
    # Filtriamo solo le uscite
    df_uscite = df[(df['Conto Uscita'] != '-') & (df['Conto Entrata'] == '-')].copy()
    df_uscite['Valore'] = pd.to_numeric(df_uscite['Valore'])
    
    # Assicuriamoci che la colonna 'Data' sia un formato datetime comprensibile
    df_uscite['Data'] = pd.to_datetime(df_uscite['Data'], utc=True)

    # --- SEZIONE FILTRO TEMPORALE ---
    st.subheader("📅 Filtro Temporale")
    
    # Scegliamo il tipo di visualizzazione
    tipo_periodo = st.radio(
        "Scegli il periodo di analisi:",
        ["Tutto il periodo", "Annuale", "Mensile", "Periodo Personalizzato"],
        horizontal=True
    )

    # Creiamo un DataFrame filtrato che inizialmente è uguale a tutte le uscite
    df_filtrato = df_uscite.copy()

    if not df_uscite.empty:
        if tipo_periodo == "Annuale":
            # Estraiamo gli anni unici presenti nei dati e li ordiniamo in modo decrescente
            anni = sorted(df_uscite['Data'].dt.year.unique(), reverse=True)
            anno_selezionato = st.selectbox("Seleziona l'anno:", anni)
            df_filtrato = df_uscite[df_uscite['Data'].dt.year == anno_selezionato]

        elif tipo_periodo == "Mensile":
            # Creiamo una lista di "Anno-Mese" (es. 2024-03) per il menu a tendina
            mesi = sorted(df_uscite['Data'].dt.to_period('M').unique(), reverse=True)
            # Convertiamo i periodi in stringhe per renderli leggibili nella selectbox
            mesi_str = [str(m) for m in mesi]
            mese_selezionato_str = st.selectbox("Seleziona il mese:", mesi_str)
            # Filtriamo usando la stringa
            df_filtrato = df_uscite[df_uscite['Data'].dt.to_period('M').astype(str) == mese_selezionato_str]

        elif tipo_periodo == "Periodo Personalizzato":
            min_data = df_uscite['Data'].min().date()
            max_data = df_uscite['Data'].max().date()
            
            # Il date_input restituisce una tupla. 
            date_selezionate = st.date_input(
                "Seleziona il range di date:",
                value=(min_data, max_data),
                min_value=min_data,
                max_value=max_data
            )
            
            # Controlliamo che l'utente abbia selezionato sia inizio che fine
            if len(date_selezionate) == 2:
                data_inizio, data_fine = date_selezionate
                # Convertiamo in datetime per il confronto con Pandas
                data_inizio = pd.to_datetime(data_inizio).tz_localize('UTC')
                data_fine = pd.to_datetime(data_fine).tz_localize('UTC')
                
                df_filtrato = df_uscite[(df_uscite['Data'] >= data_inizio) & (df_uscite['Data'] <= data_fine)]
            else:
                st.info("Seleziona anche la data di fine per applicare il filtro.")
    # --------------------------------

    st.divider()

    # Controlliamo se ci sono dati dopo aver applicato i filtri temporali
    if df_filtrato.empty:
        st.warning("Nessuna spesa registrata nel periodo selezionato. Prova a cambiare le date.")
    else:
        st.title("🔍 Analisi Dettagliata Spese")

        # Filtro Categoria basato SUI DATI FILTRATI
        categorie = ["Tutte"] + list(df_filtrato['Categoria'].dropna().unique())
        cat_selezionata = st.selectbox("Seleziona una categoria per il dettaglio:", categorie)

        if cat_selezionata != "Tutte":
            df_plot = df_filtrato[df_filtrato['Categoria'] == cat_selezionata]
        else:
            df_plot = df_filtrato

        col1, col2 = st.columns([2, 1])

        with col1:
            st.subheader(f"Sottocategorie: {cat_selezionata}")
            
            # Raggruppiamo i dati per il grafico
            dati_barre = df_plot.groupby('Sottocategoria')['Valore'].sum().reset_index()
            
            if not dati_barre.empty:
                fig_sub = px.bar(
                    dati_barre,
                    x='Sottocategoria', y='Valore',
                    color='Sottocategoria',
                    text_auto='.2s'
                )
                st.plotly_chart(fig_sub, use_container_width=True)
            else:
                st.info("Nessun dato per questa categoria nel periodo scelto.")

        with col2:
            st.subheader("Top 5 Spese Singole")
            top_5 = df_plot.sort_values(by='Valore', ascending=False).head(5)
            for _, row in top_5.iterrows():
                # Formattiamo la data per renderla più leggibile
                data_str = row['Data'].strftime('%d/%m/%Y')
                st.warning(f"**€ {row['Valore']:.2f}** - {row['Note']} ({row['Sottocategoria']})\n\n📅 {data_str}")

        st.divider()
        
        # Analisi di Pareto (Regola 80/20)
        st.subheader("📊 Analisi di Incidenza (Pareto)")
        pareto_df = df_filtrato.groupby('Categoria')['Valore'].sum().sort_values(ascending=False).reset_index()
        pareto_df['Percentuale'] = (pareto_df['Valore'] / pareto_df['Valore'].sum()) * 100
        
        st.dataframe(pareto_df.style.format({'Valore': '€ {:.2f}', 'Percentuale': '{:.1f}%'}), use_container_width=True)

else:
    st.error("Carica i dati nella Home!")
    if st.button("Vai alla Home"):
        st.switch_page("app.py")