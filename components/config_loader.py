import json
import os
import streamlit as st

FILE_CONFIG = "models/config.json"


def load_user_config(utente):
    cache_key = f"_config_{utente}"
    if cache_key in st.session_state:
        return st.session_state[cache_key]
    config = {}
    if os.path.exists(FILE_CONFIG):
        try:
            with open(FILE_CONFIG, 'r') as f:
                config = json.load(f)
        except (json.JSONDecodeError, IOError):
            config = {}
    result = config.get(utente, {})
    st.session_state[cache_key] = result
    return result


def clear_config_cache(utente=None):
    if utente:
        key = f"_config_{utente}"
        if key in st.session_state:
            del st.session_state[key]
    else:
        keys_to_delete = [k for k in list(st.session_state.keys()) if k.startswith("_config_")]
        for k in keys_to_delete:
            del st.session_state[k]


def get_valuta(utente):
    conf = load_user_config(utente)
    return conf.get("extra", {}).get("valuta", "€")


def get_colore_tema(utente):
    conf = load_user_config(utente)
    return conf.get("extra", {}).get("colore_tema", "#1f77b4")


def get_saldi_iniziali(utente):
    conf = load_user_config(utente)
    return conf.get("saldi iniziali", {})


def get_budget(utente):
    conf = load_user_config(utente)
    return conf.get("budget", {})


def get_extra(utente):
    conf = load_user_config(utente)
    return conf.get("extra", {})


def get_ricorrenti(utente):
    conf = load_user_config(utente)
    return conf.get("transazioni_ricorrenti", [])


def get_saldi_odierni(utente):
    conf = load_user_config(utente)
    return conf.get("saldi_odierni", {})
