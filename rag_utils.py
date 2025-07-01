import os
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.text_splitter import CharacterTextSplitter
from langchain.document_loaders import PyPDFLoader
import streamlit as st

def upload_and_index_pdf():
    uploaded_file = st.file_uploader("Upload a PDF", type=["pdf"])
    if uploaded_file is not None:
        # Save the PDF
        os.makedirs("slides", exist_ok=True)
        save_path = os.path.join("slides", uploaded_file.name)
        with open(save_path, "wb") as f:
            f.write(uploaded_file.read())

        # Load and split PDF
        loader = PyPDFLoader(save_path)
        pages = loader.load()
        splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        docs = splitter.split_documents(pages)

        # Create vectorstore
        embeddings = OpenAIEmbeddings()
        vectorstore = FAISS.from_documents(docs, embeddings)

        # Save vectorstore locally
        os.makedirs("vectorstore", exist_ok=True)
        vectorstore.save_local("vectorstore")
        st.success("✅ Slides indexed and saved to vectorstore.")

def load_vectorstore():
    embeddings = OpenAIEmbeddings()
    return FAISS.load_local("vectorstore", embeddings, allow_dangerous_deserialization=True)
