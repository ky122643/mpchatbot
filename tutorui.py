import sqlite3
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import openai
import fitz
import base64
import collections
import re
import os
from datetime import datetime
from upload_slides import upload_and_index_pdf

# Initialize SQLite database connection
db_path = "datab.db"
conn = sqlite3.connect(db_path, check_same_thread=False)
cursor = conn.cursor()
client = openai.OpenAI()

# Load student data
def load_student_data():
    cursor.execute("SELECT * FROM student_data")
    rows = cursor.fetchall()
    columns = [desc[0].lower() for desc in cursor.description]
    return [dict(zip(columns, row)) for row in rows]

# Load conversation data
def load_conversation_data():
    cursor.execute("SELECT * FROM student_conversations")
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    return [dict(zip(columns, row)) for row in rows]

# Tutor dashboard UI
def display_tutor_ui():
    st.title("📊 Tutor Dashboard")

    student_data = load_student_data()
    conversation_data = load_conversation_data()
    student_df = pd.DataFrame(student_data)

    if student_df.empty:
        st.info("No student data available.")
        return

    student_df['timestamp'] = pd.to_datetime(student_df['timestamp'], errors='coerce')
    student_df = student_df.dropna(subset=["grade"])
    student_df["grade"] = student_df["grade"].str.upper().str.strip()
    student_df["question_count"] = student_df["questions"].apply(lambda q: len(str(q).split("?")) if pd.notnull(q) else 0)

    grade_map = {"A": 4, "B": 3, "C": 2, "D": 1}
    reverse_map = {v: k for k, v in grade_map.items()}
    student_df["grade_value"] = student_df["grade"].map(grade_map)

    st.markdown("---")
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Overview", "📈 Dashboard", "🧠 Breakdown", "📚 Upload Slides"])

    with tab1:
        st.subheader("📋 Student Overview")
        table_data = [{
            "ID": entry.get("id"),
            "Student": entry.get("username"),
            "Timestamp": entry.get("timestamp"),
            "Grade": entry.get("grade"),
            "Questions": entry.get("questions"),
            "Feedback": entry.get("feedback")
        } for entry in student_data]

        df = pd.DataFrame(table_data)
        df['Timestamp'] = pd.to_datetime(df['Timestamp'], errors='coerce')
        df = df.sort_values(by="Timestamp", ascending=False)

        st.dataframe(df, use_container_width=True)

    with tab2:
        st.subheader("📈 Interactive Performance Dashboard")

        kpi1, kpi2, kpi3 = st.columns(3)
        kpi1.metric("👨‍🎓 Total Students", len(student_df["username"].unique()))
        avg_value = student_df["grade_value"].mean()
        avg_letter = reverse_map.get(round(avg_value), "N/A")
        kpi2.metric("📊 Avg Grade", f"{avg_value:.2f} ({avg_letter})")
        kpi3.metric("❓ Avg Questions", f"{student_df['question_count'].mean():.2f}")

        st.markdown("---")

        col1, col2 = st.columns(2)
        with col1:
            grade_counts = student_df["grade"].value_counts().reindex(["A", "B", "C", "D"]).fillna(0)
            fig_grade = px.pie(
                names=grade_counts.index,
                values=grade_counts.values,
                title="🎯 Grade Distribution",
                hole=0.4
            )
            st.plotly_chart(fig_grade, use_container_width=True)

        with col2:
            time_series = student_df.groupby(student_df["timestamp"].dt.date).size()
            fig_time = px.line(
                x=time_series.index,
                y=time_series.values,
                labels={"x": "Date", "y": "Submissions"},
                title="📅 Submissions Over Time"
            )
            st.plotly_chart(fig_time, use_container_width=True)

        st.markdown("### 🧠 Engagement vs Performance")
        scatter_fig = px.scatter(
            student_df,
            x="question_count",
            y="grade_value",
            color="username",
            title="📌 Questions Asked vs Grade",
            labels={"question_count": "# Questions", "grade_value": "Grade"},
            hover_data=["username", "grade"]
        )
        scatter_fig.update_yaxes(
            tickvals=[1, 2, 3, 4],
            ticktext=["D", "C", "B", "A"]
        )
        st.plotly_chart(scatter_fig, use_container_width=True)

    with tab3:
        st.subheader("🔍 Chatbot Interaction Breakdown")

        all_questions = " ".join(student_df["questions"].dropna().values)
        question_words = re.findall(r"\b(how|what|why|when|where|who|can|do|is|should)\b", all_questions, re.IGNORECASE)
        question_freq = collections.Counter(question_words)

        fig_qtype = px.bar(
            x=list(question_freq.keys()),
            y=list(question_freq.values()),
            title="🗣️ Common Question Starters",
            labels={"x": "Question Word", "y": "Frequency"}
        )
        st.plotly_chart(fig_qtype, use_container_width=True)

        st.plotly_chart(px.line(
            student_df.sort_values("timestamp"),
            x="timestamp",
            y="grade_value",
            color="username",
            title="📈 Grade Trends by Student",
            markers=True
        ).update_yaxes(tickvals=[1, 2, 3, 4], ticktext=["D", "C", "B", "A"]), use_container_width=True)

    with tab4:
        upload_and_index_pdf()
        if os.path.exists("uploaded_slides"):
            uploaded_files = os.listdir("uploaded_slides")
            st.write("📁 Uploaded Slide Files:")
            for f in uploaded_files:
                st.markdown(f"- `{f}`")

            st.write("📄 **Preview Uploaded Slide**")
            selected_file = st.selectbox("Select a file to preview", uploaded_files)

            if selected_file:
                file_path = os.path.join("uploaded_slides", selected_file)
                try:
                    doc = fitz.open(file_path)
                    for page_num in range(len(doc)):
                        page = doc.load_page(page_num)
                        text = page.get_text()
                        with st.expander(f"📄 Page {page_num + 1}"):
                            st.text(text if text else "[No extractable text on this page]")
                except Exception as e:
                    st.error(f"Error reading file: {e}")
        else:
            st.info("No uploaded slides found.")
