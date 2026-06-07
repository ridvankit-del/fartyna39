import streamlit as st
import sqlite3
import hashlib
import pandas as pd

# 1. КОНФИГУРАЦИЯ СТРАНИЦЫ
st.set_page_config(page_title="Blackwood Enterprise AI HR", layout="wide")

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

# 3. ФУНКЦИИ БЕЗОПАСНОСТИ И БД
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def init_db():
    connection = sqlite3.connect('talent_hub.db')
    cursor = connection.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password_hash TEXT, role TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS resumes 
                      (id INTEGER PRIMARY KEY, name TEXT, role TEXT, content TEXT, status TEXT, experience INTEGER)''')
    
    # Проверка и миграция структуры (добавление колонки experience, если её нет)
    try:
        cursor.execute("ALTER TABLE resumes ADD COLUMN experience INTEGER")
        connection.commit()
    except sqlite3.OperationalError:
        pass

    admin_password_hash = hash_password("admin123")
    cursor.execute("INSERT OR REPLACE INTO users (username, password_hash, role) VALUES (?, ?, ?)", ("admin", admin_password_hash, "admin"))
    connection.commit()
    connection.close()

def analyze_candidate_score(resume_text, role, experience):
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

# 4. СОСТОЯНИЕ СЕССИИ
if 'user_role' not in st.session_state:
    st.session_state.user_role = None

# 5. ЭКРАН АВТОРИЗАЦИИ
if st.session_state.user_role is None:
    st.title("🔐 Blackwood AI HR Enterprise")
    mode = st.radio("Режим работы:", ["Вход", "Регистрация сотрудников"], horizontal=True)
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
                st.error("Неверный логин или пароль")
            conn.close()
    else:
        key = st.text_input("Ключ доступа (Пароль Администратора)", type="password")
        role = st.selectbox("Назначаемая роль", ["manager", "recruiter"])
        if st.button("Зарегистрировать"):
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
st.sidebar.write(f"👤 Авторизован: **{st.session_state.user_role.upper()}**")
if st.sidebar.button("Выйти из системы"):
    st.session_state.user_role = None
    st.rerun()

st.title("💼 Система управления талантами Blackwood")

# МОДУЛЬ 1: Загрузка резюме (Рекрутер + Админ)
if st.session_state.user_role in ['admin', 'recruiter']:
    st.header("📥 Модуль импорта кандидатов")
    with st.form("resume_form"):
        name = st.text_input("ФИО Кандидата")
        role = st.selectbox("Профильная вакансия", list(JOB_REQUIREMENTS.keys()))
        years = st.number_input("Подтвержденный стаж (лет)", min_value=0, max_value=40, value=0)
        text = st.text_area("Текстовое содержимое резюме / Ключевые навыки")
        if st.form_submit_button("Загрузить и запустить ИИ-анализ"):
            if name and text:
                conn = sqlite3.connect('talent_hub.db')
                c = conn.cursor()
                c.execute("INSERT INTO resumes (name, role, content, status, experience) VALUES (?, ?, ?, ?, ?)", 
                          (name, role, text, 'Новый', years))
                conn.commit()
                conn.close()
                st.success(f"Кандидат {name} успешно добавлен в воронку со статусом 'Новый'!")
            else:
                st.error("Пожалуйста, заполните все поля формы.")

# МОДУЛЬ 2: Коммерческая аналитика и CRM (Менеджер + Админ)
if st.session_state.user_role in ['admin', 'manager']:
    st.header("📊 Коммерческий аналитический центр")
    
    conn = sqlite3.connect('talent_hub.db')
    df = pd.read_sql("SELECT * FROM resumes", conn)
    conn.close()
    
    if not df.empty:
        # Считаем скоринг для всех кандидатов в фоне
        df['Score'] = df.apply(lambda x: analyze_candidate_score(x['content'], x['role'], x['experience'])['total'], axis=1)
        
        # Разделение интерфейса на вкладки
        tab_crm, tab_metrics, tab_offers = st.tabs(["🎯 Воронка кандидатов (CRM)", "📈 Бизнес-метрики", "📄 Генератор офферов"])
        
        # ВКЛАДКА 1: Профессиональная воронка
        with tab_crm:
            st.subheader("Управление статусами соискателей")
            status_filter = st.selectbox("Фильтр по этапу воронки", ["Все", "Новый", "Собеседование", "Оффер", "Отказ"])
            
            filtered_df = df if status_filter == "Все" else df[df['status'] == status_filter]
            
            for _, row in filtered_df.sort_values(by='Score', ascending=False).iterrows():
                res_details = analyze_candidate_score(row['content'], row['role'], row['experience'])
                
                with st.expander(f"[{row['status']}] {row['name']} — Соответствие: {row['Score']}% (Стаж: {row['experience']} л.)"):
                    col_info, col_actions = st.columns([2, 1])
                    
                    with col_info:
                        st.write(f"**Резюме:** {row['content']}")
                        st.write("**Разбивка по компетенциям:**")
                        for skill, val in res_details['details'].items():
                            st.write(f"- {skill}: {val}%")
                            st.progress(val / 100)
                    
                    with col_actions:
                        st.write("**Управление этапом:**")
                        new_status = st.selectbox("Изменить статус на:", ["Новый", "Собеседование", "Оффер", "Отказ"], key=f"status_select_{row['id']}", index=["Новый", "Собеседование", "Оффер", "Отказ"].index(row['status']))
                        
                        if st.button("Обновить статус", key=f"status_btn_{row['id']}"):
                            conn = sqlite3.connect('talent_hub.db')
                            c = conn.cursor()
                            c.execute("UPDATE resumes SET status=? WHERE id=?", (new_status, row['id']))
                            conn.commit()
                            conn.close()
                            st.success("Статус обновлен!")
                            st.rerun()
                            
                        if st.button("🗑️ Удалить соискателя", key=f"del_{row['id']}"):
                            conn = sqlite3.connect('talent_hub.db')
                            conn.execute("DELETE FROM resumes WHERE id=?", (row['id'],))
                            conn.commit()
                            conn.close()
                            st.success("Удалено")
                            st.rerun()
        
        # ВКЛАДКА 2: Финансовые метрики для бизнеса
        with tab_metrics:
            st.subheader("Эффективность рекрутинга")
            col_m1, col_m2, col_m3 = st.columns(3)
            
            total_candidates = len(df)
            offers_count = len(df[df['status'] == "Оффер"])
            conversion = round((offers_count / total_candidates) * 100) if total_candidates > 0 else 0
            estimated_cost = total_candidates * 1200 
            
            col_m1.metric("Всего обработано резюме", total_candidates)
            col_m2.metric("Конверсия воронки в офферы", f"{conversion}%")
            col_m3.metric("Инвестиции в подбор (угар.)", f"{estimated_cost} ₽", "-12% расходов")
            
            st.write("### Распределение кандидатов по уровню соответствия")
            st.bar_chart(df['Score'])
            
        # ВКЛАДКА 3: Генератор предложений о работе (Job Offers)
        with tab_offers:
            st.subheader("Автоматическое составление Job Offer")
            offer_candidates = df[df['status'] == "Оффер"]
            
            if not offer_candidates.empty:
                selected_candidate = st.selectbox("Выберите кандидата для формирования оффера:", offer_candidates['name'])
                cand_row = df[df['name'] == selected_candidate].iloc[0]
                
                offer_text = f"""
👋 Уважаемый(а) {cand_row['name']}!
                
Команда ресторанной сети Blackwood Enterprise рада пригласить Вас на должность: **{cand_row['role']}**.
                
Наш ИИ-ассистент высоко оценил Ваш опыт работы ({cand_row['experience']} л.) и навыки. 
Мы предлагаем Вам конкурентные условия труда, официальное оформление и гибкий график.
                
Ожидаем Вашего ответа в течение 3 рабочих дней.
С уважением, HR-департамент Blackwood.
                """
                st.info("Текст оффера сгенерирован автоматически:")
                st.code(offer_text, language="markdown")
            else:
                st.info("Чтобы сгенерировать оффер, переведите хотя бы одного кандидата в статус 'Оффер' во вкладке CRM.")
                
    else:
        st.info("В коммерческой базе данных пока нет загруженных анкет соискателей.")
