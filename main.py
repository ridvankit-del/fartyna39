import streamlit as st
import tensorflow as tf
import numpy as np
import matplotlib.pyplot as plt
import time
import os
from dotenv import load_dotenv

# Загружаем переменные безопасности
load_dotenv()
SECRET_KEY = os.getenv("STREAMLIT_SECRET_KEY", "default_fallback_key")

st.set_page_config(page_title="Secure AI Suite v2.1", page_icon="🛡️", layout="wide")

# --- ЗАЩИТА: Rate Limiting ---
if "last_request_time" not in st.session_state:
    st.session_state.last_request_time = 0.0


def check_rate_limit():
    current_time = time.time()
    if current_time - st.session_state.last_request_time < 0.3:
        st.warning("⚠️ Слишком много запросов! Пожалуйста, подождите.")
        st.stop()
    st.session_state.last_request_time = current_time


# --- ПАНЕЛЬ УПРАВЛЕНИЯ ---
st.sidebar.title("🛡️ Secure AI Control")
app_mode = st.sidebar.selectbox("Выберите задачу:", ["🏦 Кредитный Скоринг v2.0", "🏡 Оценка недвижимости (Исправлено)"])
market_condition = st.sidebar.slider("Экономическая ситуация", 0.5, 1.5, 1.0, 0.1)

if SECRET_KEY != "default_fallback_key":
    st.sidebar.success("🔑 Ключ безопасности активирован")


# --- МОДЕЛИ ИИ (КЭШИРОВАНИЕ И СТАБИЛИЗАЦИЯ) ---
@st.cache_resource
def train_credit_model():
    np.random.seed(42)
    X = np.random.rand(400, 2)
    y = np.zeros((400, 1))
    for i in range(400):
        if X[i, 0] > 0.4 and X[i, 1] < 0.7: y[i] = 1.0
    model = tf.keras.Sequential([
        tf.keras.layers.Dense(16, input_shape=[2], activation='relu'),
        tf.keras.layers.Dense(1, activation='sigmoid')
    ])
    model.compile(optimizer='adam', loss='binary_crossentropy')
    model.fit(X, y, epochs=120, verbose=0)
    return model, X, y


@st.cache_resource
def train_housing_model():
    np.random.seed(42)
    # Генерируем данные
    size = np.random.uniform(30, 150, (500, 1))
    distance = np.random.uniform(1, 20, (500, 1))
    X = np.hstack((size, distance))

    # Формула цены: База $50 000 + $1200 за кв.м - $2000 за км от центра
    y = 50000 + (size * 1200) - (distance * 2000) + np.random.normal(0, 5000, (500, 1))

    # Чтобы сеть не ломалась от больших чисел (площадь 150 и цена 200000),
    # используем слой нормализации прямо внутри Keras
    normalizer = tf.keras.layers.Normalization(axis=-1)
    normalizer.adapt(X)

    model = tf.keras.Sequential([
        normalizer,
        tf.keras.layers.Dense(32, activation='relu'),
        tf.keras.layers.Dense(16, activation='relu'),
        tf.keras.layers.Dense(1)  # Выход без активации для точной цены
    ])
    model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=0.05), loss='mse')
    model.fit(X, y, epochs=150, verbose=0)
    return model, X, y


# --- ЛОГИКА РЕЖИМОВ ---
if app_mode == "🏦 Кредитный Скоринг v2.0":
    st.title("🏦 Безопасный Кредитный Скоринг")

    col1, col2 = st.columns(2)
    with col1:
        hist = st.slider("Кредитный рейтинг", 0.0, 1.0, 0.7, 0.01)
    with col2:
        debt = st.slider("Уровень долга", 0.0, 1.0, 0.4, 0.01)

    check_rate_limit()
    model, X, y = train_credit_model()
    prob = model.predict(np.array([[hist, debt]], dtype=float))[0][0] / market_condition

    st.metric(label="Шанс одобрения", value=f"{min(max(prob * 100, 0.0), 100.0):.2f}%")
    if prob >= 0.5:
        st.success("🤖 Робот: ОДОБРЕНО")
    else:
        st.error("🤖 Робот: ОТКАЗ")

elif app_mode == "🏡 Оценка недвижимости (Исправлено)":
    st.title("🏡 Исправленный Оценщик Недвижимости")

    col1, col2 = st.columns(2)
    with col1:
        size_input = st.slider("Площадь квартиры (кв. м.)", 30, 150, 70, 1)
    with col2:
        dist_input = st.slider("Расстояние до центра (км)", 1, 20, 5, 1)

    check_rate_limit()
    model, X, y = train_housing_model()

    # Предсказание ИИ
    raw_price = model.predict(np.array([[size_input, dist_input]], dtype=float))[0][0]
    # Применяем рыночный коэффициент
    final_price = raw_price * market_condition

    st.markdown("---")
    st.subheader("💰 Расчетная Стоимость от ИИ")
    st.metric(label="Прогнозная цена объекта", value=f"${max(final_price, 15000.0):,.2f}")
    st.info(f"Коэффициент макроэкономики: {market_condition}x")