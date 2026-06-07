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

def hash_password(password): return hashlib.sha256(password.encode()).hexdigest()

def init_db():
    conn = sqlite3.connect('talent_hub.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password_hash TEXT, role TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS resumes 
                      (id INTEGER PRIMARY KEY, name TEXT, role TEXT, content TEXT, status TEXT, experience INTEGER, ai_summary TEXT)''')
    try:
        c.execute("ALTER TABLE resumes ADD COLUMN experience INTEGER")
        c.execute("ALTER TABLE resumes ADD COLUMN ai_summary TEXT")
    except: pass
    c.execute("INSERT OR IGNORE INTO users VALUES (?, ?, ?)", ("admin", hash_password("admin123"), "admin"))
    conn.commit(); conn.close()

# 3. БЕЗОПАСНОСТЬ И ЛОГИКА
def check_access(required_role=None):
    if 'user_role' not in st.session_state or st.session_state.user_role is None: return False
    if required_role and st.session_state.user_role != 'admin' and st.session_state.user_role != required_role: return False
    return True

def ask_llm_analysis(resume_text, role, experience, requirements):
    if not OPENROUTER_API_KEY: return "⚠️ API-ключ не настроен."
    prompt = f"Ты HR-директор Blackwood. Проанализируй кандидата на роль {role}. Опыт: {experience} лет. Текст: {resume_text}. Выдай структурированный Markdown отчет."
    try:
        resp = requests.post("https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}"},
            json={"model": "meta-llama/llama-3-8b-instruct:free", "messages": [{"role": "user", "content": prompt}]}, timeout=20)
        return resp.json()['choices'][0]['message']['content'] if resp.status_code == 200 else "Ошибка API"
    except: return "Ошибка связи с ИИ"

# 4. МОДАЛЬНОЕ ОКНО
@st.dialog("📋 Живой ИИ-Анализ профиля")
def show_candidate_modal(row):
    st.write(f"### {row['name']}")
    st.markdown(row['ai_summary'] if row['ai_summary'] else "Анализ не проводился.")
    if st.button("Закрыть"): st.rerun()

# 5. ОСНОВНОЙ ИНТЕРФЕЙС
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
        conn.close()
else:
    if st.sidebar.button("Выйти"): st.session_state.user_role = None; st.rerun()
    
    st.markdown('<p class="main-title">💼 BLACKWOOD ENTERPRISE</p>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">AI Talent Hub & Кадровое планирование</p>', unsafe_allow_html=True)
    
    # МОДУЛЬ 1: Рекрутинг
    if check_access('recruiter'):
        st.subheader("📥 Умный импорт соискателей")
        uploaded_file = st.file_uploader("Загрузить файл", type=['pdf', 'docx'])
        name = st.text_input("ФИО Кандидата")
        role = st.selectbox("Вакансия", list(JOB_REQUIREMENTS.keys()))
        years = st.number_input("Стаж", 0, 40)
        
        if st.button("Запустить ИИ-анализ"):
            text = "Анализ текста из файла..."
            with st.spinner("ИИ анализирует..."):
                summary = ask_llm_analysis(text, role, years, "")
                conn = sqlite3.connect('talent_hub.db')
                conn.execute("INSERT INTO resumes (name, role, content, status, experience, ai_summary) VALUES (?,?,?,?,?,?)", 
                             (name, role, text, 'Новый', years, summary))
                conn.commit(); conn.close()
                st.success("Кандидат добавлен!")

    # МОДУЛЬ 2: CRM
    if check_access('manager'):
        st.subheader("📊 Аналитический центр и CRM")
        conn    cats = JOB_REQUIREMENTS.get(role, {})
    total = 0
    details = {}
    for cat, skills in cats.items():
        for skill, weight in skills.items():
            val = weight * 100 if skill.lower() in resume_text.lower() else 0
            total += val
            details[f"{cat}: {skill}"] = int(val)
    return {"total": min(int(total * (1.1 if experience > 2 else 1.0)), 100), "details": details}

# 4. МОДАЛЬНОЕ ОКНО
@st.dialog("📋 Живой ИИ-Анализ профиля")
def show_candidate_modal(row):
    st.write(f"### {row['name']}")
    st.markdown(row['ai_summary'] if row['ai_summary'] else "Анализ не проводился.")
    if st.button("Закрыть"): st.rerun()

# 5. ОСНОВНОЙ ИНТЕРФЕЙС
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
        conn.close()
else:
    if st.sidebar.button("Выйти"): st.session_state.user_role = None; st.rerun()
    
    st.markdown('<p class="main-title">💼 BLACKWOOD ENTERPRISE</p>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">AI Talent Hub & Кадровое планирование</p>', unsafe_allow_html=True)
    
    # МОДУЛЬ 1: Рекрутинг
    if check_access('recruiter'):
        st.subheader("📥 Умный импорт соискателей")
        uploaded_file = st.file_uploader("Загрузить файл", type=['pdf', 'docx'])
        name = st.text_input("ФИО Кандидата")
        role = st.selectbox("Вакансия", list(JOB_REQUIREMENTS.keys()))
        years = st.number_input("Стаж", 0, 40)
        
        if st.button("Запустить ИИ-анализ"):
            text = "Анализ текста из файла..."
            with st.spinner("ИИ анализирует..."):
                summary = ask_llm_analysis(text, role, years, "")
                conn = sqlite3.connect('talent_hub.db')
                conn.execute("INSERT INTO resumes (name, role, content, status, experience, ai_summary) VALUES (?,?,?,?,?,?)", 
                             (name, role, text, 'Новый', years, summary))
                conn.commit(); conn.close()
                st.success("Кандидат добавлен!")

    # МОДУЛЬ 2: CRM
    if check_access('manager'):
        st.subheader("📊 Аналитический центр и CRM")
        conn = sqlite3.connect('talent_hub.db')
        df = pd.read_sql("SELECT * FROM resumes", conn)
        conn.close()
        
        if not df.empty:
            tab1, tab2, tab3 = st.tabs(["🎯 CRM Воронка", "📈 Аналитика", "📄 Офферы"])
            with tab1:
                for _, row in df.iterrows():
                    col1, col2 = st.columns([3, 1])
                    col1.markdown(f"**{row['name']}** | *{row['role']}*")
                    if col2.button("👁️ Профиль", key=f"view_{row['id']}"):
                        show_candidate_modal(row)
            with tab2:
                st.bar_chart(df.groupby('role')['id'].count())
            with tab3:
                st.info("Генератор офферов доступен для кандидатов со статусом 'Оффер'.")
        else:
            st.info("В базе данных нет анкет.")    details = {}
    for cat, skills in cats.items():
        for skill, weight in skills.items():
            val = weight * 100 if skill.lower() in resume_text.lower() else 0
            total += val
            details[f"{cat}: {skill}"] = int(val)
    return {"total": min(int(total), 100), "details": details}

# 4. МОДАЛЬНОЕ ОКНО
@st.dialog("📋 Живой ИИ-Анализ профиля")
def show_candidate_modal(row, res_details):
    st.write(f"### {row['name']}")
    st.markdown(row['ai_summary'] if row['ai_summary'] else "Нет данных")
    st.write("---")
    if st.button("Закрыть"): st.rerun()

# 5. ОСНОВНОЙ ИНТЕРФЕЙС
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
        conn.close()
else:
    if st.sidebar.button("Выйти"): st.session_state.user_role = None; st.rerun()
    
    st.markdown('<p class="main-title">💼 BLACKWOOD ENTERPRISE</p>', unsafe_allow_html=True)
    
    # МОДУЛЬ 1: Рекрутинг
    if check_access('recruiter'):
        st.subheader("📥 Импорт соискателей")
        uploaded_file = st.file_uploader("Загрузить файл", type=['pdf', 'docx'])
        name = st.text_input("ФИО")
        role = st.selectbox("Вакансия", list(JOB_REQUIREMENTS.keys()))
        
        if st.button("Запустить ИИ"):
            text = "Анализ текста из файла..." 
            with st.spinner("ИИ анализирует..."):
                summary = ask_llm_analysis(text, role, 0, "")
                conn = sqlite3.connect('talent_hub.db')
                conn.execute("INSERT INTO resumes (name, role, content, status, experience, ai_summary) VALUES (?,?,?,?,?,?)", 
                             (name, role, text, 'Новый', 0, summary))
                conn.commit(); conn.close()
                st.success("Добавлено!")

    # МОДУЛЬ 2: CRM
    if check_access('manager'):
        st.subheader("📊 Аналитика и CRM")
        conn = sqlite3.connect('talent_hub.db')
        df = pd.read_sql("SELECT * FROM resumes", conn)
        conn.close()
        
        if not df.empty:
            tab1, tab2 = st.tabs(["🎯 Воронка", "📈 Метрики"])
            with tab1:
                for _, row in df.iterrows():
                    col1, col2 = st.columns([3, 1])
                    col1.write(f"**{row['name']}** - {row['role']}")
                    if col2.button("👁️ Профиль", key=f"view_{row['id']}"):
                        show_candidate_modal(row, {"details": {}})
            with tab2:
                st.bar_chart(df.groupby('role')['id'].count())
        else:
            st.info("В базе данных нет анкет.")
