import streamlit as st
import sqlite3
import os
import json
import re 
from datetime import datetime
from openai import OpenAI
# from dotenv import load_dotenv

# load_dotenv(override=True)
db_path = "datab.db"
conn = sqlite3.connect(db_path, check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS student_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    timestamp TEXT,
    grade TEXT,
    questions TEXT,
    feedback TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS student_conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    timestamp TEXT,
    messages TEXT
)
""")
conn.commit()

# load_file function
def load_file(filename):
    with open(filename, "r") as file:
        return file.read()

# load context and grading criteria
interviewee_context = load_file("context.txt")
grading_criteria = load_file("grading_criteria.txt")

# (💡 Ensure you define this key correctly for OpenAI to work)
# openai_api_key = os.getenv("api_key")
# client = OpenAI(api_key=openai_api_key)

# function to evaluate performance
def evaluate_performance(questions):
    performance_prompt = f"""
    {grading_criteria}

    The following is the list of questions asked by the student. Evaluate their performance.

    Student's questions:
    {questions}
    """

    stream = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": performance_prompt}],
        stream=True
    )

    feedback_response = ""
    for chunk in stream:
        content = getattr(chunk.choices[0].delta, "content", "") or ""
        feedback_response += content

    match = re.search(r"Grade:\s*([A-F][+-]?)", feedback_response)
    if match:
        grade = match.group(1)
        feedback_response = feedback_response[:match.start()].strip()
    else:
        grade = "Grade not found, please review manually."

    return feedback_response.strip(), grade

# save student data
def save_student_data(username, grade, questions, feedback):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    questions_text = "\n".join(questions)
    
    cursor.execute("""
    INSERT INTO student_data (username, timestamp, grade, questions, feedback)
    VALUES (?, ?, ?, ?, ?)
    """, (username, timestamp, grade, questions_text, feedback))
    conn.commit()
    st.success("Student data saved successfully!")

# save student conversation
def save_conversation(username, conversation):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    filtered_conversation = [msg for msg in conversation if msg["role"] != "system"]
    conversation_text = json.dumps(filtered_conversation)
    
    cursor.execute("""
    INSERT INTO student_conversations (username, timestamp, messages)
    VALUES (?, ?, ?)
    """, (username, timestamp, conversation_text))
    conn.commit()
    st.success("Conversation saved successfully!")

# load past conversations
def load_conversations(username):
    cursor.execute("""
    SELECT messages FROM student_conversations
    WHERE username = ?
    ORDER BY timestamp ASC
    """, (username,))
    results = cursor.fetchall()

    if not results:
        return []

    conversations = []
    for result in results:
        raw_messages = result[0]
        if not raw_messages:
            continue
        try:
            messages = []
            current_role = None
            current_content = []
            
            for line in raw_messages.split("\n"):
                if line.startswith("user:"):
                    if current_role:
                        messages.append({
                            "role": current_role,
                            "content": "\n".join(current_content).strip()
                        })
                    current_role = "user"
                    current_content = [line.split(": ", 1)[1]]
                elif line.startswith("assistant:"):
                    if current_role:
                        messages.append({
                            "role": current_role,
                            "content": "\n".join(current_content).strip()
                        })
                    current_role = "assistant"
                    current_content = [line.split(": ", 1)[1]]
                else:
                    current_content.append(line.strip())
            
            if current_role:
                messages.append({
                    "role": current_role,
                    "content": "\n".join(current_content).strip()
                })

            conversations.append(messages)
        except Exception as e:
            st.error(f"Error processing conversation data: {e}")
            continue
    return conversations

# reset conversation
def reset_conversation():
    st.session_state.messages = [
        {"role": "system", "content": interviewee_context},
        {"role": "assistant", "content": "Hi, I'm here to help you with questions about the manufacturing process."}
    ]
    st.session_state.user_questions = []
    st.session_state.conversation_ended = False

# chatbot UI
def chatbot_page():
    if "conversations" not in st.session_state:
        st.session_state.conversations = []

    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "system", "content": interviewee_context},
            {"role": "assistant", "content": "Hi, I'm here to help you with questions about the manufacturing process."}
        ]

    if "user_questions" not in st.session_state:
        st.session_state.user_questions = []

    if "username" not in st.session_state:
        st.session_state.username = "guest"

    if "conversation_ended" not in st.session_state:
        st.session_state.conversation_ended = False

    if "is_review_mode" not in st.session_state:
        st.session_state.is_review_mode = False

    st.title("📋 DAST Chatbot")
    st.write("This chatbot helps you ask interview-style questions about the manufacturing process.")

    if not st.session_state.get("conversations_loaded", False):
        st.session_state.conversations = load_conversations(st.session_state.username)
        st.session_state.conversations_loaded = True

    # Sidebar conversation history
    st.sidebar.title(f"{st.session_state.username}'s Past Conversations")
    if st.session_state.conversations:
        for idx, conv in enumerate(st.session_state.conversations):
            preview = next((msg["content"] for msg in conv if msg["role"] == "user"), "No user message")
            preview_snippet = preview[:40] + "..." if len(preview) > 40 else preview

            cursor.execute("""
            SELECT timestamp FROM student_conversations
            WHERE username = ?
            ORDER BY timestamp ASC
            LIMIT 1 OFFSET ?
            """, (st.session_state.username, idx))
            timestamp_result = cursor.fetchone()
            timestamp = timestamp_result[0] if timestamp_result else "Unknown time"

            if st.sidebar.button(f"📅 {timestamp} | 🗨️ {preview_snippet}"):
                st.session_state.is_review_mode = True
                st.session_state.messages = conv
                st.session_state.conversation_ended = True
                st.session_state.user_questions = [msg["content"] for msg in conv if msg["role"] == "user"]
    else:
        st.sidebar.write("No previous conversations found.")

    if st.button("🔥 Start New Conversation (remember to save your conversations!)"):
        reset_conversation()
        st.session_state.is_review_mode = False

    for message in st.session_state.messages:
        if message["role"] != "system":
            st.chat_message(message["role"]).markdown(message["content"])

    if not st.session_state.conversation_ended and not st.session_state.is_review_mode:
        if user_input := st.chat_input("Ask a question about the manufacturing process:", key="user_input"):
            st.session_state.messages.append({"role": "user", "content": user_input})
            st.session_state.user_questions.append(user_input)
            st.chat_message("user").markdown(user_input)

            conversation = st.session_state.messages

            stream = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=conversation,
                stream=True
            )

            assistant_response = ""
            for chunk in stream:
                content = getattr(chunk.choices[0].delta, "content", "") or ""
                assistant_response += content

            st.chat_message("assistant").markdown(assistant_response)
            st.session_state.messages.append({"role": "assistant", "content": assistant_response})
    else:
        st.write("This is a previously saved conversation and cannot be edited.")

    if st.button("Save and End Conversation") and not st.session_state.conversation_ended and not st.session_state.is_review_mode:
        st.markdown("### Analyzing your performance...")
        st.session_state.conversation_ended = True
        feedback, grade = evaluate_performance(st.session_state.user_questions)
        save_conversation(st.session_state.username, st.session_state.messages)
        save_student_data(st.session_state.username, grade, st.session_state.user_questions, feedback)
        st.markdown(f"**Feedback:** {feedback.strip()}")

        full_feedback_text = f"""Username: {st.session_state.username}
        Grade: {grade}

        Questions:
        {chr(10).join(st.session_state.user_questions)}

        Feedback:
        {feedback}
        """

        st.download_button(
            label="📄 Download Feedback",
            data=full_feedback_text,
            file_name=f"{st.session_state.username}_feedback.txt",
            mime="text/plain"
        )
