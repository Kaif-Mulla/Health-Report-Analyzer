import streamlit as st
import pdfplumber
from groq import Groq
import sqlite3
import os
from dotenv import load_dotenv

# ================= LOAD ENV =================
load_dotenv()

API_KEY = os.getenv("GROQ_API_KEY")

if not API_KEY:
    st.error("❌ GROQ API KEY not found. Check .env file")
    st.stop()

client = Groq(api_key=API_KEY)

# ================= PDF TEXT EXTRACTION =================
def extract_text_from_pdf(file):
    text = ""

    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"

    return text


# ================= AI ANALYSIS =================
def analyze_with_ai(text):

    prompt = f"""
    You are an AI medical assistant.

    Analyze this blood report and provide:
    - Important observations
    - Possible health risks
    - Simple suggestions

    Blood Report:
    {text}
    """

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content


# ================= DATABASE INIT =================
def init_db():
    conn = sqlite3.connect("reports.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reports(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_text TEXT,
            ai_result TEXT
        )
    """)

    conn.commit()
    conn.close()


# ================= SAVE REPORT =================
def save_report(report_text, ai_result):
    conn = sqlite3.connect("reports.db")
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO reports(report_text, ai_result) VALUES (?, ?)",
        (report_text, ai_result)
    )

    conn.commit()
    conn.close()


# ================= FETCH HISTORY =================
def get_history():
    conn = sqlite3.connect("reports.db")
    cursor = conn.cursor()

    cursor.execute("SELECT ai_result FROM reports ORDER BY id DESC")
    rows = cursor.fetchall()

    conn.close()
    return rows


# ================= STREAMLIT UI =================
st.set_page_config(page_title="AI Health Report Analyzer")

st.title("🩺 AI Health Report Analyzer")
st.write("Upload your Blood Report PDF and get AI-based health insights.")

init_db()

uploaded_file = st.file_uploader(
    "Upload Blood Report PDF",
    type=["pdf"]
)

if st.button("Analyze Report"):

    if uploaded_file:

        with st.spinner("Extracting text..."):
            extracted_text = extract_text_from_pdf(uploaded_file)

        st.success("✅ Text Extracted Successfully")

        st.subheader("Extracted Text Preview")
        st.text(extracted_text[:500])

        with st.spinner("Analyzing with AI..."):
            ai_result = analyze_with_ai(extracted_text)

        st.subheader("🧠 AI Health Insights")
        st.write(ai_result)

        save_report(extracted_text, ai_result)

    else:
        st.error("Please upload a PDF first.")


# ================= HISTORY =================
st.subheader("📜 Previous Reports")

history = get_history()

for i, row in enumerate(history, 1):
    st.write(f"Report {i}")
    st.write(row[0])
    st.divider()