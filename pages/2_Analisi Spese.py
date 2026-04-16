import streamlit as st
import pandas as pd
import plotly.express as px



st.set_page_config(page_title="Analisi Spese", layout="wide")

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

st.title(f"📊 Analisi Spese di {st.session_state['utente']}")

if 'df' in st.session_state:
    df = st.session_state['df'].copy()
    df_uscite = df[(df['Conto Uscita'] != '-') & (df['Conto Entrata'] == '-')].copy()
    df_uscite['Valore'] = pd.to_numeric(df_uscite['Valore'])

    st.title("🔍 Analisi Dettagliata Spese")

    # Filtro Categoria
    categorie = ["Tutte"] + list(df_uscite['Categoria'].unique())
    cat_selezionata = st.selectbox("Seleziona una categoria per il dettaglio:", categorie)

    if cat_selezionata != "Tutte":
        df_plot = df_uscite[df_uscite['Categoria'] == cat_selezionata]
    else:
        df_plot = df_uscite

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader(f"Sottocategorie: {cat_selezionata}")
        fig_sub = px.bar(
            df_plot.groupby('Sottocategoria')['Valore'].sum().reset_index(),
            x='Sottocategoria', y='Valore',
            color='Sottocategoria',
            text_auto='.2s'
        )
        st.plotly_chart(fig_sub, use_container_width=True)

    with col2:
        st.subheader("Top 5 Spese Singole")
        top_5 = df_plot.sort_values(by='Valore', ascending=False).head(5)
        for _, row in top_5.iterrows():
            st.warning(f"**€ {row['Valore']}** - {row['Note']} ({row['Sottocategoria']})")

    st.divider()
    
    # Analisi di Pareto (Regola 80/20)
    st.subheader("📊 Analisi di Incidenza (Pareto)")
    pareto_df = df_uscite.groupby('Categoria')['Valore'].sum().sort_values(ascending=False).reset_index()
    pareto_df['Percentuale'] = (pareto_df['Valore'] / pareto_df['Valore'].sum()) * 100
    
    st.dataframe(pareto_df.style.format({'Valore': '€ {:.2f}', 'Percentuale': '{:.1f}%'}), use_container_width=True)

else:
    st.error("Carica i dati nella Home!")
    if st.button("Vai alla Home"):
        st.switch_page("app.py") # Cambia con il nome del tuo file principale se diverso