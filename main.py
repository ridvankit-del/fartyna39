import streamlit as st
import pandas as pd

# 1. СЛОВАРЬ ПРОФЕССИЙ И ЧЕК-ЛИСТОВ
PROFESSION_CRITERIA = {
    "Повар": ["Тех. карты", "Работа с грилем", "Санитарные нормы", "Скорость"],
    "Су-шеф": ["Управление сменой", "Инвентаризация", "Контроль качества", "Обучение персонала"],
    "Шеф-повар": ["Разработка меню", "Foodcost", "Управление командой", "Бюджетирование"],
    "Менеджер": ["Работа с R-Keeper/iiko", "Кассовая дисциплина", "Управление конфликтами"],
    "Хостес": ["Грамотная речь", "Внешний вид", "Бронирование", "Этикет"],
    "Официант": ["Знание меню", "Upsell (продажи)", "Сервис", "Работа с POS-системами"]
}

# Инициализация базы
if 'talent_db' not in st.session_state:
    st.session_state.talent_db = {prof: [] for prof in PROFESSION_CRITERIA.keys()}

st.set_page_config(page_title="Blackwood Restaurant Talent", layout="wide")

st.title("👨‍🍳 BLACKWOOD RESTAURANT TALENT HUB")

# 2. БОКОВАЯ ПАНЕЛЬ (Выбор и Добавление)
with st.sidebar:
    selected_prof = st.selectbox("Выберите категорию:", list(PROFESSION_CRITERIA.keys()))
    
    st.divider()
    st.subheader("📥 Новый кандидат")
    with st.form("add_cand"):
        name = st.text_input("Имя")
        exp_years = st.number_input("Стаж (лет)", 0, 30)
        skills_input = st.text_area("Ключевые навыки (через запятую)")
        if st.form_submit_button("Добавить"):
            st.session_state.talent_db[selected_prof].append({
                "Имя": name, 
                "Стаж": exp_years, 
                "Навыки": [s.strip() for s in skills_input.split(',')]
            })
            st.success("Добавлено")

# 3. ОСНОВНАЯ ОБЛАСТЬ (Сравнительный анализ)
st.subheader(f"Кандидаты: {selected_prof}")
candidates = st.session_state.talent_db[selected_prof]

if candidates:
    for cand in candidates:
        with st.container(border=True):
            col1, col2, col3 = st.columns([2, 1, 1])
            col1.write(f"### {cand['Имя']} (Стаж: {cand['Стаж']} лет)")
            
            # Логика AI-оценки соответствия
            required_skills = PROFESSION_CRITERIA[selected_prof]
            matches = [s for s in cand['Навыки'] if s in required_skills]
            score = (len(matches) / len(required_skills)) * 100
            
            col2.metric("Соответствие", f"{score:.0f}%")
            if score > 70:
                col3.success("РЕКОМЕНДОВАН")
            else:
                col3.warning("ТРЕБУЕТ ДОП. ПРОВЕРКИ")
            
            st.write(f"**Сильные стороны:** {', '.join(matches)}")
else:
    st.info("Добавьте кандидатов в текущую категорию через боковую панель.")
