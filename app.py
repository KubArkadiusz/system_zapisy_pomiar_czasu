import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import pandas as pd

# --- POŁĄCZENIE Z BAZĄ ---
if not firebase_admin._apps:
    try:
        cred = credentials.Certificate('serviceAccountKey.json')
        firebase_admin.initialize_app(cred)
    except Exception as e:
        st.error(f"Błąd klucza Firebase: {e}")

db = firestore.client()

# --- USTAWIENIA STRONY ---
st.set_page_config(page_title="Zapisy - Harpagańska Dycha", layout="centered")

st.title("🏃 12. Harpagańska Dycha")
st.markdown("## FORMULARZ ZGŁOSZENIOWY")
st.info("Wypełnij uważnie wszystkie pola. Gwiazdka (*) oznacza pole obowiązkowe.")

# --- FORMULARZ ---
with st.form("formularz_startowy", clear_on_submit=True):
    
    st.subheader("1. Dane zawodnika")
    col1, col2 = st.columns(2)
    with col1:
        imie = st.text_input("Imię *")
        nazwisko = st.text_input("Nazwisko *")
        plec = st.selectbox("Płeć *", ["Mężczyzna", "Kobieta"])
    with col2:
        data_ur = st.date_input("Data urodzenia *", value=datetime(1995, 1, 1))
        miejscowosc = st.text_input("Miejscowość *")

    st.subheader("2. Klub i Drużyna")
    klub = st.text_input("Klub / Drużyna * (jeśli brak, wpisz 'brak')")

    st.subheader("3. Oświadczenia")
    akceptacja = st.checkbox("Akceptuję regulamin biegu i RODO *")

    # Przycisk wysyłki
    submit = st.form_submit_button("ZAREJESTRUJ MNIE")

    if submit:
        # Sprawdzanie czy pola są wypełnione
        if not (imie.strip() and nazwisko.strip() and miejscowosc.strip() and klub.strip()):
            st.error("❌ Musisz wypełnić wszystkie pola oznaczone gwiazdką!")
        elif not akceptacja:
            st.error("❌ Musisz zaakceptować regulamin!")
        else:
            # Obliczanie kategorii wiekowej
            wiek = datetime.now().year - data_ur.year
            kod_plci = "M" if plec == "Mężczyzna" else "K"
            kategoria = f"{kod_plci}{(wiek // 10) * 10}"

            # Pobieranie liczby zapisanych osób dla numeru startowego
            aktualni = db.collection("zawodnicy").get()
            nowy_nr = len(aktualni) + 1

            # Przygotowanie danych do Firebase
            zawodnik_dane = {
                "Imię": imie.strip(),
                "Nazwisko": nazwisko.strip(),
                "Kobieta/Mężczyzna": kod_plci,
                "Klub": klub.strip(),
                "Miejscowość": miejscowosc.strip(),
                "Data_Urodzenia": datetime.combine(data_ur, datetime.min.time()),
                "Kategoria_Wiekowa": kategoria,
                "Numer_Startowy": nowy_nr,
                "Czas": "00:00:00",
                "Pozycja_Meta": 0
            }

            # ZAPIS DO BAZY
            db.collection("zawodnicy").add(zawodnik_dane)
            st.success(f"✅ Sukces! {imie}, zostałeś zapisany z numerem {nowy_nr}")
            st.balloons()
            st.rerun()

# --- LISTA STARTOWA POD FORMULARZEM ---
st.markdown("---")
st.subheader("📋 LISTA STARTOWA")

docs = db.collection("zawodnicy").order_by("Numer_Startowy").stream()
wszyscy = [d.to_dict() for d in docs]

if wszyscy:
    df = pd.DataFrame(wszyscy)
    # Wybieramy czytelne kolumny
    df_view = df[["Numer_Startowy", "Imię", "Nazwisko", "Miejscowość", "Klub", "Kategoria_Wiekowa"]]
    df_view.columns = ["Nr", "Imię", "Nazwisko", "Miejscowość", "Klub", "Kat."]
    st.table(df_view)
else:
    st.write("Lista jest obecnie pusta.")
