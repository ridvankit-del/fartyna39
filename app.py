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
from datetime import datetime

# ==========================================
# КОНФИГУРАЦИЯ И ЛОГИРОВАНИЕ
# ==========================================
st.set_page_config(page_title="Blackwood Enterprise ATS", layout="wide")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("Blackwood_ATS")

# Симуляция переменных окружения (в проде брать из st.secrets)
DEFAULT_ADMIN_PWD = st.secrets.get("ADMIN_PASSWORD", "admin123")
OPENROUTER_API_KEY = st.secrets.get("OPENROUTER_API_KEY", "")

JOB_REQUIREMENTS = {
    "Повар": {"Hard": ["Технологические карты", "СанПиН", "Гриль"], "Soft": ["Чистоплотность", "Выносливость"]},
    "Шеф-повар": {"Hard": ["Foodcost", "Инвентаризация", "Разработка меню"], "Soft": ["Лидерство", "Управление"]},
    "Официант": {"Hard": ["Стандарты сервиса", "R-Keeper/iiko", "Upsell"], "Soft": ["Коммуникабельность", "Грамотная речь"]}
}

# ==========================================
# СЛОЙ ДАННЫХ (DATABASE SERVICE)
# ==========================================
class DatabaseManager:
    """Управляет подключениями и транзакциями. Защита от SQL-инъекций."""
    def __init__(self, db_name="blackwood_pro.db"):
        self.db_name = db_name
        self.init_db()

    def get_connection(self):
        return sqlite3.connect(self.db_name, check_same_thread=False)

    def init_db(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Таблица пользователей
            cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                username TEXT UNIQUE NOT NULL,
                                password_hash BLOB NOT NULL,
                                role TEXT NOT NULL,
                                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
            # Таблица резюме (добавлены индексы и аудит)
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
            # Индексы для быстрого поиска
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_status ON resumes(status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_role ON resumes(role)')
            
            # Создание дефолтного админа, если база пустая
            cursor.execute("SELECT COUNT(*) FROM users WHERE username='admin'")
            if cursor.fetchone()[0] == 0:
                pwd_hash = SecurityService.hash_password(DEFAULT_ADMIN_PWD)
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
            logger.info(f"Добавлено новое резюме: {data['name']}")

    def update_resume_status(self, resume_id: int, new_status: str, updated_by: str):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE resumes SET status = ?, updated_by = ? WHERE id = ?", (new_status, updated_by, resume_id))
            conn.commit()
            logger.info(f"Статус кандидата ID {resume_id} изменен на {new_status} пользователем {updated_by}")

    def delete_resume(self, resume_id: int):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM resumes WHERE id = ?", (resume_id,))
            conn.commit()

# ==========================================
# СЛОЙ БЕЗОПАСНОСТИ И АВТОРИЗАЦИИ
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
        # Имитация защиты от Brute Force (задержка ответа)
        time.sleep(0.5) 
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT password_hash, role FROM users WHERE username = ?", (username,))
            user_record = cursor.fetchone()
            if user_record and SecurityService.verify_password(password, user_record[0]):
                logger.info(f"Успешный вход: {username}")
                return user_record[1]
            logger.warning(f"Неудачная попытка входа для пользователя: {username}")
            return None

# ==========================================
# СЛОЙ БИЗНЕС-ЛОГИКИ (AI & FILES)
# ==========================================
class FileParserService:
    MAX_FILE_SIZE_MB = 5

    @staticmethod
    def extract_text(uploaded_file) -> str:
        if uploaded_file.size > (FileParserService.MAX_FILE_SIZE_MB * 1024 * 1024):
            raise ValueError(f"Файл слишком большой. Максимум {FileParserService.MAX_FILE_SIZE_MB} МБ.")
        
        file_ext = uploaded_file.name.split('.')[-1].lower()
        try:
            if file_ext == 'pdf':
                reader = pypdf.PdfReader(io.BytesIO(uploaded_file.read()))
                return " ".join([page.extract_text() or "" for page in reader.pages]).strip()
            elif file_ext in ['docx', 'doc']:
                return docx2txt.process(io.BytesIO(uploaded_file.read())).strip()
            else:
                raise ValueError("Неподдерживаемый формат файла. Только PDF или DOCX.")
        except Exception as e:
            logger.error(f"Ошибка парсинга файла: {str(e)}")
            raise e

class AIService:
    def __init__(self, api_key: str):
        self.api_key = api_key
        # Используем более мощную и стабильную модель для JSON
        self.model = "google/gemini-flash-1.5-8b" 

    def analyze_candidate(self, resume_text: str, role: str, experience: int, reqs: dict) -> tuple:
        if not self.api_key:
            return "⚠️ API ключ не настроен", 0, "{}"

        prompt = f"""
        Ты HR-эксперт. Проанализируй резюме на позицию '{role}' (заявлен стаж {experience} лет).
        Оцени навыки (включая синонимы): Hard {reqs['Hard']}, Soft {reqs['Soft']}.
        Резюме: {resume_text[:3000]}...
        
        Твой ответ должен строго содержать:
        1. Итоговый вердикт (Нанимаем / Интервью / Отказ)
        2. Сильные стороны
        3. Риски
        
        В конце ответа выведи технический JSON блок строго в формате:
        ```json
        {{
            "score": 85,
            "details": {{"Навык 1": 90, "Навык 2": 0}}
        }}
        ```
        """
        
        # Паттерн Retry (отказоустойчивость)
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key.strip()}"},
                    json={"model": self.model, "messages": [{"role": "user", "content": prompt}]},
                    timeout=45 # Увеличенный таймаут
                )
                response.raise_for_status()
                content = response.json()['choices'][0]['message']['content']
                return self._parse_llm_response(content, reqs)
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Сбой API (попытка {attempt+1}/{max_retries}): {e}")
                time.sleep(2 ** attempt) # Экспоненциальная задержка
                
        return "❌ Ошибка связи с ИИ после 3 попыток.", 0, "{}"

    def _parse_llm_response(self, content: str, reqs: dict) -> tuple:
        ai_score = 0
        ai_skills_json = "{}"
        
        # Надежный поиск JSON через RegEx
        json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
        if json_match:
            try:
                data = json.loads(json_match.group(1))
                ai_score = int(data.get("score", 0))
                ai_skills_json = json.dumps(data.get("details", {}), ensure_ascii=False)
                # Удаляем JSON из визуального отчета
                content = content.replace(json_match.group(0), "").strip()
            except json.JSONDecodeError as e:
                logger.error(f"LLM вернула битый JSON: {e}")
        
        return content, ai_score, ai_skills_json

# ==========================================
# ИНИЦИАЛИЗАЦИЯ СЕРВИСОВ (Синглтоны)
# ==========================================
@st.cache_resource
def get_db():
    return DatabaseManager()

db = get_db()
ai_service = AIService(OPENROUTER_API_KEY)

# ==========================================
# UI: ЭКРАН АВТОРИЗАЦИИ
# ==========================================
if 'user' not in st.session_state:
    st.session_state.user = None

def login_screen():
    st.markdown("## 🔐 Вход в систему (Enterprise ATS)")
    with st.form("login_form"):
        username = st.text_input("Логин")
        password = st.text_input("Пароль", type="password")
        if st.form_submit_button("Войти", width="stretch"):
            role = SecurityService.authenticate(username, password, db)
            if role:
                st.session_state.user = {"username": username, "role": role}
                st.rerun()
            else:
                st.error("Неверный логин или пароль")

# ==========================================
# UI: ОСНОВНОЙ ДАШБОРД
# ==========================================
def main_dashboard():
    user_info = st.session_state.user
    st.sidebar.markdown(f"👤 **{user_info['username'].upper()}** (`{user_info['role']}`)")
    
    # Динамический ключ
    user_api = st.sidebar.text_input("🔑 API Ключ (Override)", type="password")
    if user_api: ai_service.api_key = user_api

    if st.sidebar.button("🚪 Выйти", width="stretch"):
        st.session_state.user = None
        st.rerun()

    st.title("💼 Blackwood Talent Hub")
    
    tab_import, tab_crm, tab_analytics = st.tabs(["📥 Импорт", "🎯 CRM", "📈 Аналитика"])

    # --- Вкладка 1: ИМПОРТ ---
    with tab_import:
        uploaded_file = st.file_uploader("Загрузить резюме", type=['pdf', 'docx'])
        file_text = ""
        if uploaded_file:
            try:
                file_text = FileParserService.extract_text(uploaded_file)
                st.success("Файл прочитан!")
            except ValueError as e:
                st.error(str(e))

        with st.form("candidate_form"):
            col1, col2 = st.columns(2)
            name = col1.text_input("ФИО")
            role = col1.selectbox("Вакансия", list(JOB_REQUIREMENTS.keys()))
            exp = col2.number_input("Стаж (лет)", min_value=0, max_value=50, value=0)
            text = st.text_area("Текст", value=file_text, height=150)
            
            if st.form_submit_button("🚀 Анализировать и сохранить", width="stretch"):
                if not name or not text:
                    st.warning("Заполните ФИО и текст резюме.")
                else:
                    with st.spinner("🧠 AI анализирует кандидата..."):
                        report, score, skills = ai_service.analyze_candidate(text, role, exp, JOB_REQUIREMENTS[role])
                        db.add_resume({
                            "name": name, "role": role, "content": text, "experience": exp,
                            "ai_summary": report, "ai_score": score, "ai_skills_json": skills,
                            "file_name": uploaded_file.name if uploaded_file else "Manual",
                            "updated_by": user_info['username']
                        })
                    st.success("Кандидат сохранен!")
                    st.rerun()

    # --- Вкладка 2: CRM ---
    with tab_crm:
        df = db.fetch_all_resumes()
        if not df.empty:
            col_search, col_filter = st.columns(2)
            search_q = col_search.text_input("🔍 Поиск по ФИО или навыкам")
            status_filter = col_filter.selectbox("Фильтр статуса", ["Все", "Новый", "Собеседование", "Оффер", "Отказ"])
            
            if status_filter != "Все":
                df = df[df['status'] == status_filter]
            if search_q:
                df = df[df['name'].str.contains(search_q, case=False) | df['content'].str.contains(search_q, case=False)]

            for _, row in df.iterrows():
                with st.expander(f"{row['ai_score']}% | {row['name']} - {row['role']} [{row['status']}]"):
                    st.markdown(row['ai_summary'])
                    new_status = st.selectbox("Статус:", ["Новый", "Собеседование", "Оффер", "Отказ"], 
                                              index=["Новый", "Собеседование", "Оффер", "Отказ"].index(row['status']), 
                                              key=f"status_{row['id']}")
                    
                    col_btn1, col_btn2 = st.columns([1, 5])
                    if col_btn1.button("💾 Сохранить", key=f"save_{row['id']}"):
                        db.update_resume_status(row['id'], new_status, user_info['username'])
                        st.rerun()
                    if col_btn2.button("🗑️ Удалить", type="primary", key=f"del_{row['id']}"):
                        db.delete_resume(row['id'])
                        st.rerun()

    # --- Вкладка 3: АНАЛИТИКА ---
    with tab_analytics:
        df = db.fetch_all_resumes()
        if not df.empty:
            col1, col2, col3 = st.columns(3)
            col1.metric("Всего кандидатов", len(df))
            col2.metric("Средний AI Score", int(df['ai_score'].mean()))
            col3.metric("Офферов", len(df[df['status'] == 'Оффер']))
            
            st.bar_chart(df.groupby('role')['id'].count())

# ==========================================
# ТОЧКА ВХОДА
# ==========================================
if __name__ == "__main__":
    if st.session_state.user is None:
        login_screen()
    else:
        main_dashboard()
