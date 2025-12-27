import streamlit as st
import pandas as pd

# --- KONFIGURACJA STRONY ---
st.set_page_config(page_title="Lista Startowa - Harpagańska Dycha", page_icon="🏃", layout="wide")

st.title("🏃 12. Harpagańska Dycha")
st.subheader("Oficjalna Lista Startowa")

# --- FUNKCJA POBIERANIA DANYCH Z GOOGLE DRIVE ---
@st.cache_data(ttl=600)  # Odświeżaj dane co 10 minut
def load_data():
    # Link do Twojego pliku skonwertowany na format CSV dla łatwego odczytu
    file_id = "1Iaj_ivUyrnRmRujm4PnPL_d1En3M9JLI"
    url = f"https://docs.google.com/spreadsheets/d/{file_id}/export?format=xlsx"
    
    try:
        # Odczytujemy plik Excel (wymaga biblioteki openpyxl)
        df = pd.read_excel(url)
        return df
    except Exception as e:
        st.error(f"Nie udało się pobrać danych: {e}")
        return None

# --- WYŚWIETLANIE DANYCH ---
data = load_data()

if data is not None:
    # Wybieramy tylko kluczowe kolumny do wyświetlenia (zgodnie z plikiem z dostartu)
    # Jeśli nazwy kolumn w Twoim Excelu są inne, dostosuj je poniżej:
    kolumny_widoczne = ["Nr zawodnika", "Imię", "Nazwisko", "Miasto", "Nazwa klubu", "Kategoria"]
    
    # Sprawdzamy, czy te kolumny istnieją w pliku
    dostepne_kolumny = [c for c in kolumny_widoczne if c in data.columns]
    
    # Statystyki
    st.write(f"Liczba zapisanych zawodników: **{len(data)}**")
    
    # Tabela z możliwością wyszukiwania
    st.dataframe(
        data[dostepne_kolumny].sort_values(by="Nr"), 
        use_container_width=True, 
        hide_index=True
    )
else:
    st.info("Trwa ładowanie listy startowej lub plik jest pusty.")

# --- STOPKA ---
st.divider()
st.caption("Dane odświeżają się automatycznie co 10 minut. Źródło: dostartu.pl")
