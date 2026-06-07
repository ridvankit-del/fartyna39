import streamlit as st
import numpy as np
import time
import os
from dotenv import load_dotenv

load_dotenv()
SECRET_KEY = os.getenv("STREAMLIT_SECRET_KEY", "default_fallback_key")

st.set_page_config(page_title="Secure AI Suite v3.0", page_icon="🛡️", layout="wide")

if "last_request_time" not in st.session_state:
    st.session_state.last_request_time = 0.0

def check_rate_limit():
    current_time = time.time()
    if current_time - st.session_state.last_request_time < 0.3:
        st.warning("⚠️ Слишком много запросов! Пожалуйста, подождите.")
        st.stop()
    st.session_state.last_request_time = current_time

st.sidebar.title("🛡️ Secure AI Control")
app_mode = st.sidebar.selectbox("Выберите задачу:", ["🏦 Кредитный Скоринг v2.0", "🏡 Оценка недвижимости"])
market_condition = st.sidebar.slider("Экономическая ситуация", 0.5, 1.5, 1.0, 0.1)

if SECRET_KEY != "default_fallback_key":
    st.sidebar.success("🔑 Ключ безопасности активирован")

def predict_credit(hist, debt):
    score = (hist * 3.5) - (debt * 4.0) + 0.5
    prob = 1 / (1 + np.exp(-score))
    return prob

def predict_housing(size, distance):
    base_price = 50000.0 + (size * 1200.0) - (distance * 2000.0)
    noise = np.sin(size) * 3000.0
    return base_price + noise

if app_mode == "🏦 Кредитный Скоринг v2.0":
    st.title("🏦 Безопасный Кредитный Скоринг")
    col1, col2 = st.columns(2)
    with col1: hist = st.slider("Кредитный рейтинг", 0.0, 1.0, 0.7, 0.01)
    with col2: debt = st.slider("Уровень долга", 0.0, 1.0, 0.4, 0.01)
    
    check_rate_limit()
    prob = predict_credit(hist, debt) / market_condition
    
    st.metric(label="Шанс одобрения", value=f"{min(max(prob*100, 0.0), 100.0):.2f}%")
    if prob >= 0.5: st.success("🤖 Робот: ОДОБРЕНО")
    else: st.error("🤖 Робот: ОТКАЗ")

elif app_mode == "🏡 Оценка недвижимости":
    st.title("🏡 Исправленный Оценщик Недвижимости")
    col1, col2 = st.columns(2)
    with col1: size_input = st.slider("Площадь квартиры (кв. м.)", 30, 150, 70, 1)
    with col2: dist_input = st.slider("Расстояние до центра (км)", 1, 20, 5, 1)
    
    check_rate_limit()
    raw_price = predict_housing(size_input, dist_input)
    final_price = raw_price * market_condition
    
    st.markdown("---")
    st.subheader("💰 Расчетная Стоимость от ИИ")
    st.metric(label="Прогнозная цена объекта", value=f"${max(final_price, 15000.0):,.2f}")    if prob >= 0.5: st.success("🤖 Робот: ОДОБРЕНО")
    else: st.error("🤖 Робот: ОТКАЗ")

elif app_mode == "🏡 Оценка недвижимости (Исправлено)":
    st.title("🏡 Исправленный Оценщик Недвижимости")
    
    col1, col2 = st.columns(2)
    with col1: size_input = st.slider("Площадь квартиры (кв. м.)", 30, 150, 70, 1)
    with col2: dist_input = st.slider("Расстояние до центра (км)", 1, 20, 5, 1)
    
    check_rate_limit()
    
    # Считаем цену без TensorFlow
    raw_price = predict_housing(size_input, dist_input)
    final_price = raw_price * market_condition
    
    st.markdown("---")
    st.subheader("💰 Расчетная Стоимость от ИИ")
    st.metric(label="Прогнозная цена объекта", value=f"${max(final_price, 15000.0):,.2f}")
    st.info(f"Коэффициент макроэкономики: {market_condition}x")
