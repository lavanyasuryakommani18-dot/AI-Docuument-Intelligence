import streamlit as st
from pypdf import PdfReader

st.set_page_config(
    page_title="AI Document Intelligence",
    page_icon="🤖"
)

st.title("🤖 AI Document Intelligence Platform")
st.write("Upload a PDF or TXT document and analyze its content.")

uploaded_file = st.file_uploader(
    "📄 Upload your document",
    type=["pdf", "txt"]
)

if uploaded_file is not None:

    st.success("Document uploaded successfully! ✅")

    text = ""

    if uploaded_file.type == "application/pdf":
        reader = PdfReader(uploaded_file)

        for page in reader.pages:
            page_text = page.extract_text()

            if page_text:
                text += page_text + "\n"

    elif uploaded_file.type == "text/plain":
        text = uploaded_file.read().decode("utf-8")

    if text.strip():
        st.subheader("📋 Extracted Document Text")

        st.text_area(
            "Document content",
            text,
            height=300
        )

        st.success("✅ Document text extracted successfully!")

    else:
        st.warning("⚠️ No readable text found in this document.")