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
        # Sidebar user info (top)
        st.sidebar.success(f"✅ Logged in as {st.session_state.username} ({st.session_state.role})")

        # Buttons for Home and Logout on top
        home_btn = st.sidebar.button("🏠 Home")
        logout_btn = st.sidebar.button("🚪 Logout")

        if "page" not in st.session_state:
            st.session_state.page = "home"

        if home_btn:
            st.session_state.page = "home"
        elif logout_btn:
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

        # Spacer to push the profile icon to the bottom
        st.sidebar.markdown("<div style='flex-grow: 1'></div>", unsafe_allow_html=True)
        # Use this if needed to add vertical space; alternatively use empty lines:
        for _ in range(15):
            st.sidebar.text("")

        # Profile circle button with image (or initials)
        profile_clicked = st.sidebar.button(
            "👤",
            key="profile_icon",
            help="View Profile",
            # Custom CSS to style it as a circle:
        )

        # Set page to profile if clicked
        if profile_clicked:
            st.session_state.page = "profile"

        # Render selected page
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
