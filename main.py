import streamlit as st
import numpy as np
import pandas as pd
import time
import os
from dotenv import load_dotenv

# 1. ИНИЦИАЛИЗАЦИЯ И СТИЛИЗАЦИЯ
load_dotenv()
SECRET_KEY = os.getenv("STREAMLIT_SECRET_KEY", "default_fallback_key")

# Устанавливаем темную/светлую тему по умолчанию и красивый заголовок в табе браузера
st.set_page_config(
    page_title="AI Analytics Premium Suite", 
    page_icon="🛡️", 
    layout="wide",
    initial_sidebar_state="expanded"
)

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


# 2. ДИЗАЙН БОКОВОЙ ПАНЕЛИ
with st.sidebar:
    st.markup("<h2 style='text-align: center; color: #ff4b4b;'>🎮 CONTROL PANEL</h2>", unsafe_allow_html=True)
    st.write("---")
    
    app_mode = st.selectbox(
        "🔮 Аналитический модуль:", 
        ["🏦 Кредитный Скоринг Premium", "🏡 Оценка и Прогноз Недвижимости"]
    )
    
    st.write("---")
    st.subheader("🌐 Макроэкономика")
    market_condition = st.slider(
        "Рыночный коэффициент", 
        0.5, 1.5, 1.0, 0.1,
        help="Влияние инфляции и кризисов на итоговые вычисления нейросети."
    )
    
    st.write("---")
    if SECRET_KEY != "default_fallback_key":
        st.info("🔐 **Лицензия:** Enterprise AI Activated")
    else:
        st.warning("🔓 **Лицензия:** Демо-режим (Пулл ключей пуст)")


# 3. ЛОГИКА И ДИЗАЙН ОСНОВНЫХ СТРАНИЦ

# --- ДИЗАЙН: КРЕДИТНЫЙ СКОРИНГ ---
if app_mode == "🏦 Кредитный Скоринг Premium":
    st.title("🏦 Интеллектуальный Кредитный Скоринг")
    st.markdown("##### *Система автоматического скоринга контрагентов на базе скоринговых матриц*")
    st.write("---")
    
    # Визуальный контейнер для формы ввода
    with st.container(border=True):
        st.subheader("📋 Профиль заёмщика")
        col1, col2 = st.columns(2)
        with col1:
            hist = st.slider("Кредитный рейтинг", 0.0, 1.0, 0.7, 0.01, help="1.0 — идеальная история без просрочек, 0.0 — дефолт.")
        with col2:
            debt = st.slider("Уровень долговой нагрузки", 0.0, 1.0, 0.4, 0.01, help="Соотношение платежей по кредитам к ежемесячному доходу.")

    check_rate_limit()
    
    # Эффект "ИИ думает"
    with st.spinner("Нейросеть обрабатывает транзакции..."):
        time.sleep(0.1) # Микро-задержка для симуляции вычислений
        prob = (predict_credit(hist, debt) / market_condition) * 100
        prob = min(max(prob, 0.0), 100.0)

    st.write("")
    
    # Разделяем результаты на красивую карточку вердикта и аналитический график
    res_col1, res_col2 = st.columns([1, 1.2])
    
    with res_col1:
        st.subheader("🎯 Результат скоринга")
        with st.container(border=True):
            st.metric(label="Вероятность возврата кредита", value=f"{prob:.2f}%")
            
            # Индикатор в виде прогресс-бара
            st.progress(int(prob))
            
            st.write("")
            if prob >= 50.0:
                st.success("✅ **РЕШЕНИЕ: ОДОБРЕНО** \n\nКлиент благонадёжен. Риски в пределах нормы.")
            else:
                st.error("❌ **РЕШЕНИЕ: ОТКАЗ** \n\nСлишком высокий риск невозврата средств.")
                
    with res_col2:
        st.subheader("📊 Стресс-тестирование рейтинга")
        x_range = np.linspace(0.0, 1.0, 50)
        y_range = [min(max((predict_credit(x, debt) / market_condition) * 100, 0.0), 100.0) for x in x_range]
        chart_data = pd.DataFrame({"Рейтинг": x_range, "Шанс одобрения %": y_range})
        
        # Строим красивый график
        st.line_chart(chart_data, x="Рейтинг", y="Шанс одобрения %", color="#ff4b4b")


# --- ДИЗАЙН: НЕДВИЖИМОСТЬ ---
elif app_mode == "🏡 Оценка и Прогноз Недвижимости":
    st.title("🏡 ИИ-Оценщик & Предиктор Стоимости")
    st.markdown("##### *Автоматическая оценка ликвидационной стоимости жилья и симуляция изменения тренда*")
    st.write("---")
    
    with st.container(border=True):
        st.subheader("📊 Технические характеристики объекта")
        col1, col2 = st.columns(2)
        with col1:
            size_input = st.slider("Площадь жилья (кв. м.)", 30, 150, 70, 1)
        with col2:
            dist_input = st.slider("Удаленность от центра города (км)", 1, 20, 5, 1)

    check_rate_limit()
    
    with st.spinner("Анализ сделок в выбранном радиусе..."):
        time.sleep(0.1)
        current_price = max(predict_housing(size_input, dist_input) * market_condition, 15000.0)

    st.write("")
    res_col1, res_col2 = st.columns([1, 1.2])
    
    with res_col1:
        st.subheader("💰 Рыночная оценка")
        with st.container(border=True):
            st.metric(label="Текущая справедливая цена", value=f"${current_price:,.2f}")
            st.write("---")
            st.write("📋 **Экспертная сводка:**")
            st.write(f"• Средняя цена кв. метра: **${(current_price/size_input):.2f}**")
            st.write(f"• Коэффициент локации: **{-dist_input * 2000:+,}** к базовой стоимости")
            
            if market_condition > 1.2:
                st.warning("🔥 Рынок перегрет. Возможна ценовая коррекция.")
            elif market_condition < 0.8:
                st.info("📉 Рынок недооценен. Идеальное время для покупки.")
            else:
                st.success("⚖️ Рыночный баланс стабилен.")
                
    with res_col2:
        st.subheader("🔮 Инвестиционный прогноз на 5 лет")
        years = ["2026", "2027", "2028", "2029", "2030", "2031"]
        prices = [current_price]
        for i in range(1, 6):
            growth = 1.05 + (market_condition - 1.0) * 0.05 
            next_price = prices[-1] * growth + (np.sin(i) * 2000)
            prices.append(max(next_price, 15000.0))
            
        forecast_data = pd.DataFrame({"Год": years, "Прогноз цены ($)": prices})
        
        # Интерактивный Bar Chart
        st.bar_chart(forecast_data, x="Год", y="Прогноз цены ($)", color="#2e7bcf")            
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
