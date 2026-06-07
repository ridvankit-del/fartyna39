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
    page_title="Blackwood Terminal v6.0", 
    page_icon="👑", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- PREMIUM CSS STYLES (THE CORE DESIGN) ---
premium_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .viewerBadge_link__1S137 {display: none !important;}
    
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #050506 !important;
        font-family: 'SF Pro Display', -apple-system, sans-serif !important;
    }
    
    [data-testid="stSidebar"] {
        background-color: #0B0B0D !important;
        border-right: 1px solid #1A1A1E !important;
    }
    
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #0E0E12 !important;
        border: 1px solid #1C1C22 !important;
        border-radius: 14px !important;
        padding: 24px !important;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4) !important;
    }
    
    button[data-baseweb="tab"] {
        color: #55555C !important;
        font-size: 15px !important;
        font-weight: 600 !important;
        letter-spacing: 0.5px !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #FFDD2D !important;
        border-bottom: 2px solid #FFDD2D !important;
    }
    
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #FFDD2D 0%, #FFAA00 100%) !important;
    }
    </style>
"""
st.markdown(premium_style, unsafe_allow_html=True)

# ИИ-ЛОГИКА (Мозг системы)
def get_ai_insight(value, type="credit"):
    if type == "credit":
        if value > 75: return "✅ **AI-АНАЛИЗ:** Высокая кредитоспособность. Риск дефолта минимален. Рекомендовано к одобрению в приоритетном порядке."
        if value > 45: return "⚠️ **AI-АНАЛИЗ:** Пограничное состояние. Требуется дополнительное обеспечение залога или ручной андеррайтинг."
        return "❌ **AI-АНАЛИЗ:** Критическая долговая нагрузка. Автоматизированная система блокирует сделку во избежание потерь."
    else:
        if value > 100000: return "📉 **AI-АНАЛИЗ:** Объект переоценен рынком. Рекомендуем отложить сделку до наступления коррекции."
        return "💎 **AI-АНАЛИЗ:** Активы недооценены. Отличная точка входа для инвестиционного портфеля."

# 2. БОКОВАЯ ПАНЕЛЬ
with st.sidebar:
    st.markdown("<h2 style='text-align: center; color: #FFDD2D; font-family: monospace; letter-spacing: 4px;'>BLACKWOOD</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #44444A; font-size: 10px; letter-spacing: 2px;'>QUANTITATIVE ANALYTICS</p>", unsafe_allow_html=True)
    st.markdown("<div style='height: 1px; background: #222; margin: 20px 0;'></div>", unsafe_allow_html=True)
    
    market_condition = st.slider("Индекс волатильности (VIX)", 0.5, 1.5, 1.0, 0.1)
    
    if SECRET_KEY != "default_fallback_key":
        st.markdown("<p style='color: #FFDD2D; font-size: 11px;'>🔒 STATUS: ENTERPRISE NODE</p>", unsafe_allow_html=True)

# 3. ЦЕНТРАЛЬНЫЙ ПУЛЬТ
tab1, tab2 = st.tabs(["🏦 КРЕДИТНЫЙ АНДЕРРАЙТИНГ", "🏢 АНАЛИЗ ЗАЛОГОВЫХ АКТИВОВ"])

# ВКЛАДКА 1
with tab1:
    st.markdown("<h2 style='color: #FFF;'>Дебиторские риски и скоринг</h2>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    hist = col1.slider("Кредитный рейтинг", 0.0, 1.0, 0.7, key="c1")
    debt = col2.slider("Долговая нагрузка (DTI)", 0.0, 1.0, 0.4, key="c2")
    
    prob = ((hist * 3.5) - (debt * 4.0) + 0.5) * 100 / market_condition
    prob = min(max(prob, 0.0), 100.0)
    
    st.metric("Индекс надежности", f"{prob:.2f}%")
    st.progress(int(prob))
    
    st.markdown(f"""<div style="background: #0E0E12; border: 1px solid #1C1C22; padding: 20px; border-radius: 12px; margin-top: 20px; border-left: 4px solid #FFDD2D;">
        <p style="color: #FFF; font-size: 15px;">{get_ai_insight(prob, 'credit')}</p></div>""", unsafe_allow_html=True)
    
    # График
    chart_data = pd.DataFrame({'Надежность': np.random.randn(20).cumsum()})
    st.line_chart(chart_data, color="#FFDD2D")

# ВКЛАДКА 2
with tab2:
    st.markdown("<h2 style='color: #FFF;'>Анализ залоговых активов</h2>", unsafe_allow_html=True)
    size = st.slider("Площадь (кв. м.)", 30, 150, 70, key="h1")
    price = (50000.0 + (size * 1200.0)) * market_condition
    
    st.metric("Fair Market Value", f"${price:,.2f}")
    
    stress_price = price * 0.8
    st.warning(f"📊 **Стресс-тест (-20% рынка):** ${stress_price:,.2f}")
    
    st.markdown(f"""<div style="background: #0E0E12; border: 1px solid #1C1C22; padding: 20px; border-radius: 12px; margin-top: 20px; border-left: 4px solid #00f4b4;">
        <p style="color: #FFF; font-size: 15px;">{get_ai_insight(price, 'real_estate')}</p></div>""", unsafe_allow_html=True)
    
    # Гистограмма
    forecast_data = pd.DataFrame({"Год": ["2026", "2027", "2028"], "Прогноз": [price, price*1.05, price*1.12]})
    st.bar_chart(forecast_data, x="Год", y="Прогноз", color="#FFDD2D")

# Добавим для объема футер и отладку
st.markdown("<div style='height: 50px;'></div>", unsafe_allow_html=True)
st.caption("Blackwood Analytics Terminal v6.0 | Confidential | Internal Use Only")
