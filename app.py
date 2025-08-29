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

# === ЗАГРУЗКА CSV ===
df_cards = pd.read_csv(CSV_FILE)

# === ИНИЦИАЛИЗАЦИЯ СОСТОЯНИЯ ===
if "mode" not in st.session_state:
    st.session_state.mode = "По картинке"
if "current_image" not in st.session_state:
    st.session_state.current_image = None
if "current_card" not in st.session_state:
    st.session_state.current_card = None
if "attempts" not in st.session_state:
    st.session_state.attempts = 3
if "hints" not in st.session_state:
    st.session_state.hints = []
if "result" not in st.session_state:
    st.session_state.result = ""

# === ФУНКЦИЯ НОВОГО РАУНДА ===
def start_new_round():
    st.session_state.attempts = 3
    st.session_state.hints = []
    st.session_state.result = ""

    if st.session_state.mode == "По картинке":
        st.session_state.current_image = get_random_image()
        st.session_state.current_card = None

    elif st.session_state.mode == "По описанию":
        st.session_state.current_card = get_random_card_from_csv(df_cards)
        st.session_state.current_image = None

    elif st.session_state.mode == "Смешанный":
        # Выбираем случайную карту и пробуем найти её картинку
        card = get_random_card_from_csv(df_cards)
        st.session_state.current_card = card
        candidate_name = card["name"].replace(" ", "_").lower()
        images = [f for f in os.listdir(IMAGE_FOLDER) if f.lower().startswith(candidate_name)]
        st.session_state.current_image = random.choice(images) if images else None

# === ВЫБОР РЕЖИМА ===
st.title("🎴 Угадай карту")
mode = st.radio("Выберите режим:", ["По картинке", "По описанию", "Смешанный"], key="mode_select")
if st.session_state.mode != mode:
    st.session_state.mode = mode
    start_new_round()

st.write(f"Попыток осталось: **{st.session_state.attempts}**")

# === ИНТЕРФЕЙС ДЛЯ РЕЖИМОВ ===
if st.session_state.mode == "По картинке" and st.session_state.current_image:
    image_path = os.path.join(IMAGE_FOLDER, st.session_state.current_image)
    img = Image.open(image_path)
    st.image(img, caption="Ваша карта", use_container_width=True)

elif st.session_state.mode == "По описанию" and st.session_state.current_card is not None:
    st.subheader("Описание карты:")
    st.info(st.session_state.current_card["description"])

elif st.session_state.mode == "Смешанный":
    if st.session_state.current_card is not None:
        st.subheader("Описание карты:")
        st.info(st.session_state.current_card["description"])
    if st.session_state.current_image:
        image_path = os.path.join(IMAGE_FOLDER, st.session_state.current_image)
        img = Image.open(image_path)
        st.image(img, caption="Ваша карта", use_container_width=True)

# === Ввод ответа ===
if st.session_state.result == "":
    guess = st.text_input("Введите название карты", key="guess_input")
    if st.button("Отправить"):
        if guess.strip():
            # Определяем правильный ответ
            if st.session_state.mode == "По картинке":
                correct_answer = st.session_state.current_image.rsplit(".", 1)[0]
                words = split_original_name(correct_answer)

            elif st.session_state.mode == "По описанию":
                correct_answer = st.session_state.current_card["name"]
                words = correct_answer.split()

            elif st.session_state.mode == "Смешанный":
                correct_answer = st.session_state.current_card["name"]
                words = correct_answer.split()

            # Проверка
            if normalize_name(guess) == normalize_name(correct_answer):
                st.session_state.result = "✅ Верно!"
            else:
                st.session_state.attempts -= 1
                if st.session_state.attempts == 2:
                    hint = generate_first_hint(words)
                    st.session_state.hints.append(f"Подсказка: {hint}")
                elif st.session_state.attempts == 1:
                    hint = generate_second_hint(words)
                    st.session_state.hints.append(f"Подсказка: {hint}")
                if st.session_state.attempts == 0:
                    st.session_state.result = f"❌ Попытки закончились! Правильный ответ: {correct_answer}"
        st.rerun()

# === ПОДСКАЗКИ ===
if st.session_state.hints:
    st.subheader("💡 Подсказки:")
    for hint in st.session_state.hints:
        st.info(hint)

# === РЕЗУЛЬТАТ И КНОПКА НОВОЙ ИГРЫ ===
if st.session_state.result:
    st.subheader(st.session_state.result)
    if st.button("Начать заново"):
        start_new_round()
        st.rerun()
