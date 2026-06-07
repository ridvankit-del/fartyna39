import streamlit as st
import numpy as np
import time
import os
from dotenv import load_dotenv

load_dotenv()
SECRET_KEY = os.getenv("STREAMLIT_SECRET_KEY", "default_fallback_key")

st.set_page_config(page_title="Secure AI Suite", page_icon="🛡️", layout="wide")

if "last_request_time" not in st.session_state:
    st.session_state.last_request_time = 0.0

def check_rate_limit():
    current_time = time.time()
    if current_time - st.session_state.last_request_time < 0.3:
        st.warning("⚠️ Слишком много запросов!")
        st.stop()
    st.session_state.last_request_time = current_time

st.sidebar.title("🛡️ Secure AI Control")
app_mode = st.sidebar.selectbox("Выберите задачу:", ["🏦 Кредитный Скоринг", "🏡 Оценка недвижимости"])
market_condition = st.sidebar.slider("Экономическая ситуация", 0.5, 1.5, 1.0, 0.1)

if SECRET_KEY != "default_fallback_key":
    st.sidebar.success("🔑 Ключ активирован")

if app_mode == "🏦 Кредитный Скоринг":
    st.title("🏦 Безопасный Кредитный Скоринг")
    hist = st.slider("Кредитный рейтинг", 0.0, 1.0, 0.7, 0.01)
    debt = st.slider("Уровень долга", 0.0, 1.0, 0.4, 0.01)
    
    check_rate_limit()
    score = (hist * 3.5) - (debt * 4.0) + 0.5
    prob = 1 / (1 + np.exp(-score))
    prob = prob / market_condition
    
    st.metric(label="Шанс одобрения", value=f"{min(max(prob*100, 0.0), 100.0):.2f}%")
    if prob >= 0.5:
        st.success("🤖 Робот: ОДОБРЕНО")
    else:
        st.error("🤖 Робот: ОТКАЗ")

elif app_mode == "🏡 Оценка недвижимости":
    st.title("🏡 Оценщик Недвижимости")
    size_input = st.slider("Площадь квартиры (кв. м.)", 30, 150, 70, 1)
    dist_input = st.slider("Расстояние до центра (км)", 1, 20, 5, 1)
    
    check_rate_limit()
    base_price = 50000.0 + (size_input * 1200.0) - (dist_input * 2000.0)
    final_price = (base_price + np.sin(size_input) * 3000.0) * market_condition
    
    st.markdown("---")
    st.metric(label="Прогнозная цена объекта", value=f"${max(final_price, 15000.0):,.2f}")
