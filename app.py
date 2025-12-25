import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import pandas as pd

# 1. Połączenie z Firebase - upewnij się, że plik JSON jest w głównym folderze
if not firebase_admin._apps:
    cred = credentials.Certificate('serviceAccountKey.json')
    firebase_admin.initialize_app(cred)

db = firestore.client()

# --- KONFIGURACJA STRONY ---
st.set_page_config(page_title="Zapisy - 12. Harpaganska Dycha", page_icon="🏅", layout="centered")

# Nagłówek wizualny
st.image("https://img.freepik.com/free-vector/marathon-runners-concept-illustration_114360-10111.jpg", use_container_width=True)
st.title("🏃 12. Harpaganska Dycha")
st.markdown("---")

# Pobranie konfiguracji limitu (jeśli nie ma w bazie, ustawiamy na sztywno 150)
conf_ref = db.collection("ustawienia").document("limit").get()
max_entries = conf_ref.to_dict().get("wartosc", 150) if conf_ref.exists else 150

# Pobieranie aktualnej liczby zawodników
docs = db.collection("zawodnicy").stream()
zawodnicy = [d.to_dict() for d in docs]
current_count = len(zawodnicy)

# --- PASEK POSTĘPU ---
st.subheader("📊 Stan zapisów")
col_stat1, col_stat2 = st.columns(2)
col_stat1.metric("Zapisani zawodnicy", f"{current_count}")
col_stat2.metric("Limit miejsc", f"{max_entries}")

procent = min(current_count / max_entries, 1.0)
st.progress(procent)

if current_count >= max_entries:
    st.error("⚠️ Brak wolnych miejsc! Rejestracja została zakończona.")
else:
    # --- FORMULARZ W STYLU DOSTARTU.PL ---
    st.markdown("### 📝 Formularz zgłoszeniowy")
    st.caption("Pola oznaczone gwiazdką (*) są obowiązkowe.")

    with st.form("rejestracja_zawodnika", clear_on_submit=True):
        st.markdown("#### 1. Dane podstawowe")
        c1, c2 = st.columns(2)
        with c1:
            imie = st.text_input("Imię *")
            nazwisko = st.text_input("Nazwisko *")
            plec = st.selectbox("Płeć *", ["Mężczyzna", "Kobieta"])
        with c2:
            data_ur = st.date_input("Data urodzenia *", value=datetime(1990, 1, 1), min_value=datetime(1940, 1, 1))
            miejscowosc = st.text_input("Miejscowość *")

        st.markdown("#### 2. Klub i start")
        c3, c4 = st.columns(2)
        with c3:
            klub = st.text_input("Klub / Drużyna *", help="Wpisz 'indywidualnie' jeśli nie należysz do klubu")
        with c4:
            kraj = st.text_input("Kraj *", value="Polska")

        st.markdown("#### 3. Zgody i oświadczenia")
        st.write("Aby wysłać zgłoszenie, musisz zaakceptować poniższe warunki:")
        zgoda_reg = st.checkbox("Akceptuję regulamin 12. Harpaganskiej Dychy *")
        zgoda_dane = st.checkbox("Wyrażam zgodę na publikację moich danych na liście startowej *")

        # Przycisk wysyłania
        submit = st.form_submit_button("ZAREJESTRUJ MNIE")

        if submit:
            # Weryfikacja
            pola = [imie, nazwisko, miejscowosc, klub, kraj]
            if any(len(p.strip()) == 0 for p in pola):
                st.error("❌ Musisz wypełnić wszystkie pola tekstowe!")
            elif not (zgoda_reg and zgoda_dane):
                st.error("❌ Musisz zaznaczyć wymagane zgody!")
            else:
                # Logika kategorii wiekowej
                rok_teraz = datetime.now().year
                wiek = rok_teraz - data_ur.year
                plec_kod = "M" if plec == "Mężczyzna" else "K"
                kat = f"{plec_kod}{(wiek // 10) * 10}"
                
                # Przygotowanie danych
                nowy_zawodnik = {
                    "Imię": imie.strip(),
                    "Nazwisko": nazwisko.strip(),
                    "Kobieta/Mężczyzna": plec_kod,
                    "Klub": klub.strip(),
                    "Miejscowość": miejscowosc.strip(),
                    "Data_Urodzenia": datetime.combine(data_ur, datetime.min.time()),
                    "Kategoria_Wiekowa": kat,
                    "Numer_Startowy": current_count + 1, # Automatyczne nadawanie numeru
                    "Czas": "00:00:00",
                    "Pozycja_Meta": 0
                }
                
                db.collection("zawodnicy").add(nowy_zawodnik)
                st.success(f"Dziękujemy {imie}! Zostałeś pomyślnie zarejestrowany.")
                st.balloons()
                st.rerun()

# --- PUBLICZNA LISTA STARTOWA ---
st.markdown("---")
st.subheader("📋 Lista startowa")

if zawodnicy:
    df = pd.DataFrame(zawodnicy)
    # Wybieramy tylko kolumny widoczne dla wszystkich
    df_view = df[["Numer_Startowy", "Imię", "Nazwisko", "Miejscowość", "Klub", "Kategoria_Wiekowa"]]
    df_view.columns = ["Nr", "Imię", "Nazwisko", "Miejscowość", "Klub", "Kat."]
    st.table(df_view.sort_values("Nr"))
else:
    st.info("Brak osób na liście. Zapisz się jako pierwszy!")
