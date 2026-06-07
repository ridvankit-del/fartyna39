import streamlit as st

# Инициализация хранилища черновиков
if 'user_drafts' not in st.session_state:
    st.session_state.user_drafts = []

st.set_page_config(page_title="Blackwood HR Portal", layout="wide")

# Простейшая имитация входа
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🔐 Вход в личный кабинет HR")
    username = st.text_input("Логин")
    if st.button("Войти"):
        st.session_state.logged_in = True
        st.rerun()
else:
    st.sidebar.success(f"Вы вошли как HR-менеджер")
    if st.sidebar.button("Выйти"):
        st.session_state.logged_in = False
        st.rerun()

    st.title("💼 Кабинет: Очередь на проверку")

    # Форма загрузки в черновики
    with st.expander("➕ Добавить резюме в очередь на проверку"):
        with st.form("draft_form"):
            name = st.text_input("Имя кандидата")
            role = st.selectbox("Категория", ["Повар", "Су-шеф", "Шеф-повар", "Менеджер", "Хостес", "Официант"])
            details = st.text_area("Текст резюме/Заметки")
            if st.form_submit_button("Сохранить в черновики"):
                st.session_state.user_drafts.append({"Имя": name, "Роль": role, "Резюме": details})
                st.success("Сохранено в личный кабинет!")

    # Вывод черновиков
    st.subheader("📝 Ваши сохраненные резюме")
    if not st.session_state.user_drafts:
        st.info("Черновиков нет.")
    else:
        for idx, draft in enumerate(st.session_state.user_drafts):
            with st.container(border=True):
                col1, col2 = st.columns([3, 1])
                col1.write(f"**{draft['Имя']}** | *{draft['Роль']}*")
                col1.write(f"Текст: {draft['Резюме'][:100]}...")
                
                if col2.button("Отправить в общий реестр", key=f"btn_{idx}"):
                    # Логика переноса из черновиков в talent_db
                    st.session_state.talent_db[draft['Роль']].append({"Имя": draft['Имя'], "Стаж": 0, "Навыки": []})
                    del st.session_state.user_drafts[idx]
                    st.rerun()
