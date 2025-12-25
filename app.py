import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import pandas as pd

# 1. Konfiguracja połączenia z Firebase
if not firebase_admin._apps:
    # Zmieniono na poprawną nazwę pliku po Twojej poprawce
    cred = credentials.Certificate('serviceAccountKey.json')
    firebase_admin.initialize_app(cred)

db = firestore.client()

st.set_page_config(page_title="System Pomiaru Czasu", layout="wide")
st.title("🏃 System Zapisów i Wyników Biegowych")

# --- PANEL BOCZNY ---
st.sidebar.header("Ustawienia Zawodów")
limit_zapisow = st.sidebar.number_input("Limit zawodników", min_value=1, value=100)

# --- SEKCJA 1: FORMULARZ ZAPISÓW ---
st.header("📝 Formularz zgłoszeniowy")

# Pobranie aktualnej liczby zapisanych osób
zawodnicy_ref = db.collection("zawodnicy")
docs = zawodnicy_ref.stream()
lista_zawodnikow = [d.to_dict() for d in docs]
aktualna_liczba = len(lista_zawodnikow)

if aktualna_liczba >= limit_zapisow:
    st.error(f"Osiągnięto limit zapisów ({limit_zapisow}). Rejestracja zamknięta.")
else:
    with st.form("rejestracja", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            imie = st.text_input("Imię")
            nazwisko = st.text_input("Nazwisko")
            plec = st.selectbox("Płeć", ["M", "K"], index=0)
            data_urodz = st.date_input("Data urodzenia", min_value=datetime(1940, 1, 1), value=datetime(1990, 1, 1))
        with col2:
            klub = st.text_input("Klub / Drużyna")
            miejscowosc = st.text_input("Miejscowość")
            nr_startowy = st.number_input("Nr startowy", min_value=1, step=1)

        submit = st.form_submit_button("Zatwierdź zgłoszenie")

        if submit:
            if imie and nazwisko:
                # Obliczanie kategorii wiekowej (np. M40, K20)
                wiek = datetime.now().year - data_urodz.year
                kat_wiekowa = f"{plec}{(wiek // 10) * 10}"
                
                nowy_zawodnik = {
                    "Imię": imie,
                    "Nazwisko": nazwisko,
                    "Kobieta/Mężczyzna": plec,
                    "Klub": klub,
                    "Miejscowość": miejscowosc,
                    "Data_Urodzenia": datetime.combine(data_urodz, datetime.min.time()),
                    "Kategoria_Wiekowa": kat_wiekowa,
                    "Numer_Startowy": nr_startowy,
                    "Czas": "00:00:00",
                    "Pozycja_Meta": 0
                }
                
                db.collection("zawodnicy").add(nowy_zawodnik)
                st.success(f"Dodano zawodnika: {imie} {nazwisko}")
                st.rerun()
            else:
                st.warning("Proszę wypełnić Imię i Nazwisko.")

# --- SEKCJA 2: LISTA STARTOWA I WYNIKI ---
st.divider()
st.header("📊 Lista Startowa / Wyniki")

if lista_zawodnikow:
    df = pd.DataFrame(lista_zawodnikow)
    
    # Przekształcenie daty do czytelnego formatu
    if "Data_Urodzenia" in df.columns:
        df["Data_Urodzenia"] = pd.to_datetime(df["Data_Urodzenia"]).dt.date
    
    # Sortowanie: najpierw ci z czasem na mecie (Pozycja_Meta > 0)
    df = df.sort_values(by=["Pozycja_Meta", "Numer_Startowy"], ascending=[False, True])
    
    # Wyświetlanie tabeli z Twoimi polami
    kolumny_do_pokazania = ["Numer_Startowy", "Imię", "Nazwisko", "Klub", "Kategoria_Wiekowa", "Czas", "Pozycja_Meta"]
    st.dataframe(df[kolumny_do_pokazania], use_container_width=True)
    
    st.write(f"Zapisanych: **{len(df)}** / {limit_zapisow}")
else:
    st.info("Brak zapisanych zawodników w bazie.")
