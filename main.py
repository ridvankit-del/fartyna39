import streamlit as st
import pandas as pd
import re

# Настройка интерфейса под HR-задачи
st.set_page_config(page_title="Blackwood Talent Hub", layout="wide")

st.markdown("""
    <style>
    .stApp {background: #050506; color: #E0E0E0;}
    .report-card {background: #1C1C22; padding: 20px; border-radius: 12px; border-left: 4px solid #FFDD2D;}
    </style>
""", unsafe_allow_html=True)

st.title("🧠 BLACKWOOD TALENT INTELLIGENCE")

# Вкладки
tab1, tab2 = st.tabs(["📄 АНАЛИЗ РЕЗЮМЕ", "🔍 СРАВНЕНИЕ С ВАКАНСИЕЙ"])

with tab1:
    st.subheader("Парсинг резюме")
    resume_text = st.text_area("Вставьте текст резюме:", height=300)
    
    if st.button("Проанализировать"):
        # Логика поиска ключевых навыков (AI-база)
        skills = ["Python", "Machine Learning", "Streamlit", "SQL", "Docker", "Git"]
        found_skills = [skill for skill in skills if skill.lower() in resume_text.lower()]
        
        st.markdown("<div class='report-card'>", unsafe_allow_html=True)
        st.write("### 🤖 ИИ-Отчет:")
        st.write(f"**Найденные навыки:** {', '.join(found_skills)}")
        st.write(f"**Score:** {len(found_skills)/len(skills)*100:.0f}% соответствия технологическому стеку.")
        st.markdown("</div>", unsafe_allow_html=True)

with tab2:
    st.subheader("Сравнение кандидат vs Вакансия")
    job_desc = st.text_area("Описание вакансии:", height=150)
    # Здесь в будущем будет алгоритм Cosine Similarity для сравнения векторов текста
