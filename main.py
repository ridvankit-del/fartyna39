import streamlit as st
import numpy as np
import pandas as pd
import time
import os
from dotenv import load_dotenv

# 1. ИНИЦИАЛИЗАЦИЯ И ПОЛНАЯ ПЕРЕЗАПИСЬ СТИЛЕЙ
load_dotenv()
SECRET_KEY = os.getenv("STREAMLIT_SECRET_KEY", "default_fallback_key")

st.set_page_config(
    page_title="Blackwood Terminal v5.0", 
    page_icon="👑", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ADVANCED CUSTOM UI ENHANCEMENT (THEME OVERRIDE) ---
custom_dark_theme = """
    <style>
    /* Отсекаем технические оверлеи */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .viewerBadge_link__1S137 {display: none !important;}
    
    /* Глубокий премиальный фон всего приложения */
    html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        background-color: #050506 !important;
        font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }
    
    /* Сайдбар как монолитная темная панель */
    [data-testid="stSidebar"] {
        background-color: #0B0B0D !important;
        border-right: 1px solid #1A1A1E !important;
    }
    
    /* Полное переопределение стандартных контейнеров Streamlit */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #0E0E12 !important;
        border: 1px solid #1C1C22 !important;
        border-radius: 14px !important;
        padding: 24px !important;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4) !important;
    }
    
    /* Стилизация интерактивных табов (вкладок) */
    button[data-baseweb="tab"] {
        color: #55555C !important;
        font-size: 15px !important;
        font-weight: 600 !important;
        letter-spacing: 0.5px !important;
        padding: 12px 20px !important;
        transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1) !important;
    }
    button[data-baseweb="tab"]:hover {
        color: #FFDD2D !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #FFDD2D !important;
        border-bottom: 2px solid #FFDD2D !important;
    }
    
    /* Тонкая настройка ползунков (Sliders) */
    div[data-testid="stSlider"] {
        padding-top: 10px !important;
        padding-bottom: 10px !important;
    }
    
    /* Т-Желтый прогресс-бар */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #FFDD2D 0%, #FFAA00 100%) !important;
        border-radius: 6px !important;
    }
    </style>
"""
st.markdown(custom_dark_theme, unsafe_allow_html=True)

if "last_request_time" not in st.session_state:
    st.session_state.last_request_time = 0.0

def check_rate_limit():
    current_time = time.time()
    if current_time - st.session_state.last_request_time < 0.3:
        st.warning("⚠️ Слишком много запросов!")
        st.stop()
    st.session_state.last_request_time = current_time

# Математические модели
def predict_credit(hist, debt):
    score = (hist * 3.5) - (debt * 4.0) + 0.5
    return 1 / (1 + np.exp(-score))

def predict_housing(size, distance):
    base_price = 50000.0 + (size * 1200.0) - (distance * 2000.0)
    return base_price + np.sin(size) * 3000.0


# 2. БОКОВАЯ ПАНЕЛЬ (КОНТРОЛЬНЫЙ ЦЕНТР)
with st.sidebar:
    st.write("")
    st.markdown("<h2 style='text-align: center; color: #FFDD2D; font-family: monospace; letter-spacing: 4px; font-size: 26px; margin-bottom: 0px;'>BLACKWOOD</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #44444A; font-size: 10px; letter-spacing: 2px; margin-top: 2px; font-weight: bold;'>QUANTITATIVE ANALYTICS</p>", unsafe_allow_html=True)
    st.markdown("<div style='height: 1px; background: linear-gradient(90deg, transparent, #222, transparent); margin: 20px 0;'></div>", unsafe_allow_html=True)
    
    st.markdown("<p style='color: #888892; font-size: 11px; font-weight: bold; letter-spacing: 1px; margin-bottom: 5px;'>SYSTEM RISK (VIX)</p>", unsafe_allow_html=True)
    market_condition = st.slider(
        "Индекс волатильности (VIX)", 
        0.5, 1.5, 1.0, 0.1,
        label_visibility="collapsed",
        help="Макроэкономическая поправка на волатильность."
    )
    
    st.markdown("<div style='height: 1px; background: linear-gradient(90deg, transparent, #222, transparent); margin: 20px 0;'></div>", unsafe_allow_html=True)
    if SECRET_KEY != "default_fallback_key":
        st.markdown("<p style='color: #FFDD2D; font-size: 11px; letter-spacing: 1px;'>🔒 <b>STATUS:</b> ENTERPRISE NODE</p>", unsafe_allow_html=True)
    else:
        st.markdown("<p style='color: #44444A; font-size: 11px; letter-spacing: 1px;'>🔓 <b>STATUS:</b> PRIVATE OPEN RELEASE</p>", unsafe_allow_html=True)


# 3. ЦЕНТРАЛЬНЫboard С ПАНЕЛЯМИ
tab1, tab2 = st.tabs(["🏦 КРЕДИТНЫЙ АНДЕРРАЙТИНГ", "🏢 АНАЛИЗ ЗАЛОГОВЫХ АКТИВОВ"])


# --- ВКЛАДКА 1: КРЕДИТНЫЙ СКОРИНГ ---
with tab1:
    st.write("")
    st.markdown("<h1 style='color: #FFF; font-size: 32px; font-weight: 500; margin-bottom: 0px;'>Дебиторские риски и скоринг</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #55555C; font-size: 14px; margin-top: 5px;'>Автоматизированный анализ вероятности дефолта контрагента</p>", unsafe_allow_html=True)
    st.write("")
    
    with st.container(border=True):
        st.markdown("<p style='color: #FFDD2D; font-size: 12px; font-weight: bold; letter-spacing: 1.5px; margin-bottom: 20px;'>КОЭФФИЦИЕНТЫ МОДЕЛИ</p>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("<p style='color: #888; font-size: 13px; margin-bottom: 2px;'>Внутренний скоринговый балл</p>", unsafe_allow_html=True)
            hist = st.slider("Рейтинг", 0.0, 1.0, 0.7, 0.01, key="credit_hist", label_visibility="collapsed")
        with col2:
            st.markdown("<p style='color: #888 pipe; font-size: 13px; margin-bottom: 2px;'>Показатель долговой нагрузки (DTI)</p>", unsafe_allow_html=True)
            debt = st.slider("Долг", 0.0, 1.0, 0.4, 0.01, key="credit_debt", label_visibility="collapsed")

    check_rate_limit()
    
    with st.spinner(""):
        time.sleep(0.05)
        prob = (predict_credit(hist, debt) / market_condition) * 100
        prob = min(max(prob, 0.0), 100.0)

    st.write("")
    res_col1, res_col2 = st.columns([1, 1.4])
    
    with res_col1:
        st.markdown("<p style='font-size: 12px; font-weight: bold; color: #55555C; letter-spacing: 1.5px; margin-bottom: 15px;'>ВЕРДИКТ СИСТЕМЫ</p>", unsafe_allow_html=True)
        
        # Полностью кастомная карточка результата вместо стандартного st.metric
        metric_html = f"""
            <div style="background-color: #0E0E12; border: 1px solid #1C1C22; padding: 25px; border-radius: 14px; box-shadow: 0 4px 20px rgba(0,0,0,0.3);">
                <p style="color: #888892; font-size: 13px; margin: 0; font-weight: 500;">Индекс финансовой надежности</p>
                <p style="color: #FFF; font-size: 42px; font-weight: 600; margin: 10px 0 15px 0; font-family: monospace;">{prob:.2f}%</p>
            </div>
        """
        st.markdown(metric_html, unsafe_allow_html=True)
        st.write("")
        st.progress(int(prob))
        st.write("")
        
        if prob >= 50.0:
            st.markdown("<div style='background-color: rgba(0, 244, 180, 0.04); border: 1px solid rgba(0, 244, 180, 0.3); padding: 18px; border-radius: 10px; color: #00f4b4; font-size: 13px; font-weight: 500; text-align: center; letter-spacing: 0.5px;'>ОДОБРЕНО ИИ БАНКА</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div style='background-color: rgba(255, 75, 75, 0.04); border: 1px solid rgba(255, 75, 75, 0.3); padding: 18px; border-radius: 10px; color: #ff4b4b; font-size: 13px; font-weight: 500; text-align: center; letter-spacing: 0.5px;'>БЛОКИРОВКА: ВЫСОКИЙ РИСК</div>", unsafe_allow_html=True)
                
    with res_col2:
        st.markdown("<p style='font-size: 12px; font-weight: bold; color: #55555C; letter-spacing: 1.5px; margin-bottom: 15px;'>КРИВАЯ ЧУВСТВИТЕЛЬНОСТИ МОДЕЛИ</p>", unsafe_allow_html=True)
        x_range = np.linspace(0.0, 1.0, 50)
        y_range = [min(max((predict_credit(x, debt) / market_condition) * 100, 0.0), 100.0) for x in x_range]
        chart_data = pd.DataFrame({"Рейтинг контрагента": x_range, "Надежность %": y_range})
        st.line_chart(chart_data, x="Рейтинг контрагента", y="Надежность %", color="#FFDD2D")


# --- ВКЛАДКА 2: НЕДВИЖИМОСТЬ ---
with tab2:
    st.write("")
    st.markdown("<h1 style='color: #FFF; font-size: 32px; font-weight: 500; margin-bottom: 0px;'>Предиктивная оценка недвижимости</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #55555C; font-size: 14px; margin-top: 5px;'>Расчет справедливой залоговой стоимости и симуляция трендов</p>", unsafe_allow_html=True)
    st.write("")
    
    with st.container(border=True):
        st.markdown("<p style='color: #FFDD2D; font-size: 12px; font-weight: bold; letter-spacing: 1.5px; margin-bottom: 20px;'>АРХИТЕКТУРА ОБЪЕКТА ОБЕСПЕЧЕНИЯ</p>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("<p style='color: #888; font-size: 13px; margin-bottom: 2px;'>Общая полезная площадь (кв. м.)</p>", unsafe_allow_html=True)
            size_input = st.slider("Площадь", 30, 150, 70, 1, key="house_size", label_visibility="collapsed")
        with col2:
            st.markdown("<p style='color: #888; font-size: 13px; margin-bottom: 2px;'>Удаленность от центрального хаба (км)</p>", unsafe_allow_html=True)
            dist_input = st.slider("Удаленность", 1, 20, 5, 1, key="house_dist", label_visibility="collapsed")

    check_rate_limit()
    
    with st.spinner(""):
        time.sleep(0.05)
        current_price = max(predict_housing(size_input, dist_input) * market_condition, 15000.0)

    st.write("")
    res_col1, res_col2 = st.columns([1, 1.4])
    
    with res_col1:
        st.markdown("<p style='font-size: 12px; font-weight: bold; color: #55555C; letter-spacing: 1.5px; margin-bottom: 15px;'>РЕЗУЛЬТАТЫ АУДИТА</p>", unsafe_allow_html=True)
        
        # Кастомная карточка стоимости
        price_html = f"""
            <div style="background-color: #0E0E12; border: 1px solid #1C1C22; padding: 25px; border-radius: 14px; box-shadow: 0 4px 20px rgba(0,0,0,0.3);">
                <p style="background: linear-gradient(90deg, #FFDD2D, #FFAA00); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 12px; margin: 0; font-weight: bold; letter-spacing: 1px;">FAIR MARKET VALUE</p>
                <p style="color: #FFF; font-size: 42px; font-weight: 600; margin: 10px 0 10px 0; font-family: monospace;">${current_price:,.2f}</p>
                <div style="height: 1px; background: #1C1C22; margin: 15px 0;"></div>
                <p style="color: #888892; font-size: 13px; margin: 5px 0;">• Метр площади: <b style="color: #FFF;">${(current_price/size_input):.2f}</b></p>
                <p style="color: #888892; font-size: 13px; margin: 5px 0;">• Дисконт локации: <b style="color: #ff4b4b;">{-dist_input * 2000:+,}</b></p>
            </div>
        """
        st.markdown(price_html, unsafe_allow_html=True)
        st.write("")
        
        if market_condition > 1.2:
            st.markdown("<div style='background-color: rgba(255, 152, 0, 0.04); border: 1px solid rgba(255, 152, 0, 0.3); padding: 12px; border-radius: 8px; color: #ff9800; font-size: 13px; font-weight: 500; text-align: center;'>⚠️ РЫНОК ПЕРЕГРЕТ (ЛОКАЛЬНЫЙ ПУЗЫРЬ)</div>", unsafe_allow_html=True)
        elif market_condition < 0.8:
            st.markdown("<div style='background-color: rgba(0, 244, 180, 0.04); border: 1px solid rgba(0, 244, 180, 0.3); padding: 12px; border-radius: 8px; color: #00f4b4; font-size: 13px; font-weight: 500; text-align: center;'>📉 АКТИВ НЕДООЦЕНЕН (СИГНАЛ К ВЫКУПУ)</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div style='border: 1px solid #1C1C22; padding: 12px; border-radius: 8px; color: #888; font-size: 13px; text-align: center;'>⚖️ ВОЛАТИЛЬНОСТЬ В ПРЕДЕЛАХ НОРМЫ</div>", unsafe_allow_html=True)
                
    with res_col2:
        st.markdown("<p style='font-size: 12px; font-weight: bold; color: #55555C; letter-spacing: 1.5px; margin-bottom: 15px;'>ПРОГНОЗ ДОЛГОСРОЧНОГО ЦЕНОВОГО ТРЕНДА</p>", unsafe_allow_html=True)
        years = ["2026", "2027", "2028", "2029", "2030", "2031"]
        prices = [current_price]
        for i in range(1, 6):
            growth = 1.05 + (market_condition - 1.0) * 0.05 
            next_price = prices[-1] * growth + (np.sin(i) * 2000)
            prices.append(max(next_price, 15000.0))
            
        forecast_data = pd.DataFrame({"Год": years, "Прогноз цен ($)": prices})
        st.bar_chart(forecast_data, x="Год", y="Прогноз цен ($)", color="#FFDD2D")
