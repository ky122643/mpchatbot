import os
import re
import streamlit as st
import tempfile
import fitz  # PyMuPDF
from langchain.embeddings import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma
from langchain.docstore.document import Document
from dotenv import load_dotenv

load_dotenv()

UPLOAD_FOLDER = "uploaded_slides"
VECTOR_DB_DIR = "slides_index"

embeddings = OpenAIEmbeddings()
vectordb = Chroma(
    collection_name="mp_collection",
    persist_directory=VECTOR_DB_DIR,
    embedding_function= embeddings
)

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    texts = []
    for page in doc:
        blocks = page.get_text("blocks")
        blocks.sort(key=lambda b: (b[1], b[0]))
        page_text = "\n".join(block[4].strip() for block in blocks if block[4].strip())
        texts.append(page_text)
    return texts

def split_into_chunks(texts, filename):
    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
    chunks = []
    for i, text in enumerate(texts):
        docs = splitter.create_documents([text], metadatas=[{"source": filename, "page": i + 1}])
        chunks.extend(docs)
    return chunks

def clean_text(text):
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"•", "-", text)
    return text.strip()

def upload_and_index_pdf():
    st.title("📚 Upload Lecture Slides")

    uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])
    if uploaded_file:
        #with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf", dir=UPLOAD_FOLDER) as tmp_file:
            #tmp_file.write(uploaded_file.getvalue())
            #tmp_file_path = tmp_file.name

        #with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf", dir=UPLOAD_FOLDER) as tmp_file:
            #tmp_file.write(uploaded_file.getvalue())
            #tmp_file_path = tmp_file.name  # Save the path
            # File is now closed and usable

        # Define full path for saving uploaded file
        upload_path = os.path.join(UPLOAD_FOLDER, uploaded_file.name)

        # Save the uploaded PDF directly (no tempfile needed)
        with open(upload_path, "wb") as f:
            f.write(uploaded_file.getbuffer())


        st.success(f"✅ {uploaded_file.name} uploaded successfully!")

        with st.spinner("🔍 Extracting text and updating vector store..."):
            #page_texts = extract_text_from_pdf(tmp_file_path)
            page_texts = extract_text_from_pdf(upload_path)
            docs = [
                Document(page_content=page, metadata={"source": uploaded_file.name, "page": i + 1}) 
                for i, page in enumerate(page_texts)
                ]

            # Index with ChromaDB
            embeddings = OpenAIEmbeddings()
            #vectordb = Chroma(collection_name="mp_collection",persist_directory=VECTOR_DB_DIR, embedding_function=embeddings)
            #vectordb.add_documents(docs)
            #vectordb.persist()
            vectordb = Chroma(
            collection_name="mp_collection",
            persist_directory=VECTOR_DB_DIR,
            embedding_function=embeddings
            )
            vectordb.add_documents(docs)
            vectordb.persist()

        st.success("✅ Lecture slides added to the vector store successfully!")

