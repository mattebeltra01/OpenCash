import streamlit as st
import pandas as pd
import json
import os
import plotly.graph_objects as go

from components.config_loader import load_user_config, get_valuta, get_colore_tema

st.set_page_config(page_title="Budgeting", layout="wide")

if 'utente' not in st.session_state:
    st.session_state['utente'] = "Ospite"

if 'df' not in st.session_state or st.session_state['df'] is None:
    st.warning("⚠️ Nessun dato caricato. Torna alla Home per caricare il tuo file CSV.")
    if st.button("Vai alla Home"):
        st.switch_page("app.py")
    st.stop()

utente_corrente = st.session_state['utente']
user_conf = load_user_config(utente_corrente)
budget_impostati = user_conf.get("budget", {})
extra_conf = user_conf.get("extra", {})
valuta = get_valuta(utente_corrente)
colore_tema = get_colore_tema(utente_corrente)

soglia_allerta = extra_conf.get("soglia_allerta_budget", 0.85)
target_risparmio = extra_conf.get("obiettivo_risparmio", 0.0)

st.title(f"🎯 Obiettivi e Budget di {utente_corrente}")

st.subheader("📈 Analisi Risparmio Mensile")

df_full = st.session_state['df'].copy()
df_full['Data'] = pd.to_datetime(df_full['Data'], utc=True, errors='coerce')
df_full['Valore'] = pd.to_numeric(df_full['Valore'], errors='coerce').fillna(0)

df_full = df_full.dropna(subset=['Data'])
df_full['Mese_Anno'] = df_full['Data'].dt.strftime('%Y-%m')

entrate_m = df_full[(df_full['Conto Uscita'] == '-') & (df_full['Conto Entrata'] != '-')].groupby('Mese_Anno')['Valore'].sum()
uscite_m = df_full[(df_full['Conto Uscita'] != '-') & (df_full['Conto Entrata'] == '-')].groupby('Mese_Anno')['Valore'].sum()

df_risparmio = pd.DataFrame({
    'Entrate': entrate_m,
    'Uscite': uscite_m
}).fillna(0)

df_risparmio = df_risparmio.sort_index(ascending=True)
df_risparmio['Risparmio_Reale'] = df_risparmio['Entrate'] - df_risparmio['Uscite']
df_risparmio = df_risparmio.tail(12)

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
        yaxis_title=f"Risparmio Netto ({valuta})",
        showlegend=False,
        xaxis=dict(type='category')
    )

    st.plotly_chart(fig_saving, use_container_width=True)

    c1, c2, c3 = st.columns(3)
    media_risp = df_risparmio['Risparmio_Reale'].mean()
    mesi_ok = sum(1 for v in df_risparmio['Risparmio_Reale'] if v >= target_risparmio)

    c1.metric("Media Risparmio (12m)", f"{valuta} {media_risp:,.2f}")
    c2.metric("Mesi Target Raggiunto", f"{mesi_ok} / {len(df_risparmio)}")
    c3.metric("Obiettivo Mensile", f"{valuta} {target_risparmio:,.0f}")
else:
    st.info("📊 Non ci sono abbastanza dati validi per mostrare lo storico del risparmio.")

df = st.session_state['df'].copy()
df_uscite = df[(df['Conto Uscita'] != '-') & (df['Conto Entrata'] == '-')].copy()
df_uscite['Valore'] = pd.to_numeric(df_uscite['Valore'], errors='coerce').fillna(0)
df_uscite['Data'] = pd.to_datetime(df_uscite['Data'], utc=True, errors='coerce')

df_uscite['Mese_Anno'] = df_uscite['Data'].dt.strftime('%Y-%m')

mesi_disponibili = sorted(df_uscite['Mese_Anno'].dropna().unique(), reverse=True)

if not mesi_disponibili:
    st.info("Nessuna spesa trovata nel file.")
    st.stop()

mese_selezionato = st.selectbox("📅 Seleziona il mese da analizzare:", mesi_disponibili, index=0)

st.divider()

st.subheader(f"Stato del Budget - {mese_selezionato}")

df_mese = df_uscite[df_uscite['Mese_Anno'] == mese_selezionato]
spesa_reale = df_mese.groupby('Categoria')['Valore'].sum()

if not budget_impostati:
    st.warning("Non hai ancora impostato nessun budget! Vai nella pagina Impostazioni per configurarli.")
else:
    for cat, limite in budget_impostati.items():
        reale = spesa_reale.get(cat, 0.0)
        percentuale = min(reale / limite, 1.0) if limite > 0 else 0

        col_testo, col_bar = st.columns([1, 3])
        with col_testo:
            st.write(f"**{cat}**")
            st.caption(f"Speso: {valuta} {reale:,.2f} / {valuta} {limite:,.2f}")

        with col_bar:
            percent_css = min(reale / limite * 100, 100) if limite > 0 else 0

            if reale >= limite:
                color_hex = "#FF4B4B"
            elif reale >= (limite * soglia_allerta):
                color_hex = "#FFA500"
            else:
                color_hex = "#28A745"

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

            if reale > limite and mese_selezionato == mesi_disponibili[0]:
                st.caption(f"⚠️ Hai sforato di {valuta} {(reale - limite):,.2f}!")

categorie_spese_non_a_budget = [c for c in spesa_reale.index if c not in budget_impostati.keys()]
if categorie_spese_non_a_budget:
    st.markdown("---")
    st.caption("Spese in categorie senza un budget predefinito:")
    for cat in categorie_spese_non_a_budget:
        st.write(f"- {cat}: {valuta} {spesa_reale[cat]:,.2f}")
