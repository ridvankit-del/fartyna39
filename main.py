import streamlit as st
import numpy as np
import pandas as pd
import time
import os
from dotenv import load_dotenv

# 1. ИНИЦИАЛИЗАЦИЯ И ЗАЩИТА
load_dotenv()
SECRET_KEY = os.getenv("STREAMLIT_SECRET_KEY", "default_fallback_key")

st.set_page_config(page_title="Advanced AI Analytics Suite", page_icon="🚀", layout="wide")

if "last_request_time" not in st.session_state:
    st.session_state.last_request_time = 0.0

def check_rate_limit():
    current_time = time.time()
    if current_time - st.session_state.last_request_time < 0.3:
        st.warning("⚠️ Слишком много запросов! Притормозите.")
        st.stop()
    st.session_state.last_request_time = current_time

# 2. БОКОВАЯ ПАНЕЛЬ
st.sidebar.title("🎮 Настройки Системы")
app_mode = st.sidebar.selectbox("Выберите аналитический модуль:", ["🏦 Кредитный Скоринг v4.0", "🏡 Оценка и Прогноз Недвижимости"])
market_condition = st.sidebar.slider("Рыночный коэффициент (Макроэкономика)", 0.5, 1.5, 1.0, 0.1)

if SECRET_KEY != "default_fallback_key":
    st.sidebar.success("🔑 Лицензия ИИ активирована")

# Math Магия (Замена TensorFlow)
def predict_credit(hist, debt):
    score = (hist * 3.5) - (debt * 4.0) + 0.5
    return 1 / (1 + np.exp(-score))

def predict_housing(size, distance):
    base_price = 50000.0 + (size * 1200.0) - (distance * 2000.0)
    return base_price + np.sin(size) * 3000.0

# 3. ЛОГИКА МОДУЛЕЙ

# --- МОДУЛЬ 1: КРЕДИТНЫЙ СКОРИНГ ---
if app_mode == "🏦 Кредитный Скоринг v4.0":
    st.title("🏦 Интеллектуальный Кредитный Скоринг")
    st.caption("Анализ платежеспособности кандидата на основе математической модели ИИ")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📝 Вводные данные")
        hist = st.slider("Кредитный рейтинг пользователя", 0.0, 1.0, 0.7, 0.01)
        debt = st.slider("Текущий уровень долга", 0.0, 1.0, 0.4, 0.01)
        
        check_rate_limit()
        prob = (predict_credit(hist, debt) / market_condition) * 100
        prob = min(max(prob, 0.0), 100.0)
        
        st.markdown("---")
        st.metric(label="Рассчитанная вероятность одобрения", value=f"{prob:.2f}%")
        if prob >= 50.0:
            st.success("🤖 Вердикт ИИ: ОДОБРИТЬ КРЕДИТ")
        else:
            st.error("🤖 Вердикт ИИ: ОТКЛОНИТЬ ЗАЯВКУ")
            
    with col2:
        st.subheader("📊 График зависимости скоринга")
        # Генерируем данные для графика симуляции
        x_range = np.linspace(0.0, 1.0, 50)
        y_range = [min(max((predict_credit(x, debt) / market_condition) * 100, 0.0), 100.0) for x in x_range]
        
        chart_data = pd.DataFrame({"Рейтинг (Ось X)": x_range, "Шанс одобрения % (Ось Y)": y_range})
        st.line_chart(chart_data, x="Рейтинг (Ось X)", y="Шанс одобрения % (Ось Y)", color="#ff4b4b")
        st.info("💡 График показывает, как рос бы шанс одобрения при твоём текущем уровне долга, если бы ты поднимал кредитный рейтинг.")

# --- МОДУЛЬ 2: НЕДВИЖИМОСТЬ ---
elif app_mode == "🏡 Оценка и Прогноз Недвижимости":
    st.title("🏡 ИИ-Оценщик & Предиктор Стоимости")
    st.caption("Анализ стоимости жилья и симуляция изменения цены на 5 лет вперёд")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📍 Параметры объекта")
        size_input = st.slider("Площадь объекта (кв. м.)", 30, 150, 70, 1)
        dist_input = st.slider("Удаленность от центра (км)", 1, 20, 5, 1)
        
        check_rate_limit()
        current_price = max(predict_housing(size_input, dist_input) * market_condition, 15000.0)
        
        st.markdown("---")
        st.metric(label="Текущая рыночная стоимость", value=f"${current_price:,.2f}")
        
    with col2:
        st.subheader("🔮 Прогноз стоимости на 5 лет ($)")
        # Имитируем прогноз тренда цен на 5 лет вперед с учетом макроэкономики
        years = ["2026 (Сейчас)", "2027", "2028", "2029", "2030", "2031"]
        prices = [current_price]
        for i in range(1, 6):
            # Цена растет на стабильный процент + случайное влияние рынка
            growth = 1.05 + (market_condition - 1.0) * 0.05 
            next_price = prices[-1] * growth + (np.sin(i) * 2000)
            prices.append(max(next_price, 15000.0))
            
        forecast_data = pd.DataFrame({"Год": years, "Прогноз цены": prices})
        st.bar_chart(forecast_data, x="Год", y="Прогноз цены", color="#00f4b4")
        st.info("📈 Инвестиционный прогноз: Стоимость рассчитана с учётом заложенных макроэкономических рисков.")
