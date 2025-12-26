import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import pandas as pd

# 1. Inicjalizacja Firebase z Secrets
if not firebase_admin._apps:
    try:
        fb_dict = dict(st.secrets["firebase"])
        fb_dict["private_key"] = fb_dict["private_key"].replace("\\n", "\n")
        cred = credentials.Certificate(fb_dict)
        firebase_admin.initialize_app(cred)
    except Exception as e:
        st.error(f"Błąd inicjalizacji Firebase: {e}")

db = firestore.client()

st.title("🏃 12. Harpagańska Dycha")

# --- FORMULARZ ---
with st.form("rejestracja", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        imie = st.text_input("Imię *")
        nazwisko = st.text_input("Nazwisko *")
        plec = st.selectbox("Płeć *", ["Mężczyzna", "Kobieta"])
    with col2:
        data_ur = st.date_input("Data urodzenia *", value=datetime(1995, 1, 1))
        miejscowosc = st.text_input("Miejscowość *")
        klub = st.text_input("Klub / Drużyna *")

    submit = st.form_submit_button("ZAREJESTRUJ MNIE")

    if submit:
        if not all([imie.strip(), nazwisko.strip(), miejscowosc.strip(), klub.strip()]):
            st.warning("Uzupełnij wszystkie pola!")
        else:
            try:
                # Przygotowanie danych
                wiek = datetime.now().year - data_ur.year
                plec_kod = "M" if plec == "Mężczyzna" else "K"
                kat = f"{plec_kod}{(wiek // 10) * 10}"
                
                nowy_zawodnik = {
                    "Imię": imie.strip(),
                    "Nazwisko": nazwisko.strip(),
                    "Kobieta/Mężczyzna": plec_kod,
                    "Klub": klub.strip(),
                    "Miejscowość": miejscowosc.strip(),
                    "Data_Urodzenia": datetime.combine(data_ur, datetime.min.time()),
                    "Kategoria_Wiekowa": kat,
                    "Numer_Startowy": 0, # To uzupełnimy później automatycznie
                    "Czas": "00:00:00",
                    "Pozycja_Meta": 0
                }
                
                # PRÓBA ZAPISU Z PODGLĄDEM BŁĘDU
                doc_ref = db.collection("zawodnicy").add(nowy_zawodnik)
                st.success(f"✅ Zapisano pomyślnie! ID: {doc_ref[1].id}")
                st.balloons()
                # Nie robimy st.rerun() od razu, żeby zobaczyć komunikat sukcesu
            except Exception as e:
                st.error(f"❌ Błąd podczas zapisu do bazy: {e}")

# --- LISTA STARTOWA (PODGLĄD) ---
st.divider()
st.subheader("📋 Lista startowa")

try:
    docs = db.collection("zawodnicy").stream()
    zawodnicy = [d.to_dict() for d in docs]
    if zawodnicy:
        df = pd.DataFrame(zawodnicy)
        st.dataframe(df[["Imię", "Nazwisko", "Klub", "Kategoria_Wiekowa"]])
    else:
        st.info("Baza jest pusta.")
except Exception as e:
    st.error(f"Błąd pobierania listy: {e}")
