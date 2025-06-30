import os
import tempfile
import shutil
import fitz  # PyMuPDF
import streamlit as st

def upload_and_index_pdf():
    uploaded_file = st.file_uploader("Upload Lecture PDF", type=["pdf"])

    if uploaded_file:
        # Create a permanent directory if not exists
        os.makedirs("uploaded_slides", exist_ok=True)

        # Save permanently with the original file name
        permanent_path = os.path.join("uploaded_slides", uploaded_file.name)
        with open(permanent_path, "wb") as f:
            f.write(uploaded_file.read())

        st.success(f"✅ File permanently saved to: `{permanent_path}`")

        # Now process the PDF (e.g. for RAG indexing)
        try:
            doc = fitz.open(permanent_path)
            st.success(f"📄 Successfully indexed `{uploaded_file.name}` with {len(doc)} pages.")
            return doc  # You can return it for indexing if needed
        except Exception as e:
            st.error(f"⚠️ Failed to read PDF: {e}")
            return None
