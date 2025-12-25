import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import pandas as pd

# 1. Połączenie z Firebase
if not firebase_admin._apps:
    cred = credentials.Certificate('serviceAccountKey.json')
    firebase_admin.initialize_app(cred)

db = firestore.client()

# --- KONFIGURACJA STRONY I LOGOWANIE ---
st.set_page_config(page_title="Pomiar Czasu - Zapisy", page_icon="🏃", layout="wide")

# Prosta baza haseł (docelowo można przenieść do Firebase)
ADMIN_PASSWORD = "admin123" # Zmień na swoje!

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

def login():
    st.sidebar.title("Logowanie Admina")
    pwd = st.sidebar.text_input("Hasło", type="password")
    if st.sidebar.button("Zaloguj"):
        if pwd == ADMIN_PASSWORD:
            st.session_state['logged_in'] = True
            st.sidebar.success("Zalogowano!")
            st.rerun()
        else:
            st.sidebar.error("Błędne hasło")

if not st.session_state['logged_in']:
    login()

# --- POBIERANIE USTAWIEŃ I DANYCH ---
# Pobieramy limit z osobnej kolekcji 'ustawienia' lub używamy domyślnego
limit_ref = db.collection("ustawienia").document("konfiguracja").get()
if limit_ref.exists:
    limit_zapisow = limit_ref.to_dict().get("limit", 100)
else:
    limit_zapisow = 100

# Pobieranie zawodników
zawodnicy_ref = db.collection("zawodnicy")
docs = zawodnicy_ref.stream()
lista_zawodnikow = [doc.to_dict() for doc in docs]
aktualna_liczba = len(lista_zawodnikow)

# --- WIDOK ADMINA ---
if st.session_state['logged_in']:
    st.sidebar.divider()
    if st.sidebar.button("Wyloguj"):
        st.session_state['logged_in'] = False
        st.rerun()
        
    st.header("⚙️ Panel Administratora")
    nowy_limit = st.number_input("Ustaw nowy limit zawodników", min_value=1, value=limit_zapisow)
    if st.button("Zapisz nowy limit"):
        db.collection("ustawienia").document("konfiguracja").set({"limit": nowy_limit})
        st.success("Limit zaktualizowany!")
        st.rerun()
    st.divider()

# --- SEKCJA ZAPISÓW (DLA WSZYSTKICH) ---
st.title("🏃 System Zapisów Biegowych")

if aktualna_liczba >= limit_zapisow:
    st.error(f"❌ Rejestracja zamknięta! Osiągnięto limit {limit_zapisow} osób.")
else:
    st.subheader(f"📝 Formularz zgłoszeniowy (Miejsc pozostało: {limit_zapisow - aktualna_liczba})")
    
    with st.form("form_zapisy", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            imie = st.text_input("Imię *")
            nazwisko = st.text_input("Nazwisko *")
            plec = st.selectbox("Płeć *", ["M", "K"])
            data_urodzenia = st.date_input("Data urodzenia *", value=datetime(1990, 1, 1))
        with col2:
            klub = st.text_input("Klub / Drużyna *")
            miejscowosc = st.text_input("Miejscowość *")
            nr_startowy = st.number_input("Nr startowy *", min_value=1, step=1)

        submitted = st.form_submit_button("Zatwierdź zgłoszenie")

        if submitted:
            # WALIDACJA: Sprawdzenie czy pola nie są puste
            if not all([imie, nazwisko, klub, miejscowosc]):
                st.error("❗ Wszystkie pola oznaczone gwiazdką (*) są wymagane!")
            else:
                wiek = datetime.now().year - data_urodzenia.year
                kat_wiekowa = f"{plec}{(wiek // 10) * 10}"
                
                nowy_zawodnik = {
                    "Imię": imie,
                    "Nazwisko": nazwisko,
                    "Kobieta/Mężczyzna": plec,
                    "Klub": klub,
                    "Miejscowość": miejscowosc,
                    "Data_Urodzenia": datetime.combine(data_urodzenia, datetime.min.time()),
                    "Kategoria_Wiekowa": kat_wiekowa,
                    "Numer_Startowy": nr_startowy,
                    "Czas": "00:00:00",
                    "Pozycja_Meta": 0
                }
                db.collection("zawodnicy").add(nowy_zawodnik)
                st.success("✅ Zapisano pomyślnie!")
                st.rerun()

# --- SEKCJA LISTY (DLA WSZYSTKICH) ---
st.divider()
st.header("📋 Lista zapisanych zawodników")

if lista_zawodnikow:
    df = pd.DataFrame(lista_zawodnikow)
    # Wybieramy tylko kolumny, które mają być publiczne
    kolumny = ["Numer_Startowy", "Imię", "Nazwisko", "Klub", "Miejscowość", "Kategoria_Wiekowa"]
    # Upewniamy się, że kolumny istnieją w danych
    df_display = df[[c for c in kolumny if c in df.columns]]
    st.dataframe(df_display.sort_values(by="Numer_Startowy"), use_container_width=True)
else:
    st.info("Brak zapisanych zawodników.")
