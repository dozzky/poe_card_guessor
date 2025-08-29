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
    """Приводим имя к нижнему регистру, убираем пробелы, подчеркивания и суффикс '_card'."""
    name = name.lower().replace(" ", "").replace("_", "")
    if name.endswith("card"):
        name = name[:-4]
    return name

def split_original_name(name: str) -> list[str]:
    """Возвращает слова из имени файла без расширения и суффикса _card."""
    clean_name = name.rsplit(".", 1)[0].replace("_card", "")
    return clean_name.split("_")

def find_image_for_card(card_name: str):
    """Ищет файл картинки по названию карты с учётом '_card' и разных расширений."""
    base_name = card_name.replace(" ", "_") + "_card"
    for ext in ALLOWED_EXT:
        path = os.path.join(IMAGE_FOLDER, base_name + ext)
        if os.path.exists(path):
            return base_name + ext
    return None

def get_random_card_from_csv(df):
    return df.sample(1).iloc[0]

def generate_first_hint(words: list[str]) -> str:
    return " | ".join(" ".join("_" for _ in word) for word in words)

def generate_second_hint(words: list[str]) -> str:
    hint_words = []
    for word in words:
        if len(word) <= 2:
            indices = [0]
        else:
            num_reveals = random.choice([1, 2])
            possible_indices = list(range(len(word)))
            random.shuffle(possible_indices)
            indices = []
            for idx in possible_indices:
                if all(abs(idx - chosen) > 1 for chosen in indices):
                    indices.append(idx)
                if len(indices) == num_reveals:
                    break
        hint_word = " ".join(letter if i in indices else "_" for i, letter in enumerate(word))
        hint_words.append(hint_word)
    return " | ".join(hint_words)

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
if "current_image" not in st.session_state:
    st.session_state.current_image = None
if "attempts" not in st.session_state:
    st.session_state.attempts = 3
if "hints" not in st.session_state:
    st.session_state.hints = []
if "result" not in st.session_state:
    st.session_state.result = ""
if "options" not in st.session_state:
    st.session_state.options = []
if "show_image" not in st.session_state:
    st.session_state.show_image = False

# === ФУНКЦИЯ НОВОГО РАУНДА ===
def start_new_round():
    st.session_state.current_card = None
    st.session_state.current_image = None
    st.session_state.result = ""
    st.session_state.hints = []
    st.session_state.attempts = 3
    st.session_state.options = []
    st.session_state.show_image = False

    mode = st.session_state.mode
    card = get_random_card_from_csv(df_cards)
    st.session_state.current_card = card

    if mode == "По картинке":
        st.session_state.current_image = find_image_for_card(card["name"])
        st.session_state.show_image = True

    elif mode == "По описанию":
        st.session_state.show_image = False

    elif mode == "Лёгкий режим":
        st.session_state.current_image = find_image_for_card(card["name"])
        st.session_state.show_image = True

    elif mode == "Случайный режим":
        if random.choice([True, False]):
            st.session_state.current_image = find_image_for_card(card["name"])
            st.session_state.show_image = True
        else:
            st.session_state.show_image = False

    elif mode == "Множественный выбор":
        st.session_state.current_image = find_image_for_card(card["name"])
        st.session_state.show_image = True
        st.session_state.options = generate_options(df_cards, card["name"], 4)

# === ИНТЕРФЕЙС ===
st.title("🎴 Угадай карту")
mode = st.radio(
    "Выберите режим:",
    ["По картинке", "По описанию", "Лёгкий режим", "Случайный режим", "Множественный выбор"],
    key="mode_select"
)
if st.session_state.mode != mode:
    st.session_state.mode = mode
    start_new_round()

card = st.session_state.current_card

# === ПОКАЗ КАРТИНКИ ===
if st.session_state.show_image and st.session_state.current_image:
    image_path = os.path.join(IMAGE_FOLDER, st.session_state.current_image)
    if os.path.exists(image_path):
        img = Image.open(image_path)
        st.image(img, caption="Ваша карта", use_container_width=True)
    else:
        st.warning("Картинка не найдена для этой карты.")

# === ЛОГИКА ДЛЯ РАЗНЫХ РЕЖИМОВ ===
if st.session_state.mode == "Множественный выбор":
    # Показываем кнопки выбора
    if st.session_state.result == "":
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

else:
    # Для остальных режимов
    if st.session_state.result == "":
        guess = st.text_input("Введите название карты", key="guess_input")
        if st.button("Отправить"):
            if guess.strip():
                correct_answer = card["name"]
                if normalize_name(guess) == normalize_name(correct_answer):
                    st.session_state.result = "✅ Верно!"
                else:
                    st.session_state.attempts -= 1
                    words = split_original_name(correct_answer.replace(" ", "_") + "_card")
                    if st.session_state.attempts == 2:
                        st.session_state.hints.append(f"Подсказка: {generate_first_hint(words)}")
                    elif st.session_state.attempts == 1:
                        st.session_state.hints.append(f"Подсказка: {generate_second_hint(words)}")
                    if st.session_state.attempts == 0:
                        st.session_state.result = f"❌ Попытки закончились! Правильный ответ: {correct_answer}"
                st.rerun()
    else:
        st.subheader(st.session_state.result)
        if st.button("Начать заново"):
            start_new_round()
            st.rerun()

# === ПОДСКАЗКИ ===
if st.session_state.hints:
    st.subheader("💡 Подсказки:")
    for hint in st.session_state.hints:
        st.info(hint)
