import sqlite3
import streamlit as st
import pandas as pd
import json
from datetime import datetime
from upload_slides import upload_and_index_pdf

# Initialize SQLite database connection
db_path = "datab.db"
conn = sqlite3.connect(db_path, check_same_thread=False)
cursor = conn.cursor()

# Load student data
def load_student_data():
    cursor.execute("SELECT * FROM student_data")
    rows = cursor.fetchall()
    columns = [desc[0].lower() for desc in cursor.description]
    return [dict(zip(columns, row)) for row in rows]

# Load conversation data
def load_conversation_data():
    #cursor.execute("SELECT * FROM student_data")
    cursor.execute("SELECT * FROM student_conversations")
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    return [dict(zip(columns, row)) for row in rows]

# Tutor dashboard UI
def display_tutor_ui():
    st.title("📋 Tutor Dashboard")
    tab1, tab2, tab3 = st.tabs(["📋 Student Overview", "📊 Analyse", "📚 Upload Slides"])

    student_data = load_student_data()
    conversation_data = load_conversation_data()

    with tab1:
        # Format student data
        table_data = [{
        "ID": entry.get("id"),
        "Student": entry.get("username"),
        "Timestamp": entry.get("timestamp"),  # could be None or missing
        "Grade": entry.get("grade"),
        "Questions": entry.get("questions"),
        "Feedback": entry.get("feedback")
        } for entry in student_data]

        df = pd.DataFrame(table_data)
        
        # Debug step: print columns to check
        # st.write("📋 Available columns:", df.columns.tolist())
        # st.write(list(df.columns))

        if "Timestamp" in df.columns: 
            df['Timestamp'] = pd.to_datetime(df['Timestamp'], errors='coerce')
            df = df.sort_values(by="Timestamp", ascending=False)
        else: 
            st.warning (" 'Timestamp' column missing in student data.")
        
        search_query = st.text_input("Search student data by student name, grade, or ID", "").strip().lower()
        show_top_5 = st.checkbox("Show Only Top 5 Rows", value=True)
        
        # Filter data
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

        st.write("#### Student Data (for best viewing, download and top right align):")
        if not filtered_df.empty:
            st.dataframe(filtered_df[["ID", "Student", "Timestamp", "Grade", "Questions", "Feedback"]],
                         width=1000, height=400)
            # Add dropdown to select a student row by ID
            selected_id = st.selectbox("🔍 Select a Student ID to view full details:", filtered_df["ID"].tolist())
            selected_row = filtered_df[filtered_df["ID"] == selected_id].iloc[0]
            
            # Expandable section for full details
            with st.expander(f"📄 Full Details for {selected_row['Student']} (ID: {selected_row['ID']})"):
                st.markdown(f"**Grade:** {selected_row['Grade']}")
                st.markdown("**Questions Asked:**")
                st.code(selected_row['Questions'], language="markdown")
                st.markdown("**Feedback:**")
                st.info(selected_row['Feedback'])

                # Automatically find conversation by student name
                matching_logs = [entry for entry in conversation_data if entry["username"] == selected_row["Student"]]

                if matching_logs:
                    log = matching_logs[-1]  # Get most recent
                    try:
                        messages = json.loads(log["messages"])
                        st.markdown(f"### 🗨️ Conversation Log (ID: {log['id']}) on {log['timestamp']}")
                        for msg in messages:
                            role = msg.get("role", "user")
                            content = msg.get("content", "")
                            st.chat_message(role).markdown(content)
                    except Exception as e:
                        st.error(f"❌ Error loading messages: {e}")
                else:
                    st.warning("⚠️ No conversation log found for this student.")
                
    with tab2:
        st.subheader("📊 Performance Analysis")
        student_df = pd.DataFrame(student_data)

        if not student_df.empty:
            student_df['timestamp'] = pd.to_datetime(student_df['timestamp'], errors='coerce')
            student_df = student_df.dropna(subset=["grade"])
            student_df["grade"] = student_df["grade"].str.upper().str.strip()

            st.write("### Grade Distribution")
            grade_counts = student_df["grade"].value_counts().reindex(["A", "B", "C", "D"]).fillna(0)
            st.bar_chart(grade_counts)

            st.write("### Submissions Over Time")
            time_series = student_df.groupby(student_df["timestamp"].dt.date).size()
            st.line_chart(time_series)

            st.markdown("---")
            st.subheader("🧑‍🎓 Individual Student Performance")
            student_names = student_df["username"].unique()
            selected_student = st.selectbox("Select a student", student_names)

            if selected_student:
                # latest_record = student_df[student_df["username"] == selected_student].iloc[-1]
                student_records = student_df[student_df["username"] == selected_student].copy()

                grade_map = {'A': 4, 'B': 3, 'C': 2, 'D': 1}
                reverse_map = {v: k for k, v in grade_map.items()}

                student_records = student_records[student_records["grade"].isin(grade_map.keys())]
                student_records["grade_num"] = student_records["grade"].map(grade_map)

                if not student_records.empty:
                    # Average grade calculation
                    avg_score = student_records["grade_num"].mean()
                    rounded_avg = round(avg_score)
                    overall_grade = reverse_map.get(rounded_avg, "N/A")

                    # Latest submission
                    latest_record = student_records.sort_values(by="timestamp").iloc[-1]

                    st.markdown(f"**📊 Overall Grade (Average):** {overall_grade}")
                    st.markdown(f"**📅 Latest Submission Date:** {latest_record['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
                    st.markdown(f"**📝 Latest Grade:** {latest_record['grade']}")
                    st.markdown(f"**Questions Asked:** {latest_record['questions']}")
                    questions_list = latest_record['questions'].split("\n")  # Assuming newline-separated questions
                    for q in questions_list:
                        if q.strip():  # Skip empty lines
                            st.markdown(f"- {q.strip()}")
                    st.markdown("**Feedback:**")
                    st.info(latest_record['feedback'])

                else:
                    st.warning("No valid grade data available for this student.")
                    #st.markdown(f"**Latest Submission Date:** {latest_record['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
                    #st.markdown(f"**Grade:** {latest_record['grade']}")
                    #st.markdown(f"**Questions Asked:** {latest_record['questions']}")
                    #st.markdown("**Feedback:**")
                    #st.info(latest_record['feedback'])
        else:
            st.info("No student data available for analysis.")

    with tab3:
        upload_and_index_pdf()
