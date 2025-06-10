import os
import re
import json
import streamlit as st
import fitz  # PyMuPDF
#from dotenv import load_dotenv
#load_dotenv()

UPLOAD_FOLDER = "uploaded_slides"
INDEX_FILE = "slides_index.json"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    texts = []
    for page_num, page in enumerate(doc, start=1):
        blocks = page.get_text("blocks")
        blocks.sort(key=lambda b: (b[1], b[0]))  # top to bottom, then left to right
        page_text = "\n".join(block[4].strip() for block in blocks if block[4].strip())
        texts.append({"page": page_num, "text": clean_text(page_text)})
    return texts

def clean_text(text):
    text = re.sub(r"\s+", " ", text)
    text = text.replace("•", "-")
    return text.strip()

def save_indexed_data(filename, pages):
    # Load existing index
    if os.path.exists(INDEX_FILE):
        with open(INDEX_FILE, "r", encoding="utf-8") as f:
            index_data = json.load(f)
    else:
        index_data = []

    # Add new entry
    index_data.append({
        "filename": filename,
        "pages": pages
    })

    # Save updated index
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(index_data, f, indent=2)

def upload_and_index_pdf():
    st.title("📚 Upload Lecture Slides")

    uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])
    if uploaded_file:
        upload_path = os.path.join(UPLOAD_FOLDER, uploaded_file.name)

        # Save uploaded file
        with open(upload_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        st.success(f"✅ {uploaded_file.name} uploaded successfully!")

        with st.spinner("🔍 Extracting text and saving to index..."):
            page_texts = extract_text_from_pdf(upload_path)
            save_indexed_data(uploaded_file.name, page_texts)

        st.success("✅ Lecture slides indexed successfully!")

