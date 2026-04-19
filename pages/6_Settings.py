import streamlit as st
import pandas as pd
import json
import os

from components.config_loader import load_user_config, FILE_CONFIG, clear_config_cache

st.set_page_config(page_title="Impostazioni", layout='wide')

if 'utente' not in st.session_state:
    st.session_state['utente'] = "Ospite"

utente_attivo = st.session_state['utente']

def load_config():
    if os.path.exists(FILE_CONFIG):
        try:
            with open(FILE_CONFIG, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}

def save_config(aggiornati):
    try:
        with open(FILE_CONFIG, 'w') as f:
            json.dump(aggiornati, f, indent=4)
    except IOError as e:
        st.error(f"Errore nel salvataggio: {e}")

config = load_config()

# Se l'utente attivo non esiste ancora nel JSON creiamo un template di base per lui
if utente_attivo not in config:
    config[utente_attivo] = {
        "conti": ["Conto Principale"],
        "saldi iniziali": {"Conto Principale": 0.0},
        "saldi_odierni": {},
        "budget": {"Generale": 500.0},
        "extra": {
            "obiettivo_risparmio": 100.0,
            "soglia_allerta_budget": 0.85,
            "valuta": "€",
            "colore_tema": "#1f77b4"
        }
    }

# Estraiamo solo i dati dell'utente loggato
user_conf = config[utente_attivo]

# --- 3. Interfaccia utente (TABS) ---
st.title(f"⚙️ Impostazioni Profilo: {utente_attivo}")
st.write("Modifica i tuoi parametri. Le modifiche avranno effetto solo sul tuo profilo.")

# Usiamo i tab per tenere la pagina ordinata
tab_conti, tab_saldi_odierni, tab_budget, tab_extra, tab_ricorrenti = st.tabs(["🏦 Conti & Saldi", "📅 Saldi Odierni", "🎯 Budget Mensile", "🛠️ Preferenze Extra", "🔄 Ricorrenti"])

# TAB 1
with tab_conti:
    st.subheader("Gestione dei Conti")
    st.write("Aggiungi un nuovo conto o modifica il saldo di partenza (per correggere i grafici). Puoi eliminare una riga selezionandola e premendo CANC sulla tastiera.")
    
    # Prepariamo i dati per il data_editor
    lista_conti = user_conf.get("conti", [])
    dict_saldi = user_conf.get("saldi iniziali", {})
    
    # Creiamo un DataFrame per l'editor
    dati_conti = [{"Nome Conto": c, "Saldo Iniziale": dict_saldi.get(c, 0.0)} for c in lista_conti]
    df_conti = pd.DataFrame(dati_conti)
    
    if df_conti.empty: # Sicurezza se non ci sono conti
        df_conti = pd.DataFrame(columns=["Nome Conto", "Saldo Iniziale"])
        
    # Questo è l'editor interattivo! num_rows="dynamic" permette di aggiungere righe in basso.
    edited_conti = st.data_editor(df_conti, num_rows="dynamic", use_container_width=True, key="edit_conti")

# TAB 2 - Saldi Odierni
with tab_saldi_odierni:
    st.subheader("Saldi Odierni dei Conti")
    st.write("Inserisci il saldo attuale di ogni conto. L'app calcolerà automaticamente i saldi iniziali sottraendo i movimenti registrati nel CSV. Così se perdi un valore puoi sempre recuperarlo!")

    dict_saldi_odierni = user_conf.get("saldi_odierni", {})
    lista_conti_correnti = user_conf.get("conti", [])

    dati_saldi_odierni = []
    for c in lista_conti_correnti:
        dati_saldi_odierni.append({
            "Nome Conto": c,
            "Saldo Odierno": dict_saldi_odierni.get(c, 0.0)
        })

    df_saldi_odierni = pd.DataFrame(dati_saldi_odierni)
    if df_saldi_odierni.empty:
        df_saldi_odierni = pd.DataFrame(columns=["Nome Conto", "Saldo Odierno"])

    edited_saldi_odierni = st.data_editor(
        df_saldi_odierni,
        num_rows="fixed",
        use_container_width=True,
        key="edit_saldi_odierni"
    )

    st.divider()
    st.subheader("Calcolo Automatico Saldi Iniziali")
    st.write("Inserisci i saldi odierni sopra, poi premi il bottone per ricalcolare i saldi iniziali in base alle transazioni del CSV caricato.")

    if st.button("🔄 Calcola Saldi Iniziali dai Saldi Odierni", type="primary", use_container_width=True):
        if 'df' not in st.session_state or st.session_state['df'] is None:
            st.error("⚠️ Nessun file CSV caricato! Carica prima il file dalla Home.")
        else:
            df_calc = st.session_state['df'].copy()

            variazioni = {}
            for _, row in df_calc.iterrows():
                uscita = str(row.get('Conto Uscita', '-')).strip()
                entrata = str(row.get('Conto Entrata', '-')).strip()
                valore = float(row['Valore'])
                if uscita != '-':
                    variazioni[uscita] = variazioni.get(uscita, 0) - valore
                if entrata != '-':
                    variazioni[entrata] = variazioni.get(entrata, 0) + valore

            nuovi_saldi_iniziali = {}
            nuovi_saldi_odierni = {}
            risultati = []
            for index, row in edited_saldi_odierni.iterrows():
                conto = str(row["Nome Conto"]).strip()
                if conto and conto != "nan":
                    try:
                        saldo_od = float(row["Saldo Odierno"])
                    except (ValueError, TypeError):
                        saldo_od = 0.0
                    nuovi_saldi_odierni[conto] = saldo_od
                    variazione = variazioni.get(conto, 0)
                    saldo_iniz = round(saldo_od - variazione, 2)
                    nuovi_saldi_iniziali[conto] = saldo_iniz
                    risultati.append({
                        "Conto": conto,
                        "Saldo Odierno": saldo_od,
                        "Variazione Totale": variazione,
                        "Saldo Iniziale Calcolato": saldo_iniz
                    })

            if risultati:
                df_risultati = pd.DataFrame(risultati)
                st.dataframe(df_risultati, use_container_width=True, hide_index=True)

                user_conf["saldi iniziali"] = nuovi_saldi_iniziali
                user_conf["saldi_odierni"] = nuovi_saldi_odierni
                config[utente_attivo] = user_conf
                save_config(config)
                st.success("✅ Saldi iniziali ricalcolati e salvati con successo!")
            else:
                st.warning("Nessun conto trovato per il calcolo.")

# TAB 3 - Budget
with tab_budget:
    st.subheader("Limiti di Spesa per Categoria")
    st.write("Imposta quanto vuoi spendere al massimo per ogni categoria. Aggiungi nuove categorie in fondo.")
    
    dict_budget = user_conf.get("budget", {})
    dati_budget = [{"Categoria": k, "Limite Spesa": v} for k, v in dict_budget.items()]
    df_budget = pd.DataFrame(dati_budget)
    
    if df_budget.empty:
        df_budget = pd.DataFrame(columns=["Categoria", "Limite Spesa"])
        
    edited_budget = st.data_editor(df_budget, num_rows="dynamic", use_container_width=True, key="edit_budget")

# TAB 4 - Extra
with tab_extra:
    st.subheader("Obiettivi e Personalizzazione")
    extra_conf = user_conf.get("extra", {})
    
    col1, col2 = st.columns(2)
    with col1:
        obiettivo = st.number_input("Obiettivo Risparmio Mensile", value=float(extra_conf.get("obiettivo_risparmio", 0.0)), step=50.0)
        
        # Mostriamo lo slider in percentuale (es. 85%) ma salviamo in decimale (0.85)
        soglia = st.slider("Avviso Sforamento Budget (%)", 50, 100, int(extra_conf.get("soglia_allerta_budget", 0.85) * 100)) / 100.0
        valuta = st.text_input("Valuta Principale", value=extra_conf.get("valuta", "€"))
        
    with col2:
        colore = st.color_picker("Colore Tema Profilo", value=extra_conf.get("colore_tema", "#1f77b4"))

# TAB 5 - Ricorrenti
with tab_ricorrenti:
    st.subheader("Transazioni Ricorrenti")
    st.write("Definisci entrate e uscite che si ripetono ogni mese. Saranno mostrate come promemoria nella Dashboard.")
    
    lista_ricorrenti = user_conf.get("transazioni_ricorrenti", [])
    
    if lista_ricorrenti:
        df_ricorrenti = pd.DataFrame(lista_ricorrenti)
        colonne_ordo = ["note", "valore", "categoria", "sottocategoria", "conto_uscita", "conto_entrata", "giorno_mese", "frequenza"]
        for c in colonne_ordo:
            if c not in df_ricorrenti.columns:
                df_ricorrenti[c] = ""
        df_ricorrenti = df_ricorrenti[colonne_ordo]
    else:
        df_ricorrenti = pd.DataFrame(columns=["note", "valore", "categoria", "sottocategoria", "conto_uscita", "conto_entrata", "giorno_mese", "frequenza"])
    
    edited_ricorrenti = st.data_editor(df_ricorrenti, num_rows="dynamic", use_container_width=True, key="edit_ricorrenti")

st.divider()

# --- 4. Tasto salvataggio
if st.button("💾 Salva Impostazioni nel Profilo", type="primary", use_container_width=True):
    
    # 1. Recuperiamo i Conti puliti (ignoriamo righe con nomi vuoti)
    nuovi_conti = []
    nuovi_saldi = {}
    for index, row in edited_conti.iterrows():
        conto = str(row["Nome Conto"]).strip()
        if conto != "nan" and conto != "":
            nuovi_conti.append(conto)
            try: 
                nuovi_saldi[conto] = float(row["Saldo Iniziale"])
            except ValueError:
                nuovi_saldi[conto] = 0.0

    # 1b. Recuperiamo i Saldi Odierni
    nuovi_saldi_odierni = {}
    for index, row in edited_saldi_odierni.iterrows():
        conto = str(row["Nome Conto"]).strip()
        if conto and conto != "nan":
            try:
                nuovi_saldi_odierni[conto] = float(row["Saldo Odierno"])
            except (ValueError, TypeError):
                nuovi_saldi_odierni[conto] = 0.0

    # 2. Recuperiamo il Budget pulito
    nuovo_budget = {}
    for index, row in edited_budget.iterrows():
        cat = str(row["Categoria"]).strip()
        if cat != "nan" and cat != "":
            try:
                nuovo_budget[cat] = float(row["Limite Spesa"])
            except ValueError:
                nuovo_budget[cat] = 0.0

    nuove_ricorrenti = []
    for index, row in edited_ricorrenti.iterrows():
        note = str(row.get("note", "")).strip()
        if note and note != "nan":
            try:
                valore = float(row.get("valore", 0))
            except (ValueError, TypeError):
                valore = 0.0
            try:
                giorno = int(float(row.get("giorno_mese", 1)))
                giorno = max(1, min(28, giorno))
            except (ValueError, TypeError):
                giorno = 1
            nuove_ricorrenti.append({
                "note": note,
                "valore": valore,
                "categoria": str(row.get("categoria", "")).strip(),
                "sottocategoria": str(row.get("sottocategoria", "-")).strip(),
                "conto_uscita": str(row.get("conto_uscita", "-")).strip(),
                "conto_entrata": str(row.get("conto_entrata", "-")).strip(),
                "giorno_mese": giorno,
                "frequenza": str(row.get("frequenza", "mensile")).strip()
            })

    # 3. Aggiorniamo il dizionario dell'utente
    user_conf["conti"] = nuovi_conti
    user_conf["saldi iniziali"] = nuovi_saldi
    user_conf["saldi_odierni"] = nuovi_saldi_odierni
    user_conf["budget"] = nuovo_budget
    user_conf["extra"] = {
        "obiettivo_risparmio": obiettivo,
        "soglia_allerta_budget": soglia,
        "valuta": valuta,
        "colore_tema": colore
    }
    user_conf["transazioni_ricorrenti"] = nuove_ricorrenti

    # 4. Aggiorniamo l'intero file JSON
    config[utente_attivo] = user_conf
    save_config(config)
    clear_config_cache()
    
    # 5. Aggiorniamo la session_state così le altre pagine vedono le modifiche subito
    st.session_state['lista_conti'] = nuovi_conti
    st.session_state['budget'] = nuovo_budget
    
    st.success("✅ Modifiche salvate con successo! Le tue dashboard sono state aggiornate.")