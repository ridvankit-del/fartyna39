import streamlit as st
import sqlite3
import hashlib
import pandas as pd
import requests
import json
import io
import pypdf
import docx2txt

# --- КОНФИГУРАЦИЯ ---
st.set_page_config(page_title="Blackwood Enterprise HR", layout="wide")
OPENROUTER_API_KEY = st.secrets.get("OPENROUTER_API_KEY")

# --- БЕЗОПАСНОСТЬ И БД ---
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def init_db():
    conn = sqlite3.connect('talent_hub.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password_hash TEXT, role TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS resumes (id INTEGER PRIMARY KEY, name TEXT, role TEXT, content TEXT, status TEXT, experience INTEGER, ai_summary TEXT)''')
    # Дефолтный админ
    c.execute("INSERT OR IGNORE INTO users VALUES (?, ?, ?)", ("admin", hash_password("admin123"), "admin"))
    conn.commit(); conn.close()

def check_access(required_role=None):
    if 'user_role' not in st.session_state: return False
    if required_role and st.session_state.user_role != 'admin' and st.session_state.user_role != required_role: return False
    return True

# --- ИИ ЛОГИКА ---
def ask_llm_analysis(resume_text, role, experience, requirements):
    if not OPENROUTER_API_KEY: return "⚠️ API-ключ не настроен."
    prompt = f"Ты HR Blackwood. Проанализируй кандидата на роль {role}. Стаж: {experience}. Критерии: {requirements}. Текст: {resume_text}. Выдай отчет в Markdown."
    try:
        resp = requests.post("https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}"},
            json={"model": "meta-llama/llama-3-8b-instruct:free", "messages": [{"role": "user", "content": prompt}]}, timeout=20)
        return resp.json()['choices'][0]['message']['content'] if resp.status_code == 200 else "Ошибка API"
    except: return "Ошибка связи с ИИ"

# --- ИНТЕРФЕЙС ---
init_db()
if 'user_role' not in st.session_state: st.session_state.user_role = None

if st.session_state.user_role is None:
    st.title("🔐 Вход в систему")
    user = st.text_input("Логин")
    pwd = st.text_input("Пароль", type="password")
    if st.button("Войти"):
        conn = sqlite3.connect('talent_hub.db')
        c = conn.cursor()
        c.execute("SELECT password_hash, role FROM users WHERE username=?", (user,))
        data = c.fetchone()
        if data and hash_password(pwd) == data[0]:
            st.session_state.user_role = data[1]
            st.rerun()
        else: st.error("Ошибка")
else:
    st.sidebar.write(f"Пользователь: {st.session_state.user_role}")
    if st.sidebar.button("Выйти"): st.session_state.user_role = None; st.rerun()

    if check_access('recruiter'):
        st.header("📥 Умный импорт резюме")
        up_file = st.file_uploader("Загрузить файл", type=['pdf', 'docx'])
        name = st.text_input("ФИО")
        role = st.selectbox("Вакансия", ["Повар", "Шеф-повар", "Официант"])
        if st.button("Запустить ИИ-анализ"):
            text = "" # Здесь логика извлечения из up_file
            with st.spinner("Анализ..."):
                summary = ask_llm_analysis(text, role, 0, "")
                conn = sqlite3.connect('talent_hub.db')
                conn.execute("INSERT INTO resumes (name, role, content, status, experience, ai_summary) VALUES (?,?,?,?,?,?)", 
                             (name, role, text, 'Новый', 0, summary))
                conn.commit(); conn.close()
                st.success("Готово!")

    if check_access('manager'):
        st.header("📊 CRM Воронка")
        conn = sqlite3.connect('talent_hub.db')
        df = pd.read_sql("SELECT * FROM resumes", conn)
        st.dataframe(df)
        conn.close()
