import streamlit as st
import sqlite3
import hashlib
import pandas as pd

# 1. КОНФИГУРАЦИЯ СТРАНИЦЫ И КАСТОМНЫЙ ДИЗАЙН (CSS)
st.set_page_config(page_title="Blackwood Enterprise AI HR", layout="wide")

# Внедряем фирменные стили Blackwood (тёмный премиальный акцент, скругления, тени)
st.markdown("""
    <style>
        /* Главный заголовок */
        .main-title {
            font-size: 42px !important;
            font-weight: 800 !important;
            color: #1E1E1E;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            margin-bottom: 5px;
        }
        .subtitle {
            font-size: 18px !important;
            color: #666666;
            margin-bottom: 30px;
        }
        /* Карточки метрик */
        div[data-testid="stMetricSimpleValue"] {
            font-size: 28px !important;
            font-weight: 700 !important;
            color: #111111;
        }
        /* Брендированные контейнеры */
        .custom-card {
            background-color: #F9F9FB;
            padding: 20px;
            border-radius: 12px;
            border-left: 5px solid #1E1E1E;
            box-shadow: 0 4px 6px rgba(0,0,0,0.02);
            margin-bottom: 15px;
        }
    </style>
""", unsafe_allow_html=True)

# 2. РАСШИРЕННАЯ МАТРИЦА КОМПЕТЕНЦИЙ (HH-STYLE)
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

# 3. ФУНКЦИИ БЕЗОПАСНОСТИ И БД
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

    admin_password_hash = hash_password("admin123")
    cursor.execute("INSERT OR REPLACE INTO users (username, password_hash, role) VALUES (?, ?, ?)", ("admin", admin_password_hash, "admin"))
    connection.commit()
    connection.close()

def calc_score(resume_text, role, experience):
    categories = JOB_REQUIREMENTS.get(role, {})
    if not categories:
        return {"total": 0, "details": {}}
    
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

# 4. СОСТОЯНИЕ СЕССИИ (Укоротили проверку, чтобы избежать обрывов строк)
if 'user_role' not in st.session_state:
    st.session_state.user_role = None

# 5. ЭКРАН АВТОРИЗАЦИИ
if st.session_state.user_role is None:
    st.markdown('<p class="main-title">🔐 Blackwood HR</p>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Вход в корпоративную панель управления талантами</p>', unsafe_allow_html=True)
    
    mode = st.radio("Режим работы:", ["Вход", "Регистрация сотрудников"], horizontal=True)
    
    with st.container():
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
                        st.success("Сотрудник успешно добавлен в систему!")
                    except:
                        st.error("Этот логин занят!")
                else:
                    st.error("Неверный ключ администратора!")
                conn.close()
    st.stop()

# 6. ОСНОВНОЙ БИЗНЕС-ИНТЕРФЕЙС
st.sidebar.markdown("### 🏢 Панель управления")
st.sidebar.write(f"Пользователь: **{st.session_state.user_role.upper()}**")
if st.sidebar.button("🚪 Выйти из системы", use_container_width=True):
    st.session_state.user_role = None
    st.rerun()

st.markdown('<p class="main-title">💼 BLACKWOOD ENTERPRISE</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">AI Talent Hub & Кадровое планирование</p>', unsafe_allow_html=True)
st.write("---")

# МОДУЛЬ 1: Загрузка резюме (Рекрутер + Админ)
if st.session_state.user_role in ['admin', 'recruiter']:
    st.subheader("📥 Импорт новых соискателей")
    with st.form("resume_form"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("ФИО Кандидата", placeholder="Иванов Иван Иванович")
            role = st.selectbox("Профильная вакансия", VACANCIES_LIST)
        with col2:
            years = st.number_input("Подтвержденный стаж (лет)", min_value=0, max_value=40, value=0)
            text = st.text_area("Ключевые навыки / Текст резюме", placeholder="Перечислите навыки через запятую или вставьте текст...")
            
        if st.form_submit_button("🔥 Запустить ИИ-скрининг и добавить в воронку", use_container_width=True):
            if name and text:
                conn = sqlite3.connect('talent_hub.db')
                c = conn.cursor()
                c.execute("INSERT INTO resumes (name, role, content, status, experience) VALUES (?, ?, ?, ?, ?)", 
                          (name, role, text, 'Новый', years))
                conn.commit()
                conn.close()
                st.success(f"Кандидат {name} успешно добавлен!")
                st.rerun()
            else:
                st.error("Пожалуйста, заполните все поля формы.")
    st.write("---")

# МОДУЛЬ 2: Коммерческая аналитика и CRM (Менеджер + Админ)
if st.session_state.user_role in ['admin', 'manager']:
    st.subheader("📊 Аналитический центр и CRM")
    
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
        
        # ВКЛАДКА 1: CRM Воронка
        with tab_crm:
            col_f1, col_f2 = st.columns([1, 2])
            with col_f1:
                status_filter = st.selectbox("🎯 Фильтр этапа:", ["Все"] + allowed_statuses)
            
            df['normalized_status'] = df['status'].apply(lambda x: "Новый" if x == "new" else x)
            filtered_df = df if status_filter == "Все" else df[df['normalized_status'] == status_filter]
            
            st.write("") 
            
            for _, row in filtered_df.sort_values(by='Score', ascending=False).iterrows():
                res_details = calc_score(row['content'], row['role'], row['experience'])
                current_status = row['normalized_status']
                score_color = "🟢" if row['Score'] >= 70 else ("🟡" if row['Score'] >= 40 else "🔴")
                
                with st.expander(f"{score_color} {row['name']} | Вакансия: {row['role']} (ИИ-Матчинг: {row['Score']}%)"):
                    st.markdown(f"""
                    <div class="custom-card">
                        <h4>Профиль соискателя</h4>
                        <p><b>Опыт работы:</b> {row['experience']} л. | <b>Текущий статус:</b> {current_status}</p>
                        <p><b>Текст резюме:</b> {row['content']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    col_info, col_actions = st.columns([2, 1])
                    with col_info:
                        st.markdown("**Метрики соответствия hard-skills:**")
                        for skill, val in res_details['details'].items():
                            st.write(f"- {skill}: {val}%")
                            st.progress(val / 100)
                    
                    with col_actions:
                        st.markdown("**Действия:**")
                        new_status = st.selectbox(
                            "Изменить этап на:", 
                            allowed_statuses, 
                            key=f"status_select_{row['id']}_{row['name']}", 
                            index=allowed_statuses.index(current_status)
                        )
                        
                        if st.button("💾 Сохранить статус", key=f"status_btn_{row['id']}_{row['name']}", use_container_width=True):
                            conn = sqlite3.connect('talent_hub.db')
                            c = conn.cursor()
                            c.execute("UPDATE resumes SET status=? WHERE id=?", (new_status, row['id']))
                            conn.commit()
                            conn.close()
                            st.success("Обновлено!")
                            st.rerun()
                            
                        if st.button("🗑️ Удалить анкету", key=f"del_{row['id']}_{row['name']}", use_container_width=True):
                            conn = sqlite3.connect('talent_hub.db')
                            conn.execute("DELETE FROM resumes WHERE id=?", (row['id'],))
                            conn.commit()
                            conn.close()
                            st.rerun()
        
        # ВКЛАДКА 2: Аналитика
        with tab_metrics:
            st.write("")
            col_m1, col_m2, col_m3 = st.columns(3)
            
            total_candidates = len(df)
            offers_count = len(df[df['normalized_status'] == "Оффер"])
            conversion = round((offers_count / total_candidates) * 100) if total_candidates > 0 else 0
            estimated_cost = total_candidates * 1200 
            
            with col_m1:
                st.metric("Обработано анкет", f"{total_candidates} чел.", "База данных")
            with col_m2:
                st.metric("Конверсия в офферы", f"{conversion}%", "Успешный подбор")
            with col_m3:
                st.metric("Бюджет на HR (угар.)", f"{estimated_cost} ₽", "-12% расходов")
            
            st.write("---")
            st.markdown("### 📊 Распределение ИИ-рейтинга соискателей")
            st.bar_chart(df['Score'])
            
        # ВКЛАДКА 3: Офферы
        with tab_offers:
            st.write("")
            offer_candidates = df[df['normalized_status'] == "Оффер"]
            
            if not offer_candidates.empty:
                selected_candidate = st.selectbox("Выберите одобренного кандидата:", offer_candidates['name'])
                cand_row = df[df['name'] == selected_candidate].iloc[0]
                
                offer_text = f"""
👋 Уважаемый(а) {cand_row['name']}!
                
Команда ресторанной сети Blackwood Enterprise рада пригласить Вас на должность: **{cand_row['role']}**.
                
Наш ИИ-ассистент высоко оценил Ваш опыт работы ({cand_row['experience']} л.) и ключевые навыки. 
Мы предлагаем Вам конкурентные условия труда, официальное оформление и гибкий график.
                
Ожидаем Вашего ответа в течение 3 рабочих дней.
С уважением, HR-департамент Blackwood.
                """
                st.success("✨ Фирменный оффер успешно сформирован:")
                st.code(offer_text, language="markdown")
            else:
                st.info("Чтобы сгенерировать оффер, переведите хотя бы одного кандидата в статус 'Оффер' во вкладке CRM.")
                
    else:
        st.info("В коммерческой базе данных пока нет загруженных анкет соискателей.")
