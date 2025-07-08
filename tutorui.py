import sqlite3
import streamlit as st
import pandas as pd
import plotly.express as px
import json
import openai
import fitz
import base64
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
    st.title("📋 Tutor Dashboard")
    tab1, tab2, tab3 = st.tabs(["📊 Dashboard Overview", "📋 Student Records", "📚 Upload Slides"])

    student_data = load_student_data()
    conversation_data = load_conversation_data()

    with tab1:
        st.subheader("📈 Dashboard Overview")

        df = pd.DataFrame(student_data)
        if not df.empty:
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
            df = df.dropna(subset=['grade'])
            df['grade'] = df['grade'].str.upper()

            # KPIs
            total_students = df['username'].nunique()
            avg_grade = df['grade'].map({"A": 4, "B": 3, "C": 2, "D": 1}).mean()
            grade_letter = {4: "A", 3: "B", 2: "C", 1: "D"}.get(round(avg_grade), "N/A")
            total_questions = df['questions'].apply(lambda q: len(str(q).split('?'))).sum()

            kpi1, kpi2, kpi3 = st.columns(3)
            kpi1.metric("🧑‍🎓 Total Students", total_students)
            kpi2.metric("📊 Avg Grade", grade_letter)
            kpi3.metric("❓ Total Questions Asked", total_questions)

            # Charts
            st.write("### 📊 Grade Distribution")
            grade_counts = df['grade'].value_counts().reindex(["A", "B", "C", "D"]).fillna(0)
            st.bar_chart(grade_counts)

            st.write("### 📅 Submissions Over Time")
            time_series = df.groupby(df['timestamp'].dt.date).size()
            st.line_chart(time_series)

        else:
            st.info("No data available yet.")

    with tab2:
        st.subheader("📋 Student Records")
        table_data = [{
            "ID": entry.get("id"),
            "Student": entry.get("username"),
            "Timestamp": entry.get("timestamp"),
            "Grade": entry.get("grade"),
            "Questions": entry.get("questions"),
            "Feedback": entry.get("feedback")
        } for entry in student_data]

        df = pd.DataFrame(table_data)
        if "Timestamp" in df.columns:
            df['Timestamp'] = pd.to_datetime(df['Timestamp'], errors='coerce')
            df = df.sort_values(by="Timestamp", ascending=False)

        search_query = st.text_input("Search by name, ID, or grade", "").strip().lower()
        show_top_5 = st.checkbox("Show Top 5", value=True)

        filtered_data = [
            entry for entry in table_data
            if (
                (len(search_query) == 1 and search_query in ["a", "b", "c", "d"] and entry['Grade'].lower() == search_query) or
                (search_query not in ["a", "b", "c", "d"] and (
                    search_query in entry['Student'].lower() or search_query in str(entry['ID']).lower()))
            ) and entry['Grade'].lower() != "grade not found, please review manually"
        ]
        filtered_df = pd.DataFrame(filtered_data)
        if show_top_5 and not filtered_df.empty:
            filtered_df = filtered_df.head(5)

        if not filtered_df.empty:
            st.dataframe(filtered_df["ID", "Student", "Timestamp", "Grade", "Questions", "Feedback"], width=1000, height=400)
            selected_id = st.selectbox("🔍 Select Student ID", filtered_df["ID"].tolist())
            selected_row = filtered_df[filtered_df["ID"] == selected_id].iloc[0]

            with st.expander(f"📄 Details for {selected_row['Student']} (ID: {selected_row['ID']})"):
                st.markdown(f"**Grade:** {selected_row['Grade']}")
                st.markdown("**Questions Asked:**")
                st.code(selected_row['Questions'])
                st.markdown("**Feedback:**")
                st.info(selected_row['Feedback'])

                matching_logs = [entry for entry in conversation_data if entry["username"] == selected_row["Student"]]
                if matching_logs:
                    log = matching_logs[-1]
                    try:
                        messages = json.loads(log["messages"])
                        st.markdown(f"### 🗨️ Conversation Log (ID: {log['id']}) on {log['timestamp']}")
                        for msg in messages:
                            st.chat_message(msg["role"]).markdown(msg["content"])
                    except Exception as e:
                        st.error(f"❌ Error loading messages: {e}")
                else:
                    st.warning("⚠️ No conversation log found for this student.")

    with tab3:
        upload_and_index_pdf()
        if os.path.exists("uploaded_slides"):
            uploaded_files = os.listdir("uploaded_slides")
            st.write("📁 Uploaded Slides:")
            for f in uploaded_files:
                st.markdown(f"- `{f}`")

            st.write("📄 **Preview Uploaded Slide**")
            selected_file = st.selectbox("Select a file", uploaded_files)
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
