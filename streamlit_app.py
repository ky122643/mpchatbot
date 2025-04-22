import streamlit as st
from openai import OpenAI
from auth import login
from chatbot import chatbot_page
from tutorui import display_tutor_ui

# initialize session state variables
if "username" not in st.session_state:
    st.session_state.username = None
if "role" not in st.session_state:
    st.session_state.role = None
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "page" not in st.session_state:
    st.session_state.page = "main"

def go_to_main():
    st.session_state.page = "main"

def go_to_chatbot():
    st.session_state.page = "chatbot"

def go_to_tutorui():
    st.session_state.page = "tutorui"

def logout():
    st.session_state.username = None
    st.session_state.role = None
    st.session_state.logged_in = False
    st.session_state.page = "main"

# login logic
if not st.session_state.logged_in:
    st.title("Login Page")
    if login():  # calls the login function from auth.py
        st.session_state.logged_in = True
        # assign the username and role after successful login
        st.session_state.username = st.session_state.username or "guest"
        role = st.session_state.role  # Ensure role is set by the `login` function
        if role == "student":
            go_to_chatbot()
        elif role == "tutor":
            go_to_tutorui()
else:
    # sidebar logout button
    st.sidebar.button("Logout", on_click=logout)

    # route pages based on role
    role = st.session_state.role
    if st.session_state.page == "chatbot" and role == "student":
        chatbot_page()
    elif st.session_state.page == "tutorui" and role == "tutor":
        display_tutor_ui()
    else:
        st.title("Invalid Page")
        st.write("You do not have access to this page.")
