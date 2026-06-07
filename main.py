import streamlit as st
import sqlite3
import hashlib

# 1. Сначала КОНФИГУРАЦИЯ страницы
st.set_page_config(page_title="Blackwood HR System", layout="wide")

# 2. ИНИЦИАЛИЗАЦИЯ базы данных
def init_db():
    # ... (твоя функция инициализации)
    pass

init_db()

# 3. ТОЛЬКО ПОСЛЕ ЭТОГО инициализация session_state
if 'user_role' not in st.session_state:
    st.session_state.user_role = None

# 4. И ТОЛЬКО ПОСЛЕ ВСЕГО ЭТОГО проверка
if st.session_state.user_role is None:
    # ... (логика входа)# --- 3. АВТОРИЗАЦИЯ И РЕГИСТРАЦИЯ (СМЕННАЯ ПОЗИЦИЯ) ---
if st.session_state.user_role is None:
    st.title("🔐 Blackwood Access Portal")
    
    # Выбор режима
    mode = st.radio("Выберите действие:", ["Вход", "Регистрация (только админом)"], horizontal=True)
    
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
            else:
                st.error("Неверные данные")
            conn.close()
            
    else: # Режим регистрации
        admin_key = st.text_input("Ключ администратора", type="password")
        role = st.selectbox("Роль для нового пользователя", ["manager", "recruiter"])
        
        if st.button("Зарегистрироваться"):
            # Проверка администратора (регистрация только через верный пароль админа)
            conn = sqlite3.connect('talent_hub.db')
            c = conn.cursor()
            c.execute("SELECT password_hash FROM users WHERE username='admin'")
            admin_data = c.fetchone()
            
            if admin_data and hash_password(admin_key) == admin_data[0]:
                try:
                    c.execute("INSERT INTO users VALUES (?, ?, ?)", (user, hash_password(pwd), role))
                    conn.commit()
                    st.success("Пользователь успешно создан!")
                except:
                    st.error("Логин уже занят.")
            else:
                st.error("Неверный ключ администратора!")
            conn.close()
    st.stop()
