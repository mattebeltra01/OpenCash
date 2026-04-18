import streamlit as st
import pandas as pd

from components.config_loader import get_valuta, get_colore_tema, get_coordinate_home

st.set_page_config(page_title="Mappa Spese", layout="wide")

if 'utente' not in st.session_state:
    st.session_state['utente'] = "Ospite"

if 'df' not in st.session_state or st.session_state['df'] is None:
    st.warning("⚠️ Nessun dato caricato. Torna alla Home per caricare il tuo file CSV.")
    if st.button("Vai alla Home"):
        st.switch_page("app.py")
    st.stop()

import plotly.express as px

utente_corrente = st.session_state['utente']
valuta = get_valuta(utente_corrente)
colore_tema = get_colore_tema(utente_corrente)
coordinate_home = get_coordinate_home(utente_corrente)

st.title(f"📊 Mappa delle Spese di {utente_corrente}")

if 'df' in st.session_state:
    df = st.session_state['df'].copy()

    split_pos = df['Posizione'].str.split(' ', expand=True)
    df['lat'] = pd.to_numeric(split_pos[0], errors='coerce')
    df['lon'] = pd.to_numeric(split_pos[1], errors='coerce')
    df = df.dropna(subset=['lat', 'lon'])

    st.title("📍 Mappa Geografica delle Spese")
    st.write("Visualizza dove effettui i tuoi acquisti più frequenti.")

    cat_map = st.multiselect("Filtra per Categoria:", options=df['Categoria'].unique(), default=df['Categoria'].unique())
    df_map = df[df['Categoria'].isin(cat_map)]

    fig_map = px.scatter_mapbox(
        df_map,
        lat="lat",
        lon="lon",
        size="Valore",
        color="Categoria",
        hover_name="Note",
        hover_data={"Valore": True, "Sottocategoria": True, "lat": False, "lon": False},
        zoom=12,
        height=600,
        center={"lat": coordinate_home[0], "lon": coordinate_home[1]},
        mapbox_style="carto-positron",
        color_discrete_sequence=[colore_tema] + px.colors.qualitative.Set2
    )

    st.plotly_chart(fig_map, use_container_width=True)

else:
    st.error("Carica i dati nella Home!")
    if st.button("Vai alla Home"):
        st.switch_page("app.py")
