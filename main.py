import streamlit as st
import sqlite3
import hashlib
import pandas as pd
import pypdf
import docx2txt
import io
import requests
import json

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
# Защищенное получение API-ключа из Secrets (Streamlit Cloud)
OPENROUTER_API_KEY = st.secrets.get("OPENROUTER_API_KEY")

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
    if not OPENROUTER_API_KEY:
        return "⚠️ Ошибка: API-ключ не настроен в Secrets вашего Streamlit Cloud приложения. Переключено на оффлайн-режим."

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
    st.sidebar.markdown("### 🏢 Панель управления
