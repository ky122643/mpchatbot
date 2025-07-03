import streamlit as st
import json

def load_user_info():
    try:
        with open("users.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def profile_page():
    st.title("👤 My Profile")

    username = st.session_state.get("username", "guest")
    users = load_user_info()
    user_data = users.get(username, {})

    st.markdown(f"### 👋 Welcome, `{username}`!")
    st.markdown(f"- **Email**: `{user_data.get('email', 'N/A')}`")
    st.markdown(f"- **Role**: `{user_data.get('role', 'user')}`")

    st.markdown("---")

    st.subheader("🔐 Account Settings")

    with st.expander("Change Password"):
        new_pass = st.text_input("New Password", type="password")
        confirm_pass = st.text_input("Confirm Password", type="password")
        if st.button("Update Password"):
            if new_pass != confirm_pass:
                st.error("Passwords do not match.")
            elif len(new_pass) < 8:
                st.error("Password must be at least 8 characters long.")
            else:
                # Save new password
                user_data["password"] = hashlib.sha256(new_pass.encode()).hexdigest()
                users[username] = user_data
                with open("users.json", "w") as f:
                    json.dump(users, f, indent=4)
                st.success("✅ Password updated successfully.")

    st.markdown("---")
    st.markdown("💡 You can suggest more profile features like avatars, edit email, or usage stats.")

