import sqlite3
import streamlit as st
import pandas as pd
from datetime import datetime


# initialize SQLite database connection
db_path = "datab.db"
conn = sqlite3.connect(db_path, check_same_thread=False)
cursor = conn.cursor()


# function to load student data
def load_student_data():
    cursor.execute("SELECT * FROM student_data")
    rows = cursor.fetchall()
    columns = [desc[0].lower() for desc in cursor.description] 
    data = [dict(zip(columns, row)) for row in rows]
    return data

# function to load conversation data
def load_conversation_data():
    cursor.execute("SELECT * FROM student_conversations")
    rows = cursor.fetchall()
    columns = [desc[0].lower() for desc in cursor.description]
    data = [dict(zip(columns, row)) for row in rows]
    return data


# tutor UI
def display_tutor_ui():
    st.title("📋 Tutor Dashboard")
    
    # load student data and conversation logs
    student_data = load_student_data()
    conversation_data = load_conversation_data()

    # process student data for display
    table_data = []
    for entry in student_data:
        table_data.append({
            "ID": entry["id"],
            "Student": entry["username"],
            "Timestamp": entry["timestamp"],
            "Grade": entry["grade"],
            "Questions": entry["questions"],
            "Feedback": entry["feedback"]
        })

    # if no data, create empty DataFrame
    if not table_data:
        df = pd.DataFrame(columns=["ID", "Student", "Timestamp", "Grade", "Questions", "Feedback"])
    else:
        df = pd.DataFrame(table_data)

    if "Timestamp" in df.columns:
        df['Timestamp'] = pd.to_datetime(df['Timestamp'], errors='coerce')
    else:
        st.error("Timestamp column not found in student data!")
        return


    # sort by time
    df = df.sort_values(by=['Timestamp'], ascending=False)

    # toggle button for showing top 5 rows
    show_top_5 = st.checkbox("Show Only Top 5 Rows", value=True)

    
    # search bar
    search_query = st.text_input("Search student data by student name, grade, or ID", "").strip().lower()

    # apply search filters
    filtered_data = [
        entry for entry in table_data
        if (
            # check if the query is a grade ("a", "b", "c", "d") and match grade
            (len(search_query) == 1 and search_query in ["a", "b", "c", "d"] 
             and entry['Grade'].lower() == search_query)
            or
            # else treat the query as a student name or ID
            (
                len(search_query) > 1
                or search_query not in ["a", "b", "c", "d"]
            )
            and (
                search_query in entry['Student'].lower() 
                or search_query in str(entry['ID']).lower()
            )
        )
        # exclude entries with "Grade not found, please review manually"
        and entry['Grade'].lower() != "grade not found, please review manually"
    ]
    
    # convert to DataFrame
    filtered_df = pd.DataFrame(filtered_data)
    
    # apply top5 filtering if checkbox is ticked
    if show_top_5 and not filtered_df.empty:
        filtered_df = filtered_df.head(5)
    
    # display data
    st.write("### Student Data (for best viewing, download and top left align):")
    if not filtered_df.empty:
        st.dataframe(filtered_df[['ID', 'Student', 'Timestamp', 'Grade', 'Questions', 'Feedback']], width=1000, height=400)
    else:
        st.write("No data found for the current query.")


    st.markdown('##')

    
    # add conversation transcript finder
    st.write("### Conversation Finder:")
    conversation_search_id = st.text_input("Search conversation logs by ID", "").strip()
    
    # check if the ID exists in conversation data to pull up conversation log
    if conversation_search_id:
        matching_logs = [
            entry for entry in conversation_data if str(entry['id']) == conversation_search_id
        ]
    
        if matching_logs:
            log = matching_logs[0]
            st.write(f"### Conversation Log for ID {log['id']} - {log['username']} ({log['timestamp']}):")
            
            # join as one block
            conversation_lines = log["messages"].split("\n")
            
            # accumulate user and assistant messages
            current_role = None
            current_message = []
    
            for line in conversation_lines:
                if line.startswith("user:"):
                    # when new user message, flush previous message
                    if current_role == "user" or current_role == "assistant":
                        st.markdown(f"**{current_role.capitalize()}:** {'\n'.join(current_message)}")
                    current_role = "user"
                    current_message = [line[5:].strip()]  # remove "user:" part
                elif line.startswith("assistant:"):
                    # same but for assistant
                    if current_role == "user" or current_role == "assistant":
                        st.markdown(f"**{current_role.capitalize()}:** {'\n'.join(current_message)}")
                    current_role = "assistant"
                    current_message = [line[10:].strip()]
                else:
                    # continue appending messages
                    current_message.append(line.strip())
    
            if current_role:
                st.markdown(f"**{current_role.capitalize()}:** {'\n'.join(current_message)}")
        else:
            st.write("No conversation log found for the given ID.")
            
    if __name__ == "__main__":
        display_tutor_ui()
