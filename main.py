import streamlit as st
import sqlite3
import hashlib

# --- 1. ФУНКЦИИ БЕЗОПАСНОСТИ И БД ---
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def init_db():
    conn = sqlite3.connect('talent_hub.db')
    c = conn.cursor()
    # Таблица пользователей
    c.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password_hash TEXT, role TEXT)''')
    # Таблица резюме
    c.execute('''CREATE TABLE IF NOT EXISTS resumes (id INTEGER PRIMARY KEY, name TEXT, role TEXT, content TEXT, status TEXT)''')
    
    # Создаем админа, если база пуста
    c.execute("SELECT * FROM users")
    if not c.fetchone():
        c.execute("INSERT INTO users VALUES (?, ?, ?)", ("admin", hash_password("admin123"), "admin"))
    conn.commit()
    conn.close()

# --- 2. ИНИЦИАЛИЗАЦИЯ ---
init_db()
if 'user_role' not in st.session_state: st.session_state.user_role = None

st.set_page_config(page_title="Blackwood HR System", layout="wide")

# --- 3. АВТОРИЗАЦИЯ ---
if st.session_state.user_role is None:
    st.title("🔐 Авторизация")
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
        else:
            st.error("Неверный логин или пароль")
        conn.close()
    st.stop()

# --- 4. ОСНОВНОЙ ИНТЕРФЕЙС ---
st.sidebar.write(f"👤 Роль: **{st.session_state.user_role}**")
if st.sidebar.button("Выйти"):
    st.session_state.user_role = None
    st.rerun()

st.title(f"💼 Панель {st.session_state.user_role.upper()}")

# Регистрация (только для админа)
if st.session_state.user_role == 'admin':
    with st.expander("➕ Создать нового пользователя"):
        new_u = st.text_input("Логин пользователя")
        new_p = st.text_input("Пароль", type="password")
        new_r = st.selectbox("Роль", ["manager", "recruiter"])
        if st.button("Зарегистрировать"):
            conn = sqlite3.connect('talent_hub.db')
            c = conn.cursor()
            try:
                c.execute("INSERT INTO users VALUES (?, ?, ?)", (new_u, hash_password(new_p), new_r))
                conn.commit()
                st.success("Пользователь добавлен")
            except: st.error("Ошибка")
            conn.close()

# Функционал для Рекрутера (загрузка)
if st.session_state.user_role in ['admin', 'recruiter']:
    st.subheader("📥 Загрузка резюме")
    with st.form("resume_form"):
        name = st.text_input("Имя кандидата")
        role = st.selectbox("Должность", ["Повар", "Су-шеф", "Шеф-повар", "Менеджер", "Хостес", "Официант"])
        text = st.text_area("Описание/Резюме")
        if st.form_submit_button("Отправить на проверку"):
            conn = sqlite3.connect('talent_hub.db')
            c = conn.cursor()
            c.execute("INSERT INTO resumes (name, role, content, status) VALUES (?, ?, ?, ?)", (name, role, text, 'new'))
            conn.commit()
            conn.close()
            st.success("Отправлено на проверку!")

# Функционал для Менеджера (проверка)
if st.session_state.user_role in ['admin', 'manager']:
    st.subheader("🔍 Очередь на проверку")
    conn = sqlite3.connect('talent_hub.db')
    df = pd.read_sql("SELECT * FROM resumes WHERE status='new'", conn)
    st.table(df)
    conn.close()
