import streamlit as st
import time
#from auth import login_and_register
#from tutorui import display_tutor_ui
#from chatbot import chatbot_page
from openai import OpenAI
import os
os.environ["OPENAI_API_KEY"]=st.secrets["OPENAI_API_KEY"]
# load_dotenv()
# openai_api_key = os.getenv("OPENAI_API_KEY")  # in environment variables
# #openai_api_key = open('api_key.txt', 'r')
# client = OpenAI(api_key=OPENAI_API_KEY)
# # st.set_page_config(page_title="Login System", page_icon="🔒", layout="centered")
st.write(OPENAI_API_KEY)
# Set session timeout (30 minutes)
SESSION_TIMEOUT = 1800
# Pass the key to the OpenAI client (v1.x+)
client = openai.OpenAI(api_key=OPENAI_API_KEY)  # explicit, or rely on env variable
 
# Example: Make a simple API call
try:
    response = client.models.list()  # List available models
    st.write("Models:", [model.id for model in response.data])
except Exception as e:
    st.error(f"OpenAI API error: {e}")
# # Initialize session state if not already set
# if "logged_in" not in st.session_state:
#     st.session_state.logged_in = False
# if "last_active" not in st.session_state:
#     st.session_state.last_active = time.time()
        
# # Check for session expiration
# if st.session_state.logged_in and time.time() - st.session_state.last_active > SESSION_TIMEOUT:
#     st.warning("🔒 Session expired after 30 minutes of inactivity. Please log in again.")
#     st.session_state.logged_in = False
#     st.session_state.username = ""
#     st.session_state.role = ""
#     st.rerun()

#     st.set_page_config(page_title="Login System", page_icon="🔒", layout="centered")

# # Login Page
# if not st.session_state.logged_in:
#     st.title("🔒 Welcome! Please Login or Register")
#     login_successful = login_and_register()

#     if login_successful:
#         st.rerun()  # rerun to trigger login display immediately

# else:
#     st.sidebar.success(f"✅ Logged in as {st.session_state.username} ({st.session_state.role})")

#         # Add a Logout button
#     if st.sidebar.button("Logout"):
#         for key in list(st.session_state.keys()):
#             del st.session_state[key]
#         st.rerun()

#         # Role-based navigation
#     if st.session_state.role == "tutor":
#         display_tutor_ui()
#     elif st.session_state.role == "student":
#         chatbot_page()
#     else:
#         st.error("Unknown role. Please contact administrator.")

# # if __name__ == "__main__":
# #    main()
