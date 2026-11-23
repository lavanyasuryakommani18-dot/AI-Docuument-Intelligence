import streamlit as st
from google import genai
from google.genai import types
import io
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from pypdf import PdfReader


# =================================
# PAGE SETTINGS
# =================================

st.set_page_config(
    page_title="AI Document Intelligence",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 AI Document Intelligence Platform")

st.write(
    "Upload PDF/TXT documents or enter a website URL "
    "to analyze information using AI."
)


# =================================
# GEMINI API CONFIGURATION
# =================================

# Primary model and backup model
MODEL_NAMES = [
    "gemini-3.1-flash-lite",
    "gemini-3.8-flash"
]

try:

    api_key = st.secrets["GEMINI_API_KEY"]

    client = genai.Client(
        api_key=api_key
    )

except Exception:

    client = None


# =================================
# COMMON AI FUNCTION WITH RETRY
# =================================

def generate_ai_result(contents):

    if client is None:
        raise Exception("Gemini API key is missing.")

    last_error = None

    for model_name in MODEL_NAMES:

        for attempt in range(2):

            try:

                response = client.models.generate_content(

                    model=model_name,

                    contents=contents,

                    config=types.GenerateContentConfig(
                        temperature=0.2,
                        max_output_tokens=900
                    )
                )

                result = response.text

                if not result:
                    raise Exception("Gemini returned an empty response.")

                return result

            except Exception as e:

                last_error = e

                error_message = str(e).upper()

                temporary_errors = [
                    "503",
                    "UNAVAILABLE",
                    "429",
                    "RESOURCE_EXHAUSTED",
                    "500",
                    "502",
                    "504",
                    "INTERNAL"
                ]

                is_temporary = any(
                    error in error_message
                    for error in temporary_errors
                )

                # Retry once for temporary errors
                if is_temporary and attempt == 0:

                    time.sleep(2)
                    continue

                # Move to backup model
                break

    raise Exception(
        "All Gemini models failed. "
        f"Last error: {last_error}"
    )


# =================================
# PDF TEXT EXTRACTION
# =================================

@st.cache_data(show_spinner=False)
def extract_document_text(pdf_bytes):

    reader = PdfReader(
        io.BytesIO(pdf_bytes)
    )

    extracted_text = []

    for page in reader.pages:

        page_text = page.extract_text()

        if page_text:

            extracted_text.append(page_text)

    return "\n".join(extracted_text)


# =================================
# WEBSITE CONTENT EXTRACTION
# =================================

@st.cache_data(
    ttl=600,
    show_spinner=False
)
def extract_website_content(url):

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(
        url,
        headers=headers,
        timeout=15
    )

    response.raise_for_status()

    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )

    for tag in soup([
        "script",
        "style",
        "nav",
        "footer",
        "header",
        "noscript"
    ]):

        tag.decompose()

    title = (
        soup.title.get_text(strip=True)
        if soup.title
        else "Website Content"
    )

    content = (
        soup.find("main")
        or soup.find("article")
        or soup.body
    )

    if content is None:

        return title, ""

    website_text = content.get_text(
        separator=" ",
        strip=True
    )

    return title, website_text


# =================================
# SECTION 1: DOCUMENT ANALYSIS
# =================================

st.header("📄 Document Analysis")

uploaded_file = st.file_uploader(
    "Upload your document",
    type=["pdf", "txt"]
)


if uploaded_file is not None:

    st.success(
        "Document uploaded successfully! ✅"
    )

    text = ""
    pdf_bytes = None
    is_scanned_pdf = False

    # ---------------------------------
    # PDF EXTRACTION
    # ---------------------------------

    if uploaded_file.name.lower().endswith(".pdf"):

        pdf_bytes = uploaded_file.getvalue()

        try:

            with st.spinner(
                "📄 Extracting PDF text..."
            ):

                text = extract_document_text(
                    pdf_bytes
                )

            if not text.strip():

                is_scanned_pdf = True

        except Exception as e:

            st.error(
                f"PDF extraction error: {e}"
            )

    # ---------------------------------
    # TXT EXTRACTION
    # ---------------------------------

    elif uploaded_file.name.lower().endswith(".txt"):

        text = uploaded_file.getvalue().decode(
            "utf-8",
            errors="replace"
        )

    # ---------------------------------
    # DISPLAY EXTRACTED TEXT
    # ---------------------------------

    if text.strip():

        st.subheader(
            "📋 Extracted Document Text"
        )

        st.text_area(
            "Document content",
            text,
            height=220
        )

        st.success(
            "Document text extracted successfully! ✅"
        )

    # ---------------------------------
    # SCANNED PDF
    # ---------------------------------

    elif is_scanned_pdf:

        st.info(
            "📷 Scanned PDF detected. "
            "Gemini AI will read the PDF directly."
        )

    else:

        st.warning(
            "No readable text found."
        )

    # ---------------------------------
    # DOCUMENT AI ANALYSIS
    # ---------------------------------

    if text.strip() or is_scanned_pdf:

        st.subheader(
            "🤖 AI Document Analysis"
        )

        doc_option = st.selectbox(
            "Choose an AI action",
            [
                "Summarize Document",
                "Extract Important Information",
                "Classify Document",
                "Ask Questions"
            ],
            key="document_action"
        )

        doc_question = ""

        if doc_option == "Ask Questions":

            doc_question = st.text_input(
                "❓ Enter your question about the document",
                key="document_question"
            )

        if st.button(
            "✨ Generate AI Result",
            key="document_generate"
        ):

            if client is None:

                st.error(
                    "Gemini API key not found. "
                    "Please check Streamlit Secrets."
                )

            elif (
                doc_option == "Ask Questions"
                and not doc_question.strip()
            ):

                st.warning(
                    "Please enter your question."
                )

            else:

                # PROMPTS

                if doc_option == "Summarize Document":

                    prompt = """
You are an AI document analysis assistant.

Summarize this document in simple and clear language.

Include:
1. Main topic
2. Important points
3. Main conclusion

Use headings and bullet points.
Do not invent information.
"""

                elif doc_option == "Extract Important Information":

                    prompt = """
You are an AI document analysis assistant.

Extract the important information from this document.

Include:
1. Important facts
2. Names and dates
3. Key information
4. Important numbers

Use clear headings and bullet points.
Do not invent information.
"""

                elif doc_option == "Classify Document":

                    prompt = """
You are an AI document classification system.

Identify the category of this document.

Explain:
1. Document type
2. Main purpose
3. Reason for classification

Use simple language.
"""

                else:

                    prompt = f"""
You are an AI document question-answering assistant.

Answer ONLY using the information in the document.

QUESTION:
{doc_question}

If the answer is unavailable, say:
Answer not found in the document.
"""

                # ---------------------------------
                # AI PROCESSING
                # ---------------------------------

                try:

                    if is_scanned_pdf:

                        contents = [

                            types.Part.from_text(
                                text=prompt
                            ),

                            types.Part.from_bytes(
                                data=pdf_bytes,
                                mime_type="application/pdf"
                            )
                        ]

                    else:

                        # Limit large text for faster processing
                        document_text = text[:20000]

                        if len(text) > 20000:

                            st.info(
                                "Large document detected. "
                                "The first 20,000 characters "
                                "are being analyzed."
                            )

                        contents = f"""
{prompt}

DOCUMENT:
{document_text}
"""

                    with st.spinner(
                        "🤖 Gemini AI is analyzing the document..."
                    ):

                        result = generate_ai_result(
                            contents
                        )

                    st.subheader("🧠 AI Result")

                    st.write(result)

                    st.success(
                        "Document analysis completed! ✅"
                    )

                    st.download_button(
                        "⬇️ Download AI Result",
                        result,
                        file_name="AI_Document_Result.txt",
                        mime="text/plain"
                    )

                except Exception as e:

                    st.error(
                        f"Document AI Error: {e}"
                    )


# =================================
# SECTION 2: WEBSITE INTELLIGENCE
# =================================

st.divider()

st.header(
    "🌐 Website Content Intelligence"
)

st.write(
    "Paste a website URL to extract content "
    "and generate AI-powered notes."
)


# ---------------------------------
# SESSION STATE
# ---------------------------------

if "website_text" not in st.session_state:

    st.session_state.website_text = ""

if "website_title" not in st.session_state:

    st.session_state.website_title = ""


# ---------------------------------
# WEBSITE URL INPUT
# ---------------------------------

website_url = st.text_input(
    "🔗 Enter Website URL",
    placeholder="https://www.example.com",
    key="website_url"
)


# =================================
# WEBSITE EXTRACTION
# =================================

if st.button(
    "🌐 Extract Website Content",
    key="website_extract"
):

    parsed_url = urlparse(
        website_url.strip()
    )

    if (
        parsed_url.scheme not in ["http", "https"]
        or not parsed_url.netloc
    ):

        st.warning(
            "Please enter a valid website URL."
        )

    else:

        try:

            with st.spinner(
                "🌐 Extracting website content..."
            ):

                website_title, website_text = (
                    extract_website_content(
                        website_url.strip()
                    )
                )

            if not website_text.strip():

                st.warning(
                    "No readable content found."
                )

                st.session_state.website_text = ""

            else:

                st.session_state.website_title = (
                    website_title
                )

                # Limit website content
                st.session_state.website_text = (
                    website_text[:10000]
                )

                st.success(
                    "Website content extracted successfully! ✅"
                )

        except requests.exceptions.RequestException as e:

            st.error(
                f"Unable to access website: {e}"
            )

        except Exception as e:

            st.error(
                f"Website extraction error: {e}"
            )


# =================================
# DISPLAY WEBSITE CONTENT
# =================================

if st.session_state.website_text:

    st.subheader("📌 Website Title")

    st.write(
        st.session_state.website_title
    )

    st.subheader(
        "📋 Extracted Website Content"
    )

    st.text_area(
        "Website text",
        st.session_state.website_text,
        height=200,
        key="website_content_display"
    )

    st.divider()

    # ---------------------------------
    # WEBSITE AI OPTIONS
    # ---------------------------------

    st.subheader(
        "🤖 Website AI Analysis"
    )

    website_option = st.selectbox(
        "Choose an AI action",
        [
            "Summarize Website",
            "Extract Important Information",
            "Generate Short Notes",
            "Ask Questions"
        ],
        key="website_action"
    )

    # ---------------------------------
    # LANGUAGE SELECTION
    # ---------------------------------

    language = st.selectbox(
        "🌍 Select Notes Language",
        [
            "English",
            "Telugu",
            "Telugu + English"
        ],
        key="website_language"
    )

    # ---------------------------------
    # QUESTION INPUT
    # ---------------------------------

    website_question = ""

    if website_option == "Ask Questions":

        website_question = st.text_input(
            "❓ Ask a question about this website",
            key="website_question"
        )

    # =================================
    # WEBSITE AI GENERATION
    # =================================

    if st.button(
        "✨ Generate Website AI Result",
        key="website_generate"
    ):

        if client is None:

            st.error(
                "Gemini API key not found."
            )

        elif (
            website_option == "Ask Questions"
            and not website_question.strip()
        ):

            st.warning(
                "Please enter your question."
            )

        else:

            # LANGUAGE INSTRUCTIONS

            language_instruction = {

                "English":
                "Write completely in simple English.",

                "Telugu":
                "Write completely in natural Telugu.",

                "Telugu + English":
                "Explain in natural Telugu mixed with simple English words."
            }

            # ---------------------------------
            # SELECT TASK
            # ---------------------------------

            if website_option == "Summarize Website":

                task = """
Summarize the website content.

Include:
1. Main topic
2. Important points
3. Main conclusion
"""

            elif website_option == "Extract Important Information":

                task = """
Extract important information from the website.

Use headings and bullet points.
Include important facts, dates, names and numbers.
"""

            elif website_option == "Generate Short Notes":

                task = """
Create short and easy-to-understand study notes.

Include:
1. Topic headings
2. Short explanations
3. Important points
4. Key takeaways

Keep the notes concise.
"""

            else:

                task = f"""
Answer this question using ONLY the website content:

{website_question}

If the answer is unavailable, say:
Answer not found in the website content.
"""

            # ---------------------------------
            # FINAL PROMPT
            # ---------------------------------

            prompt = f"""
You are an AI Website Intelligence Assistant.

TASK:
{task}

LANGUAGE:
{language_instruction[language]}

RULES:
1. Use only the provided website content.
2. Do not invent information.
3. Explain in simple language.
4. Use clear headings and bullet points.
5. Keep the output useful and concise.

WEBSITE TITLE:
{st.session_state.website_title}

WEBSITE CONTENT:
{st.session_state.website_text}
"""

            # ---------------------------------
            # GENERATE AI RESULT
            # ---------------------------------

            try:

                with st.spinner(
                    "🤖 Gemini AI is analyzing the website..."
                ):

                    result = generate_ai_result(
                        prompt
                    )

                st.subheader(
                    "🧠 AI Generated Result"
                )

                st.write(result)

                st.success(
                    "Website analysis completed! ✅"
                )

                st.download_button(
                    "⬇️ Download Website AI Result",
                    result,
                    file_name="Website_AI_Notes.txt",
                    mime="text/plain"
                )

            except Exception as e:

                st.error(
                    f"Website AI Analysis Error: {e}"
                )


# =================================
# END OF PROJECT
# =================================

st.divider()

st.caption(
    "🤖 AI Document Intelligence Platform | "
    "Powered by Gemini AI and Streamlit"
)
