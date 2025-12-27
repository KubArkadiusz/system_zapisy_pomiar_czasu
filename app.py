import streamlit as st
import pandas as pd

# --- KONFIGURACJA STRONY ---
st.set_page_config(page_title="Lista Startowa", page_icon="🏃", layout="wide")

st.title("🏃 System pomiaru czasu by Arek")
st.subheader("Oficjalna Lista Startowa")

# --- FUNKCJA POBIERANIA DANYCH ---
@st.cache_data(ttl=600)  # Odświeżaj co 10 minut
def load_data():
    file_id = "1Iaj_ivUyrnRmRujm4PnPL_d1En3M9JLI"
    url = f"https://docs.google.com/spreadsheets/d/{file_id}/export?format=xlsx"
    
    try:
        df = pd.read_excel(url)
        # 1. Usuwamy całkowicie puste wiersze
        df = df.dropna(subset=["Imię", "Nazwisko"], how="all")
        
        # 2. Naprawiamy kolumnę "Nr" (żeby nie było np. 1.0)
        if "Nr" in df.columns:
            df["Nr"] = pd.to_numeric(df["Nr"], errors='coerce').fillna(0).astype(int)
            
        return df
    except Exception as e:
        st.error(f"Nie udało się pobrać danych: {e}")
        return None

# --- WYŚWIETLANIE DANYCH ---
data = load_data()

if data is not None and not data.empty:
    # Twoje poprawione nazwy kolumn
    kolumny_widoczne = ["Nr", "Imię", "Nazwisko", "Miasto", "Nazwa klubu", "Kategoria"]
    
    # Filtrujemy tylko te, które faktycznie są w pliku
    dostepne_kolumny = [c for c in kolumny_widoczne if c in data.columns]
    
    # Statystyki
    st.success(f"Liczba zapisanych zawodników: **{len(data)}**")
    
    # Tabela
    # Sortujemy po numerze, a jeśli numery są zerami (brak), to po nazwisku
    if "Nr" in data.columns:
        data = data.sort_values(by="Nr", ascending=True)
        
    st.dataframe(
        data[dostepne_kolumny],
        use_container_width=True,
        hide_index=True
    )
else:
    st.info("Lista startowa jest obecnie pusta lub trwa jej ładowanie.")

# --- STOPKA ---
st.divider()
st.caption("Dane odświeżają się automatycznie co 10 minut.")
