import sqlite3
import streamlit as st
import pandas as pd
import plotly.express as px
import json
import openai
import fitz
import os
from datetime import datetime
from upload_slides import upload_and_index_pdf

# Database setup
conn = sqlite3.connect("datab.db", check_same_thread=False)
cursor = conn.cursor()
client = openai.OpenAI()

# Load functions

def load_student_data():
    cursor.execute("SELECT * FROM student_data")
    rows = cursor.fetchall()
    columns = [desc[0].lower() for desc in cursor.description]
    return [dict(zip(columns, row)) for row in rows]

def load_conversation_data():
    cursor.execute("SELECT * FROM student_conversations")
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    return [dict(zip(columns, row)) for row in rows]

# Dashboard UI

def display_tutor_ui():
    st.title("📊 Tutor Dashboard")
    student_data = load_student_data()
    conversation_data = load_conversation_data()

    student_df = pd.DataFrame(student_data)

    if not student_df.empty:
        student_df['timestamp'] = pd.to_datetime(student_df['timestamp'], errors='coerce')
        student_df = student_df.dropna(subset=["grade"])
        student_df["grade"] = student_df["grade"].str.upper().str.strip()

        # Top KPIs
        st.markdown("### 📈 Key Performance Metrics")
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Students", len(student_df["username"].unique()))
        col2.metric("Avg. Grade", student_df["grade"].mode()[0])
        col3.metric("Total Sessions", len(student_df))

        # Tabs for views
        tab1, tab2, tab3 = st.tabs(["Overview", "Insights", "Upload Slides"])

        with tab1:
            st.subheader("📋 Student Table")
            search = st.text_input("🔍 Search by Name or Grade")
            filtered_df = student_df.copy()
            if search:
                filtered_df = filtered_df[filtered_df["username"].str.contains(search, case=False) | filtered_df["grade"].str.contains(search, case=False)]

            st.dataframe(filtered_df, use_container_width=True)

            selected_id = st.selectbox("Select Student ID for Details", options=filtered_df["id"].unique())
            selected_row = filtered_df[filtered_df["id"] == selected_id].iloc[0]

            with st.expander(f"🧑‍🎓 {selected_row['username']} Details"):
                st.markdown(f"**Grade:** {selected_row['grade']}")
                st.markdown(f"**Questions Asked:**")
                st.code(selected_row['questions'])
                st.markdown("**Feedback:**")
                st.info(selected_row['feedback'])

                logs = [c for c in conversation_data if c["username"] == selected_row["username"]]
                if logs:
                    log = logs[-1]
                    messages = json.loads(log["messages"])
                    for m in messages:
                        st.chat_message(m["role"]).markdown(m["content"])

        with tab2:
            st.subheader("📊 Analytics")
            grade_counts = student_df["grade"].value_counts().reindex(["A", "B", "C", "D"]).fillna(0)
            st.write("### Grade Distribution")
            fig1 = px.bar(grade_counts, x=grade_counts.index, y=grade_counts.values, labels={'x': 'Grade', 'y': 'Count'}, title="Grade Breakdown")
            st.plotly_chart(fig1, use_container_width=True)

            st.write("### Submissions Over Time")
            time_series = student_df.groupby(student_df["timestamp"].dt.date).size()
            st.line_chart(time_series)

        with tab3:
            upload_and_index_pdf()
            if os.path.exists("uploaded_slides"):
                files = os.listdir("uploaded_slides")
                st.write("### 📁 Uploaded Files")
                for f in files:
                    st.markdown(f"- `{f}`")

                selected_file = st.selectbox("Preview a file", files)
                if selected_file:
                    try:
                        doc = fitz.open(os.path.join("uploaded_slides", selected_file))
                        for i in range(len(doc)):
                            with st.expander(f"📄 Page {i+1}"):
                                text = doc.load_page(i).get_text()
                                st.text(text or "No text found.")
                    except Exception as e:
                        st.error(f"Failed to read file: {e}")
    else:
        st.info("No student data available yet.")
