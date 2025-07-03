import streamlit as st
import sqlite3
import os
import json
import re 
from datetime import datetime
from openai import OpenAI
from langchain.vectorstores import FAISS
from langchain.embeddings.openai import OpenAIEmbeddings
from rag_utils import load_vectorstore

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

def load_vectorstore():
    if os.path.exists("vectorstore"):
        embeddings = OpenAIEmbeddings()
        return FAISS.load_local("vectorstore", embeddings)
    return None

# function to evaluate performance
def evaluate_performance(questions, client):
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
        raw_json = result[0]
        try:
            messages = json.loads(raw_json)
            conversations.append(messages)
        except json.JSONDecodeError as e:
            st.error(f"Failed to load conversation: {e}")
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
def chatbot_page(client):
    # Load vectorstore with fallback
    try:
        vectorstore = load_vectorstore()
    except Exception as e:
        vectorstore = None
        st.warning("⚠️ Could not load vectorstore. Falling back to general GPT.")

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

    def user_bubble(text):
        bubble_html = f"""
        <div style="
            background-color:#DCF8C6; 
            color: #000000;
            padding: 10px 15px; 
            border-radius: 20px 20px 0 20px;
            max-width: 70%;
            margin-left: auto; 
            margin-bottom: 10px;
            font-family: Arial, sans-serif;
            box-shadow: 1px 1px 3px rgba(0,0,0,0.1);
        ">
            {text}
        </div>
        """
        st.markdown(bubble_html, unsafe_allow_html=True)

    def assistant_bubble(text):
        bubble_html = f"""
        <div style="
            background-color:#F1F0F0; 
            color: #000000;
            padding: 10px 15px; 
            border-radius: 20px 20px 20px 0;
            max-width: 70%;
            margin-right: auto;
            margin-bottom: 10px;
            font-family: Arial, sans-serif;
            box-shadow: 1px 1px 3px rgba(0,0,0,0.1);
        ">
            {text}
        </div>
        """
        st.markdown(bubble_html, unsafe_allow_html=True)
        
    for message in st.session_state.messages:
        if message["role"] != "system":
            if message["role"] == "user":
                user_bubble(message["content"])
            else:
                assistant_bubble(message["content"])

    if not st.session_state.conversation_ended and not st.session_state.is_review_mode:
        if user_input := st.chat_input("Ask a question about the manufacturing process:", key="user_input"):
            st.session_state.messages.append({"role": "user", "content": user_input})
            st.session_state.user_questions.append(user_input)
            st.chat_message("user").markdown(user_input)

            # Try RAG context
            retrieved_docs = []
            if vectorstore:
                try:
                    retriever = vectorstore.as_retriever()
                    retrieved_docs = retriever.get_relevant_documents(user_input)
                except Exception as e:
                    st.warning("⚠️ Retrieval failed. Proceeding without slide context.")

            context = "\n\n".join(doc.page_content for doc in retrieved_docs[:3]) if retrieved_docs else ""

            messages = [
                {"role": "system", "content": "You are an expert on the manufacturing process. Use the context from the slides if it's relevant."},
            ]
            if context:
                messages.append({"role": "system", "content": f"Relevant context from slides:\n{context}"})

            messages.extend(st.session_state.messages)

            stream = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
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
        feedback, grade = evaluate_performance(st.session_state.user_questions, client)
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
