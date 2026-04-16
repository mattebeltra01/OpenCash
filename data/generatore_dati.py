import pandas as pd
import random
from datetime import datetime, timedelta

# ==========================================
# CONFIGURAZIONE (Facile da modificare)
# ==========================================

# Categorie e Sottocategorie per le SPESE
SPESE_CAT = {
    "Casa": ["Affitto", "Bollette", "Manutenzione", "Altro"],
    "Cibo": ["Spesa", "Ristorante", "Delivery", "Altro"],
    "Trasporti": ["Macchina", "Benzina", "Manutenzione", "Mezzi Pubblici", "Altro"],
    "Svago": ["Viaggi", "Hobby", "Abbonamenti", "Altro"],
    "Shopping": ["Abbigliamento", "Bellezza", "Elettrodomestici", "Altro"],
    "Varie": ["Regali", "Imprevisti", "Altro"]
}

# Categorie per le ENTRATE (senza sottocategorie)
ENTRATE_CAT = ["Stipendio", "Regali", "Vendite", "Premi", "Altro"]

# Conti disponibili
CONTI = ["Banca1", "Banca2", "Banca3", "Contanti"]

# ==========================================

def genera_dataset(righe=100, file_output="data/NetWorth.csv"):
    records = []
    
    # Impostiamo una data di partenza
    current_date = datetime(2026, 1, 1, 8, 30)
    
    # Teniamo traccia dei saldi per NON ANDARE IN ROSSO. 
    # Partiamo con un po' di fondi iniziali.
    saldi = {"Banca1": 3000, "Banca2": 1500, "Banca3": 500, "Contanti": 250}
    
    for _ in range(righe):
        # 1. Gestione Data: Aggiungiamo un tempo random tra 1 ora e 2 giorni per mantenerle in ordine
        current_date += timedelta(minutes=random.randint(60, 2880))
        data_str = current_date.strftime('%Y-%m-%dT%H:%M:%S+02:00')
        
        # 2. Posizione: Randomizziamo leggermente attorno alle coordinate che hai fornito
        lat = 44.910 + random.uniform(-0.005, 0.005)
        lon = 10.651 + random.uniform(-0.005, 0.005)
        posizione = f"{lat:.14f} {lon:.14f}"
        
        # Scegliamo il tipo di transazione (60% Spesa, 30% Entrata, 10% Trasferimento)
        tipo_transazione = random.choices(['spesa', 'entrata', 'trasferimento'], weights=[60, 30, 10])[0]
        
        if tipo_transazione == 'entrata':
            cat = random.choice(ENTRATE_CAT)
            sub_cat = "-"
            # Lo stipendio è più alto delle altre entrate
            valore = random.randint(1500, 3000) if cat == "Stipendio" else random.randint(20, 500)
            
            conto_in = random.choice(CONTI)
            conto_out = "-"
            saldi[conto_in] += valore
            note = f"Incasso {cat}"
            
        elif tipo_transazione == 'spesa':
            cat = random.choice(list(SPESE_CAT.keys()))
            sub_cat = random.choice(SPESE_CAT[cat])
            
            # Diamo valori sensati in base alla spesa
            if sub_cat == "Affitto":
                valore = random.randint(500, 1000)
            elif sub_cat in ["Spesa", "Bollette"]:
                valore = random.randint(40, 200)
            else:
                valore = random.randint(5, 100)
                
            conto_out = random.choice(CONTI)
            conto_in = "-"
            
            # CONTROLLO SALDO: Se andiamo in rosso, skippiamo questa spesa o cambiamo conto
            if saldi[conto_out] < valore:
                # Se non ha soldi, fingiamo un'entrata d'emergenza prima della spesa
                saldi[conto_out] += 1000
                records.append([
                    data_str, posizione, 1000, "Altro", "-", "Ricarica automatica per fondi insufficienti", "-", conto_out
                ])
                # Avanziamo di un minuto per la spesa successiva
                current_date += timedelta(minutes=1)
                data_str = current_date.strftime('%Y-%m-%dT%H:%M:%S+02:00')

            saldi[conto_out] -= valore
            note = f"Acquisto {sub_cat}"
            
        else:  # Trasferimento
            conto_out, conto_in = random.sample(CONTI, 2)
            cat = "Trasferimento"
            sub_cat = "-"
            valore = random.randint(50, 500)
            
            # Controlliamo che il conto di uscita abbia i soldi, sennò trasferiamo solo metà di quello che c'è
            if saldi[conto_out] < valore:
                valore = saldi[conto_out] // 2
                
            if valore > 0: # Registriamo solo se c'è effettivamente qualcosa da spostare
                saldi[conto_out] -= valore
                saldi[conto_in] += valore
                note = "Giroconto personale"
            else:
                continue

        # Aggiungiamo la riga al nostro dataset
        records.append([
            data_str, posizione, valore, cat, sub_cat, note, conto_out, conto_in
        ])

    # Creazione DataFrame e salvataggio CSV
    df = pd.DataFrame(records, columns=[
        "Data", "Posizione", "Valore", "Categoria", "Sottocategoria", "Note", "Conto Uscita", "Conto Entrata"
    ])
    
    df.to_csv(file_output, index=False)
    print(f"File '{file_output}' generato con successo con {len(df)} righe!")
    print("Saldi finali simulati:", saldi)

# Esegui lo script generando 150 righe fittizie
if __name__ == "__main__":
    genera_dataset(2000)