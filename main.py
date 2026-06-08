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
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def init_db():
    connection = sqlite3.connect('talent_hub.db')
    cursor = connection.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password_hash TEXT, role TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS resumes 
                      (id INTEGER PRIMARY KEY, name TEXT, role TEXT, content TEXT, status TEXT, experience INTEGER, 
                       ai_summary TEXT, ai_score INTEGER, ai_skills_json TEXT)''')
    
    try: cursor.execute("ALTER TABLE resumes ADD COLUMN experience INTEGER")
    except sqlite3.OperationalError: pass
    try: cursor.execute("ALTER TABLE resumes ADD COLUMN ai_summary TEXT")
    except sqlite3.OperationalError: pass
    try: cursor.execute("ALTER TABLE resumes ADD COLUMN ai_score INTEGER DEFAULT 0")
    except sqlite3.OperationalError: pass
    try: cursor.execute("ALTER TABLE resumes ADD COLUMN ai_skills_json TEXT")
    except sqlite3.OperationalError: pass
    
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

def ask_llm_semantic_analysis(resume_text, role, experience, requirements, api_key):
    if not api_key:
        return "⚠️ Ошибка: API-ключ не настроен. Введите его в боковой панели или укажите в Secrets.", 0, "{}"

    all_skills = requirements.get("Hard Skills", []) + requirements.get("Soft Skills", [])
    skills_structure = {skill: 0 for skill in all_skills}

    prompt = f"""
    Ты — экспертный ИИ-директор по персоналу ресторанной сети 'Blackwood Enterprise'.
    Твоя задача — провести глубокий смысловой аудит резюме. Оценивай контекст: если кандидат описал навык синонимами или своими словами — засчитывай его.
    
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
    Структура отчета:
    1. ### 🤖 Настоящее ИИ-Заключение Blackwood (Итоговый вердикт: нанимаем/на интервью/отказ)
    2. **Сильные стороны:** (Соответствие навыков ресторанной сфере)
    3. **Скрытые риски и зоны роста:** (Чего не хватает, стабильность на прошлых местах)
    4. **Фактор стажа:** (Оценка опыта для данной позиции)
    
    В САМОМ КОНЦЕ ОТВЕТА выведи технический блок с оценками в формате JSON внутри тегов [DATA]...[/DATA].
    Оцени каждый навык от 0 до 100. Высчитай общий средний рейтинг (score) от 0 до 100.
    Шаблон технического блока:
    [DATA]
    {{
      "score": 85,
      "details": {json.dumps(skills_structure, ensure_ascii=False)}
    }}
    [/DATA]
    """

    try:
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key.strip()}",
                "Content-Type": "application/json"
            },
            data=json.dumps({
                "model": "google/gemini-flash-1.5-8b:free",
                "messages": [{"role": "user", "content": prompt}]
            }),
            timeout=15
        )
        if response.status_code == 200:
            raw_content = response.json()['choices'][0]['message']['content']
            
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
                    st.warning(f"Разбор текста выполнен, но метрики не десериализованы: {je}")
            
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
    else
