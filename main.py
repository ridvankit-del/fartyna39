import streamlit as st
import pandas as pd

# Инициализация хранилища базы талантов
if 'talent_db' not in st.session_state:
    st.session_state.talent_db = {
        "Data Science & AI": [],
        "Fullstack Dev": [],
        "Digital Marketing": [],
        "Finance & Risk": []
    }

st.set_page_config(page_title="Blackwood Talent Hub", layout="wide")

# CSS для карточек категорий
st.markdown("""
    <style>
    .cat-card {background: #1C1C22; padding: 15px; border-radius: 10px; margin-bottom: 10px; border: 1px solid #333;}
    </style>
""", unsafe_allow_html=True)

st.title("🧠 BLACKWOOD TALENT HUB")

# Боковая панель для навигации по категориям
with st.sidebar:
    st.header("📂 Категории")
    selected_cat = st.radio("Выберите направление:", list(st.session_state.talent_db.keys()))
    
    st.divider()
    st.subheader("📥 Добавить кандидата")
    with st.form("add_candidate"):
        name = st.text_input("Имя кандидата")
        skills = st.text_input("Навыки (через запятую)")
        submitted = st.form_submit_button("Добавить в базу")
        if submitted and name:
            st.session_state.talent_db[selected_cat].append({"Имя": name, "Навыки": skills})
            st.success(f"Добавлен в {selected_cat}")

# Основная область анализа
st.subheader(f"Анализ профилей: {selected_cat}")

# Вывод резюме в категории
candidates = st.session_state.talent_db[selected_cat]
if not candidates:
    st.info("В этой категории пока нет резюме.")
else:
    for cand in candidates:
        with st.container():
            st.markdown(f"<div class='cat-card'>", unsafe_allow_html=True)
            col1, col2 = st.columns([3, 1])
            col1.write(f"### {cand['Имя']}")
            col1.write(f"**Стек:** {cand['Навыки']}")
            # Здесь будет кнопка для глубокого анализа
            if col2.button("Анализ", key=cand['Имя']):
                st.session_state.current_analysis = cand
            st.markdown("</div>", unsafe_allow_html=True)

# Окно детального анализа (если выбрано)
if 'current_analysis' in st.session_state:
    st.divider()
    st.subheader(f"🔍 Глубокий разбор: {st.session_state.current_analysis['Имя']}")
    # ИИ-логика для разбора конкретного кандидата
    st.write("ИИ-аналитик изучает соответствие опыту...")
