import streamlit as st
import sqlite3
import hashlib
import pandas as pd

# 1. КОНФИГУРАЦИЯ
st.set_page_config(page_title="Blackwood AI HR", layout="wide")

# 2. НАСТРОЙКИ AI
JOB_REQUIREMENTS = {
    "Повар": {"Тех. карты": 0.3, "Санитарные нормы": 0.4, "Работа с грилем": 0.2, "Скорость": 0.1},
    "Шеф-повар": {"Foodcost": 0.5, "Разработка меню": 0.3, "Управление командой": 0.2},
    "Официант": {"Знание меню": 0.4, "Upsell": 0.3, "Сервис": 0.3}
}

# 3. ФУНКЦИИ
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def init_db():
    connection = sqlite3.connect('talent_hub.db')
    cursor = connection.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password_hash TEXT, role TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS resumes (id INTEGER PRIMARY KEY, name TEXT, role TEXT, content TEXT, status TEXT, experience INTEGER)''')
    
    admin_password_hash = hash_password("admin123")
    cursor.execute("INSERT OR REPLACE INTO users (username, password_hash, role) VALUES (?, ?, ?)", ("admin", admin_password_hash, "admin"))
    connection.commit()
    connection.close()

def analyze_candidate_score(resume_text, role, experience):
    requirements = JOB_REQUIREMENTS.get(role, {})
    if not requirements:
        return {"total": 0, "details": {}}
    
    base_score = 0
    details = {}
    for skill, weight in requirements.items():
        if skill.lower() in resume_text.lower():
            base_score += weight * 100
            details[skill] = round(weight * 100)
        else:
            details[skill] = 0
            
    if experience >= 5: exp_multiplier = 1.3
    elif experience >= 2: exp_multiplier = 1.1
    else: exp_multiplier = 1.0
    
    total_score = min(round(base_score * exp_multiplier), 100)
    return {"total": total_score, "details": details}

init_db()

# 4. СОСТОЯНИЕ
if 'user_role' not in st.session_state:
    st.session_state.user_role = None

# 5. АВТОРИЗАЦИЯ
if st.session_state.user_role is None:
    st.title("🔐 Вход в систему")
    mode = st.radio("Режим:", ["Вход", "Регистрация"], horizontal=True)
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
        key = st.text_input("Ключ администратора", type="password")
        role = st.selectbox("Роль", ["manager", "recruiter"])
        if st.button("Зарегистрироваться"):
            conn = sqlite3.connect('talent_hub.db')
            c = conn.cursor()
            c.execute("SELECT password_hash FROM users WHERE username='admin'")
            admin_data = c.fetchone()
            if admin_data and hash_password(key) == admin_data[0]:
                try:
                    c.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)", (user, hash_password(pwd), role))
                    conn.commit()
                    st.success("Пользователь создан!")
                except: st.error("Логин занят.")
            else: st.error("Неверный ключ!")
            conn.close()
    st.stop()

# 6. ИНТЕРФЕЙС
st.sidebar.write(f"👤 Роль: **{st.session_state.user_role.upper()}**")
if st.sidebar.button("Выйти"):
    st.session_state.user_role = None
    st.rerun()

st.title(f"💼 Панель {st.session_state.user_role.upper()}")

if st.session_state.user_role in ['admin', 'recruiter']:
    st.header("📥 Добавить кандидата")
    with st.form("resume_form"):
        name = st.text_input("Имя")
        role = st.selectbox("Должность", list(JOB_REQUIREMENTS.keys()))
        years = st.number_input("Стаж (лет)", min_value=0, max_value=40)
        text = st.text_area("Описание навыков")
        if st.form_submit_button("Добавить"):
            conn = sqlite3.connect('talent_hub.db')
            c = conn.cursor()
            c.execute("INSERT INTO resumes (name, role, content, status, experience) VALUES (?, ?, ?, ?, ?)", (name, role, text, 'new', years))
            conn.commit()
            conn.close()
            st.success("Кандидат добавлен!")

if st.session_state.user_role in ['admin', 'manager']:
    st.header("📊 Профессиональный анализ")
    conn = sqlite3.connect('talent_hub.db')
    df = pd.read_sql("SELECT * FROM resumes WHERE status='new'", conn)
    conn.close()
    
    if not df.empty:
        for _, row in df.iterrows():
            res = analyze_candidate_score(row['content'], row['role'], row['experience'])
            with st.expander(f"{row['name']} | Рейтинг: {res['total']}%"):
                col1, col2 = st.columns([2, 1])
                col1.write(f"**Навыки:** {row['content']}")
                for skill, val in res['details'].items():
                    col2.write(f"{skill}:")
                    col2.progress(val / 100)
                if st.button("🗑️ Удалить", key=f"del_{row['id']}"):
                    conn = sqlite3.connect('talent_hub.db')
                    conn.execute("DELETE FROM resumes WHERE id=?", (row['id'],))
                    conn.commit()
                    conn.close()
                    st.rerun()
    else: st.info("Очередь пуста.")
