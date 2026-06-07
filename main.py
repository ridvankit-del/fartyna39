import streamlit as st
import sqlite3
import hashlib
import pandas as pd

# 1. КОНФИГУРАЦИЯ СТРАНИЦЫ И СТИЛИ
st.set_page_config(page_title="Blackwood Enterprise AI HR", layout="wide")

st.markdown("""
    <style>
        .main-title {
            font-size: 40px !important;
            font-weight: 800 !important;
            color: #1E1E1E;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            margin-bottom: 5px;
        }
        .subtitle {
            font-size: 18px !important;
            color: #666666;
            margin-bottom: 25px;
        }
        .custom-card {
            background-color: #F9F9FB;
            padding: 20px;
            border-radius: 12px;
            border-left: 5px solid #1E1E1E;
            box-shadow: 0 4px 6px rgba(0,0,0,0.02);
            margin-bottom: 15px;
        }
        /* Стилизация картинок внутри карточек */
        .candidate-avatar {
            border-radius: 50%;
            object-fit: cover;
        }
    </style>
""", unsafe_allow_html=True)

# 2. МАТРИЦА КОМПЕТЕНЦИЙ
JOB_REQUIREMENTS = {
    "Повар": {
        "Hard Skills": {"Тех. карты": 0.3, "Санитарные нормы": 0.4, "Работа с грилем": 0.2},
        "Процессы": {"Скорость": 0.1}
    },
    "Шеф-повар": {
        "Управление": {"Foodcost": 0.5, "Инвентаризация": 0.2, "Управление командой": 0.3}
    },
    "Официант": {
        "Сервис": {"Знание меню": 0.4, "Стандарты сервиса": 0.3},
        "Продажи": {"Upsell": 0.3}
    }
}
VACANCIES_LIST = list(JOB_REQUIREMENTS.keys())

# 3. ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def init_db():
    connection = sqlite3.connect('talent_hub.db')
    cursor = connection.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password_hash TEXT, role TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS resumes 
                      (id INTEGER PRIMARY KEY, name TEXT, role TEXT, content TEXT, status TEXT, experience INTEGER)''')
    try:
        cursor.execute("ALTER TABLE resumes ADD COLUMN experience INTEGER")
        connection.commit()
    except sqlite3.OperationalError:
        pass
    admin_hash = hash_password("admin123")
    cursor.execute("INSERT OR REPLACE INTO users (username, password_hash, role) VALUES (?, ?, ?)", ("admin", admin_hash, "admin"))
    connection.commit()
    connection.close()

def calc_score(resume_text, role, experience):
    categories = JOB_REQUIREMENTS.get(role, {})
    if not categories: return {"total": 0, "details": {}}
    total_score = 0
    details = {}
    for cat_name, skills in categories.items():
        for skill, weight in skills.items():
            if skill.lower() in resume_text.lower():
                total_score += weight * 100
                details[f"{cat_name}: {skill}"] = round(weight * 100)
            else:
                details[f"{cat_name}: {skill}"] = 0
    if experience >= 5: exp_multiplier = 1.3
    elif experience >= 2: exp_multiplier = 1.1
    else: exp_multiplier = 1.0
    total_score = min(round(total_score * exp_multiplier), 100)
    return {"total": total_score, "details": details}

init_db()

if 'user_role' not in st.session_state:
    st.session_state.user_role = None

# ВСПЛЫВАЮЩЕЕ ОКНО (MODAL DIALOG) ДЛЯ ПРОСМОТРА ПРОФИЛЯ
@st.dialog("📋 Детальный ИИ-анализ кандидата")
def show_candidate_modal(row, res_details):
    st.write(f"### {row['name']}")
    st.write(f"**Вакансия:** {row['role']} | **Стаж:** {row['experience']} л.")
    st.write(f"**Текущий этап воронки:** {row['normalized_status']}")
    st.write("---")
    
    st.markdown("**Соответствие ключевым требованиям:**")
    for skill, val in res_details['details'].items():
        st.write(f"- {skill}: {val}%")
        st.progress(val / 100)
        
    st.write("---")
    st.markdown("**Полный текст резюме:**")
    st.info(row['content'])
    
    if st.button("Закрыть окно", use_container_width=True):
        st.rerun()

# 4. ЭКРАН АВТОРИЗАЦИИ
if st.session_state.user_role is None:
    # Заглушка-атмосферное фото для ресторанной сети на экране входа
    st.image("https://images.unsplash.com/photo-1555396273-367ea4eb4db5?auto=format&fit=crop&w=1200&q=80", use_container_width=True)
    
    st.markdown('<p class="main-title">🔐 Blackwood HR</p>', unsafe_allow_html=True)
    mode = st.radio("Режим работы:", ["Вход", "Регистрация сотрудников"], horizontal=True)
    
    user = st.text_input("Логин")
    pwd = st.text_input("Пароль", type="password")
    
    if mode == "Вход":
        if st.button("Войти в систему", use_container_width=True):
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
    else:
        key = st.text_input("Ключ доступа (Пароль Администратора)", type="password")
        role = st.selectbox("Назначаемая роль", ["manager", "recruiter"])
        if st.button("Зарегистрировать сотрудника", use_container_width=True):
            conn = sqlite3.connect('talent_hub.db')
            c = conn.cursor()
            c.execute("SELECT password_hash FROM users WHERE username='admin'")
            admin_data = c.fetchone()
            if admin_data and hash_password(key) == admin_data[0]:
                try:
                    c.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)", (user, hash_password(pwd), role))
                    conn.commit()
                    st.success("Сотрудник успешно добавлен!")
                except:
                    st.error("Этот логин занят!")
            else:
                st.error("Неверный ключ администратора!")
            conn.close()
    st.stop()

# 5. ОСНОВНОЙ ИНТЕРФЕЙС
# Изображение/Логотип в сайдбаре
st.sidebar.image("https://images.unsplash.com/photo-1453614512568-c4024d13c247?auto=format&fit=crop&w=300&q=80", caption="Blackwood Enterprise", use_container_width=True)
st.sidebar.write(f"Пользователь: **{st.session_state.user_role.upper()}**")
if st.sidebar.button("🚪 Выйти", use_container_width=True):
    st.session_state.user_role = None
    st.rerun()

st.markdown('<p class="main-title">💼 BLACKWOOD ENTERPRISE</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">AI Talent Hub & Мониторинг воронки</p>', unsafe_allow_html=True)

# МОДУЛЬ РЕКРУТЕРА
if st.session_state.user_role in ['admin', 'recruiter']:
    st.subheader("📥 Импорт новых соискателей")
    with st.form("resume_form"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("ФИО Кандидата", placeholder="Иванов Иван Иванович")
            role = st.selectbox("Профильная вакансия", VACANCIES_LIST)
        with col2:
            years = st.number_input("Подтвержденный стаж (лет)", min_value=0, max_value=40, value=0)
            text = st.text_area("Ключевые навыки / Текст резюме")
        if st.form_submit_button("🔥 Запустить ИИ-скрининг", use_container_width=True):
            if name and text:
                conn = sqlite3.connect('talent_hub.db')
                conn.execute("INSERT INTO resumes (name, role, content, status, experience) VALUES (?, ?, ?, ?, ?)", (name, role, text, 'Новый', years))
                conn.commit()
                conn.close()
                st.success("Кандидат добавлен!")
                st.rerun()

# МОДУЛЬ МЕНЕДЖЕРА
if st.session_state.user_role in ['admin', 'manager']:
    conn = sqlite3.connect('talent_hub.db')
    df = pd.read_sql("SELECT * FROM resumes", conn)
    conn.close()
    
    if not df.empty:
        scores = []
        for _, r in df.iterrows():
            res_analysis = calc_score(r['content'], r['role'], r['experience'])
            scores.append(res_analysis['total'])
        df['Score'] = scores
        
        tab_crm, tab_metrics, tab_offers = st.tabs(["🎯 CRM Воронка", "📈 Аналитика", "📄 Офферы"])
        allowed_statuses = ["Новый", "Собеседование", "Оффер", "Отказ"]
        
        with tab_crm:
            status_filter = st.selectbox("🎯 Фильтр этапа:", ["Все"] + allowed_statuses)
            df['normalized_status'] = df['status'].apply(lambda x: "Новый" if x == "new" else x)
            filtered_df = df if status_filter == "Все" else df[df['normalized_status'] == status_filter]
            
            for _, row in filtered_df.sort_values(by='Score', ascending=False).iterrows():
                res_details = calc_score(row['content'], row['role'], row['experience'])
                current_status = row['normalized_status']
                score_color = "🟢" if row['Score'] >= 70 else ("🟡" if row['Score'] >= 40 else "🔴")
                
                # Создаем красивый UI-блок для каждого кандидата
                with st.container():
                    col_img, col_main, col_btns = st.columns([1, 4, 2])
                    
                    with col_img:
                        # Подгружаем дефолтную заглушку аватара для солидности интерфейса
                        st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=70)
                        
                    with col_main:
                        st.markdown(f"#### {score_color} {row['name']}")
                        st.markdown(f"**Вакансия:** {row['role']} | **Рейтинг ИИ:** {row['Score']}% | **Стаж:** {row['experience']} л.")
                        
                    with col_btns:
                        # КНОПКА, ТРИГГЕРЯЩАЯ ВСПЛЫВАЮЩЕЕ ОКНО (DIALOG)
                        if st.button("👁️ Посмотреть профиль", key=f"view_{row['id']}", use_container_width=True):
                            show_candidate_modal(row, res_details)
                            
                        new_status = st.selectbox("Этап:", allowed_statuses, key=f"sel_{row['id']}", index=allowed_statuses.index(current_status))
                        if st.button("💾 Обновить статус", key=f"upd_{row['id']}", use_container_width=True):
                            conn = sqlite3.connect('talent_hub.db')
                            conn.execute("UPDATE resumes SET status=? WHERE id=?", (new_status, row['id']))
                            conn.commit()
                            conn.close()
                            st.rerun()
                st.markdown("---")
                
        with tab_metrics:
            col_m1, col_m2 = st.columns(2)
            col_m1.metric("Всего кандидатов", len(df))
            col_m2.metric("Сформировано офферов", len(df[df['normalized_status'] == "Оффер"]))
            st.bar_chart(df['Score'])
            
        with tab_offers:
            offer_candidates = df[df['normalized_status'] == "Оффер"]
            if not offer_candidates.empty:
                selected = st.selectbox("Выберите кандидата:", offer_candidates['name'])
                cand_row = df[df['name'] == selected].iloc[0]
                st.success("📄 О
