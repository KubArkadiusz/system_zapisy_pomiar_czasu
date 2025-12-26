import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import pandas as pd

# Inicjalizacja Firebase z Secrets
if not firebase_admin._apps:
    fb_dict = dict(st.secrets["firebase"])
    fb_dict["private_key"] = fb_dict["private_key"].replace("\\n", "\n")
    cred = credentials.Certificate(fb_dict)
    firebase_admin.initialize_app(cred)

db = firestore.client()

st.title("🏃 12. Harpagańska Dycha")
st.subheader("Panel Rejestracji Uczestników")

# Formularz
with st.form("rejestracja_zawodnika", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        imie = st.text_input("Imię *")
        nazwisko = st.text_input("Nazwisko *")
        plec = st.selectbox("Płeć *", ["Mężczyzna", "Kobieta"])
    with col2:
        data_ur = st.date_input("Data urodzenia *", value=datetime(1995, 1, 1))
        miejscowosc = st.text_input("Miejscowość *")
        klub = st.text_input("Klub / Drużyna *")

    # To rozwiązuje błąd "Missing Submit Button"
    submit = st.form_submit_button("ZAREJESTRUJ MNIE")

    if submit:
        if not all([imie, nazwisko, miejscowosc, klub]):
            st.error("Wszystkie pola są wymagane!")
        else:
            wiek = datetime.now().year - data_ur.year
            kat = f"{'M' if plec == 'Mężczyzna' else 'K'}{(wiek // 10) * 10}"
            
            dane = {
                "Imię": imie,
                "Nazwisko": nazwisko,
                "Kobieta/Mężczyzna": "M" if plec == "Mężczyzna" else "K",
                "Klub": klub,
                "Miejscowość": miejscowosc,
                "Data_Urodzenia": datetime.combine(data_ur, datetime.min.time()),
                "Kategoria_Wiekowa": kat,
                "Czas": "00:00:00",
                "Pozycja_Meta": 0
            }
            db.collection("zawodnicy").add(dane)
            st.success("Zapisano pomyślnie!")
            st.rerun()

# Lista pod spodem
docs = db.collection("zawodnicy").stream()
zawodnicy = [d.to_dict() for d in docs]
if zawodnicy:
    st.table(pd.DataFrame(zawodnicy)[["Imię", "Nazwisko", "Klub", "Kategoria_Wiekowa"]])
