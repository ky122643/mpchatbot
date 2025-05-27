import streamlit as st
import json
import os
import hashlib
import re
import time

users_file = "users.json"

def load_users(file):
    try:
        with open(file, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_users(file, users):
    with open(file, "w") as f:
        json.dump(users, f, indent=4)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def check_password(password, hashed_password):
    return hash_password(password) == hashed_password

def is_strong_password(password):
    return (
        len(password) >= 8 and
        re.search(r"[A-Z]", password) and
        re.search(r"[a-z]", password) and
        re.search(r"[0-9]", password) and
        re.search(r"[!@#$%^&*(),.?\":{}|<>]", password)
    )

MAX_ATTEMPTS = 5
LOCKOUT_TIME = 600  # 10 minutes in seconds

def is_locked_out():
    state = st.session_state
    if "failed_attempts" not in state:
        state.failed_attempts = 0
        state.lockout_start = 0

    if state.failed_attempts >= MAX_ATTEMPTS:
        if time.time() - state.lockout_start < LOCKOUT_TIME:
            return True
        else:
            state.failed_attempts = 0  # Reset after lockout period
            state.lockout_start = 0
    return False

def login_and_register():

    if "failed_attempts" not in st.session_state:
        st.session_state.failed_attempts = 0
    if "lockout_start" not in st.session_state:
        st.session_state.lockout_start = 0

    users = load_users(users_file)
    tab_login, tab_register, tab_forgot = st.tabs(["🔑 Login", "📝 Register", "❓ Forgot Password"])

    with tab_login:
        login_input = st.text_input("Username or Email", key="login_user_email_input")
        password = st.text_input("Password", type="password", key="login_password_input")

        # Check if user is locked out
        if st.session_state.failed_attempts >= MAX_ATTEMPTS:
            time_since_lockout = time.time() - st.session_state.lockout_start
            if time_since_lockout < LOCKOUT_TIME:
                minutes_left = int((LOCKOUT_TIME - time_since_lockout) / 60)
                st.error(f"Too many failed attempts. Try again in {minutes_left} minute(s).")
            else:
                st.session_state.failed_attempts = 0  # Reset after timeout
                st.session_state.lockout_start = 0

        elif st.button("Login", key="login_button"):
            hashed = hash_password(password)
            for username, data in users.items():
                if (login_input == username or login_input == data.get("email")) and hashed == data["password"]:
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.session_state.role = data.get("role", "user")
                    st.session_state.failed_attempts = 0  # Reset on successful login
                    st.success(f"Welcome, {username}!")
                    st.rerun()
                    return True

            # Failed login
            st.session_state.failed_attempts += 1
            if st.session_state.failed_attempts >= MAX_ATTEMPTS:
                st.session_state.lockout_start = time.time()
                st.error("Too many failed attempts. You are now locked out temporarily.")
            else:
                remaining = MAX_ATTEMPTS - st.session_state.failed_attempts
                st.error(f"Invalid username/email or password. {remaining} attempt(s) left.")
    
    with tab_register:
        new_username = st.text_input("New Username", key="register_username_input")
        new_email = st.text_input("Email", key="register_email_input")
        new_password = st.text_input("Password", type="password", key="register_password_input")
        role = st.selectbox("Role", ["student", "tutor"], key="register_role_select")
        if st.button("Register", key="register_button"):
            if new_username in users:
                st.error("Username already exists.")
            elif any(data.get("email") == new_email for data in users.values()):
                st.error("Email already in use.")
            elif not is_strong_password(new_password):
                st.error("Password must be at least 8 characters long and contain at least one uppercase letter, one lowercase letter, one number, and one special character(!#%&).")
            else:
                users[new_username] = {
                    "email": new_email,
                    "password": hash_password(new_password),
                    "role": role
                }
                save_users(users_file, users)
                st.success("Registration successful! You can now log in.")

    with tab_forgot:
        st.subheader("Reset Your Password")
        forgot_input = st.text_input("Enter your Username or Email", key="forgot_user")
        new_password = st.text_input("New Password", type="password", key="forgot_pass1")
        confirm_password = st.text_input("Confirm New Password", type="password", key="forgot_pass2")

        if st.button("Reset Password"):
            if new_password != confirm_password:
                st.error("Passwords do not match.")
            elif not new_password:
                st.error("Password cannot be empty.")
            else:
                found = False
                for username, data in users.items():
                    if forgot_input == username or forgot_input == data.get("email"):
                        data["password"] = hash_password(new_password)
                        save_users(users_file, users)
                        st.success("Password reset successful! You can now log in.")
                        found = True
                        break
                if not found:
                    st.error("No user found with that username or email.")


    return False
