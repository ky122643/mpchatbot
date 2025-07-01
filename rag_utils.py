import os
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.text_splitter import CharacterTextSplitter
from langchain.document_loaders import PyPDFLoader
import streamlit as st

print("✅ rag_utils.py imported successfully")

def load_vectorstore():
    from langchain.vectorstores import FAISS
    from langchain.embeddings.openai import OpenAIEmbeddings
    embeddings = OpenAIEmbeddings()
    return FAISS.load_local("vectorstore", embeddings, allow_dangerous_deserialization=True)

def upload_and_index_pdf():
    pass
