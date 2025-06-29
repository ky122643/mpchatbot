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
    cursor.execute("SELECT * FROM student_data")
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

                matching_logs = [entry for entry in conversation_data if str(entry.get("username")) == str(selected_row.get("Student"))]

                if matching_logs:
                    log = matching_logs[-1]
                    st.markdown(f"**Conversation on {log['timestamp']}**")

                # Show chat style
                    messages = json.loads(log["messages"])
                    st.write("### 🗨️ Conversation Log")
                    for msg in messages:
                        if msg["role"] == "user":
                            st.chat_message("user").markdown(msg["content"])
                        elif msg["role"] == "assistant":
                            st.chat_message("assistant").markdown(msg["content"])

                    st.markdown("### 📝 Feedback")
                    st.markdown(f"**Grade:** {selected_row['Grade']}")
                    st.markdown("**Summary Feedback:**")
                    st.info(selected_row["Feedback"])
                else:
                    st.warning("No conversation log found for this student.")
                    
        else:
            st.write("No data found for the current query.")

        #st.markdown('##')
        #st.write("### Conversation Finder:")
        #conversation_search_id = st.text_input("Search conversation logs by ID", "").strip()

        #if conversation_search_id:
            #matching_logs = [entry for entry in conversation_data if str(entry['id']) == conversation_search_id]
            #if matching_logs:
                #log = matching_logs[0]
                #st.write(f"### Conversation Log for ID {log['id']} - {log['username']} ({log['timestamp']}):")

                # Parse messages
                #conversation_lines = log["messages"].split("\n")
                #current_role, current_message = None, []

                #for line in conversation_lines:
                    #if line.startswith("user:"):
                        #if current_message:
                            #st.markdown(f"**{current_role.capitalize()}:** {' '.join(current_message)}")
                        #current_role = "user"
                        #current_message = [line[5:].strip()]
                    #elif line.startswith("assistant:"):
                        #if current_message:
                            #st.markdown(f"**{current_role.capitalize()}:** {' '.join(current_message)}")
                        #current_role = "assistant"
                        #current_message = [line[10:].strip()]
                    #else:
                        #current_message.append(line.strip())

                #if current_message:
                    #st.markdown(f"**{current_role.capitalize()}:** {' '.join(current_message)}")
            #else:
                #st.write("No conversation log found for the given ID.")
                
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
                latest_record = student_df[student_df["username"] == selected_student].iloc[-1]
                st.markdown(f"**Latest Submission Date:** {latest_record['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
                st.markdown(f"**Grade:** {latest_record['grade']}")
                st.markdown(f"**Questions Asked:** {latest_record['questions']}")
                st.markdown("**Feedback:**")
                st.info(latest_record['feedback'])
        else:
            st.info("No student data available for analysis.")

    with tab3:
        upload_and_index_pdf()
