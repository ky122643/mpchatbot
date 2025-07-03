import streamlit as st
import time
from openai import OpenAI
from auth import login_and_register
from tutorui import display_tutor_ui
from chatbot import chatbot_page


apikey=st.secrets["OPENAI_API_KEY"]
# st.write('success' if apikey else 'error')
# Pass the key to the OpenAI client (v1.x+)
client = OpenAI(api_key=apikey)  # explicit, or rely on env variable

# Example: Make a simple API call
#try:
    #response = client.models.list()  # List available models
    #st.write("Models:", [model.id for model in response.data])
#except Exception as e:
    #st.error(f"OpenAI API error: {e}")

# SESSION MANAGEMENT
SESSION_TIMEOUT = 1800  # 30 minutes

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "last_active" not in st.session_state:
    st.session_state.last_active = time.time()

if st.session_state.logged_in and time.time() - st.session_state.last_active > SESSION_TIMEOUT:
    st.warning("🔒 Session expired after 30 minutes of inactivity. Please log in again.")
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.role = ""
    st.rerun()

# MAIN UI
if not st.session_state.logged_in:
    st.title("🔒 Welcome! Please Login or Register")
    login_successful = login_and_register()
    if login_successful:
        st.rerun()

else:
        st.sidebar.success(f"✅ Logged in as {st.session_state.username} ({st.session_state.role})")

        # Sidebar Buttons
        home_btn = st.sidebar.button("🏠 Home")
        profile_btn = st.sidebar.button("👤 Profile")
        logout_btn = st.sidebar.button("🚪 Logout")

        # Track which page to show
        if "page" not in st.session_state:
            st.session_state.page = "home"

        if home_btn:
            st.session_state.page = "home"
        elif profile_btn:
            st.session_state.page = "profile"
        elif logout_btn:
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

        # Render based on selected page
        if st.session_state.page == "home":
            if st.session_state.role == "tutor":
                display_tutor_ui()
            elif st.session_state.role == "student":
                chatbot_page(client)
            else:
                st.error("Unknown role. Please contact administrator.")

        elif st.session_state.page == "profile":
            from profile import profile_page
            profile_page()
