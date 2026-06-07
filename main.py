import streamlit as st
import sqlite3
import hashlib

# --- ФУНКЦИИ БЕЗОПАСНОСТИ ---
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(username, password, role):
    conn = sqlite3.connect('talent_hub.db')
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users VALUES (?, ?, ?)", (username, hash_password(password), role))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

# --- ПАНЕЛЬ РЕГИСТРАЦИИ (ТОЛЬКО ДЛЯ ДИРЕКТОРА) ---
if st.session_state.get('user_role') == 'admin':
    with st.expander("➕ Создать новую учетную запись"):
        st.subheader("Регистрация пользователя")
        new_user = st.text_input("Логин нового пользователя")
        new_pwd = st.text_input("Пароль", type="password")
        new_role = st.selectbox("Роль", ["manager", "recruiter"])
        
        if st.button("Зарегистрировать в системе"):
            if register_user(new_user, new_pwd, new_role):
                st.success(f"Пользователь {new_user} успешно создан!")
            else:
                st.error("Пользователь с таким логином уже существует.")
