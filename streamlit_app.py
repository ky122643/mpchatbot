import streamlit as st
from openai import OpenAI
apikey=st.secrets["OPENAI_API_KEY"]
st.write(apikey)
