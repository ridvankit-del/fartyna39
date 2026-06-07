import streamlit as st
import sqlite3
import hashlib
import pandas as pd

# 1. КОНФИГУРАЦИЯ
st.set_page_config(page_title="Blackwood AI HR", layout="wide")

# 2. НАСТРОЙКИ AI
JOB_REQUIREMENTS = {
    "Повар": ["Тех. карты", "Санитарные нормы", "Работа с грилем", "Скорость"],
    "Шеф-повар": ["Foodcost", "Разработка меню", "Управление командой", "Бюджетирование"],
    "Официант": ["Знание меню", "Upsell", "Сервис", "POS"]
}

# 3. ФУНКЦИИ БД И БЕЗОПАСНОСТИ
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def init_db():
    conn = sqlite3.connect('talent_hub.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password_hash TEXT, role TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS resumes (id INTEGER PRIMARY KEY, name TEXT, role TEXT, content TEXT, status TEXT)''')
    c.execute("SELECT * FROM users WHERE username='admin'")
    if not c.fetchone():
        c.execute("INSERT INTO users VALUES (?, ?, ?)", ("admin", hash_password("admin123"), "admin"))
    conn.commit()
    conn.close()

def analyze_candidate(resume_text, role):
    required = JOB_REQUIREMENTS.get(role, [])
    if not required: return 0
    score = sum(1 for skill in required if skill.lower() in resume_text.lower())
    return round((score / len(required)) * 100)

init_db()

# 4. СОСТОЯНИЕ
if 'user_role' not in st.session_state: st.session_state.user_role = None

# 5. АВТОРИЗАЦИЯ И РЕГИСТРАЦИЯ
if st.session_state.user_role is None:
    st.title("🔐 Вход в систему Blackwood")
    mode = st.radio("Действие:", ["Вход", "Регистрация"], horizontal=True)
    user = st.text_input("Логин")
    pwd = st.text_input("Пароль", type="password")
    
    if mode == "Вход":
        if st.button("Войти"):
            conn = sqlite3.connect('talent_hub.db')
            c = conn.cursor()
            c.execute("SELECT password_hash, role FROM users WHERE username=?", (user,))
            data = c.fetchone()
            if data and hash_password(pwd) == data[0]:
                st.session_state.user_role = data[1]
                st.rerun()
            else: st.error("Неверные данные")
            conn.close()
    else:
        admin_key = st.text_input("Ключ администратора", type="password")
        role = st.selectbox("Роль нового сотрудника", ["manager", "recruiter"])
        if st.button("Регистрация"):
            conn = sqlite3.connect('talent_hub.db')
            c = conn.cursor()
            c.execute("SELECT password_hash FROM users WHERE username='admin'")
            admin_data = c.fetchone()
            if admin_data and hash_password(admin_key) == admin_data[0]:
                try:
                    c.execute("INSERT INTO users VALUES (?, ?, ?)", (user, hash_password(pwd), role))
                    conn.commit()
                    st.success("Пользователь создан!")
                except: st.error("Логин уже занят!")
            else: st.error("Неверный ключ!")
            conn.close()
    st.stop()

# 6. ОСНОВНОЙ ИНТЕРФЕЙС
st.sidebar.write(f"👤 Роль: **{st.session_state.user_role.upper() if st.session_state.user_role else 'Гость'}**")
if st.sidebar.button("Выйти"):
    st.session_state.user_role = None
    st.rerun()

st.title(f"💼 Панель: {st.session_state.user_role.upper()}")

# Загрузка (Рекрутер + Админ)
if st.session_state.user_role in ['admin', 'recruiter']:
    st.subheader("📥 Загрузить резюме")
    with st.form("resume_form"):
        name = st.text_input("Имя кандидата")
        role = st.selectbox("Должность", list(JOB_REQUIREMENTS.keys()))
        text = st.text_area("Навыки и описание")
        if st.form_submit_button("Добавить в базу"):
            conn = sqlite3.connect('talent_hub.db')
            c = conn.cursor()
            c.execute("INSERT INTO resumes (name, role, content, status) VALUES (?, ?, ?, ?)", (name, role, text, 'new'))
            conn.commit()
            conn.close()
            st.success("Кандидат добавлен!")

# Аналитика (Менеджер + Админ)
if st.session_state.user_role in ['admin', 'manager']:
    st.subheader("📊 Анализ кандидатов")
    conn = sqlite3.connect('talent_hub.db')
    df = pd.
