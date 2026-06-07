import streamlit as st
import sqlite3
import bcrypt

# --- ИНИЦИАЛИЗАЦИЯ БД ---
def init_db():
    conn = sqlite3.connect('talent_hub.db')
    c = conn.cursor()
    # Таблица пользователей (с хэшами паролей)
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (username TEXT PRIMARY KEY, password_hash TEXT, role TEXT)''')
    # Таблица резюме
    c.execute('''CREATE TABLE IF NOT EXISTS resumes 
                 (id INTEGER PRIMARY KEY, name TEXT, role TEXT, content TEXT, status TEXT)''')
    conn.commit()
    conn.close()

# --- ЛОГИКА ПАРОЛЕЙ ---
def verify_password(password, hashed):
    return bcrypt.checkpw(password.encode(), hashed)

# --- ИНТЕРФЕЙС УПРАВЛЕНИЯ ---
st.set_page_config(page_title="Blackwood Secure Core")

init_db()

# Пример входа с проверкой БД
st.title("🔐 Авторизация")
user = st.text_input("Логин")
pwd = st.text_input("Пароль", type="password")

if st.button("Войти"):
    conn = sqlite3.connect('talent_hub.db')
    c = conn.cursor()
    c.execute("SELECT password_hash, role FROM users WHERE username=?", (user,))
    data = c.fetchone()
    if data and verify_password(pwd, data[0]):
        st.session_state.user_role = data[1]
        st.success("Доступ разрешен")
    else:
        st.error("Неверные данные")
    conn.close()
