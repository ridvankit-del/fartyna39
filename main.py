import streamlit as st
import pandas as pd
import numpy as np
import io

# Настройки страницы
st.set_page_config(page_title="Blackwood Enterprise", layout="wide")

st.markdown("""<style>.stApp {background: #050506; color: white;}</style>""", unsafe_allow_html=True)

st.title("👑 BLACKWOOD ANALYTICS ENTERPRISE")

# Вкладки с расширенным функционалом
tab_single, tab_bulk, tab_portfolio = st.tabs(["🎯 ЭКСПРЕСС-АНАЛИЗ", "📊 МАССОВЫЙ СКОРИНГ (CSV)", "💼 ПОРТФЕЛЬ"])

# --- ВКЛАДКА 1: ЭКСПРЕСС-АНАЛИЗ ---
with tab_single:
    col1, col2 = st.columns([1, 1])
    with col1:
        hist = st.slider("Кредитный рейтинг", 0.0, 1.0, 0.7)
        debt = st.slider("Долговая нагрузка", 0.0, 1.0, 0.4)
        if st.button("Добавить в портфель"):
            st.session_state.portfolio = st.session_state.get("portfolio", []) + [{"Тип": "Кредит", "Риск": hist}]
    with col2:
        st.metric("Скоринг", f"{((hist*3.5)-(debt*4.0)+0.5)*100:.2f}%")

# --- ВКЛАДКА 2: МАССОВЫЙ СКОРИНГ ---
with tab_bulk:
    st.subheader("Загрузка реестра контрагентов")
    uploaded_file = st.file_uploader("Загрузите CSV с параметрами", type=["csv"])
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        # Автоматический ИИ-скоринг колонки
        df['AI_Score'] = df['rating'] * 10
        st.dataframe(df, use_container_width=True)
        
        # Экспорт в Excel
        buffer = io.BytesIO()
        df.to_excel(buffer, index=False)
        st.download_button("Скачать отчет .xlsx", data=buffer.getvalue(), file_name="ai_report.xlsx")

# --- ВКЛАДКА 3: ПОРТФЕЛЬ ---
with tab_portfolio:
    st.subheader("Управление инвестиционным портфелем")
    if "portfolio" in st.session_state:
        port_df = pd.DataFrame(st.session_state.portfolio)
        st.table(port_df)
    else:
        st.info("Портфель пуст. Добавьте активы из раздела экспресс-анализа.")

#
