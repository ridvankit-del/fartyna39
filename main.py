import streamlit as st
import numpy as np
import pandas as pd
import time
import os
from dotenv import load_dotenv

# 1. ИНИЦИАЛИЗАЦИЯ
load_dotenv()
SECRET_KEY = os.getenv("STREAMLIT_SECRET_KEY", "default_fallback_key")

st.set_page_config(
    page_title="Blackwood Quantitative Analytics Suite", 
    page_icon="👑", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- PREMIUM INVESTMENT TERMINAL VISUAL STYLE (T-BANK / WALL STREET) ---
premium_style = """
    <style>
    /* Отключаем элементы брендинга Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .viewerBadge_link__1S137 {display: none !important;}
    
    /* Стилизация главного фона и шрифтов */
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #0B0B0C !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }
    
    /* Эстетичные карточки с эффектом Glassmorphism */
    [data-testid="stMetric"] {
        background-color: #141416 !important;
        border: 1px solid #232326 !important;
        padding: 20px !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2) !important;
    }
    
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #141416 !important;
        border: 1px solid #232326 !important;
        border-radius: 16px !important;
        padding: 25px !important;
        margin-bottom: 20px !important;
    }
    
    /* Кастомизация сайдбара */
    [data-testid="stSidebar"] {
        background-color: #0E0E10 !important;
        border-right: 1px solid #232326 !important;
    }
    
    /* Фирменный Т-Желтый прогресс-бар */
    .stProgress > div > div > div > div {
        background-color: #FFDD2D !important;
        border-radius: 4px !important;
    }
    
    /* Стилизация вкладок (Tabs) */
    button[data-baseweb="tab"] {
        color: #888888 !important;
        font-size: 16px !important;
        font-weight: 500 !important;
        border: none !important;
        transition: all 0.3s ease !important;
    }
    button[data-baseweb="tab"]:hover {
        color: #FFDD2D !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #FFDD2D !important;
        border-bottom: 2px solid #FFDD2D !important;
    }
    
    /* Тонкая настройка шрифтов заголовков */
    h1, h2, h3 {
        font-weight: 600 !important;
        letter-spacing: -0.5px !important;
    }
    </style>
"""
st.markdown(premium_style, unsafe_allow_html=True)

if "last_request_time" not in st.session_state:
    st.session_state.last_request_time = 0.0

def check_rate_limit():
    current_time = time.time()
    if current_time - st.session_state.last_request_time < 0.3:
        st.warning("⚠️ Слишком много запросов! Притормозите.")
        st.stop()
    st.session_state.last_request_time = current_time

# Математическое ядро терминала
def predict_credit(hist, debt):
    score = (hist * 3.5) - (debt * 4.0) + 0.5
    return 1 / (1 + np.exp(-score))

def predict_housing(size, distance):
    base_price = 50000.0 + (size * 1200.0) - (distance * 2000.0)
    return base_price + np.sin(size) * 3000.0


# 2. БОКОВОЙ ТЕРМИНАЛ (CONTROL PANEL)
with st.sidebar:
    st.write("")
    st.markdown("<h2 style='text-align: center; color: #FFDD2D; font-family: monospace; letter-spacing: 3px; font-size: 24px; margin-bottom: 0px;'>BLACKWOOD</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #555559; font-size: 10px; letter-spacing: 1px; margin-top: 2px;'>QUANTITATIVE ANALYTICS</p>", unsafe_allow_html=True)
    st.write("---")
    
    st.markdown("<p style='color: #888888; font-size: 12px; font-weight: bold; letter-spacing: 1px;'>GLOBAL MARKET RISK</p>", unsafe_allow_html=True)
    market_condition = st.slider(
        "Индекс волатильности (VIX)", 
        0.5, 1.5, 1.0, 0.1,
        label_visibility="collapsed",
        help="Макроэкономическая коррекция на системные риски рынка."
    )
    
    st.write("---")
    if SECRET_KEY != "default_fallback_key":
        st.markdown("<p style='color: #FFDD2D; font-size: 12px; letter-spacing: 0.5px;'>🔒 <b>STATUS:</b> ENTERPRISE NODE</p>", unsafe_allow_html=True)
    else:
        st.markdown("<p style='color: #555559; font-size: 12px; letter-spacing: 0.5px;'>🔓 <b>STATUS:</b> PRIVATE COMMERCIAL</p>", unsafe_allow_html=True)


# 3. ЦЕНТРАЛЬНЫЙ ПУЛЬТ (ВКЛАДКИ)
tab1, tab2 = st.tabs(["🏦 Кредитный риск-менеджмент", "🏢 Оценка материальных активов"])


# --- ВКЛАДКА 1: КРЕДИТНЫЙ СКОРИНГ ---
with tab1:
    st.write("")
    st.markdown("<h2 style='color: #FFF; font-size: 28px; margin-bottom: 5px;'>Риск-менеджмент: Верификация дебиторов</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: #666; font-size: 14px;'>Мгновенный предиктивный скоринг контрагентов на базе скоринговых матриц Blackwood</p>", unsafe_allow_html=True)
    st.write("")
    
    with st.container(border=True):
        st.markdown("<p style='color: #FFDD2D; font-size: 13px; font-weight: bold; letter-spacing: 1px; margin-bottom: 15px;'>ВВОДНЫЕ ПАРАМЕТРЫ ЗАЁМЩИКА</p>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            st.caption("Внутренний кредитный рейтинг")
            hist = st.slider("Кредитный рейтинг", 0.0, 1.0, 0.7, 0.01, key="credit_hist", label_visibility="collapsed")
        with col2:
            st.caption("Показатель долговой нагрузки (DTI)")
            debt = st.slider("Долговая нагрузка", 0.0, 1.0, 0.4, 0.01, key="credit_debt", label_visibility="collapsed")

    check_rate_limit()
    
    with st.spinner("Расчет вектора дефолта..."):
        time.sleep(0.1)
        prob = (predict_credit(hist, debt) / market_condition) * 100
        prob = min(max(prob, 0.0), 100.0)

    st.write("")
    res_col1, res_col2 = st.columns([1, 1.3])
    
    with res_col1:
        st.markdown("<p style='font-size: 14px; font-weight: bold; color: #888; letter-spacing: 0.5px;'>АНАЛИТИЧЕСКИЙ ВЕРДИКТ</p>", unsafe_allow_html=True)
        with st.container(border=True):
            st.metric(label="Индекс финансовой надежности", value=f"{prob:.2f}%")
            st.write("")
            st.progress(int(prob))
            st.write("")
            if prob >= 50.0:
                st.markdown("<div style='background-color: rgba(0, 244, 180, 0.1); border: 1px solid #00f4b4; padding: 15px; border-radius: 8px; color: #00f4b4; font-size: 14px;'><b>АКТИВ ОДОБРЕН</b><br>Низкая вероятность дефолта. Риски верифицированы.</div>", unsafe_allow_html=True)
            else:
                st.markdown("<div style='background-color: rgba(255, 75, 75, 0.1); border: 1px solid #ff4b4b; padding: 15px; border-radius: 8px; color: #ff4b4b; font-size: 14px;'><b>ЛИКВИДАЦИОННЫЙ РИСК</b><br>Высокая долговая нагрузка. Операция заблокирована.</div>", unsafe_allow_html=True)
                
    with res_col2:
        st.markdown("<p style='font-size: 14px; font-weight: bold; color: #888; letter-spacing: 0.5px;'>МОДЕЛИРОВАНИЕ СТРЕСС-ТЕСТА</p>", unsafe_allow_html=True)
        x_range = np.linspace(0.0, 1.0, 50)
        y_range = [min(max((predict_credit(x, debt) / market_condition) * 100, 0.0), 100.0) for x in x_range]
        chart_data = pd.DataFrame({"Рейтинг контрагента": x_range, "Надежность %": y_range})
        st.line_chart(chart_data, x="Рейтинг контрагента", y="Надежность %", color="#FFDD2D")


# --- ВКЛАДКА 2: НЕДВИЖИМОСТЬ ---
with tab2:
    st.write("")
    st.markdown("<h2 style='color: #FFF; font-size: 28px; margin-bottom: 5px;'>Аналитика реальных активов: Оценка FMV</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: #666; font-size: 14px;'>Автоматический андеррайтинг залогового имущества и расчет долгосрочных ценовых трендов</p>", unsafe_allow_html=True)
    st.write("")
    
    with st.container(border=True):
        st.markdown("<p style='color: #FFDD2D; font-size: 13px; font-weight: bold; letter-spacing: 1px; margin-bottom: 15px;'>СПЕЦИФИКАЦИЯ ОБЪЕКТА ОБЕСПЕЧЕНИЯ</p>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            st.caption("Полезная внутренняя площадь (кв. м.)")
            size_input = st.slider("Площадь", 30, 150, 70, 1, key="house_size", label_visibility="collapsed")
        with col2:
            st.caption("Удаленность от центрального финансового хаба (км)")
            dist_input = st.slider("Удаленность", 1, 20, 5, 1, key="house_dist", label_visibility="collapsed")

    check_rate_limit()
    
    with st.spinner("Сканирование закрытых сделок..."):
        time.sleep(0.1)
        current_price = max(predict_housing(size_input, dist_input) * market_condition, 15000.0)

    st.write("")
    res_col1, res_col2 = st.columns([1, 1.3])
    
    with res_col1:
        st.markdown("<p style='font-size: 14px; font-weight: bold; color: #888; letter-spacing: 0.5px;'>РАСЧЕТ СТОИМОСТИ</p>", unsafe_allow_html=True)
        with st.container(border=True):
            st.metric(label="Fair Market Value (Справедливая цена)", value=f"${current_price:,.2f}")
            st.write("---")
            st.markdown("<p style='font-size: 12px; color: #AAA; font-weight: bold;'>АУДИТОРСКИЙ ОТЧЕТ</p>", unsafe_allow_html=True)
            st.write(f"• Интегральная цена кв. м: **${(current_price/size_input):.2f}**")
            st.write(f"• Влияние геолокации: **{-dist_input * 2000:+,}** к базовому пулу")
            st.write("")
            
            if market_condition > 1.2:
                st.markdown("<div style='color: #ff9800; font-size: 13px;'>⚠️ <b>Внимание:</b> Модель фиксирует локальный перегрев сектора.</div>", unsafe_allow_html=True)
            elif market_condition < 0.8:
                st.markdown("<div style='color: #00f4b4; font-size: 13px;'>📉 <b>Сигнал:</b> Обнаружен дисконт. Актив рекомендован к выкупу.</div>", unsafe_allow_html=True)
            else:
                st.markdown("<div style='color: #888; font-size: 13px;'>⚖️ Девиации рынка находятся в пределах волатильности.</div>", unsafe_allow_html=True)
                
    with res_col2:
        st.markdown("<p style='font-size: 14px; font-weight: bold; color: #888; letter-spacing: 0.5px;'>ИНВЕСТИЦИОННЫЙ ЦЕНОВОЙ ТРЕНД (5Y FORECAST)</p>", unsafe_allow_html=True)
        years = ["2026", "2027", "2028", "2029", "2030", "2031"]
        prices = [current_price]
        for i in range(1, 6):
            growth = 1.05 + (market_condition - 1.0) * 0.05 
            next_price = prices[-1] * growth + (np.sin(i) * 2000)
            prices.append(max(next_price, 15000.0))
            
        forecast_data = pd.DataFrame({"Год": years, "Прогноз цен ($)": prices})
        st.bar_chart(forecast_data, x="Год", y="Прогноз цен ($)", color="#FFDD2D")
