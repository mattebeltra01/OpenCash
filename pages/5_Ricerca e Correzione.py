import streamlit as st
import pandas as pd

from components.config_loader import get_valuta

st.set_page_config(page_title="Ricerca Transazioni", layout="wide")

if 'utente' not in st.session_state:
    st.session_state['utente'] = "Ospite"

if 'df' not in st.session_state or st.session_state['df'] is None:
    st.warning("⚠️ Nessun dato caricato. Torna alla Home per caricare il tuo file CSV.")
    if st.button("Vai alla Home"):
        st.switch_page("app.py")
    st.stop()

utente_corrente = st.session_state['utente']
valuta = get_valuta(utente_corrente)

st.title(f"📊 Ricerca e Correzione di {utente_corrente}")

if 'df' in st.session_state:
    df = st.session_state['df'].copy()

    st.title("🔍 Ricerca e Controllo Dati")
    st.write("Usa i filtri per trovare transazioni specifiche o controllare le note.")

    col1, col2, col3 = st.columns(3)

    with col1:
        search_query = st.text_input("Cerca nelle Note:", placeholder="Es: spesa, benzina...")

    with col2:
        filtro_conto = st.selectbox("Filtra per Conto:", ["Tutti"] + list(set(df['Conto Uscita'].unique()) | set(df['Conto Entrata'].unique())))

    with col3:
        v_min = float(df['Valore'].min())
        v_max = float(df['Valore'].max())
        if v_min == v_max:
            v_max = v_min + 1.0
        min_val, max_val = st.slider(f"Intervallo di Importo ({valuta}):", v_min, v_max, (v_min, v_max))

    df_filtered = df.copy()

    if search_query:
        df_filtered = df_filtered[df_filtered['Note'].str.contains(search_query, case=False, na=False)]

    if filtro_conto != "Tutti":
        df_filtered = df_filtered[(df_filtered['Conto Uscita'] == filtro_conto) | (df_filtered['Conto Entrata'] == filtro_conto)]

    df_filtered = df_filtered[(df_filtered['Valore'] >= min_val) & (df_filtered['Valore'] <= max_val)]

    st.metric("Risultati trovati", len(df_filtered))

    st.write("✏️ **Modifica i dati direttamente nella tabella qui sotto:**")

    df_da_modificare = df_filtered.sort_values(by='Data', ascending=False)

    df_modificato = st.data_editor(
        df_da_modificare,
        use_container_width=True,
        num_rows="dynamic"
    )

    st.divider()

    col_btn1, col_btn2 = st.columns(2)

    with col_btn1:
        if st.button("💾 Salva modifiche nell'App"):
            df_originale = st.session_state['df'].copy()
            df_senza_filtrati = df_originale.drop(index=df_filtered.index, errors='ignore')
            df_aggiornato = pd.concat([df_senza_filtrati, df_modificato])
            st.session_state['df'] = df_aggiornato.sort_values(by='Data', ascending=False)
            st.success("✅ Modifiche salvate con successo! I grafici in tutte le pagine sono stati aggiornati.")
            st.rerun()

    with col_btn2:
        csv_search = df_modificato.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Scarica solo questa tabella in CSV",
            data=csv_search,
            file_name="ricerca_patrimonio_corretto.csv",
            mime="text/csv",
        )

else:
    st.error("Carica i dati nella Home!")
    if st.button("Vai alla Home"):
        st.switch_page("app.py")
