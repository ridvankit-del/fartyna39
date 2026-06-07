import streamlit as st
import sqlite3
import hashlib
import pandas as pd

# 1. КОНФИГУРАЦИЯ СТРАНИЦЫ
st.set_page_config(page_title="Blackwood HR System", layout="wide")

# 2. ИНИЦИАЛИЗАЦИЯ БД
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

init_db()

# 3. УПРАВЛЕНИЕ СОСТОЯНИЕМ
if 'user_role' not in st.session_state:
    st.session_state.user_role = None

# 4. АВТОРИЗАЦИЯ
if st.session_state.user_role is None:
    st.title("🔐 Blackwood Access Portal")
    mode = st.radio("Выберите действие:", ["Вход", "Регистрация (через админа)"], horizontal=True)
    
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
        role = st.selectbox("Роль", ["manager", "recruiter"])
        if st.button("Зарегистрироваться"):
            conn = sqlite3.connect('talent_hub.db')
            c = conn.cursor()
            c.execute("SELECT password_hash FROM users WHERE username='admin'")
            admin_data = c.fetchone()
            if admin_data and hash_password(admin_key) == admin_data[0]:
                try:
                    c.execute("INSERT INTO users VALUES (?, ?, ?)", (user, hash_password(pwd), role))
                    conn.commit()
                    st.success("Пользователь создан!")
                except: st.error("Логин занят.")
            else: st.error("Неверный ключ админа!")
            conn.close()
    st.stop()

# 5. ОСНОВНОЙ ИНТЕРФЕЙС
st.sidebar.write(f"👤 Роль: **{st.session_state.user_role.upper()}**")
if st.sidebar.button("Выйти"):
    st.session_state.user_role = None
    st.rerun()

st.title(f"💼 Панель {st.session_state.user_role.upper()}")

if st.session_state.user_role in ['admin', 'recruiter']:
    st.subheader("📥 Загрузка резюме")
    with st.form("resume_form"):
        name = st.text_input("Имя кандидата")
        role = st.selectbox("Должность", ["Повар", "Су-шеф", "Шеф-повар", "Менеджер", "Хостес", "Официант"])
        text = st.text_area("Описание/Резюме")
        if st.form_submit_button("Отправить"):
            conn = sqlite3.connect('talent_hub.db')
            c = conn.cursor()
            c.execute("INSERT INTO resumes (name, role, content, status) VALUES (?, ?, ?, ?)", (name, role, text, 'new'))
            conn.commit()
            conn.close()
            st.success("Отправлено!")

if st.session_state.user_role in ['admin', 'manager']:
    st.subheader("🔍 Очередь на проверку")
    conn = sqlite3.connect('talent_hub.db')
    df = pd.read_sql("SELECT * FROM resumes WHERE status='new'", conn)
    st.table(df)
    conn.close()
