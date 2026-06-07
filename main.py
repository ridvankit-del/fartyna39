import streamlit as st
import numpy as np
import pandas as pd
import time
import os
from dotenv import load_dotenv

# 1. ИНИЦИАЛИЗАЦИЯ И СТИЛИЗАЦИЯ
load_dotenv()
SECRET_KEY = os.getenv("STREAMLIT_SECRET_KEY", "default_fallback_key")

st.set_page_config(
    page_title="AI Analytics Suite", 
    page_icon="🛡️", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- МАКСИМАЛЬНАЯ АНОНИМНОСТЬ: CSS МАГИЯ ---
hide_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .viewerBadge_link__1S137 {display: none !important;}
    </style>
"""
st.markdown(hide_style, unsafe_allow_html=True)

if "last_request_time" not in st.session_state:
    st.session_state.last_request_time = 0.0

def check_rate_limit():
    current_time = time.time()
    if current_time - st.session_state.last_request_time < 0.3:
        st.warning("⚠️ Слишком много запросов! Притормозите.")
        st.stop()
    st.session_state.last_request_time = current_time

# Математические модели ИИ
def predict_credit(hist, debt):
    score = (hist * 3.5) - (debt * 4.0) + 0.5
    return 1 / (1 + np.exp(-score))

def predict_housing(size, distance):
    base_price = 50000.0 + (size * 1200.0) - (distance * 2000.0)
    return base_price + np.sin(size) * 3000.0


# 2. ДИЗАЙН БОКОВОЙ ПАНЕЛИ (Оставили только глобальные настройки)
with st.sidebar:
    st.markdown("<h2 style='text-align: center; color: #ff4b4b; font-family: sans-serif; letter-spacing: 2px;'>🛡️ CORE SYSTEM</h2>", unsafe_allow_html=True)
    st.write("---")
    
    st.markdown("##### 🌐 Глобальные маркеры")
    market_condition = st.slider(
        "Рыночный коэффициент", 
        0.5, 1.5, 1.0, 0.1,
        help="Влияние внешних макроэкономических факторов на вычисления."
    )
    
    st.write("---")
    if SECRET_KEY != "default_fallback_key":
        st.markdown("<p style='color: #00f4b4; font-size: 14px;'>🔒 <b>Лицензия:</b> Enterprise AI (Protected)</p>", unsafe_allow_html=True)
    else:
        st.markdown("<p style='color: #888888; font-size: 14px;'>🔓 <b>Лицензия:</b> Public Open-Source v4.5</p>", unsafe_allow_html=True)


# 3. СОЗДАНИЕ ВКЛАДОК ПО ЦЕНТРУ СТРАНИЦЫ
tab1, tab2 = st.tabs(["🏦 Кредитный Скоринг v4.5", "🏡 Оценка и Прогноз Недвижимости"])


# --- ВКЛАДКА 1: КРЕДИТНЫЙ СКОРИНГ ---
with tab1:
    st.title("🏦 Интеллектуальный Кредитный Скоринг")
    st.markdown("##### *Автоматизированный экспресс-анализ рисков дефолта*")
    st.write("---")
    
    with st.container(border=True):
        st.subheader("📋 Профиль контрагента")
        col1, col2 = st.columns(2)
        with col1:
            hist = st.slider("Кредитный рейтинг", 0.0, 1.0, 0.7, 0.01, key="credit_hist", help="Интегральный показатель финансовой дисциплины.")
        with col2:
            debt = st.slider("Долговая нагрузка (DTI)", 0.0, 1.0, 0.4, 0.01, key="credit_debt", help="Отношение текущих обязательств к подтвержденному доходу.")

    check_rate_limit()
    
    with st.spinner("Интерполяция данных..."):
        time.sleep(0.1)
        prob = (predict_credit(hist, debt) / market_condition) * 100
        prob = min(max(prob, 0.0), 100.0)

    st.write("")
    res_col1, res_col2 = st.columns([1, 1.2])
    
    with res_col1:
        st.subheader("🎯 Результат анализа")
        with st.container(border=True):
            st.metric(label="Индекс надежности", value=f"{prob:.2f}%")
            st.progress(int(prob))
            st.write("")
            if prob >= 50.0:
                st.success("✅ **СТАТУС: ВЫСОКАЯ НАДЕЖНОСТЬ** \n\nРекомендовано автоматическое одобрение.")
            else:
                st.error("❌ **СТАТУС: КРИТИЧЕСКИЙ РИСК** \n\nТип риска: Высокая вероятность дефолта.")
                
    with res_col2:
        st.subheader("📊 Поведение модели при стресс-тесте")
        x_range = np.linspace(0.0, 1.0, 50)
        y_range = [min(max((predict_credit(x, debt) / market_condition) * 100, 0.0), 100.0) for x in x_range]
        chart_data = pd.DataFrame({"Рейтинг": x_range, "Надежность %": y_range})
        st.line_chart(chart_data, x="Рейтинг", y="Надежность %", color="#ff4b4b")


# --- ВКЛАДКА 2: НЕДВИЖИМОСТЬ ---
with tab2:
    st.title("🏡 ИИ-Оценщик & Предиктор Стоимости")
    st.markdown("##### *Расчет ликвидационной стоимости активов и симуляция трендов*")
    st.write("---")
    
    with st.container(border=True):
        st.subheader("📊 Технические параметры")
        col1, col2 = st.columns(2)
        with col1:
            size_input = st.slider("Общая площадь (кв. м.)", 30, 150, 70, 1, key="house_size")
        with col2:
            dist_input = st.slider("Удаленность от ядра инфраструктуры (км)", 1, 20, 5, 1, key="house_dist")

    check_rate_limit()
    
    with st.spinner("Анализ рыночных секторов..."):
        time.sleep(0.1)
        current_price = max(predict_housing(size_input, dist_input) * market_condition, 15000.0)

    st.write("")
    res_col1, res_col2 = st.columns([1, 1.2])
    
    with res_col1:
        st.subheader("💰 Оценка стоимости")
        with st.container(border=True):
            st.metric(label="Расчетная стоимость объекта", value=f"${current_price:,.2f}")
            st.write("---")
            st.write("📋 **Внутренний аудит:**")
            st.write(f"• Средняя стоимость кв. м: **${(current_price/size_input):.2f}**")
            st.write(f"• Индекс локации: **{-dist_input * 2000:+,}** к базе")
            
            if market_condition > 1.2:
                st.warning("⚠️ Зафиксирован аномальный перегрев сектора.")
            elif market_condition < 0.8:
                st.info("📉 Обнаружена недооценка актива.")
            else:
                st.success("⚖️ Показатели волатильности в норме.")
                
    with res_col2:
        st.subheader("🔮 Динамика стоимости (Прогноз на 5 лет)")
        years = ["2026", "2027", "2028", "2029", "2030", "2031"]
        prices = [current_price]
        for i in range(1, 6):
            growth = 1.05 + (market_condition - 1.0) * 0.05 
            next_price = prices[-1] * growth + (np.sin(i) * 2000)
            prices.append(max(next_price, 15000.0))
            
        forecast_data = pd.DataFrame({"Год": years, "Прогноз цен ($)": prices})
        st.bar_chart(forecast_data, x="Год", y="Прогноз цены ($)", color="#2e7bcf")    market_condition = st.slider(
        "Рыночный коэффициент", 
        0.5, 1.5, 1.0, 0.1,
        help="Влияние внешних макроэкономических факторов на вычисления."
    )
    
    st.write("---")
    # Эстетичное отображение статуса без грубых предупреждений
    if SECRET_KEY != "default_fallback_key":
        st.markdown("<p style='color: #00f4b4; font-size: 14px;'>🔒 <b>Лицензия:</b> Enterprise AI (Protected)</p>", unsafe_allow_html=True)
    else:
        st.markdown("<p style='color: #888888; font-size: 14px;'>🔓 <b>Лицензия:</b> Public Open-Source v4.5</p>", unsafe_allow_html=True)


# 3. ЛОГИКА И ДИЗАЙН ОСНОВНЫХ СТРАНИЦ

# --- КРЕДИТНЫЙ СКОРИНГ ---
if app_mode == "🏦 Кредитный Скоринг v4.5":
    st.title("🏦 Интеллектуальный Кредитный Скоринг")
    st.markdown("##### *Автоматизированный экспресс-анализ рисков дефолта*")
    st.write("---")
    
    with st.container(border=True):
        st.subheader("📋 Профиль контрагента")
        col1, col2 = st.columns(2)
        with col1:
            hist = st.slider("Кредитный рейтинг", 0.0, 1.0, 0.7, 0.01, help="Интегральный показатель финансовой дисциплины.")
        with col2:
            debt = st.slider("Долговая нагрузка (DTI)", 0.0, 1.0, 0.4, 0.01, help="Отношение текущих обязательств к подтвержденному доходу.")

    check_rate_limit()
    
    with st.spinner("Интерполяция данных..."):
        time.sleep(0.1)
        prob = (predict_credit(hist, debt) / market_condition) * 100
        prob = min(max(prob, 0.0), 100.0)

    st.write("")
    res_col1, res_col2 = st.columns([1, 1.2])
    
    with res_col1:
        st.subheader("🎯 Результат анализа")
        with st.container(border=True):
            st.metric(label="Индекс надежности", value=f"{prob:.2f}%")
            st.progress(int(prob))
            st.write("")
            if prob >= 50.0:
                st.success("✅ **СТАТУС: ВЫСОКАЯ НАДЕЖНОСТЬ** \n\nРекомендовано автоматическое одобрение.")
            else:
                st.error("❌ **СТАТУС: КРИТИЧЕСКИЙ РИСК** \n\nТребуется ручная верификация или отказ.")
                
    with res_col2:
        st.subheader("📊 Поведение модели при стресс-тесте")
        x_range = np.linspace(0.0, 1.0, 50)
        y_range = [min(max((predict_credit(x, debt) / market_condition) * 100, 0.0), 100.0) for x in x_range]
        chart_data = pd.DataFrame({"Рейтинг": x_range, "Надежность %": y_range})
        st.line_chart(chart_data, x="Рейтинг", y="Надежность %", color="#ff4b4b")


# --- НЕДВИЖИМОСТЬ ---
elif app_mode == "🏡 Оценка и Прогноз Недвижимости":
    st.title("🏡 ИИ-Оценщик & Предиктор Стоимости")
    st.markdown("##### *Расчет ликвидационной стоимости активов и симуляция трендов*")
    st.write("---")
    
    with st.container(border=True):
        st.subheader("📊 Технические параметры")
        col1, col2 = st.columns(2)
        with col1:
            size_input = st.slider("Общая площадь (кв. м.)", 30, 150, 70, 1)
        with col2:
            dist_input = st.slider("Удаленность от ядра инфраструктуры (км)", 1, 20, 5, 1)

    check_rate_limit()
    
    with st.spinner("Анализ рыночных секторов..."):
        time.sleep(0.1)
        current_price = max(predict_housing(size_input, dist_input) * market_condition, 15000.0)

    st.write("")
    res_col1, res_col2 = st.columns([1, 1.2])
    
    with res_col1:
        st.subheader("💰 Оценка стоимости")
        with st.container(border=True):
            st.metric(label="Расчетная стоимость объекта", value=f"${current_price:,.2f}")
            st.write("---")
            st.write("📋 **Внутренний аудит:**")
            st.write(f"• Средняя стоимость кв. м: **${(current_price/size_input):.2f}**")
            st.write(f"• Индекс локации: **{-dist_input * 2000:+,}** к базе")
            
            if market_condition > 1.2:
                st.warning("⚠️ Зафиксирован аномальный перегрев сектора.")
            elif market_condition < 0.8:
                st.info("📉 Обнаружена недооценка актива.")
            else:
                st.success("⚖️ Показатели волатильности в норме.")
                
    with res_col2:
        st.subheader("🔮 Динамика стоимости (Прогноз на 5 лет)")
        years = ["2026", "2027", "2028", "2029", "2030", "2031"]
        prices = [current_price]
        for i in range(1, 6):
            growth = 1.05 + (market_condition - 1.0) * 0.05 
            next_price = prices[-1] * growth + (np.sin(i) * 2000)
            prices.append(max(next_price, 15000.0))
            
        forecast_data = pd.DataFrame({"Год": years, "Прогноз цен ($)": prices})
        st.bar_chart(forecast_data, x="Год", y="Прогноз цен ($)", color="#2e7bcf")
