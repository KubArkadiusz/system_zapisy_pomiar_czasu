import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import pandas as pd

# 1. Inicjalizacja Firebase (połączenie z Twoją bazą)
if not firebase_admin._apps:
    cred = credentials.Certificate('serviceAccountKey.json')
    firebase_admin.initialize_app(cred)

db = firestore.client()

# --- KONFIGURACJA ESTETYKI (Styl dostartu.pl) ---
st.set_page_config(page_title="Zapisy: 12. Harpagańska Dycha", page_icon="🏅")

# Wstrzyknięcie prostego CSS dla lepszego wyglądu przycisków
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #007bff; color: white; }
    .stForm { background-color: #1e2630; padding: 20px; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏃 12. Harpagańska Dycha")
st.subheader("Panel Rejestracji Uczestników")
st.markdown("---")

# --- LICZNIK ZAPISÓW (Pasek postępu) ---
docs = db.collection("zawodnicy").stream()
wszyscy = [d.to_dict() for d in docs]
zapisani_count = len(wszyscy)
limit = 200 # Możesz zmienić limit tutaj

col_a, col_b = st.columns(2)
col_a.metric("Zapisani", f"{zapisani_count}")
col_b.metric("Limit miejsc", f"{limit}")
st.progress(min(zapisani_count / limit, 1.0))

if zapisani_count >= limit:
    st.error("❌ REJESTRACJA ZAMKNIĘTA: Brak wolnych miejsc.")
else:
    # --- FORMULARZ (WSZYSTKIE POLA WYMAGANE) ---
    with st.form("main_form", clear_on_submit=True):
        st.markdown("### 1️⃣ Dane podstawowe")
        c1, c2 = st.columns(2)
        with c1:
            imie = st.text_input("Imię *")
            nazwisko = st.text_input("Nazwisko *")
            plec = st.selectbox("Płeć *", ["Mężczyzna", "Kobieta"])
        with c2:
            data_ur = st.date_input("Data urodzenia *", value=datetime(1990, 1, 1), min_value=datetime(1940, 1, 1))
            miejscowosc = st.text_input("Miejscowość *")

        st.markdown("### 2️⃣ Klub i Drużyna")
        klub = st.text_input("Nazwa Klubu * (jeśli nie masz, wpisz 'brak')")
        
        st.markdown("### 3️⃣ Zgody")
        zgoda_1 = st.checkbox("Akceptuję regulamin biegu i oświadczam, że startuję na własną odpowiedzialność. *")
        zgoda_2 = st.checkbox("Wyrażam zgodę na przetwarzanie danych osobowych dla celów organizacji zawodów. *")

        # Przycisk wysyłki
        submit = st.form_submit_button("ZAREJESTRUJ MNIE TERAZ")

        if submit:
            # WALIDACJA: Sprawdzamy czy pola tekstowe nie są puste (strip usuwa spacje)
            if not all([imie.strip(), nazwisko.strip(), miejscowosc.strip(), klub.strip()]):
                st.error("❗ Wszystkie pola tekstowe muszą być wypełnione!")
            elif not (zgoda_1 and zgoda_2):
                st.error("❗ Musisz zaznaczyć obie zgody, aby się zapisać!")
            else:
                # Logika kategorii wiekowej (co 10 lat)
                rok_biegu = 2025
                wiek = rok_biegu - data_ur.year
                prefiks = "M" if plec == "Mężczyzna" else "K"
                kategoria = f"{prefiks}{(wiek // 10) * 10}" # np. M30, K40

                # Przygotowanie paczki danych (zgodnie z Twoją strukturą Firestore)
                nowy_zawodnik = {
                    "Imię": imie.strip(),
                    "Nazwisko": nazwisko.strip(),
                    "Kobieta/Mężczyzna": "M" if plec == "Mężczyzna" else "K",
                    "Klub": klub.strip(),
                    "Miejscowość": miejscowosc.strip(),
                    "Data_Urodzenia": datetime.combine(data_ur, datetime.min.time()),
                    "Kategoria_Wiekowa": kategoria,
                    "Numer_Startowy": zapisani_count + 1, # Automatyczne nadawanie numeru
                    "Czas": "00:00:00",
                    "Pozycja_Meta": 0
                }

                # Zapis do Firebase
                db.collection("zawodnicy").add(nowy_zawodnik)
                st.success(f"✅ Sukces! {imie}, zostałeś zapisany do kategorii {kategoria}. Do zobaczenia na starcie!")
                st.balloons()
                st.rerun()

# --- PUBLICZNA LISTA STARTOWA ---
st.markdown("---")
st.subheader("📋 Aktualna Lista Startowa")

if wszyscy:
    df = pd.DataFrame(wszyscy)
    # Wybieramy tylko te kolumny, które chcemy pokazać publicznie
    # Sortujemy po numerze startowym
    df_public = df[["Numer_Startowy", "Imię", "Nazwisko", "Miejscowość", "Klub", "Kategoria_Wiekowa"]]
    df_public.columns = ["Nr", "Imię", "Nazwisko", "Miejscowość", "Klub / Drużyna", "Kat."]
    st.table(df_public.sort_values("Nr"))
else:
    st.info("Lista jest pusta. Bądź pierwszą osobą, która się zapisze!")
