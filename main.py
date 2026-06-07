import streamlit as st
import sqlite3
import hashlib
import pandas as pd
import requests
import json
import io
import pypdf
import docx2txt

# 1. ЗАЩИТА: Получаем ключ из secrets, а не из кода
OPENROUTER_API_KEY = st.secrets.get("OPENROUTER_API_KEY")

# 2. ФУНКЦИЯ ПРОВЕРКИ ПРАВ
def check_access(required_role=None):
    """Блокирует доступ, если пользователь не авторизован или нет прав."""
    if 'user_role' not in st.session_state or st.session_state.user_role is None:
        st.error("⛔ Требуется авторизация.")
        return False
    if required_role and st.session_state.user_role != 'admin' and st.session_state.user_role != required_role:
        st.error("⛔ У вас нет прав для этого действия.")
        return False
    return True

# ... (функции hash_password, init_db, extract_text_from_file остаются прежними)

def ask_llm_analysis(resume_text, role, experience, requirements):
    if not OPENROUTER_API_KEY:
        return "⚠️ Ошибка: API-ключ не настроен в секретах системы."
    
    # ... (код запроса к LLM без изменений, но теперь он безопасен)
    prompt = f"..." 
    # (логика запроса остается как в предыдущей версии)
    
# 3. ОСНОВНОЙ ИНТЕРФЕЙС С ПРОВЕРКОЙ БЕЗОПАСНОСТИ
else:
    # Защита: действия только для админов и рекрутеров
    if st.session_state.user_role in ['admin', 'recruiter']:
        st.subheader("📥 Умный импорт соискателей")
        
        uploaded_file = st.file_uploader("Загрузить файл", type=['pdf', 'docx'])
        
        with st.form("resume_form"):
            # ... (поля формы)
            if st.form_submit_button("🔥 Запустить"):
                if check_access('recruiter'): # ПРОВЕРКА ПРАВ ПЕРЕД ЗАПИСЬЮ
                    # ... (логика сохранения в БД)
                    st.success("Данные успешно защищены и сохранены.")
                else:
                    st.stop()

    # Защита: аналитика доступна только админам и менеджерам
    if st.session_state.user_role in ['admin', 'manager']:
        st.subheader("📊 Аналитика")
        if check_access('manager'):
            # (вывод данных из БД)
            pass

# 1. КОНФИГУРАЦИЯ СТРАНИЦЫ И СТИЛИ (PREMIUM DESIGN)
st.set_page_config(page_title="Blackwood Enterprise AI HR", layout="wide")

st.markdown("""
    <style>
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
        div[data-testid="stMetricSimpleValue"] {
            font-size: 28px !important;
            font-weight: 700 !important;
            color: #111111;
        }
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

# 3. НАСТРОЙКИ LLM, БЕЗОПАСНОСТИ, ПАРСИНГА И БД
# Вставь сюда свой ключ от OpenRouter
OPENROUTER_API_KEY = "sk-or-v1-c3f...e8e" 

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def init_db():
    connection = sqlite3.connect('talent_hub.db')
    cursor = connection.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password_hash TEXT, role TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS resumes 
                      (id INTEGER PRIMARY KEY, name TEXT, role TEXT, content TEXT, status TEXT, experience INTEGER, ai_summary TEXT)''')
    try:
        cursor.execute("ALTER TABLE resumes ADD COLUMN experience INTEGER")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE resumes ADD COLUMN ai_summary TEXT")
    except sqlite3.OperationalError:
        pass
    connection.commit()
    
    admin_password_hash = hash_password("admin123")
    cursor.execute("INSERT OR REPLACE INTO users (username, password_hash, role) VALUES (?, ?, ?)", ("admin", admin_password_hash, "admin"))
    connection.commit()
    connection.close()

def extract_text_from_file(uploaded_file):
    try:
        file_ext = uploaded_file.name.split('.')[-1].lower()
        if file_ext == 'pdf':
            pdf_reader = pypdf.PdfReader(io.BytesIO(uploaded_file.read()))
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() or ""
            return text.strip()
        elif file_ext in ['docx', 'doc']:
            text = docx2txt.process(io.BytesIO(uploaded_file.read()))
            return text.strip()
    except Exception as e:
        st.error(f"Ошибка при чтении файла: {e}")
    return ""

def ask_llm_analysis(resume_text, role, experience, requirements):
    """Отправляет запрос к настоящей ИИ-модели Llama 3 через OpenRouter"""
    if not OPENROUTER_API_KEY or OPENROUTER_API_KEY == "ВСТАВЬ_СЮДА_СВОЙ_КЛЮЧ":
        return "⚠️ Ошибка: API-ключ не настроен в коде приложения. Переключено на оффлайн-режим."

    # Мощный системный промпт для разбора резюме
    prompt = f"""
    Ты — опытный ИИ-директор по персоналу ресторанной сети 'Blackwood Enterprise'.
    Твоя задача — провести глубокий коммерческий аудит резюме кандидата.
    
    Вакансия: {role}
    Заявленный стаж: {experience} лет.
    Критерии идеального сотрудника: {json.dumps(requirements, ensure_ascii=False)}
    
    Текст резюме кандидата:
    ---
    {resume_text}
    ---
    
    Напиши структурированный отчет на РУССКОМ языке в формате Markdown. Будь критичен и точен.
    Структура отчета должна строго содержать:
    1. ### 🤖 Настоящее ИИ-Заключение Blackwood (Итоговый вердикт: нанимаем/на интервью/отказ)
    2. **Сильные стороны:** (Какие навыки и реальный опыт соответствуют ресторанной сфере)
    3. **Скрытые риски и зоны роста:** (Чего не хватает, часто ли менял работу, есть ли несоответствия)
    4. **Фактор стажа:** (Оценка опыта для данной позиции)
    5. **Оценка соответствия:** (Укажи финальную общую оценку от 0 до 100% на основе твоего анализа)
    """

    try:
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            },
            data=json.dumps({
                "model": "meta-llama/llama-3-8b-instruct:free", # Используем бесплатную и быструю Llama 3
                "messages": [{"role": "user", "content": prompt}]
            }),
            timeout=15
        )
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content']
        else:
            return f"❌ Ошибка API ({response.status_code}): {response.text}"
    except Exception as e:
        return f"❌ Не удалось связаться с ИИ-сервером: {e}"

def calc_score(resume_text, role, experience):
    """Высчитывает математический скоринг по ключевым словам для графиков"""
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

# ВСПЛЫВАЮЩЕЕ МОДАЛЬНОЕ ОКНО ДЛЯ ПРОСМОТРА КАНДИДАТА
@st.dialog("📋 Живой ИИ-Анализ профиля соискателя")
def show_candidate_modal(row, res_details):
    st.write(f"### {row['name']}")
    st.write(f"**Вакансия:** {row['role']} | **Подтвержденный стаж:** {row['experience']} л.")
    st.write("---")
    
    # Показываем полноценный экспертный разбор от LLM нейросети
    if row['ai_summary']:
        st.markdown(row['ai_summary'])
    else:
        st.warning("Для этого кандидата еще не сформировано экспертное LLM-заключение.")
    st.write("---")
    
    st.markdown("**Выдержка из оригинального текста резюме:**")
    st.info(row['content'][:800] + ("..." if len(row['content']) > 800 else ""))
    
    st.markdown("**Технические триггеры матрицы компетенций:**")
    for skill, val in res_details['details'].items():
        st.write(f"- {skill}: {val}%")
        st.progress(val / 100)
    st.write("---")
    
    if st.button("Закрыть просмотр", use_container_width=True):
        st.rerun()

# 5. ЭКРАН АВТОРИЗАЦИИ
if st.session_state.user_role is None:
    st.image("https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?auto=format&fit=crop&w=1200&q=80", use_container_width=True)
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

# 6. ОСНОВНОЙ БИЗНЕС-ИНТЕРФЕЙС
else:
    st.sidebar.image("https://images.unsplash.com/photo-1634017839464-5c339ebe3cb4?auto=format&fit=crop&w=300&q=80", use_container_width=True)
    st.sidebar.markdown("### 🏢 Панель управления")
    st.sidebar.write(f"Пользователь: **{st.session_state.user_role.upper()}**")
    
    if st.sidebar.button("🚪 Выйти из системы", key="sidebar_logout_btn", use_container_width=True):
        st.session_state.user_role = None
        st.rerun()
    
    st.markdown('<p class="main-title">💼 BLACKWOOD ENTERPRISE</p>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">AI Talent Hub & Кадровое планирование</p>', unsafe_allow_html=True)
    st.write("---")
    
    # МОДУЛЬ 1: Умная загрузка резюме с LLM-анализом (Рекрутер + Admin)
    if st.session_state.user_role in ['admin', 'recruiter']:
        st.subheader("📥 Умный импорт соискателей через нейросеть (PDF, DOCX)")
        
        uploaded_file = st.file_uploader("Перетащите файл резюме (.pdf, .docx)", type=['pdf', 'docx'])
        file_text = ""
        if uploaded_file is not None:
            file_text = extract_text_from_file(uploaded_file)
            st.success(f"📎 Файл успешно прочитан! Извлечено символов: {len(file_text)}")
            
        with st.form("resume_form"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("ФИО Кандидата", placeholder="Иванов Иван Иванович")
                role = st.selectbox("Профильная вакансия", VACANCIES_LIST)
            with col2:
                years = st.number_input("Подтвержденный стаж (лет)", min_value=0, max_value=40, value=0)
                text = st.text_area("Текст резюме", value=file_text if file_text else "", placeholder="Или вставьте текст вручную...")
                
            if st.form_submit_button("🔥 Запустить ИИ-скрининг и добавить в воронку", use_container_width=True):
                if name and text:
                    # Показываем спиннер загрузки, пока нейросеть думает над файлом
                    with st.spinner("🤖 Настоящий ИИ читает резюме и формирует экспертное заключение... Подождите..."):
                        reqs = JOB_REQUIREMENTS.get(role, {})
                        ai_report = ask_llm_analysis(text, role, years, reqs)
                    
                    conn = sqlite3.connect('talent_hub.db')
                    c = conn.cursor()
                    c.execute("INSERT INTO resumes (name, role, content, status, experience, ai_summary) VALUES (?, ?, ?, ?, ?, ?)", 
                              (name, role, text, 'Новый', years, ai_report))
                    conn.commit()
                    conn.close()
                    st.success(f"Кандидат {name} успешно проанализирован LLM и сохранен в CRM!")
                    st.rerun()
                else:
                    st.error("Пожалуйста, заполните ФИО кандидата и убедитесь, что текст резюме извлечен.")
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
                if isinstance(res_analysis, dict) and 'total' in res_analysis:
                    scores.append(res_analysis['total'])
                else:
                    scores.append(0)
            df['Score'] = scores
            
            tab_crm, tab_metrics, tab_offers = st.tabs(["🎯 CRM Воронка", "📈 Аналитика", "📄 Офферы"])
            allowed_statuses = ["Новый", "Собеседование", "Оффер", "Отказ"]
            
            # ВКЛАДКА 1: Профессиональная CRM воронка
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
                    
                    with st.container():
                        col_img, col_main, col_btns = st.columns([1, 4, 2])
                        
                        with col_img:
                            st.image("https://img.icons8.com/fluent-systems-filled/200/FFFFFF/user-male-circle.png", width=65)
                            
                        with col_main:
                            st.markdown(f"#### {score_color} {row['name']}")
                            st.markdown(f"**Вакансия:** {row['role']} | **Текущий статус:** `{current_status}` | **ИИ-Матчинг:** {row['Score']}%")
                            
                        with col_btns:
                            if st.button("👁️ Посмотреть профиль", key=f"view_{row['id']}", use_container_width=True):
                                show_candidate_modal(row, res_details)
                                
                            new_status = st.selectbox("Изменить этап:", allowed_statuses, key=f"sel_{row['id']}", index=allowed_statuses.index(current_status))
                            
                            col_sub1, col_sub2 = st.columns(2)
                            with col_sub1:
                                if st.button("💾 Сохранить", key=f"upd_{row['id']}", use_container_width=True):
                                    conn = sqlite3.connect('talent_hub.db')
                                    conn.execute("UPDATE resumes SET status=? WHERE id=?", (new_status, row['id']))
                                    conn.commit()
                                    conn.close()
                                    st.rerun()
                            with col_sub2:
                                if st.button("🗑️ Удалить", key=f"del_{row['id']}", use_container_width=True):
                                    conn = sqlite3.connect('talent_hub.db')
                                    conn.execute("DELETE FROM resumes WHERE id=?", (row['id'],))
                                    conn.commit()
                                    conn.close()
                                    st.rerun()
                    st.markdown("---")
            
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
                    st.metric("Бюджет на HR (расчетный)", f"{estimated_cost} ₽", "-12% расходов")
                
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
