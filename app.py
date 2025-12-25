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

# --- KONFIGURACJA W STYLU DOSTARTU ---
st.set_page_config(page_title="Zapisy na Zawody", page_icon="🏅", layout="centered")

# Bezpieczeństwo (proste logowanie)
ADMIN_PASSWORD = "admin" 

if 'is_admin' not in st.session_state:
    st.session_state['is_admin'] = False

# Sidebar - Panel Administratora
with st.sidebar:
    st.title("🔐 Panel Organizatora")
    if not st.session_state['is_admin']:
        pwd = st.text_input("Hasło admina", type="password")
        if st.button("Zaloguj"):
            if pwd == ADMIN_PASSWORD:
                st.session_state['is_admin'] = True
                st.rerun()
            else:
                st.error("Błędne hasło")
    else:
        st.success("Zalogowano jako Admin")
        if st.button("Wyloguj"):
            st.session_state['is_admin'] = False
            st.rerun()

# Pobieranie konfiguracji limitu z Firebase
conf_ref = db.collection("ustawienia").document("limit").get()
max_entries = conf_ref.to_dict().get("wartosc", 100) if conf_ref.exists else 100

if st.session_state['is_admin']:
    st.subheader("⚙️ Zarządzanie limitem")
    nowy_limit = st.number_input("Zmień limit uczestników", value=max_entries)
    if st.button("Zaktualizuj limit"):
        db.collection("ustawienia").document("limit").set({"wartosc": nowy_limit})
        st.success("Limit zmieniony!")
        st.rerun()

# --- GŁÓWNA TREŚĆ ---
st.title("🏆 Rejestracja Zawodników")
st.info("Wypełnij poniższy formularz, aby wziąć udział w wydarzeniu.")

# Pobieranie zawodników do paska postępu i listy
docs = db.collection("zawodnicy").stream()
zawodnicy = [d.to_dict() for d in docs]
current_count = len(zawodnicy)

# Pasek postępu (jak na profesjonalnych stronach)
progress = current_count / max_entries
st.write(f"**Zajęte miejsca: {current_count} z {max_entries}**")
st.progress(min(progress, 1.0))

if current_count >= max_entries:
    st.warning("⚠️ Limit miejsc został wyczerpany. Zapraszamy na kolejną edycję!")
else:
    # --- FORMULARZ (WSZYSTKIE POLA WYMAGANE) ---
    with st.form("rejestracja_dostartu", clear_on_submit=True):
        st.subheader("👤 Dane uczestnika")
        c1, c2 = st.columns(2)
        with c1:
            imie = st.text_input("Imię *")
            nazwisko = st.text_input("Nazwisko *")
            plec = st.selectbox("Płeć *", ["M", "K"])
        with c2:
            data_ur = st.date_input("Data urodzenia *", value=datetime(1990, 1, 1))
            klub = st.text_input("Klub / Miejscowość *")
            nr_startowy = st.number_input("Sugerowany nr startowy (1-999) *", min_value=1, max_value=999)

        if st.form_submit_button("ZAREJESTRUJ MNIE"):
            # Rygorystyczna walidacja
            if not (imie and nazwisko and klub):
                st.error("❌ Wszystkie pola są wymagane! Nie zostawiłeś pustego pola?")
            else:
                # Automatyczna kategoria wiekowa (np. M40)
                wiek = datetime.now().year - data_ur.year
                kat = f"{plec}{(wiek // 10) * 10}"
                
                nowy_doc = {
                    "Imię": imie,
                    "Nazwisko": nazwisko,
                    "Kobieta/Mężczyzna": plec,
                    "Klub": klub,
                    "Miejscowość": klub, # Uproszczenie: klub i miejscowość
                    "Data_Urodzenia": datetime.combine(data_ur, datetime.min.time()),
                    "Kategoria_Wiekowa": kat,
                    "Numer_Startowy": nr_startowy,
                    "Czas": "00:00:00",
                    "Pozycja_Meta": 0
                }
                db.collection("zawodnicy").add(nowy_doc)
                st.balloons()
                st.success(f"Brawo {imie}! Jesteś na liście startowej w kategorii {kat}.")
                st.rerun()

# --- PUBLICZNA LISTA STARTOWA ---
st.divider()
st.subheader("📋 Lista Startowa")
if zawodnicy:
    df = pd.DataFrame(zawodnicy)
    # Wyświetlamy tylko te kolumny, które interesują kibiców
    df_view = df[["Numer_Startowy", "Imię", "Nazwisko", "Klub", "Kategoria_Wiekowa"]]
    st.table(df_view.sort_values("Numer_Startowy"))
else:
    st.write("Bądź pierwszy! Nikt się jeszcze nie zapisał.")
