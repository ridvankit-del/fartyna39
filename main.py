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

# Безопасный импорт ключа из настроек Streamlit Cloud (Secrets)
OPENROUTER_API_KEY = st.secrets.get("OPENROUTER_API_KEY")

st.markdown("""
    <style>
        .main-title { font-size: 42px !important; font-weight: 800 !important; color: #1E1E1E; text-transform: uppercase; letter-spacing: 1.5px; }
        .subtitle { font-size: 18px !important; color: #666666; margin-bottom: 30px; }
        div[data-testid="stMetricSimpleValue"] { font-size: 28px !important; font-weight: 700 !important; }
    </style>
""", unsafe_allow_html=True)

# 2. МАТРИЦА И БД
JOB_REQUIREMENTS = {
    "Повар": {"Hard Skills": {"Тех. карты": 0.3, "Санитарные нормы": 0.4, "Работа с грилем": 0.2}, "Процессы": {"Скорость": 0.1}},
    "Шеф-повар": {"Управление": {"Foodcost": 0.5, "Инвентаризация": 0.2, "Управление командой": 0.3}},
    "Официант": {"Сервис": {"Знание меню": 0.4, "Стандарты сервиса": 0.3}, "Продажи": {"Upsell": 0.3}}
}
VACANCIES_LIST = list(JOB_REQUIREMENTS.keys())

def hash_password(password): return hashlib.sha256(password.encode()).hexdigest()

def init_db():
    conn = sqlite3.connect('talent_hub.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password_hash TEXT, role TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS resumes (id INTEGER PRIMARY KEY, name TEXT, role TEXT, content TEXT, status TEXT, experience INTEGER, ai_summary TEXT)''')
    # Дефолт админ
    c.execute("INSERT OR IGNORE INTO users VALUES (?, ?, ?)", ("admin", hash_password("admin123"), "admin"))
    conn.commit(); conn.close()

# 3. БЕЗОПАСНОСТЬ: ПРОВЕРКА ПРАВ
def check_access(required_role=None):
    if 'user_role' not in st.session_state or st.session_state.user_role is None: return False
    if required_role and st.session_state.user_role != 'admin' and st.session_state.user_role != required_role: return False
    return True

# 4. ФУНКЦИИ ИИ И ПАРСИНГА
def extract_text_from_file(uploaded_file):
    try:
        ext = uploaded_file.name.split('.')[-1].lower()
        if ext == 'pdf':
            reader = pypdf.PdfReader(io.BytesIO(uploaded_file.read()))
            return "".join([p.extract_text() for p in reader.pages])
        elif ext in ['docx', 'doc']:
            return docx2txt.process(io.BytesIO(uploaded_file.read()))
    except: return ""
    return ""

def ask_llm_analysis(resume_text, role, experience, requirements):
    if not OPENROUTER_API_KEY: return "⚠️ Ошибка безопасности: API-ключ не настроен."
    prompt = f"Ты HR Blackwood. Проанализируй резюме: {resume_text}. Вакансия: {role}. Стаж: {experience}. Критерии: {requirements}. Дай отчет в Markdown."
    try:
        resp = requests.post("https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}"},
            json={"model": "meta-llama/llama-3-8b-instruct:free", "messages": [{"role": "user", "content": prompt}]}, timeout=20)
        return resp.json()['choices'][0]['message']['content'] if resp.status_code == 200 else "Ошибка ИИ"
    except: return "Ошибка связи с сервером"

def calc_score(resume_text, role, experience):
    cats = JOB_REQUIREMENTS.get(role, {})
    score = 0
    details = {}
    for cat, skills in cats.items():
        for skill, weight in skills.items():
            val = weight * 100 if skill.lower() in resume_text.lower() else 0
            score += val
            details[f"{cat}: {skill}"] = int(val)
    return {"total": min(int(score * (1.1 if experience > 2 else 1.0)), 100), "details": details}

# 5. ИНТЕРФЕЙС
init_db()
if 'user_role' not in st.session_state: st.session_state.user_role = None

if st.session_state.user_role is None:
    st.title("🔐 Авторизация Blackwood")
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
        else: st.error("Неверные данные")
else:
    st.sidebar.write(f"Пользователь: **{st.session_state.user_role.upper()}**")
    if st.sidebar.button("Выйти"): st.session_state.user_role = None; st.rerun()
    
    st.markdown('<p class="main-title">💼 BLACKWOOD ENTERPRISE</p>', unsafe_allow_html=True)

    # МОДУЛЬ 1: Рекрутинг (с проверкой прав)
    if check_access('recruiter'):
        st.subheader("📥 Импорт соискателей")
        up_file = st.file_uploader("Загрузить файл", type=['pdf', 'docx'])
        name = st.text_input("ФИО")
        role = st.selectbox("Вакансия", VACANCIES_LIST)
        
        if st.button("Проанализировать и сохранить"):
            text = extract_text_from_file(up_file) if up_file else ""
            with st.spinner("ИИ анализирует..."):
                summary = ask_llm_analysis(text, role, 0, "")
                conn = sqlite3.connect('talent_hub.db')
                conn.execute("INSERT INTO resumes (name, role, content, status, experience, ai_summary) VALUES (?,?,?,?,?,?)", 
                             (name, role, text, 'Новый', 0, summary))
                conn.commit(); conn.close()
                st.success("Кандидат добавлен!")

    # МОДУЛЬ 2: CRM (с проверкой прав)
    if check_access('manager'):
        st.subheader("📊 Аналитика и CRM")
        conn = sqlite3.connect('talent_hub.db')
        df = pd.read_sql("SELECT * FROM resumes", conn)
        conn.close()
        
        if not df.empty:
            tab1, tab2 = st.tabs(["🎯 Воронка", "📈 Метрики"])
            with tab1:
                st.dataframe(df)
            with tab2:
                st.bar_chart
