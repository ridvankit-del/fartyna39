import streamlit as st
import numpy as np
import pandas as pd
import time
import os
from dotenv import load_dotenv

# Инициализация и настройки страницы
load_dotenv()
SECRET_KEY = os.getenv("STREAMLIT_SECRET_KEY", "default_fallback_key")

st.set_page_config(page_title="Blackwood Terminal v6.2", page_icon="👑", layout="wide")

# CSS для идеальных пропорций и отступов
st.markdown("""
    <style>
    .stApp {background-color: #050506;}
    /* Карточки с отступами 24px для баланса */
    .block-container {padding-top: 2rem !important; padding-bottom: 2rem !important;}
    
    /* Пропорциональные карточки */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #0E0E12; 
        border: 1px solid #1C1C22; 
        border-radius: 16px; 
        padding: 24px;
        margin-bottom: 16px;
    }
    </style>
""", unsafe_allow_html=True)

# 1. ШАПКА ТЕРМИНАЛА
col_main, col_sub = st.columns([3, 1])
with col_main:
    st.title("👑 BLACKWOOD QUANTITATIVE SUITE")
    st.caption("v6.2 | INTEGRATED RISK MANAGEMENT SYSTEM")
with col_sub:
    st.metric("Market Sentiment", "Bullish", "1.2%")

st.divider()

# 2. ПРОПОРЦИОНАЛЬНАЯ РАБОЧАЯ ОБЛАСТЬ
# Используем сетку 2 к 1 для баланса между контролем и аналитикой
left_col, right_col = st.columns([2, 1])

with left_col:
    tab1, tab2 = st.tabs(["🏦 КРЕДИТНЫЙ СКОРИНГ", "🏢 АНАЛИЗ ЗАЛОГОВ"])
    
    with tab1:
        st.subheader("Параметры заёмщика")
        c1, c2 = st.columns(2)
        hist = c1.slider("Кредитный рейтинг", 0.0, 1.0, 0.7)
        debt = c2.slider("Долговая нагрузка", 0.0, 1.0, 0.4)
        
        prob = ((hist * 3.5) - (debt * 4.0) + 0.5) * 100
        st.progress(int(min(max(prob, 0), 100)))
        
    with tab2:
        st.subheader("Параметры актива")
        s1, s2 = st.columns(2)
        size = s1.slider("Площадь (кв. м.)", 30, 150, 70)
        dist = s2.slider("Дистанция (км)", 1, 20, 5)
        st.info("Расчетная ликвидность актива в норме.")

with right_col:
    # Здесь мы выводим ИИ-инсайты, которые идеально вписываются по ширине
    st.subheader("🤖 AI-Интелект")
    with st.container(border=True):
        st.markdown("### Вердикт системы")
        st.write("На базе текущих переменных модель Blackwood рекомендует осторожный подход.")
        if prob > 50:
            st.success("СТАТУС: ОДОБРЕНО")
        else:
            st.error("СТАТУС: ОТКАЗ")
            
    st.subheader("📊 Риск-профиль")
    chart_data = pd.DataFrame(np.random.randn(20, 1), columns=['Risk'])
    st.area_chart(chart_data, color="#FFDD2D")

#
