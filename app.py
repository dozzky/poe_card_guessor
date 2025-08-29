import os
import random
import streamlit as st
import pandas as pd
from PIL import Image

# === НАСТРОЙКИ ===
IMAGE_FOLDER = "images"
ALLOWED_EXT = (".png", ".jpg", ".jpeg", ".gif")
CSV_FILE = "div_cards_clean.csv"

# === ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ===
def normalize_name(name: str) -> str:
    name = name.lower().replace(" ", "").replace("_", "")
    if name.endswith("card"):
        name = name[:-4]
    return name

def split_original_name(name: str) -> list[str]:
    clean_name = name.rsplit(".", 1)[0].replace("_card", "")
    return clean_name.split("_")

def get_random_image():
    files = [f for f in os.listdir(IMAGE_FOLDER) if f.lower().endswith(ALLOWED_EXT)]
    return random.choice(files) if files else None

def get_random_card_from_csv(df):
    return df.sample(1).iloc[0]

def generate_options(df, correct_name, num_options=4):
    """Создаем список вариантов с 1 правильным и (num_options-1) случайных неправильных."""
    all_names = df["name"].tolist()
    wrong_names = random.sample([n for n in all_names if n != correct_name], num_options - 1)
    options = wrong_names + [correct_name]
    random.shuffle(options)
    return options

# === ЗАГРУЗКА CSV ===
df_cards = pd.read_csv(CSV_FILE)

# === ИНИЦИАЛИЗАЦИЯ СОСТОЯНИЯ ===
if "mode" not in st.session_state:
    st.session_state.mode = "По картинке"
if "current_card" not in st.session_state:
    st.session_state.current_card = None
if "options" not in st.session_state:
    st.session_state.options = []
if "result" not in st.session_state:
    st.session_state.result = ""

# === ФУНКЦИЯ НОВОГО РАУНДА ===
def start_new_round():
    st.session_state.result = ""
    st.session_state.current_card = None
    st.session_state.options = []

    if st.session_state.mode == "Множественный выбор":
        # Берем случайную карту
        card = get_random_card_from_csv(df_cards)
        st.session_state.current_card = card
        # Создаем варианты
        st.session_state.options = generate_options(df_cards, card["name"], 4)

# === ВЫБОР РЕЖИМА ===
st.title("🎴 Угадай карту")
mode = st.radio(
    "Выберите режим:",
    ["По картинке", "По описанию", "Лёгкий режим", "Случайный режим", "Множественный выбор"],
    key="mode_select"
)
if st.session_state.mode != mode:
    st.session_state.mode = mode
    start_new_round()

# === ИНТЕРФЕЙС РЕЖИМА МНОЖЕСТВЕННОГО ВЫБОРА ===
if st.session_state.mode == "Множественный выбор":
    if st.session_state.current_card is None:
        start_new_round()

    card = st.session_state.current_card
    st.subheader("Описание карты:")
    st.info(card["description"])

    if st.session_state.result == "":
        # Кнопки с вариантами
        for option in st.session_state.options:
            if st.button(option):
                if option == card["name"]:
                    st.session_state.result = "✅ Верно!"
                else:
                    st.session_state.result = f"❌ Неправильно! Правильный ответ: {card['name']}"
                st.rerun()
    else:
        st.subheader(st.session_state.result)
        if st.button("Начать заново"):
            start_new_round()
            st.rerun()

# === ДЛЯ ДРУГИХ РЕЖИМОВ (СТАРАЯ ЛОГИКА) ===
elif st.session_state.mode != "Множественный выбор":
    st.info("Выберите другой режим для текстового ввода или лёгкого режима.")
