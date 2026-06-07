import streamlit as st

# 1. Инициализация системы прав
if 'user_role' not in st.session_state:
    st.session_state.user_role = None  # None, 'admin', 'manager', 'recruiter'

def login():
    st.title("🔐 Авторизация в системе Blackwood")
    role = st.selectbox("Выберите роль:", ["Директор", "Проверяющий", "Рекрутер"])
    password = st.text_input("Пароль", type="password")
    
    if st.button("Войти"):
        # Упрощенная проверка паролей (в реальном проекте - через хэширование)
        if password == "admin123": st.session_state.user_role = 'admin'
        elif password == "mgr123": st.session_state.user_role = 'manager'
        elif password == "rec123": st.session_state.user_role = 'recruiter'
        else: st.error("Неверный пароль")
        st.rerun()

# 2. Логика интерфейса по ролям
if st.session_state.user_role is None:
    login()
else:
    # Сайдбар с данными пользователя
    with st.sidebar:
        st.write(f"👤 Роль: **{st.session_state.user_role}**")
        if st.button("Выйти"):
            st.session_state.user_role = None
            st.rerun()

    # Разграничение доступа
    role = st.session_state.user_role

    if role == 'recruiter':
        st.title("📥 Подача резюме")
        st.write("Минимальный доступ: только форма загрузки.")
        # [Только форма загрузки...]

    elif role == 'manager':
        st.title("🧐 Панель проверяющего")
        st.write("Доступ к черновикам и проведение скоринга.")
        # [Интерфейс черновиков и переноса в базу...]

    elif role == 'admin':
        st.title("👑 Панель управления (Директор)")
        st.write("Полный контроль над всей базой талантов.")
        st.checkbox("Показывать конфиденциальную статистику")
        # [Весь функционал...]

#
