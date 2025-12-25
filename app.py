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

# --- KONFIGURACJA STRONY ---
st.set_page_config(page_title="Panel Zapisów - Zawody", page_icon="🏃", layout="centered")

# --- CSS dla lepszego wyglądu (opcjonalnie) ---
st.markdown("""
    <style>
    .main { background-color: #f5f5f5; }
    .stButton>button { width: 100%; background-color: #007bff; color: white; border-radius: 5px; height: 3em; font-weight: bold; }
    .stTextInput>div>div>input { background-color: #ffffff; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏃 12. Harpaganska Dycha")
st.markdown("### **FORMULARZ ZGŁOSZENIOWY**")
st.info("Pola oznaczone gwiazdką (*) są obowiązkowe.")

# --- SEKCJA 1: DANE OSOBOWE ---
with st.form("form_zapisy", clear_on_submit=True):
    st.subheader("1. Dane osobowe")
    c1, c2 = st.columns(2)
    with c1:
        imie = st.text_input("Imię *")
        nazwisko = st.text_input("Nazwisko *")
        plec = st.selectbox("Płeć *", ["Mężczyzna", "Kobieta"])
    with c2:
        data_urodzenia = st.date_input("Data urodzenia *", value=datetime(1995, 1, 1), min_value=datetime(1940, 1, 1))
        miejscowosc = st.text_input("Miejscowość *")
        kraj = st.selectbox("Kraj *", ["Polska", "Inny"])

    st.divider()
    
    # --- SEKCJA 2: KLUB I START ---
    st.subheader("2. Informacje o starcie")
    c3, c4 = st.columns(2)
    with c3:
        klub = st.text_input("Klub / Drużyna (jeśli brak, wpisz 'brak') *")
    with c4:
        numer_startowy = st.number_input("Preferowany numer startowy *", min_value=1, max_value=9999, step=1)

    st.divider()

    # --- SEKCJA 3: ZGODY ---
    st.subheader("3. Oświadczenia")
    zgoda_regulamin = st.checkbox("Akceptuję regulamin zawodów *")
    zgoda_rodo = st.checkbox("Wyrażam zgodę na przetwarzanie danych osobowych *")

    # --- PRZYCISK ZAPISU ---
    submit_button = st.form_submit_button("WYŚLIJ ZGŁOSZENIE")

    if submit_button:
        # Bardzo dokładna walidacja
        pola_tekstowe = [imie, nazwisko, miejscowosc, klub]
        czy_puste = any(len(p.strip()) == 0 for p in pola_tekstowe)
        
        if czy_puste:
            st.error("❌ BŁĄD: Wszystkie pola tekstowe muszą być wypełnione!")
        elif not (zgoda_regulamin and zgoda_rodo):
            st.error("❌ BŁĄD: Musisz zaakceptować regulamin i zgody RODO!")
        else:
            # Obliczanie kategorii (np. M30)
            wiek = datetime.now().year - data_urodzenia.year
            kod_plci = "M" if plec == "Mężczyzna" else "K"
            kat_wiekowa = f"{kod_plci}{(wiek // 10) * 10}"
            
            # Mapowanie do Twojej struktury Firebase
            dane_zawodnika = {
                "Imię": imie.strip(),
                "Nazwisko": nazwisko.strip(),
                "Kobieta/Mężczyzna": kod_plci,
                "Klub": klub.strip(),
                "Miejscowość": miejscowosc.strip(),
                "Data_Urodzenia": datetime.combine(data_urodzenia, datetime.min.time()),
                "Kategoria_Wiekowa": kat_wiekowa,
                "Numer_Startowy": numer_startowy,
                "Czas": "00:00:00",
                "Pozycja_Meta": 0
            }
            
            # Zapis do Firebase
            db.collection("zawodnicy").add(dane_zawodnika)
            st.success(f"✅ Dziękujemy {imie}! Zostałeś pomyślnie dopisany do listy startowej.")
            st.balloons()
            st.rerun()

# --- SEKCJA 4: LISTA STARTOWA (WIDOK PUBLICZNY) ---
st.divider()
st.header("📋 LISTA STARTOWA")

# Pobieranie danych z bazy
docs = db.collection("zawodnicy").order_by("Numer_Startowy").stream()
lista_danych = [d.to_dict() for d in docs]

if lista_danych:
    df = pd.DataFrame(lista_danych)
    
    # Wybieramy i nazywamy kolumny jak na dostartu.pl
    df_view = df[["Numer_Startowy", "Imię", "Nazwisko", "Miejscowość", "Klub", "Kategoria_Wiekowa"]]
    df_view.columns = ["Nr", "Imię", "Nazwisko", "Miejscowość", "Klub / Drużyna", "Kat."]
    
    # Wyświetlanie jako estetyczna tabela
    st.table(df_view)
    st.write(f"Łącznie zapisanych: **{len(df)}**")
else:
    st.info("Lista startowa jest jeszcze pusta. Bądź pierwszy!")
