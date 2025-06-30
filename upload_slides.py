# upload_slides.py

import os
import tempfile
import streamlit as st
from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma

def upload_and_index_pdf():
    st.subheader("📚 Upload Slides (Tutor Only)")
    uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])
    if uploaded_file:
        # Save to temp
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(uploaded_file.read())
            tmp_path = tmp_file.name

        # Read PDF
        reader = PdfReader(tmp_path)
        text = "\n".join(page.extract_text() for page in reader.pages if page.extract_text())

        # Split
        splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
        docs = splitter.create_documents([text])

        # Embed and Store using Chroma
        embeddings = OpenAIEmbeddings()
        persist_directory = "rag_chroma_db"
        vectorstore = Chroma.from_documents(documents=docs, embedding=embeddings, persist_directory=persist_directory)
        vectorstore.persist()

        st.success("Slides uploaded and indexed successfully!")


