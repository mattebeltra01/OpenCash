import json
import os

FILE_CONFIG = "models/config.json"

def load_user_config(utente):
    if os.path.exists(FILE_CONFIG):
        try:
            with open(FILE_CONFIG, 'r') as f:
                config = json.load(f)
                return config.get(utente, {})
        except (json.JSONDecodeError, IOError):
            return {}
    return {}

def get_valuta(utente):
    conf = load_user_config(utente)
    return conf.get("extra", {}).get("valuta", "€")

def get_colore_tema(utente):
    conf = load_user_config(utente)
    return conf.get("extra", {}).get("colore_tema", "#1f77b4")

def get_coordinate_home(utente):
    conf = load_user_config(utente)
    return conf.get("extra", {}).get("coordinate_home", [44.9104, 10.6516])

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
