import streamlit as st
from pypdf import PdfReader
from google import genai

st.set_page_config(
    page_title="AI Document Intelligence",
    page_icon="🤖"
)

st.title("🤖 AI Document Intelligence Platform")
st.write("Upload a PDF or TXT document and use AI to analyze it.")

# Gemini API
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    client = genai.Client(api_key=api_key)
except Exception:
    client = None

# Upload document
uploaded_file = st.file_uploader(
    "📄 Upload your document",
    type=["pdf", "txt"]
)

if uploaded_file is not None:

    st.success("Document uploaded successfully! ✅")

    text = ""

    # PDF extraction
    if uploaded_file.type == "application/pdf":
        reader = PdfReader(uploaded_file)

        for page in reader.pages:
            page_text = page.extract_text()

            if page_text:
                text += page_text + "\n"

    # TXT extraction
    elif uploaded_file.type == "text/plain":
        text = uploaded_file.read().decode("utf-8")

    # Show extracted text
    if text.strip():

        st.subheader("📋 Extracted Document Text")

        st.text_area(
            "Document content",
            text,
            height=250
        )

        st.success("✅ Document text extracted successfully!")

        # AI section
        st.subheader("🤖 AI Document Analysis")

        option = st.selectbox(
            "Choose an AI action",
            [
                "Summarize Document",
                "Extract Important Information",
                "Classify Document",
                "Ask Questions"
            ]
        )

        question = ""

        if option == "Ask Questions":
            question = st.text_input(
                "❓ Enter your question about the document"
            )

        if st.button("✨ Generate AI Result"):

            if client is None:
                st.error(
                    "Gemini API key not found. Please check Streamlit Secrets."
                )

            elif option == "Ask Questions" and not question.strip():
                st.warning("Please enter a question.")

            else:

                if option == "Summarize Document":

                    prompt = f"""
You are an AI document analysis assistant.

Summarize the following document in simple and clear language.

DOCUMENT:
{text}
"""

                elif option == "Extract Important Information":

                    prompt = f"""
You are an AI document analysis assistant.

Extract the important information from the following document.

Give the result using clear headings and bullet points.

DOCUMENT:
{text}
"""

                elif option == "Classify Document":

                    prompt = f"""
You are an AI document classification system.

Identify what type of document this is.
Also explain briefly why you selected that category.

DOCUMENT:
{text}
"""

                else:

                    prompt = f"""
You are an AI document question-answering assistant.

Answer the user's question only using the information present
in the document.

If the answer is not available in the document, say:
"Answer not found in the document."

DOCUMENT:
{text}

USER QUESTION:
{question}
"""

                try:

                    with st.spinner("🤖 AI is analyzing the document..."):

                        response = client.interactions.create(
                            model="gemini-3.5-flash-lite",
                            input=prompt
                        )

                        result = response.output_text

                    st.subheader("🧠 AI Result")

                    st.write(result)

                    st.download_button(
                        "⬇️ Download AI Result",
                        result,
                        file_name="AI_Document_Result.txt",
                        mime="text/plain"
                    )

                except Exception as e:

                    st.error(
                        f"Something went wrong: {e}"
                    )

    else:

        st.warning(
            "⚠️ No readable text found in this document."
        )
