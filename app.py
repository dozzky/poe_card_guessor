import os
import random
import streamlit as st
from PIL import Image

# === НАСТРОЙКИ ===
IMAGE_FOLDER = "images"
ALLOWED_EXT = (".png", ".jpg", ".jpeg", ".gif")

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

def get_random_image():
    files = [f for f in os.listdir(IMAGE_FOLDER) if f.lower().endswith(ALLOWED_EXT)]
    return random.choice(files) if files else None

def generate_first_hint(words: list[str]) -> str:
    """Подсказка 1: показываем длину каждого слова символами '_', с пробелами между буквами и словами."""
    return " | ".join(" ".join("_" for _ in word) for word in words)

def generate_second_hint(words: list[str]) -> str:
    """Подсказка 2: случайно открываем 1–2 буквы в каждом слове, с пробелами между буквами и словами."""
    hint_words = []
    for word in words:
        if len(word) <= 2:
            indices = [0]  # короткие слова — показываем первую букву
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

# === ИНИЦИАЛИЗАЦИЯ СОСТОЯНИЯ ===
if "current_image" not in st.session_state:
    st.session_state.current_image = None
if "attempts" not in st.session_state:
    st.session_state.attempts = 3
if "hints" not in st.session_state:
    st.session_state.hints = []
if "result" not in st.session_state:
    st.session_state.result = ""

# === ФУНКЦИЯ НОВОГО РАУНДА ===
def start_new_round():
    st.session_state.current_image = get_random_image()
    st.session_state.attempts = 3
    st.session_state.hints = []
    st.session_state.result = ""

# === ПЕРВЫЙ ЗАПУСК ===
if st.session_state.current_image is None:
    start_new_round()

# === ИНТЕРФЕЙС ===
st.title("🎴 Угадай карту")
st.write(f"Попыток осталось: **{st.session_state.attempts}**")

if st.session_state.current_image:
    image_path = os.path.join(IMAGE_FOLDER, st.session_state.current_image)
    img = Image.open(image_path)
    st.image(img, caption="Ваша карта", use_container_width=True)

# === Ввод ответа ===
if st.session_state.result == "":
    guess = st.text_input("Введите название карты", key="guess_input")
    if st.button("Отправить"):
        if guess.strip():
            correct_answer = st.session_state.current_image.rsplit(".", 1)[0]
            words = split_original_name(correct_answer)
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
                    correct_answer = correct_answer.replace("_", " ")
                    correct_answer = correct_answer[:-4]
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
