import streamlit as st
import numpy as np
import pandas as pd
import time
import os
from dotenv import load_dotenv

# 1. ИНИЦИАЛИЗАЦИЯ И СТИЛИЗАЦИЯ ПОД Т-БАНК / WALL STREET
load_dotenv()
SECRET_KEY = os.getenv("STREAMLIT_SECRET_KEY", "default_fallback_key")

st.set_page_config(
    page_title="Blackwood Quantitative Analytics Suite", 
    page_icon="👑", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- МАКСИМАЛЬНАЯ АНОНИМНОСТЬ И ЖЕЛТО-ТЕМНЫЙ СТИЛЬ Т-БАНКА ---
t_bank_style = """
    <style>
    /* Скрываем стандартный мусор Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .viewerBadge_link__1S137 {display: none !important;}
    
    /* Т-Банк кастомизация прогресс-бара и кнопок */
    .stProgress > div > div > div > div {
        background-color: #FFDD2D !important;
    }
    </style>
"""
st.markdown(t_bank_style, unsafe_allow_html=True)

if "last_request_time" not in st.session_state:
    st.session_state.last_request_time = 0.0

def check_rate_limit():
    current_time = time.time()
    if current_time - st.session_state.last_request_time < 0.3:
        st.warning("⚠️ Слишком много запросов! Притормозите.")
        st.stop()
    st.session_state.last_request_time = current_time

# Квантовые модели
def predict_credit(hist, debt):
    score = (hist * 3.5) - (debt * 4.0) + 0.5
    return 1 / (1 + np.exp(-score))

def predict_housing(size, distance):
    base_price = 50000.0 + (size * 1200.0) - (distance * 2000.0)
    return base_price + np.sin(size) * 3000.0


# 2. ДИЗАЙН БОКОВОЙ ПАНЕЛИ TERMINAL CONTROL
with st.sidebar:
    # Логотип в стиле премиального банкинга
    st.markdown("<h2 style='text-align: center; color: #FFDD2D; font-family: monospace; letter-spacing: 1px;'>👑 BLACKWOOD</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #888888; font-size: 11px; margin-top: -15px;'>QUANTITATIVE ANALYTICS SUITE</p>", unsafe_allow_html=True)
    st.write("---")
    
    st.markdown("##### 🌐 РЫНОЧНЫЙ ДЕПАРТАМЕНТ")
    market_condition = st.slider(
        "Индекс волатильности (VIX)", 
        0.5, 1.5, 1.0, 0.1,
        help="Макроэкономическая поправка на системные риски рынка."
    )
    
    st.write("---")
    if SECRET_KEY != "default_fallback_key":
        st.markdown("<p style='color: #FFDD2D; font-size: 13px;'>🔒 <b>ЛИЦЕНЗИЯ:</b> ENTERPRISE TERMINAL</p>", unsafe_allow_html=True)
    else:
        st.markdown("<p style='color: #888888; font-size: 13px;'>🔓 <b>ЛИЦЕНЗИЯ:</b> COMMERCIAL PRIVATE MODE</p>", unsafe_allow_html=True)


# 3. ВЕРХНИЕ ВКЛАДКИ-ТАБЫ (Центральный пульт)
tab1, tab2 = st.tabs(["📊 Скоринг дебиторских рисков", "🏢 Ликвидность и Оценка недвижимости"])


# --- ВКЛАДКА 1: КРЕДИТНЫЙ СКОРИНГ (WALL STREET / Т-БАНК EDITION) ---
with tab1:
    st.markdown("<h2 style='color: #FFDD2D;'>📊 Риск-менеджмент: Анализ андеррайтинга</h2>", unsafe_allow_html=True)
    st.markdown("##### *Скоринговая матрица BQAS на основе взвешенных коэффициентов дефолта*")
    st.write("---")
    
    with st.container(border=True):
        st.markdown("<p style='color: #FFDD2D; font-weight: bold;'>📝 МЕТРИКИ КОНТРАГЕНТА</p>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            hist = st.slider("Внутренний рейтинг скоринга", 0.0, 1.0, 0.7, 0.01, key="credit_hist")
        with col2:
            debt = st.slider("Коэффициент долговой нагрузки (DTI)", 0.0, 1.0, 0.4, 0.01, key="credit_debt")

    check_rate_limit()
    
    with st.spinner("Симуляция Монте-Карло..."):
        time.sleep(0.1)
        prob = (predict_credit(hist, debt) / market_condition) * 100
        prob = min(max(prob, 0.0), 100.0)

    st.write("")
    res_col1, res_col2 = st.columns([1, 1.2])
    
    with res_col1:
        st.markdown("<p style='font-size: 18px; font-weight: bold;'>🎯 КВАНТОВЫЙ ВЕРДИКТ</p>", unsafe_allow_html=True)
        with st.container(border=True):
            st.metric(label="Вероятность исполнения обязательств", value=f"{prob:.2f}%")
            st.progress(int(prob))
            st.write("")
            if prob >= 50.0:
                st.success("🟡 **СТАТУС: АКТИВ ОДОБРЕН** \n\nРекомендация: Включить в инвестиционный портфель.")
            else:
                st.error("🚨 **СТАТУС: ЛИКВИДАЦИОННЫЙ РИСК** \n\nРекомендация: Немедленный отказ (Шорт-позиция).")
                
    with res_col2:
        st.markdown("<p style='font-size: 18px; font-weight: bold;'>📈 СТРЕСС-ТЕСТИРОВАНИЕ РЕЙТИНГА</p>", unsafe_allow_html=True)
        x_range = np.linspace(0.0, 1.0, 50)
        y_range = [min(max((predict_credit(x, debt) / market_condition) * 100, 0.0), 100.0) for x in x_range]
        chart_data = pd.DataFrame({"Внутренний рейтинг": x_range, "Надежность %": y_range})
        # Желтый фирменный график Т-Банка
        st.line_chart(chart_data, x="Внутренний рейтинг", y="Надежность %", color="#FFDD2D")


# --- ВКЛАДКА 2: НЕДВИЖИМОСТЬ ---
with tab2:
    st.markdown("<h2 style='color: #FFDD2D;'>🏢 Оценка и Анализ Реальных Активов</h2>", unsafe_allow_html=True)
    st.markdown("##### *Предиктивная оценка залоговой стоимости имущества*")
    st.write("---")
    
    with st.container(border=True):
        st.markdown("<p style='color: #FFDD2D; font-weight: bold;'>📐 ПАРАМЕТРЫ ОБЪЕКТА ЗАЛОГА</p>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            size_input = st.slider("Полезная площадь (sq. m.)", 30, 150, 70, 1, key="house_size")
        with col2:
            dist_input = st.slider("Дистанция до Центрального Хаба (км)", 1, 20, 5, 1, key="house_dist")

    check_rate_limit()
    
    with st.spinner("Расчет индекса ликвидности..."):
        time.sleep(0.1)
        current_price = max(predict_housing(size_input, dist_input) * market_condition, 15000.0)

    st.write("")
    res_col1, res_col2 = st.columns([1, 1.2])
    
    with res_col1:
        st.markdown("<p style='font-size: 18px; font-weight: bold;'>💰 СПРАВЕДЛИВАЯ СТОИМОСТЬ</p>", unsafe_allow_html=True)
        with st.container(border=True):
            st.metric(label="Fair Market Value (FMV)", value=f"${current_price:,.2f}")
            st.write("---")
            st.write("📋 **Внутренний аудит Департамента:**")
            st.write(f"• Оценка кв. метра: **${(current_price/size_input):.2f}**")
            st.write(f"• Премия за локацию: **{-dist_input * 2000:+,}** к базовой ставке")
            
            if market_condition > 1.2:
                st.warning("⚠️ Внимание: Локальный пузырь недвижимости.")
            elif market_condition < 0.8:
                st.info("📉 Сигнал: Актив торгуется с дисконтом. Рекомендован выкуп.")
            else:
                st.success("⚖️ Ценовые девиации отсутствуют.")
                
    with res_col2:
        st.markdown("<p style='font-size: 18px; font-weight: bold;'>🔮 ПРОГНОЗ ТРЕНДА ЦЕНЫ (5Y FORECAST)</p>", unsafe_allow_html=True)
        years = ["2026", "2027", "2028", "2029", "2030", "2031"]
        prices = [current_price]
        for i in range(1, 6):
            growth = 1.05 + (market_condition - 1.0) * 0.05 
            next_price = prices[-1] * growth + (np.sin(i) * 2000)
            prices.append(max(next_price, 15000.0))
            
        forecast_data = pd.DataFrame({"Год": years, "Прогноз цен ($)": prices})
        # Желто-золотой график распределения цены
        st.bar_chart(forecast_data, x="Год", y="Прогноз цен ($)", color="#FFDD2D")
