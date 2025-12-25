import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import pandas as pd

# 1. Połączenie z Firebase
if not firebase_admin._apps:
    # Upewnij się, że nazwa pliku na GitHub jest poprawna
    cred = credentials.Certificate('serviceAccountKey.json')
    firebase_admin.initialize_app(cred)

db = firestore.client()

# --- KONFIGURACJA STRONY ---
st.set_page_config(page_title="Zapisy - 12. Harpagańska Dycha", page_icon="🏅", layout="centered")

# Nagłówek wizualny
st.title("🏃 12. Harpagańska Dycha")
st.markdown("### **FORMULARZ ZGŁOSZENIOWY**")
st.info("Pola oznaczone gwiazdką (*) są obowiązkowe.")

# Pobieranie aktualnej liczby zawodników do paska postępu
docs = db.collection("zawodnicy").stream()
zawodnicy_dane = [d.to_dict() for d in docs]
current_count = len(zawodnicy_dane)
max_entries = 150 # Możesz zmienić ten limit tutaj

# Pasek postępu
st.write(f"**Zajęte miejsca: {current_count} z {max_entries}**")
st.progress(min(current_count / max_entries, 1.0))

if current_count >= max_entries:
    st.error("⚠️ Limit miejsc został wyczerpany. Rejestracja zakończona.")
else:
    # --- FORMULARZ (RYGORYSTYCZNA WALIDACJA) ---
    with st.form("form_zapisy", clear_on_submit=True):
        st.subheader("1. Dane osobowe")
        c1, c2 = st.columns(2)
        with c1:
            imie = st.text_input("Imię *")
            nazwisko = st.text_input("Nazwisko *")
            plec = st.selectbox("Płeć *", ["Mężczyzna", "Kobieta"])
        with c2:
            data_ur = st.date_input("Data urodzenia *", value=datetime(1990, 1, 1))
            miejscowosc = st.text_input("Miejscowość *")
            klub = st.text_input("Klub / Drużyna *")

        st.subheader("2. Zgody")
        zgoda_reg = st.checkbox("Akceptuję regulamin zawodów *")
        zgoda_rodo = st.checkbox("Wyrażam zgodę na przetwarzanie danych osobowych *")

        # Przycisk wysyłania
        submit = st.form_submit_button("WYŚLIJ ZGŁOSZENIE")

        if submit:
            # Sprawdzenie czy wszystkie pola tekstowe są wypełnione
            if not all([imie.strip(), nazwisko.strip(), miejscowosc.strip(), klub.strip()]):
                st.error("❌ BŁĄD: Wszystkie pola oznaczone gwiazdką (*) muszą być wypełnione!")
            elif not (zgoda_reg and zgoda_dane):
                st.error("❌ BŁĄD: Musisz zaakceptować wymagane zgody i regulamin!")
            else:
                # Obliczanie kategorii (np. M40)
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
                    "Numer_Startowy": current_count + 1, # Automatyczne nadawanie numeru
                    "Czas": "00:00:00",
                    "Pozycja_Meta": 0
                }
                
                db.collection("zawodnicy").add(nowy_zawodnik)
                st.success(f"✅ Dziękujemy {imie}! Zostałeś zapisany na listę.")
                st.balloons()
                st.rerun()

# --- PUBLICZNA LISTA STARTOWA ---
st.divider()
st.subheader("📋 LISTA STARTOWA")

if zawodnicy_dane:
    df = pd.DataFrame(zawodnicy_dane)
    # Wybieramy kolumny zgodnie ze strukturą Firebase
    df_view = df[["Numer_Startowy", "Imię", "Nazwisko", "Miejscowość", "Klub", "Kategoria_Wiekowa"]]
    df_view.columns = ["Nr", "Imię", "Nazwisko", "Miejscowość", "Klub / Drużyna", "Kat."]
    st.table(df_view.sort_values("Nr"))
else:
    st.info("Lista startowa jest jeszcze pusta.")
