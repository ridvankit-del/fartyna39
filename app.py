import streamlit as st
import sqlite3
import pandas as pd
import pypdf
import docx2txt
import io
import requests
import json
import re
import bcrypt
import logging
import time

# ==========================================
# 1. СИСТЕМНАЯ КОНФИГУРАЦИЯ И ЛОГИРОВАНИЕ
# ==========================================
st.set_page_config(page_title="Blackwood Enterprise AI HR", layout="wide")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("Blackwood_ATS")

# Стилизация интерфейса (Premium Minimalist Design)
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
            font-size: 16px !important;
            color: #666666;
            margin-bottom: 25px;
        }
        div[data-testid="stMetricSimpleValue"] {
            font-size: 26px !important;
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

# Матрица компетенций из ТЗ
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

# ==========================================
# 2. СЛОЙ ДАННЫХ (DATABASE SERVICE)
# ==========================================
class DatabaseManager:
    def __init__(self, db_name="blackwood_enterprise.db"):
        self.db_name = db_name
        self.init_db()

    def get_connection(self):
        return sqlite3.connect(self.db_name, check_same_thread=False)

    def init_db(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Таблица сотрудников компании
            cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                username TEXT UNIQUE NOT NULL,
                                password_hash BLOB NOT NULL,
                                role TEXT NOT NULL,
                                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
            
            # Таблица базы резюме
            cursor.execute('''CREATE TABLE IF NOT EXISTS resumes (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                name TEXT NOT NULL,
                                role TEXT NOT NULL,
                                content TEXT,
                                status TEXT DEFAULT 'Новый',
                                experience INTEGER,
                                ai_summary TEXT,
                                ai_score INTEGER DEFAULT 0,
                                ai_skills_json TEXT,
                                file_name TEXT,
                                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                updated_by TEXT)''')
            
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_status ON resumes(status)')
            
            # Дефолтный админ, если база только создана (пароль по умолчанию: 9391291)
            cursor.execute("SELECT COUNT(*) FROM users WHERE username='admin'")
            if cursor.fetchone()[0] == 0:
                pwd_hash = SecurityService.hash_password("9391291")
                cursor.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)", 
                               ("admin", pwd_hash, "admin"))
            conn.commit()

    def fetch_all_resumes(self):
        with self.get_connection() as conn:
            return pd.read_sql("SELECT * FROM resumes ORDER BY ai_score DESC, created_at DESC", conn)

    def add_resume(self, data: dict):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO resumes (name, role, content, experience, ai_summary, ai_score, ai_skills_json, file_name, updated_by) 
                VALUES (:name, :role, :content, :experience, :ai_summary, :ai_score, :ai_skills_json, :file_name, :updated_by)
            """, data)
            conn.commit()
            logger.info(f"Кандидат {data['name']} успешно добавлен в воронку.")

    def update_resume_status(self, resume_id: int, new_status: str, updated_by: str):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE resumes SET status = ?, updated_by = ? WHERE id = ?", (new_status, updated_by, resume_id))
            conn.commit()

    def delete_resume(self, resume_id: int):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM resumes WHERE id = ?", (resume_id,))
            conn.commit()

# ==========================================
# 3. СЛОЙ БЕЗОПАСНОСТИ (SECURITY SERVICE)
# ==========================================
class SecurityService:
    @staticmethod
    def hash_password(password: str) -> bytes:
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    @staticmethod
    def verify_password(password: str, hashed_password: bytes) -> bool:
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password)

    @staticmethod
    def authenticate(username, password, db: DatabaseManager):
        time.sleep(0.3)  # Базовая защита от брутфорса
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT password_hash, role FROM users WHERE username = ?", (username,))
            user_record = cursor.fetchone()
            if user_record and SecurityService.verify_password(password, user_record[0]):
                return user_record[1]
            return None

# ==========================================
# 4. СЛОЙ ПАРСИНГА И АНАЛИТИКИ (AI & FILES)
# ==========================================
class FileParserService:
    @staticmethod
    def extract_text(uploaded_file) -> str:
        if uploaded_file.size > (5 * 1024 * 1024):
            raise ValueError("Размер файла превышает лимит 5 МБ.")
        
        file_ext = uploaded_file.name.split('.')[-1].lower()
        try:
            if file_ext == 'pdf':
                reader = pypdf.PdfReader(io.BytesIO(uploaded_file.read()))
                return " ".join([page.extract_text() or "" for page in reader.pages]).strip()
            elif file_ext in ['docx', 'doc']:
                return docx2txt.process(io.BytesIO(uploaded_file.read())).strip()
            else:
                raise ValueError("Система принимает только файлы формата PDF или DOCX.")
        except Exception as e:
            logger.error(f"Ошибка чтения структуры документа: {e}")
            raise e

class AIService:
    def __init__(self, api_key: str):
        self.api_key = self.clean_key(api_key)
        self.model = "google/gemini-flash-1.5-8b:free"  # Стабильная бесплатная модель

    @staticmethod
    def clean_key(key: str) -> str:
        """Очищает токен от мусорных кавычек и пробелов, предотвращая ошибку 401"""
        if not key:
            return ""
        return key.strip().replace('"', '').replace("'", "")

    def analyze_candidate(self, resume_text: str, role: str, experience: int, requirements: dict) -> tuple:
        if not self.api_key:
            return "⚠️ Критическая ошибка: Не настроен API-ключ нейросети.", 0, "{}"

        all_skills = requirements.get("Hard Skills", []) + requirements.get("Soft Skills", [])
        skills_structure = {skill: 0 for skill in all_skills}

        prompt = f"""
        Ты — опытный ИИ-директор по персоналу ресторанной сети 'Blackwood Enterprise'.
        Твоя задача — провести глубокий смысловой аудит резюме. Если кандидат описал навык синонимами или с опечатками — пойми контекст и зачти это.
        
        Вакансия: {role}
        Заявленный стаж: {experience} лет.
        Критерии идеального сотрудника:
        - Hard Skills: {json.dumps(requirements.get("Hard Skills", []), ensure_ascii=False)}
        - Soft Skills: {json.dumps(requirements.get("Soft Skills", []), ensure_ascii=False)}
        
        Текст резюме кандидата:
        ---
        {resume_text[:4000]}
        ---
        
        Напиши структурированный отчет на РУССКОМ языке в формате Markdown.
        Структура отчета должна строго содержать:
        1. ### 🤖 Настоящее ИИ-Заключение Blackwood (Итоговый вердикт: нанимаем/на интервью/отказ)
        2. **Сильные стороны:** (Какие навыки и реальный опыт соответствуют ресторанной сфере)
        3. **Скрытые риски и зоны роста:** (Чего не хватает, часто ли менял работу)
        4. **Фактор стажа:** (Оценка опыта для данной позиции)
        
        В САМОМ КОНЦЕ ОТВЕТА выведи технический блок с оценками в формате JSON внутри тегов [DATA]...[/DATA].
        Оцени каждый навык из списка от 0 до 100 на основе контекста резюме. Высчитай общий средний рейтинг (score) от 0 до 100.
        Шаблон технического блока:
        [DATA]
        {{
          "score": 85,
          "details": {json.dumps(skills_structure, ensure_ascii=False)}
        }}
        [/DATA]
        """

        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    url="https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": [{"role": "user", "content": prompt}]
                    },
                    timeout=20
                )
                if response.status_code == 200:
                    raw_content = response.json()['choices'][0]['message']['content']
                    return self._parse_response(raw_content)
                elif response.status_code == 401:
                    return f"❌ Ошибка авторизации ИИ (401). Проверьте правильность токена в Secrets/Сайдбаре.", 0, "{}"
                else:
                    logger.warning(f"Сервер вернул ошибку {response.status_code}, пробую повторно...")
            except Exception as e:
                logger.error(f"Сбой сети при попытке {attempt+1}: {e}")
                time.sleep(1.5 ** attempt)

        return "❌ Не удалось связаться с ИИ-сервером после серии попыток.", 0, "{}"

    def _parse_response(self, raw_content: str) -> tuple:
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
            except Exception as e:
                logger.error(f"Не удалось распарсить JSON метрики: {e}")
        return ai_report, ai_score, ai_skills_json

# ==========================================
# 5. ИНИЦИАЛИЗАЦИЯ И СЕРВИСНЫЙ ДЕБАГ
# ==========================================
@st.cache_resource
def init_core_services():
    return DatabaseManager()

db = init_core_services()

# Определение источника API ключа
if st.secrets.get("OPENROUTER_API_KEY"):
    ENV_KEY = st.secrets.get("OPENROUTER_API_KEY")
else:
    ENV_KEY = ""

ai_service = AIService(ENV_KEY)

# ==========================================
# 6. ИНТЕРФЕЙС ПРИЛОЖЕНИЯ (UI)
# ==========================================
if 'user' not in st.session_state:
    st.session_state.user = None

# Диалоговое окно детальной аналитики (Modal Profile)
@st.dialog("📋 Контекстный ИИ-Анализ соискателя")
def show_candidate_modal(row):
    st.write(f"### {row['name']}")
    st.write(f"**Специализация:** {row['role']} | **Стаж:** {row['experience']} л.")
    st.write("---")
    
    if row['ai_summary']:
        st.markdown(row['ai_summary'])
    else:
        st.info("Заключение отсутствует.")
    st.write("---")
    
    st.markdown("**📊 Семантическая матрица соответствия:**")
    if row['ai_skills_json']:
        try:
            skills = json.loads(row['ai_skills_json'])
            for skill, val in skills.items():
                st.write(f"- {skill}: **{val}%**")
                st.progress(int(val) / 100)
        except:
            st.error("Ошибка десериализации матрицы.")
    
    if st.button("Закрыть окно", width="stretch"):
        st.rerun()

# --- ЭКРАН АВТОРИЗАЦИИ ---
if st.session_state.user is None:
    st.image("https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?auto=format&fit=crop&w=1200&q=80", use_container_width=True)
    st.markdown('<p class="main-title">🔐 Blackwood HR</p>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Вход в корпоративную систему ATS & AI Talent Hub</p>', unsafe_allow_html=True)
    
    with st.form("login_form"):
        username = st.text_input("Идентификатор (Логин)")
        password = st.text_input("Пароль доступа", type="password")
        if st.form_submit_button("Авторизоваться в системе", width="stretch"):
            role = SecurityService.authenticate(username, password, db)
            if role:
                st.session_state.user = {"username": username, "role": role}
                st.rerun()
            else:
                st.error("Ошибка безопасности: Неверная пара логин/пароль.")

# --- ОСНОВНОЙ РАБОЧИЙ ПРОСТРАНСТВО ---
else:
    user_info = st.session_state.user
    
    # Сайдбар управления
    st.sidebar.image("https://images.unsplash.com/photo-1634017839464-5c339ebe3cb4?auto=format&fit=crop&w=300&q=80", use_container_width=True)
    st.sidebar.markdown(f"### 🏢 Панель управления")
    st.sidebar.write(f"Сотрудник: **{user_info['username'].upper()}**")
    st.sidebar.write(f"Доступ: `{user_info['role'].upper()}`")
    st.sidebar.markdown("---")
    
    # Поле динамического переопределения ключа
    custom_key = st.sidebar.text_input("🔑 Изменить API Ключ OpenRouter", type="password", placeholder="Заменяет ключ по умолчанию...")
    if custom_key:
        ai_service.api_key = AIService.clean_key(custom_key)
        
    # Виджет диагностики ключа для предотвращения 401
    if ai_service.api_key:
        st.sidebar.info(f"Диагностика: Ключ подключен (Длина: {len(ai_service.api_key)} симв.)")
    else:
        st.sidebar.warning("Диагностика: Ключ ИИ отсутствует")

    if st.sidebar.button("🚪 Выйти из системы", width="stretch"):
        st.session_state.user = None
        st.rerun()

    st.markdown('<p class="main-title">💼 BLACKWOOD ENTERPRISE</p>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Интегрированная ATS-система интеллектуального скрининга кадров</p>', unsafe_allow_html=True)
    st.write("---")

    tab_import, tab_crm, tab_analytics = st.tabs(["📥 Импорт соискателей", "🎯 CRM Воронка", "📈 Аналитический Центр"])

    # --- ВКЛАДКА 1: УМНЫЙ ИМПОРТ ---
    with tab_import:
        if user_info['role'] in ['admin', 'recruiter']:
            st.subheader("Загрузка резюме в систему")
            uploaded_file = st.file_uploader("Перетащите файл резюме (.pdf, .docx)", type=['pdf', 'docx'])
            
            file_text = ""
            if uploaded_file:
                try:
                    file_text = FileParserService.extract_text(uploaded_file)
                    st.success(f"📎 Документ обработан. Распознано символов: {len(file_text)}")
                except Exception as e:
                    st.error(str(e))

            with st.form("resume_form"):
                col1, col2 = st.columns(2)
                with col1:
                    name = st.text_input("ФИО Кандидата", placeholder="Константинопольский Константин")
                    role = st.selectbox("Целевая вакансия", list(JOB_REQUIREMENTS.keys()))
                with col2:
                    years = st.number_input("Опыт работы (полных лет)", min_value=0, max_value=40, value=0)
                    text = st.text_area("Текстовое содержание", value=file_text, placeholder="Текст из файла или ручной ввод...")
                
                if st.form_submit_button("🔥 Запустить ИИ-анализ и сохранить", width="stretch"):
                    if name and text:
                        with st.spinner("🤖 Нейросеть проводит семантический аудит..."):
                            reqs = JOB_REQUIREMENTS[role]
                            report, score, skills = ai_service.analyze_candidate(text, role, years, reqs)
                            
                            db.add_resume({
                                "name": name, "role": role, "content": text, "experience": years,
                                "ai_summary": report, "ai_score": score, "ai_skills_json": skills,
                                "file_name": uploaded_file.name if uploaded_file else "Manual Input",
                                "updated_by": user_info['username']
                            })
                            st.success(f"Анализ завершен! Индекс соответствия: {score}%")
                            st.rerun()
                    else:
                        st.error("Ошибка заполнения обязательных полей (ФИО и Текст).")
        else:
            st.error("Ваш уровень доступа не позволяет импортировать новые анкеты.")

    # --- ВКЛАДКА 2: CRM ВОРОНКА ---
    with tab_crm:
        df = db.fetch_all_resumes()
        if not df.empty:
            col_s, col_f = st.columns(2)
            search_query = col_s.text_input("🔍 Быстрый поиск (ФИО/Ключевые слова)")
            status_filter = col_f.selectbox("Этап отбора:", ["Все", "Новый", "Собеседование", "Оффер", "Отказ"])
            
            if status_filter != "Все":
                df = df[df['status'] == status_filter]
            if search_query:
                df = df[df['name'].str.contains(search_query, case=False) | df['content'].str.contains(search_query, case=False)]

            st.write("---")
            allowed_statuses = ["Новый", "Собеседование", "Оффер", "Отказ"]
            
            for _, row in df.iterrows():
                score_icon = "🟢" if row['ai_score'] >= 70 else ("🟡" if row['ai_score'] >= 40 else "🔴")
                
                st.markdown(f"""
                    <div class="custom-card">
                        <span style='font-size:20px;'>{score_icon} <b>{row['name']}</b></span> — <i>{row['role']}</i><br>
                        <small>ИИ Рейтинг: {row['ai_score']}% | Стаж: {row['experience']} л. | Статус: <b>{row['status']}</b></small>
                    </div>
                """, unsafe_allow_html=True)
                
                col_b1, col_b2, col_b3 = st.columns([2, 2, 1])
                if col_b1.button("👁️ Профиль и Матрица", key=f"view_{row['id']}", width="stretch"):
                    show_candidate_modal(row)
                
                new_status = col_b2.selectbox("Сменить статус на:", allowed_statuses, index=allowed_statuses.index(row['status']), key=f"sel_{row['id']}")
                
                col_sub1, col_sub2 = col_b3.columns(2)
                if col_sub1.button("💾", key=f"save_{row['id']}", help="Сохранить изменения"):
                    db.update_resume_status(row['id'], new_status, user_info['username'])
                    st.rerun()
                if col_sub2.button("🗑️", key=f"del_{row['id']}", help="Удалить анкету"):
                    db.delete_resume(row['id'])
                    st.rerun()
        else:
            st.info("База данных соискателей пуста.")

    # --- ВКЛАДКА 3: АНАЛИТИКА ---
    with tab_analytics:
        df = db.fetch_all_resumes()
        if not df.empty:
            c1, c2, c3 = st.columns(3)
            c1.metric("Всего обработано", f"{len(df)} анкет")
            c2.metric("Средний ИИ-Score", f"{int(df['ai_score'].mean())}%")
            c3.metric("Выдано офферов", f"{len(df[df['status']=='Оффер'])} чел.")
            
            st.write("---")
            st.markdown("### 📊 Поток кандидатов в разрезе должностей")
            st.bar_chart(df.groupby('role')['id'].count())
        else:
            st.info("Нет данных для построения сквозной аналитики.")
