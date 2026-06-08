import streamlit as st
import sqlite3
import hashlib
import pandas as pd
import pypdf
import docx2txt
import io
import requests
import json
import re

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

# 2. РАСШИРЕННАЯ МАТРИЦА КОМПЕТЕНЦИЙ (HARD + SOFT)
JOB_REQUIREMENTS = {
    "Повар": {
        "Hard Skills": ["Технологические карты", "Санитарные нормы (СанПиН)", "Работа с хоспером и грилем"],
        "Soft Skills": ["Чистоплотность", "Выносливость", "Дисциплина"]
    },
    "Шеф-повар": {
        "Hard Skills": ["Контроль Foodcost", "Инвентаризация", "Разработка меню"],
        "Soft Skills": ["Лидерство", "Управление командой", "Стрессоустойчивость"]
    },
    "Официант": {
        "Hard Skills": ["Знание стандартов сервиса", "Работа с R-Keeper / iiko", "Техники Upsell продаж"],
        "Soft Skills": ["Коммуникабельность", "Дружелюбие", "Грамотная речь"]
    }
}

VACANCIES_LIST = list(JOB_REQUIREMENTS.keys())

# 3. НАСТРОЙКИ БЕЗОПАСНОСТИ, ПАРСИНГА И БД
OPENROUTER_API_KEY = st.secrets.get("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")

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def init_db():
    connection = sqlite3.connect('talent_hub.db')
    cursor = connection.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password_hash TEXT, role TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS resumes 
                      (id INTEGER PRIMARY KEY, name TEXT, role TEXT, content TEXT, status TEXT, experience INTEGER, 
                       ai_summary TEXT, ai_score INTEGER, ai_skills_json TEXT)''')
    
    # Плавная миграция базы данных под новые колонки умного ИИ-скоринга
    try: cursor.execute("ALTER TABLE resumes ADD COLUMN experience INTEGER")
    except sqlite3.OperationalError: pass
    try: cursor.execute("ALTER TABLE resumes ADD COLUMN ai_summary TEXT")
    except sqlite3.OperationalError: pass
    try: cursor.execute("ALTER TABLE resumes ADD COLUMN ai_score INTEGER DEFAULT 0")
    except sqlite3.OperationalError: pass
    try: cursor.execute("ALTER TABLE resumes ADD COLUMN ai_skills_json TEXT")
    except sqlite3.OperationalError: pass
    
    connection.commit()
    admin_password_hash = hash_password("9391291")
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

def ask_llm_semantic_analysis(resume_text, role, experience, requirements):
    """Отправляет запрос к Llama 3 для глубокого контекстного анализа и семантического скоринга"""
    if not OPENROUTER_API_KEY:
        return "⚠️ Ошибка: API-ключ не настроен.", 0, "{}"

    # Собираем плоский список навыков, которые ИИ должен оценить в JSON
    all_skills = requirements.get("Hard Skills", []) + requirements.get("Soft Skills", [])
    skills_structure = {skill: 0 for skill in all_skills}

    prompt = f"""
    Ты — опытный ИИ-директор по персоналу ресторанной сети 'Blackwood Enterprise'.
    Твоя задача — провести глубокий смысловой аудит резюме. Не цепляйся за точные слова. Если кандидат описал навык синонимами, своими словами, или с опечатками (например, "камуникабельныф" или "чистоплота") — пойми контекст и зачти это.
    
    Вакансия: {role}
    Заявленный стаж: {experience} лет.
    Критерии идеального сотрудника:
    - Hard Skills: {json.dumps(requirements.get("Hard Skills", []), ensure_ascii=False)}
    - Soft Skills: {json.dumps(requirements.get("Soft Skills", []), ensure_ascii=False)}
    
    Текст резюме кандидата:
    ---
    {resume_text}
    ---
    
    Напиши структурированный отчет на РУССКОМ языке в формате Markdown.
    Структура отчета должна строго содержать:
    1. ### 🤖 Настоящее ИИ-Заключение Blackwood (Итоговый вердикт: нанимаем/на интервью/отказ)
    2. **Сильные стороны:** (Какие навыки и реальный опыт соответствуют ресторанной сфере)
    3. **Скрытые риски и зоны роста:** (Чего не хватает, часто ли менял работу, есть ли несоответствия)
    4. **Фактор стажа:** (Оценка опыта для данной позиции)
    
    В САМОМ КОНЦЕ ОТВЕТА, строго на новой строке, выведи технический блок с оценками в формате JSON внутри тегов [DATA]...[/DATA].
    Оцени каждый навык из списка от 0 до 100 на основе контекста резюме. Высчитай общий средний рейтинг (score) от 0 до 100.
    Шаблон технического блока:
    [DATA]
    {{
      "score": 85,
      "details": {json.dumps(skills_structure, ensure_ascii=False)}
    }}
    [/DATA]
    Ничего кроме JSON внутри тегов [DATA] быть не должно. Навыки в "details" должны строго совпадать с переданным списком.
    """

    try:
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            },
            data=json.dumps({
                "model": "meta-llama/llama-3-8b-instruct:free",
                "messages": [{"role": "user", "content": prompt}]
            }),
            timeout=15
        )
        if response.status_code == 200:
            raw_content = response.json()['choices'][0]['message']['content']
            
            # Извлекаем JSON-данные скоринга из тегов [DATA]
            ai_report = raw_content
            ai_score = 0
            ai_skills_json = "{}"
            
            if "[DATA]" in raw_content and "[/DATA]" in raw_content:
                try:
                    parts = raw_content.split("[DATA]")
                    ai_report = parts[0].strip()
                    json_str = parts[1].split("[/DATA]")[0].strip()
                    
                    data_parsed = json.loads(json_str)
                    ai_score = int(data_parsed.get("score", 0))
                    ai_skills_json = json.dumps(data_parsed.get("details", {}), ensure_ascii=False)
                except Exception as je:
                    st.warning(f"Отрендерен текстовый отчет, но произошел сбой разбора метрик: {je}")
            
            return ai_report, ai_score, ai_skills_json
        else:
            return f"❌ Ошибка API ({response.status_code}): {response.text}", 0, "{}"
    except Exception as e:
        return f"❌ Не удалось связаться с ИИ-сервером: {e}", 0, "{}"

init_db()

# 4. СОСТОЯНИЕ СЕССИИ
if 'user_role' not in st.session_state:
    st.session_state.user_role = None

# МОДАЛЬНОЕ ОКНО ПРОСМОТРА КАНДИДАТА
@st.dialog("📋 Контекстный ИИ-Анализ соискателя")
def show_candidate_modal(row):
    st.write(f"### {row['name']}")
    st.write(f"**Вакансия:** {row['role']} | **Стаж:** {row['experience']} л.")
    st.write("---")
    
    if row['ai_summary']:
        st.markdown(row['ai_summary'])
    else:
        st.warning("Для этого кандидата еще не сформировано экспертное LLM-заключение.")
    st.write("---")
    
    st.markdown("**Выдержка из оригинального текста резюме:**")
    st.info(row['content'][:600] + ("..." if len(row['content']) > 600 else ""))
    
    # Выводим семантические метрики, которые посчитал ИИ
    st.markdown("**📊 Семантический анализ соответствия требованиям:**")
    if row['ai_skills_json']:
        try:
            skills_data = json.loads(row['ai_skills_json'])
            if skills_data:
                for skill, val in skills_data.items():
                    st.write(f"- {skill}: **{val}%**")
                    st.progress(int(val) / 100)
            else:
                st.info("Нет детальных метрик по навыкам.")
        except:
            st.error("Ошибка чтения сохраненной матрицы компетенций.")
    else:
        st.info("Кандидат был загружен в старой версии системы без поддержки глубокого скоринга.")
    st.write("---")
    
    if st.button("Закрыть просмотр", use_container_width=True):
        st.rerun()

# 6. ОСНОВНОЙ БИЗНЕС-ИНТЕРФЕЙС
else:
    st.sidebar.image("https://images.unsplash.com/photo-1634017839464-5c339ebe3cb4?auto=format&fit=crop&w=300&q=80", use_container_width=True)
    st.sidebar.markdown("### 🏢 Панель управления")
    st.sidebar.write(f"Пользователь: **{st.session_state.user_role.upper()}**")
    
    # --- НАЧАЛО БЛОКА ОТЛАДКИ КЛЮЧА ---
    st.sidebar.markdown("---")
    user_key_input = st.sidebar.text_input(
        "🔑 Проверка API Ключа (при 401 ошибке)", 
        type="password", 
        placeholder="Вставьте sk-or-v1-...",
        help="Если здесь пусто, система берет ключ из Secrets. Если вставить сюда — этот ключ заменит секреты."
    )
    # Если юзер ввел ключ руками — берем его, иначе берем из st.secrets
    if user_key_input:
        OPENROUTER_API_KEY = user_key_input
    else:
        OPENROUTER_API_KEY = st.secrets.get("OPENROUTER_API_KEY")
    st.sidebar.markdown("---")
    # --- КОНЕЦ БЛОКА ОТЛАДКИ КЛЮЧА ---
    
    if st.sidebar.button("🚪 Выйти из системы", key="sidebar_logout_btn", use_container_width=True):
        st.session_state.user_role = None
        st.rerun()
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
    st.markdown('<p class="subtitle">AI Talent Hub & Контекстный Смысловой Анализ</p>', unsafe_allow_html=True)
    st.write("---")
    
    # МОДУЛЬ 1: Умная загрузка резюме с семантическим ИИ-анализом
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
                    with st.spinner("🤖 ИИ проводит смысловой аудит, сопоставляет синонимы и опечатки..."):
                        reqs = JOB_REQUIREMENTS.get(role, {})
                        ai_report, ai_score, ai_skills_json = ask_llm_semantic_analysis(text, role, years, reqs)
                    
                    conn = sqlite3.connect('talent_hub.db')
                    c = conn.cursor()
                    c.execute("""INSERT INTO resumes (name, role, content, status, experience, ai_summary, ai_score, ai_skills_json) 
                                 VALUES (?, ?, ?, ?, ?, ?, ?, ?)""", 
                              (name, role, text, 'Новый', years, ai_report, ai_score, ai_skills_json))
                    conn.commit()
                    conn.close()
                    st.success(f"Кандидат {name} успешно проанализирован LLM и сохранен с ИИ-рейтингом {ai_score}%!")
                    st.rerun()
                else:
                    st.error("Пожалуйста, заполните ФИО кандидата и текст резюме.")
        st.write("---")
    
    # МОДУЛЬ 2: Коммерческая аналитика и CRM
    if st.session_state.user_role in ['admin', 'manager']:
        st.subheader("📊 Аналитический центр и CRM")
        
        conn = sqlite3.connect('talent_hub.db')
        df = pd.read_sql("SELECT * FROM resumes", conn)
        conn.close()
        
        if not df.empty:
            # Заполняем пустые или старые скоринги нулями для стабильности графиков
            df['ai_score'] = df['ai_score'].fillna(0).astype(int)
            
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
                
                for _, row in filtered_df.sort_values(by='ai_score', ascending=False).iterrows():
                    current_status = row['normalized_status']
                    score_color = "🟢" if row['ai_score'] >= 70 else ("🟡" if row['ai_score'] >= 40 else "🔴")
                    
                    with st.container():
                        col_img, col_main, col_btns = st.columns([1, 4, 2])
                        
                        with col_img:
                            st.image("https://img.icons8.com/fluent-systems-filled/200/FFFFFF/user-male-circle.png", width=65)
                            
                        with col_main:
                            st.markdown(f"#### {score_color} {row['name']}")
                            st.markdown(f"**Вакансия:** {row['role']} | **Текущий статус:** `{current_status}` | **Контекстный ИИ-Матчинг:** {row['ai_score']}%")
                            
                        with col_btns:
                            if st.button("👁️ Посмотреть профиль", key=f"view_{row['id']}", use_container_width=True):
                                show_candidate_modal(row)
                                
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
                st.bar_chart(df['ai_score'])
                
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
