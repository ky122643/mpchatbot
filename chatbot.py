import streamlit as st
import sqlite3
import os
import json
import re 
from datetime import datetime
from openai import OpenAI
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings
from langchain_openai import OpenAIEmbeddings
# from dotenv import load_dotenv

# load_dotenv(override=True)
# initialize SQLite database connection
db_path = "datab.db"
conn = sqlite3.connect(db_path, check_same_thread=False)
cursor = conn.cursor()

# create tables if they don't exist
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

# load API key
#os.environ["OPENAI_API_KEY"] = "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"
# openai_api_key = os.getenv("api_key")  # in environment variables
# # #openai_api_key = open('api_key.txt', 'r')
# client = OpenAI(api_key=openai_api_key)

# function to load text files
def load_file(filename):
    with open(filename, "r") as file:
        return file.read()

# load context and grading criteria
interviewee_context = load_file("context.txt")
grading_criteria = load_file("grading_criteria.txt")

#set up RAG retriever
embedding = OpenAIEmbeddings(openai_api_key=openai_api_key)
vectorstore = Chroma(persist_directory="rag_db", embedding_function=embedding)
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

# function to evaluate performance
def evaluate_performance(questions):
    performance_prompt = f"""
    {grading_criteria}

    The following is the list of questions asked by the student. Evaluate their performance.

    Student's questions:
    {questions}
    """

    # generate feedback using preset prompt
    stream = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": performance_prompt}],
        stream=True
    )

    feedback_response = ""  # empty string for feedback

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


# function to save student data
def save_student_data(username, grade, questions, feedback):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    questions_text = "\n".join(questions)
    
    cursor.execute("""
    INSERT INTO student_data (username, timestamp, grade, questions, feedback)
    VALUES (?, ?, ?, ?, ?)
    """, (username, timestamp, grade, questions_text, feedback))
    conn.commit()
    st.success("Student data saved successfully!")


# function to save student conversation
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


# function to load student conversation
def load_conversations(username):
    cursor.execute("""
    SELECT messages FROM student_conversations
    WHERE username = ?
    ORDER BY timestamp ASC
    """, (username,))
    results = cursor.fetchall()

    if not results:  # No conversations found
        return []

    conversations = []
    for result in results:
        raw_messages = result[0]
        if not raw_messages:  # Handle empty messages field
            continue
        try:
            # Split by "user:" or "assistant:" and keep the entire message together
            messages = []
            current_role = None
            current_content = []
            
            for line in raw_messages.split("\n"):
                if line.startswith("user:"):
                    if current_role:
                        # Add the previous message if any
                        messages.append({
                            "role": current_role,
                            "content": "\n".join(current_content).strip()
                        })
                    current_role = "user"
                    current_content = [line.split(": ", 1)[1]]  # Initialize content for this message
                elif line.startswith("assistant:"):
                    if current_role:
                        # Add the previous message if any
                        messages.append({
                            "role": current_role,
                            "content": "\n".join(current_content).strip()
                        })
                    current_role = "assistant"
                    current_content = [line.split(": ", 1)[1]]  # Initialize content for this message
                else:
                    # Continue appending lines to the current message content
                    current_content.append(line.strip())
            
            # Don't forget to add the last message
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


# function to reset conversation
def reset_conversation():
    st.session_state.messages = [
        {"role": "system", "content": interviewee_context},
        {"role": "assistant", "content": "Hi, I'm here to help you with questions about the manufacturing process."}
    ]
    st.session_state.user_questions = []
    st.session_state.conversation_ended = False

# chatbot page
def chatbot_page():
    # initialize session state attributes
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
    st.write(
        "This is an chatbot you can ask interview and questions related to the manufacturing process. "
        "You will receive feedback at the end of the conversation."
    )

    # load student conversations on app load
    if not st.session_state.get("conversations_loaded", False):
        st.session_state.conversations = load_conversations(st.session_state.username)
        st.session_state.conversations_loaded = True

    # sidebar to display previous conversations
    st.sidebar.title(f"{st.session_state.username}'s Past Conversations")
    if st.session_state.conversations:
        for idx, conv in enumerate(st.session_state.conversations):
            # Try to get a short user message for preview
            preview = next((msg["content"] for msg in conv if msg["role"] == "user"), "No user message")
            preview_snippet = preview[:40] + "..." if len(preview) > 40 else preview

            # Get timestamp from the database
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

    # reset review mode when starting a new conversation
    if st.button("🔥 Start New Conversation (remember to save your conversations!)"):
        reset_conversation()
        st.session_state.is_review_mode = False

    # display current conversation
    for message in st.session_state.messages:
        if message["role"] != "system":
            role = "assistant" if message["role"] == "assistant" else "user"
            st.chat_message(role).markdown(message["content"])


    # chat input and assistant response
    if not st.session_state.conversation_ended and not st.session_state.is_review_mode:
        if user_input := st.chat_input("Ask a question about the manufacturing process:", key="user_input"):
            st.session_state.messages.append({"role": "user", "content": user_input})
            st.session_state.user_questions.append(user_input)
            st.chat_message("user").markdown(user_input)

            # 🔍 Retrieve relevant slide context
            docs = retriever.get_relevant_documents(user_input, k=3)
            retrieved_context = "\n\n".join(doc.page_content for doc in docs)
            with st.expander("🔍 Retrieved Context (from lecture slides)"):
                st.markdown(retrieved_context)

            try:
                docs = retriever.get_relevant_documents(user_input, k=3)
            except Exception as e:
                st.error(f"RAG retrieval failed: {e}")
                docs = []

            # 🔧 Add retrieved context to system message
            rag_message = {
            "role": "system",
            "content": f"The following context from lecture slides may help answer the user's question:\n\n{retrieved_context}"
            }

            # 📦 Inject context just before user's message
            conversation = st.session_state.messages[:-1] + [rag_message, st.session_state.messages[-1]]

            # 🤖 Get assistant response using context
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

    # handle conversation end and saving
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

