import streamlit as st
import sqlite3
import hashlib
import pandas as pd

# 1. КОНФИГУРАЦИЯ СТРАНИЦЫ
st.set_page_config(page_title="Blackwood AI HR", layout="wide")

# 2. НАСТРОЙКИ AI - ВЕСА НАВЫКОВ
# Сумма весов для одной роли должна быть 1.0 (100%)
JOB_REQUIREMENTS = {
    "Повар": {"Тех. карты": 0.3, "Санитарные нормы": 0.4, "Работа с грилем": 0.2, "Скорость": 0.1},
    "Шеф-повар": {"Foodcost": 0.5, "Разработка меню": 0.3, "Управление командой": 0.2},
    "Официант": {"Знание меню": 0.4, "Upsell": 0.3, "Сервис": 0.3}
}


# 3. ФУНКЦИИ БЕЗОПАСНОСТИ И БД
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def init_db():
    connection = sqlite3.connect('talent_hub.db')
    cursor = connection.cursor()
    # Создаем таблицы
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password_hash TEXT, role TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS resumes (id INTEGER PRIMARY KEY, name TEXT, role TEXT, content TEXT, status TEXT)''')
    
    # ПРИНУДИТЕЛЬНЫЙ СБРОС АДМИНА (Если есть проблемы со входом)
    admin_password_hash = hash_password("admin123")
    cursor.execute("INSERT OR REPLACE INTO users (username, password_hash, role) VALUES (?, ?, ?)", 
                   ("admin", admin_password_hash, "admin"))
    
    connection.commit()
    connection.close()

def analyze_candidate_score(resume_text, role):
    # Улучшенная структура: навык + вес + сложность
    requirements = JOB_REQUIREMENTS.get(role, {})
    if not requirements: return {"total": 0, "details": {}}
    
    total_score = 0
    details = {}
    
    for skill, weight in requirements.items():
        # Ищем навык и проверяем наличие "сильных" слов рядом (например, "опыт", "эксперт")
        if skill.lower() in resume_text.lower():
            # Если навык найден, добавляем вес. 
            # Можно добавить множитель, если в тексте есть слово "эксперт"
            boost = 1.2 if "эксперт" in resume_text.lower() or "senior" in resume_text.lower() else 1.0
            score = weight * 100 * boost
            total_score += score
            details[skill] = round(weight * 100)
        else:
            details[skill] = 0
            
    return {"total": min(round(total_score), 100), "details": details}
    
    score = 0
    # Проходим по словарю: skill - навык, weight - его вес
    for skill, weight in requirements.items():
        if skill.lower() in resume_text.lower():
            score += weight * 100
            
    return round(score)
    
    # Подсчитываем наличие ключевых слов в тексте
    found_count = 0
    for skill in required_skills:
        if skill.lower() in resume_text.lower():
            found_count += 1
            
    # Вычисляем процент соответствия
    score = (found_count / len(required_skills)) * 100
    return round(score)

# Инициализируем базу при каждом запуске
init_db()

# 4. СОСТОЯНИЕ СЕССИИ
if 'user_role' not in st.session_state:
    st.session_state.user_role = None

# 5. ЭКРАН АВТОРИЗАЦИИ
if st.session_state.user_role is None:
    st.title("🔐 Вход в систему управления персоналом")
    
    mode = st.radio("Выберите режим:", ["Вход", "Регистрация нового пользователя"], horizontal=True)
    
    input_user = st.text_input("Введите логин:")
    input_password = st.text_input("Введите пароль:", type="password")
    
    if mode == "Вход":
        if st.button("Войти в систему"):
            connection = sqlite3.connect('talent_hub.db')
            cursor = connection.cursor()
            cursor.execute("SELECT password_hash, role FROM users WHERE username=?", (input_user,))
            user_data = cursor.fetchone()
            
            if user_data:
                stored_hash = user_data[0]
                role = user_data[1]
                
                if hash_password(input_password) == stored_hash:
                    st.session_state.user_role = role
                    connection.close()
                    st.rerun()
                else:
                    st.error("Ошибка: Неверный пароль.")
            else:
                st.error("Ошибка: Пользователь не найден.")
            connection.close()
            
    else: # Режим регистрации
        admin_key = st.text_input("Ключ администратора (пароль админа):", type="password")
        new_role = st.selectbox("Выберите роль для нового сотрудника:", ["manager", "recruiter"])
        
        if st.button("Зарегистрировать пользователя"):
            connection = sqlite3.connect('talent_hub.db')
            cursor = connection.cursor()
            
            # Проверяем пароль админа для права на регистрацию
            cursor.execute("SELECT password_hash FROM users WHERE username='admin'")
            admin_data = cursor.fetchone()
            
            if admin_data and hash_password(admin_key) == admin_data[0]:
                try:
                    cursor.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)", 
                                   (input_user, hash_password(input_password), new_role))
                    connection.commit()
                    st.success(f"Пользователь {input_user} успешно зарегистрирован!")
                except sqlite3.IntegrityError:
                    st.error("Ошибка: Такой логин уже существует в системе.")
            else:
                st.error("Ошибка: Неверный ключ администратора.")
            connection.close()
    
    st.stop()

# 6. ОСНОВНОЙ ИНТЕРФЕЙС (после входа)
st.sidebar.title("Панель управления")
st.sidebar.write(f"Текущая роль: **{st.session_state.user_role.upper()}**")
if st.sidebar.button("Выйти из системы"):
    st.session_state.user_role = None
    st.rerun()

st.title(f"💼 Панель {st.session_state.user_role.upper()}")

# Секция загрузки резюме
if st.session_state.user_role in ['admin', 'recruiter']:
    st.header("📥 Добавление нового резюме")
    with st.form("resume_form"):
    name = st.text_input("Имя кандидата")
    role = st.selectbox("Должность", list(JOB_REQUIREMENTS.keys()))
    years = st.number_input("Стаж работы (лет)", min_value=0, max_value=40, value=1) # НОВОЕ
    text = st.text_area("Описание навыков")
    if st.form_submit_button("Добавить"):
        conn = sqlite3.connect('talent_hub.db')
        c = conn.cursor()
        # Добавляем years в запрос
        c.execute("INSERT INTO resumes (name, role, content, status, experience) VALUES (?, ?, ?, ?, ?)", 
                  (name, role, text, 'new', years))
        conn.commit()
        conn.close()

# Секция анализа для Менеджера/Админа
if st.session_state.user_role in ['admin', 'manager']:
    st.header("📊 Профессиональный анализ")
    
    conn = sqlite3.connect('talent_hub.db')
    df = pd.read_sql("SELECT * FROM resumes WHERE status='new'", conn)
    conn.close()
    
    if not df.empty:
        for _, row in df.iterrows():
            result = analyze_candidate_score(row['content'], row['role'])
            score = result['total']
            
            # Определяем статус
            if score >= 80: status = "🟢 Топ-кандидат"
            elif score >= 50: status = "🟡 В резерв"
            else: status = "🔴 Отказ"
            
            with st.expander(f"{status} | {row['name']} ({row['role']}) - {score}%"):
                col1, col2 = st.columns([2, 1])
                col1.write(f"**Навыки:** {row['content']}")
                
                # Детальная аналитика по навыкам
                for skill, val in result['details'].items():
                    col2.write(f"{skill}:")
                    col2.progress(val / 100)
                
                if st.button("🗑️ Удалить запись", key=f"del_{row['id']}"):
                    # (код удаления такой же, как мы делали ранее)
                    st.rerun()
    else:
        st.info("Нет данных для анализа.")
