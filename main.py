import streamlit as st
import sqlite3
import hashlib
import pandas as pd
import requests
import json
import io
import pypdf
import docx2txt

# 1. КОНФИГУРАЦИЯ
st.set_page_config(page_title="Blackwood Enterprise AI HR", layout="wide")

# Безопасный ключ (Настрой в Secrets в Streamlit Cloud)
OPENROUTER_API_KEY = st.secrets.get("OPENROUTER_API_KEY")

st.markdown("""
    <style>
        .main-title { font-size: 42px !important; font-weight: 800 !important; color: #1E1E1E; text-transform: uppercase; letter-spacing: 1.5px; }
        .subtitle { font-size: 18px !important; color: #666666; margin-bottom: 30px; }
        div[data-testid="stMetricSimpleValue"] { font-size: 28px !important; font-weight: 700 !important; color: #111111; }
        .custom-card { background-color: #F9F9FB; padding: 20px; border-radius: 12px; border-left: 5px solid #1E1E1E; box-shadow: 0 4px 6px rgba(0,0,0,0.02); margin-bottom: 15px; }
    </style>
""", unsafe_allow_html=True)

# 2. МАТРИЦА И БД
JOB_REQUIREMENTS = {
    "Повар": {"Hard Skills": {"Тех. карты": 0.3, "Санитарные нормы": 0.4, "Работа с грилем": 0.2}, "Процессы": {"Скорость": 0.1}},
    "Шеф-повар": {"Управление": {"Foodcost": 0.5, "Инвентаризация": 0.2, "Управление командой": 0.3}},
    "Официант": {"Сервис": {"Знание меню": 0.4, "Стандарты сервиса": 0.3}, "Продажи": {"Upsell": 0.3}}
}

def hash_password(password): 
    return hashlib.sha256(password.encode()).hexdigest()

def init_db():
    conn = sqlite3.connect('talent_hub.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password_hash TEXT, role TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS resumes 
                      (id INTEGER PRIMARY KEY, name TEXT, role TEXT, content TEXT, status TEXT, experience INTEGER, ai_summary TEXT)''')
    try:
        c.execute("ALTER TABLE resumes ADD COLUMN experience INTEGER")
        c.execute("ALTER TABLE resumes ADD COLUMN ai_summary TEXT")
    except: 
        pass
    c.execute("INSERT OR IGNORE INTO users VALUES (?, ?, ?)", ("admin", hash_password("admin123"), "admin"))
    conn.commit()
    conn.close()

# 3. БЕЗОПАСНОСТЬ И ЛОГИКА
def check_access(required_role=None):
    if 'user_role' not in st.session_state or st.session_state.user_role is None: 
        return False
    if required_role and st.session_state.user_role != 'admin' and st.session_state.user_role != required_role: 
        return False
    return True

def ask_llm_analysis(resume_text, role, experience, requirements):
    if not OPENROUTER_API_KEY: 
        return "⚠️ API-ключ не настроен."
    prompt = f"Ты HR-директор Blackwood. Проанализируй кандидата на роль {role}. Опыт: {experience} лет. Текст: {resume_text}. Выдай структурированный Markdown отчет."
    try:
        resp = requests.post("https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}"},
            json={"model": "meta-llama/llama-3-8b-instruct:free", "messages": [{"role": "user", "content": prompt}]}, timeout=20)
        return resp.json()['choices'][0]['message']['content'] if resp.status_code == 200 else "Ошибка API"
    except: 
        return "Ошибка связи с ИИ"

# 4. МОДАЛЬНОЕ ОКНО
@st.dialog("📋 Живой ИИ-Анализ профиля")
def show_candidate_modal(row):
    st.write(f"### {row['name']}")
    st.markdown(row['ai_summary'] if row['ai_summary'] else "Анализ не проводился.")
    if st.button("Закрыть"): 
        st.rerun()

# 5. ОСНОВНОЙ ИНТЕРФЕЙС
init_db()
if 'user_role' not in st.session_state: 
    st.session_state.user_role = None

if st.session_state.user_role is None:
    st.title("🔐 Авторизация Blackwood")
    user = st.text_input("Логин")
    pwd = st.text_input("Пароль", type="password")
    if st.button("Войти"):
        conn = sqlite3.connect('talent_hub.db')
        c = conn.cursor()
        c.execute("SELECT password_hash, role FROM users WHERE username=?", (user,))
        data = c.fetchone()
        conn.close()
        if data and hash_password(pwd) == data[0]:
            st.session_state.user_role = data[1]
            st.rerun()
        else: 
            st.error("Неверные данные")
else:
    if st.sidebar.button
