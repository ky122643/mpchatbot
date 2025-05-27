import streamlit as st
from openai import OpenAI
apikey=st.secrets["OPENAI_API_KEY"]
st.write('success' if apikey else 'error')
# Pass the key to the OpenAI client (v1.x+)

client = OpenAI(api_key=apikey)  # explicit, or rely on env variable
 
# Example: Make a simple API call

try:

    response = client.models.list()  # List available models

    st.write("Models:", [model.id for model in response.data])

except Exception as e:

    st.error(f"OpenAI API error: {e}")
 
