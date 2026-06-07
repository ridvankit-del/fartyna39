import streamlit as st
import sqlite3
import hashlib
import pandas as pd

# 1. КОНФИГУРАЦИЯ СТРАНИЦЫ И СТИЛИ (PREMIUM DESIGN)
st.set_page_config(page_title="Blackwood Enterprise AI HR", layout="wide")

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
        /* Брендированные контейнеры-карточки */
        .custom-card {
            background-color: #F9F9FB;
            padding: 20px;
            border-radius: 12px;
            border-left: 5px solid #1E1E1E;
            box-shadow: 0 4px 6px rgba(0,0,0,0.02);
            margin-bottom: 15px;
        }
        .modal-card {
            background-color: #F0F2F6;
            padding: 15px;
            border-radius: 8px;
            border: 1px solid #E0E0E0;
            margin-bottom: 10px;
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
    else: exp_multiplier
