import streamlit as st
import json

# link to JSON file
users_file = "users.json"

def load_users(file_path):
    try:
        with open(file_path, "r") as f:
            users = json.load(f)
    except FileNotFoundError:
        st.error("User data file not found.")
        return {}
    except json.JSONDecodeError:
        st.error("Error reading user data.")
        return {}
    return users

def login():
    if "username" not in st.session_state:
        st.session_state.username = None
        st.session_state.role = None

    if st.session_state.username is None:
        st.title("Login")
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit_button = st.form_submit_button("Login")

            if submit_button:
                users = load_users(users_file)  # load users
                if username in users:
                    user_data = users[username]
                    if user_data["password"] == password:
                        st.session_state.username = username
                        st.session_state.role = user_data["role"]
                        st.success(f"{username} password verified. Press enter again to confirm log in")
                        return True
                    else:
                        st.error("Invalid password.")
                else:
                    st.error("Username not found.")
                return False
    else:
        st.info(f"Logged in as {st.session_state.username} ({st.session_state.role})")
    return st.session_state.username is not None
