import streamlit as st
import sqlite3
import hashlib
import pandas as pd

# --- КОНФИГУРАЦИЯ ---
st.set_page_config(page_title="Blackwood Talent AI", layout="wide")

# --- БАЗОВЫЕ НАСТРОЙКИ АНАЛИЗА ---
JOB_REQUIREMENTS = {
    "Повар": ["Тех. карты", "Санитарные нормы", "Работа с грилем", "Скорость"],
    "Шеф-повар": ["Foodcost", "Разработка меню", "Управление командой", "Бюджетирование"],
    "Официант": ["Знание меню", "Upsell", "Сервис", "POS"]
}

# --- ФУНКЦИИ ---
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

# --- АВТОРИЗАЦИЯ ---
if 'user_role' not in st.session_state: st.session_state.user_role = None

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
            conn.close()
    else: # Режим регистрации
        admin_key = st.text_input("Ключ администратора", type="password")
        # ВАЖНО: Определяем роль до кнопки, чтобы она всегда была видна интерпретатору
        role = st.selectbox("Роль для нового пользователя", ["manager", "recruiter"])
        
        if st.button("Регистрация"):
            conn = sqlite3.connect('talent_hub.db')
            c = conn.cursor()
            # Проверка администратора
            c.execute("SELECT password_hash FROM users WHERE username='admin'")
            admin_data = c.fetchone()
            
            if admin_data and hash_password(admin_key) == admin_data[0]:
                try:
                    # Теперь role определена выше и гарантированно существует
                    c.execute("INSERT INTO users VALUES (?, ?, ?)", (user, hash_password(pwd), role))
                    conn.commit()
                    st.success("Пользователь успешно создан!")
                except sqlite3.IntegrityError:
                    st.error("Ошибка: Логин занят!")
            else:
                st.error("Неверный ключ администратора!")
            conn.close()
            
# --- ПАНЕЛЬ УПРАВЛЕНИЯ ---
st.sidebar.write(f"👤 Роль: **{st.session_state.user_role.upper()}**")
if st.sidebar.button("Выйти"):
    st.session_state.user_role = None
    st.rerun()

st.title("💼 Аналитика талантов Blackwood")

# Раздел загрузки
if st.session_state.user_role in ['admin', 'recruiter']:
    with st.expander("📥 Добавить кандидата"):
        with st.form("add_resume"):
            name = st.text_input("Имя")
            role = st.selectbox("Должность", list(JOB_REQUIREMENTS.keys()))
            text = st.text_area("Резюме (навыки)")
            if st.form_submit_button("Анализировать"):
                conn = sqlite3.connect('talent_hub.db')
                c = conn.cursor()
                c.execute("INSERT INTO resumes (name, role, content, status) VALUES (?, ?, ?, ?)", (name, role, text, 'new'))
                conn.commit()
                conn.close()

# Раздел анализа (Топ лучших)
if st.session_state.user_role in ['admin', 'manager']:
    st.subheader("📊 Рэнкинг кандидатов")
    conn = sqlite3.connect('talent_hub.db')
    df = pd.read_sql("SELECT * FROM resumes WHERE status='new'", conn)
    conn.close()
    
    if not df.empty:
        df['Score'] = df.apply(lambda x: analyze_candidate(x['content'], x['role']), axis=1)
        df = df.sort_values(by='Score', ascending=False)
        
        for _, row in df.iterrows():
            col1, col2 = st.columns([3, 1])
            color = "green" if row['Score'] > 70 else "orange" if row['Score'] > 30 else "red"
            col1.write(f"### {row['name']} | {row['role']}")
            col1.write(f"Навыки: {row['content'][:60]}...")
            col2.metric("Рейтинг", f"{row['Score']}%")
            st.divider()
