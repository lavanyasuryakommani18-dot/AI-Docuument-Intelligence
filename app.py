import streamlit as st
from pypdf import PdfReader
from google import genai
import base64

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
    pdf_bytes = None
    is_scanned_pdf = False

    # PDF
    if uploaded_file.type == "application/pdf":

        pdf_bytes = uploaded_file.getvalue()

        reader = PdfReader(uploaded_file)

        for page in reader.pages:
            page_text = page.extract_text()

            if page_text:
                text += page_text + "\n"

        # Detect scanned PDF
        if not text.strip():
            is_scanned_pdf = True

    # TXT
    elif uploaded_file.type == "text/plain":

        text = uploaded_file.read().decode("utf-8")


    # -----------------------------
    # TEXT PDF / TXT
    # -----------------------------

    if text.strip():

        st.subheader("📋 Extracted Document Text")

        st.text_area(
            "Document content",
            text,
            height=250
        )

        st.success("✅ Document text extracted successfully!")


    # -----------------------------
    # SCANNED PDF
    # -----------------------------

    elif is_scanned_pdf:

        st.info(
            "📷 Scanned/Image PDF detected. "
            "Gemini AI will read the document directly."
        )


    else:

        st.warning(
            "⚠️ No readable text found in this document."
        )


    # -----------------------------
    # AI SECTION
    # -----------------------------

    if text.strip() or is_scanned_pdf:

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
                    "Gemini API key not found. "
                    "Please check Streamlit Secrets."
                )

            elif option == "Ask Questions" and not question.strip():

                st.warning("Please enter a question.")

            else:

                # -----------------------------
                # PROMPTS
                # -----------------------------

                if option == "Summarize Document":

                    prompt = """
You are an AI document analysis assistant.

Summarize this document in simple and clear language.

Include the main points and important information.
Do not invent information.
"""


                elif option == "Extract Important Information":

                    prompt = """
You are an AI document analysis assistant.

Extract the important information from this document.

Use clear headings and bullet points.
Do not invent information.
"""


                elif option == "Classify Document":

                    prompt = """
You are an AI document classification system.

Identify the type/category of this document.

Also explain briefly why you selected that category.
"""


                else:

                    prompt = f"""
You are an AI document question-answering assistant.

Answer the user's question ONLY using information
present in the document.

If the answer is not available in the document, say:

"Answer not found in the document."

USER QUESTION:
{question}
"""


                try:

                    with st.spinner(
                        "🤖 AI is analyzing the document..."
                    ):

                        # SCANNED PDF
                        if is_scanned_pdf:

                            pdf_base64 = base64.b64encode(
                                pdf_bytes
                            ).decode("utf-8")

                            response = client.interactions.create(

                                model="gemini-3.5-flash-lite",

                                input=[
                                    {
                                        "type": "text",
                                        "text": prompt
                                    },
                                    {
                                        "type": "document",
                                        "data": pdf_base64,
                                        "mime_type": "application/pdf"
                                    }
                                ]
                            )


                        # TEXT PDF / TXT
                        else:

                            full_prompt = f"""
{prompt}

DOCUMENT:
{text}
"""

                            response = client.interactions.create(

                                model="gemini-3.5-flash-lite",

                                input=full_prompt
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
