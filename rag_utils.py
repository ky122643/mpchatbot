# rag_utils.py
from langchain.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import PyPDFLoader
from langchain.chains import RetrievalQA
from langchain.chat_models import ChatOpenAI
import os

embedding = OpenAIEmbeddings()

def create_or_load_faiss_index(pdf_path="slides/Lecture1.pdf", index_path="faiss_index"):
    if os.path.exists(index_path):
        return FAISS.load_local(index_path, embedding)

    loader = PyPDFLoader(pdf_path)
    pages = loader.load()

    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    docs = splitter.split_documents(pages)

    vectorstore = FAISS.from_documents(docs, embedding)
    vectorstore.save_local(index_path)
    return vectorstore

def query_rag(user_question):
    vectorstore = create_or_load_faiss_index()
    qa_chain = RetrievalQA.from_chain_type(
        llm=ChatOpenAI(model="gpt-4"),
        retriever=vectorstore.as_retriever()
    )
    return qa_chain.run(user_question)
