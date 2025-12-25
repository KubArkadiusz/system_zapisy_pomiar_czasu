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

# Konfiguracja strony
st.set_page_config(page_title="Pomiar Czasu - Zapisy", page_icon="🏃")

# --- PANEL BOCZNY ---
st.sidebar.header("Ustawienia Zawodów")
limit_osob = st.sidebar.number_input("Limit zawodników", min_value=1, value=100)

st.title("🏃 System Zapisów i Wyników Biegowych")

# --- FUNKCJA ZAPISU DO BAZY ---
def zapisz_zawodnika(dane):
    try:
        # Dodajemy nowy dokument z unikalnym ID do kolekcji 'zawodnicy'
        db.collection("zawodnicy").add(dane)
        return True
    except Exception as e:
        st.error(f"Błąd bazy danych: {e}")
        return False

# --- SEKCJA FORMULARZA ---
st.header("📝 Formularz zgłoszeniowy")

with st.form("form_rejestracja", clear_on_submit=True):
    col1, col2 = st.columns(2)
    
    with col1:
        imie = st.text_input("Imię")
        nazwisko = st.text_input("Nazwisko")
        plec = st.selectbox("Płeć", ["M", "K"])
        data_urodzenia = st.date_input("Data urodzenia", min_value=datetime(1940, 1, 1), value=datetime(1990, 1, 1))
        
    with col2:
        klub = st.text_input("Klub / Drużyna")
        miejscowosc = st.text_input("Miejscowość")
        nr_startowy = st.number_input("Nr startowy", min_value=1, step=1)

    submitted = st.form_submit_button("Zatwierdź zgłoszenie")

    if submitted:
        if imie and nazwisko:
            # Obliczanie kategorii wiekowej (co 10 lat, np. M40, K30)
            wiek = datetime.now().year - data_urodzenia.year
            kat_wiekowa = f"{plec}{(wiek // 10) * 10}"
            
            # Przygotowanie słownika danych (zgodnie z Twoim Firebase)
            nowy_zawodnik = {
                "Imię": imie,
                "Nazwisko": nazwisko,
                "Kobieta/Mężczyzna": plec,
                "Klub": klub,
                "Miejscowość": miejscowosc,
                "Data_Urodzenia": datetime.combine(data_urodzenia, datetime.min.time()),
                "Kategoria_Wiekowa": kat_wiekowa,
                "Numer_Startowy": nr_startowy,
                "Czas": "00:00:00", # Domyślny czas
                "Pozycja_Meta": 0    # 0 oznacza, że jeszcze nie dobiegł
            }
            
            if zapisz_zawodnika(nowy_zawodnik):
                st.success(f"✅ Zawodnik {imie} {nazwisko} został zapisany! (Kategoria: {kat_wiekowa})")
        else:
            st.warning("⚠️ Proszę podać przynajmniej imię i nazwisko.")

# --- SEKCJA LISTY STARTOWEJ ---
st.divider()
st.header("📋 Lista Startowa")

# Pobieranie danych z Firebase w czasie rzeczywistym
zawodnicy_ref = db.collection("zawodnicy").order_by("Numer_Startowy")
docs = zawodnicy_ref.stream()
lista_zawodnikow = [doc.to_dict() for doc in docs]

if lista_zawodnikow:
    df = pd.DataFrame(lista_zawodnikow)
    # Wyświetlamy tylko najważniejsze kolumny dla przejrzystości
    st.dataframe(df[["Numer_Startowy", "Imię", "Nazwisko", "Klub", "Kategoria_Wiekowa", "Miejscowość"]], use_container_width=True)
    st.write(f"Liczba zapisanych osób: **{len(lista_zawodnikow)}**")
else:
    st.info("Baza danych jest obecnie pusta.")
