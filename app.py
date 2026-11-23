import streamlit as st
from pypdf import PdfReader
from google import genai
import base64
import requests
from bs4 import BeautifulSoup


# ---------------------------------
# WEBSITE CONTENT EXTRACTION
# ---------------------------------

def extract_website_content(url):

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(
        url,
        headers=headers,
        timeout=20
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


# ---------------------------------
# PAGE SETTINGS
# ---------------------------------

st.set_page_config(
    page_title="AI Document Intelligence",
    page_icon="🤖"
)

st.title("🤖 AI Document Intelligence Platform")

st.write(
    "Upload a PDF or TXT document and use AI to analyze it."
)


# ---------------------------------
# GEMINI API
# ---------------------------------

try:
    api_key = st.secrets["GEMINI_API_KEY"]
    client = genai.Client(api_key=api_key)

except Exception:
    client = None


# =================================
# SECTION 1: PDF / TXT ANALYSIS
# =================================

st.header("📄 Document Analysis")

uploaded_file = st.file_uploader(
    "Upload your document",
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

        if not text.strip():
            is_scanned_pdf = True

    # TXT
    elif uploaded_file.type == "text/plain":

        text = uploaded_file.read().decode("utf-8")


    # TEXT PDF / TXT

    if text.strip():

        st.subheader("📋 Extracted Document Text")

        st.text_area(
            "Document content",
            text,
            height=250
        )

        st.success(
            "Document text extracted successfully! ✅"
        )


    # SCANNED PDF

    elif is_scanned_pdf:

        st.info(
            "📷 Scanned/Image PDF detected. "
            "Gemini AI will read the document directly."
        )

    else:

        st.warning(
            "⚠️ No readable text found in this document."
        )


    # AI DOCUMENT ANALYSIS

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

                # PROMPTS

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

# =================================
# SECTION 2: WEBSITE INTELLIGENCE
# =================================

st.divider()

st.header("🌐 Website Content Intelligence")

st.write(
    "Paste a website URL to extract content and analyze it using AI."
)

website_url = st.text_input(
    "🔗 Enter Website URL",
    placeholder="https://www.example.com"
)

if "website_text" not in st.session_state:
    st.session_state.website_text = ""

if "website_title" not in st.session_state:
    st.session_state.website_title = ""

# WEBSITE EXTRACTION

if st.button("🌐 Extract Website Content"):

    if not website_url.strip():

        st.warning("Please enter a website URL.")

    elif not website_url.startswith(("http://", "https://")):

        st.warning("Please enter a valid website URL.")

    else:

        try:

            with st.spinner("🌐 Extracting website content..."):

                website_title, website_text = extract_website_content(
                    website_url.strip()
                )

            if not website_text.strip():

                st.warning("No readable content found.")

            else:

                st.session_state.website_title = website_title

                # Limit content to improve processing speed
                st.session_state.website_text = website_text[:20000]

                st.success("Website content extracted successfully! ✅")

        except requests.exceptions.RequestException as e:

            st.error(f"Unable to access website: {e}")

        except Exception as e:

            st.error(f"Something went wrong: {e}")


# DISPLAY WEBSITE CONTENT

if st.session_state.website_text:

    st.subheader("📌 Website Title")

    st.write(st.session_state.website_title)

    st.subheader("📋 Extracted Website Content")

    st.text_area(
        "Website text",
        st.session_state.website_text,
        height=200
    )

    st.divider()

    # AI OPTIONS

    st.subheader("🤖 Website AI Analysis")

    option = st.selectbox(
        "Choose an AI action",
        [
            "Summarize Website",
            "Extract Important Information",
            "Generate Short Notes",
            "Ask Questions"
        ]
    )

    language = st.selectbox(
        "🌍 Select Notes Language",
        [
            "English",
            "Telugu",
            "Telugu + English"
        ]
    )

    question = ""

    if option == "Ask Questions":

        question = st.text_input(
            "❓ Ask a question about this website"
        )

    if st.button("✨ Generate Website AI Result"):

        if client is None:

            st.error("Gemini API key not found.")

        elif option == "Ask Questions" and not question.strip():

            st.warning("Please enter your question.")

        else:

            language_instruction = {
                "English": "Write completely in simple English.",
                "Telugu": "Write completely in simple Telugu.",
                "Telugu + English": "Explain in natural Telugu mixed with simple English words."
            }

            if option == "Summarize Website":

                task = "Summarize the website content using simple language and clear headings."

            elif option == "Extract Important Information":

                task = "Extract all important information using headings and bullet points."

            elif option == "Generate Short Notes":

                task = "Create short, easy-to-understand study notes with important points."

            else:

                task = f"""
Answer this question using ONLY the website content:

{question}

If the answer is not available, say:
Answer not found in the website content.
"""

            prompt = f"""
You are an AI Website Intelligence Assistant.

TASK:
{task}

LANGUAGE:
{language_instruction[language]}

RULES:
1. Use only the provided website content.
2. Do not invent information.
3. Use simple and clear explanations.
4. Keep the output concise and useful.

WEBSITE TITLE:
{st.session_state.website_title}

WEBSITE CONTENT:
{st.session_state.website_text}
"""

            try:

                with st.spinner("🤖 Gemini AI is analyzing the website..."):

                    response = client.interactions.create(
                        model="gemini-3.8-flash",
                        input=prompt
                    )

                    result = response.output_text

                st.subheader("🧠 AI Generated Result")

                st.write(result)

                st.download_button(
                    "⬇️ Download Website Notes",
                    result,
                    file_name="Website_AI_Notes.txt",
                    mime="text/plain"
                )

            except Exception as e:

                st.error(f"AI Analysis Error: {e}")
