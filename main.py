import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", os.getenv("GROQ_API_KEY"))

client = OpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1"
)

st.set_page_config(page_title="MemoMate", layout="centered")

#CUSTOM CSS
st.markdown("""
    <style>
        html, body, [class*="css"] {
            font-family: 'Segoe UI', sans-serif;
            background-color: #2B1F1F;
            color: #F7CACA;
        }

        .stApp {
            max-width: 800px;
            margin: auto;
            padding: 2rem;
            background-color: #2B1F1F;
        }

        h1 {
            color: #F7CACA;
            text-align: center;
            margin-bottom: 1.5rem;
        }

        .stTextInput > div > div > input {
            background-color: #3E2C2C;
            color: #F7CACA;
            border: 1px solid #F7CACA;
            padding: 0.6rem;
            border-radius: 8px;
        }

        .stSelectbox > div {
            background-color: #3E2C2C;
            color: #F7CACA;
            border: 1px solid #F7CACA;
            border-radius: 8px;
        }

        .stButton > button {
            background-color: #F7CACA;
            color: #2B1F1F;
            font-weight: bold;
            border-radius: 10px;
            padding: 0.6rem 1.3rem;
            border: none;
            transition: all 0.2s ease-in-out;
        }

        .stButton > button:hover {
            background-color: #ffe5e5;
        }

        .response-card {
            background-color: #3E2C2C;
            color: #F7CACA;
            padding: 1rem;
            margin-top: 1.2rem;
            border-left: 5px solid #F7CACA;
            border-radius: 10px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.3);
            line-height: 1.6;
            white-space: pre-wrap;
        }

        .sidebar .sidebar-content {
            background-color: #3E2C2C;
        }

        /* Bot SVG Animation */
        @keyframes slideFadeIn {
            0% {
                opacity: 0;
                transform: translateY(-20px) scale(0.9);
            }
            100% {
                opacity: 1;
                transform: translateY(0) scale(1);
            }
        }

        #bot-icon {
            animation: slideFadeIn 1s ease-out forwards;
            transition: transform 0.3s ease;
            display: inline-block;
            vertical-align: middle;
            margin-right: 10px;
            height: 48px;
            width: 48px;
        }

        #bot-icon:hover {
            transform: scale(1.1);
        }
    </style>
""", unsafe_allow_html=True)

# ICON LOADER 
def custom_svg_icon(path: str, size: int = 40, color: str = "#ffffff") -> str:
    with open(path, "r", encoding="utf-8") as f:
        svg = f.read()
        svg = svg.replace("<svg", f'<svg width="{size}" height="{size}" style="fill:{color}; vertical-align:middle;"')
        return f'<span>{svg}</span>'

#TITLE 
st.markdown(f"<h1>{custom_svg_icon('assets/artificial-bot-intelligence-svgrepo-com.svg')} MemoMate </h1>", unsafe_allow_html=True)
st.markdown("Ask for a <strong>quiz</strong>, <strong>summary</strong>, or <strong>explanation</strong> of any topic, or upload a <strong>PDF/DOCX</strong> to get an explanation!", unsafe_allow_html=True)
#STATE
if "history" not in st.session_state:
    st.session_state.history = []
if "topics" not in st.session_state:
    st.session_state.topics = []

#FILE READERS 
def extract_text_from_file(uploaded_file):
    if uploaded_file.name.endswith(".pdf"):
        import fitz  # PyMuPDF
        doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        return text
    elif uploaded_file.name.endswith(".docx"):
        import docx
        doc = docx.Document(uploaded_file)
        return "\n".join([para.text for para in doc.paragraphs])
    return ""

#CLASSIFIER 
def classify_task(user_input: str) -> str:
    input_lower = user_input.lower()
    if "quiz" in input_lower:
        return "quiz"
    elif "summary" in input_lower or "summarize" in input_lower:
        return "summary"
    elif any(word in input_lower for word in ["explain", "explanation", "what is", "describe", "definition"]):
        return "explanation"
    else:
        return "clarification"

#TRACK TOPIC
def track_topic(topic: str):
    if topic and topic not in st.session_state.topics:
        st.session_state.topics.append(topic)

#GENERATE RESPONSE
def generate_response(user_input: str, task_type: str) -> str:
    topic = (
        user_input
        .replace("quiz on", "")
        .replace("summary of", "")
        .replace("summarize", "")
        .replace("explain", "")
        .replace("give me", "")
        .replace("describe", "")
        .strip()
    )

    track_topic(topic)

    if task_type == "quiz":
        user_task = (
            f"Generate 5 multiple-choice quiz questions on the topic '{topic}' for exam revision. "
            f"Each question must have 4 options labeled A, B, C, and D. "
            f"Clearly indicate the correct option after each question using the format: 'Correct Answer: <option letter>'"
        )
    elif task_type == "summary":
        user_task = f"Provide a 5-bullet summary of '{topic}' that a student can quickly revise before an exam."
    elif task_type == "explanation":
        user_task = f"Explain '{topic}' clearly in 5-8 lines. Avoid jargon and use a simple student-friendly tone."
    else:
        return "Please specify if you want a quiz, summary, or explanation."

    try:
        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You're an AI Exam Revision Assistant.\n"
                        "Your job is to help students revise for exams.\n"
                        "Use concise, student-friendly language. Be encouraging. Format in bullet points if needed.\n"
                        "Only answer the user's task — don't include instructions or repeat the prompt.\n"
                        "Add key points to every summary and explanationS"
                    ),
                },
                {"role": "user", "content": user_task},
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error from Groq: {e}"

#INPUT
user_topic = st.text_input("Enter a topic (e.g., Newton's Laws):", placeholder="Type your topic here...")
task_type  = st.selectbox("What do you want?", ["Quiz", "Summary", "Explanation"])
uploaded_file = st.file_uploader("Upload class material (PDF or DOCX):", type=["pdf","docx"])

#EXECUTION
if st.button("Revise Now"):
    if uploaded_file:
        extracted_text = extract_text_from_file(uploaded_file)
        if extracted_text:
            st.markdown("<p>File uploaded. Generating explanation...</p>", unsafe_allow_html=True)
            result = generate_response(extracted_text[:4000], "explanation")
            st.session_state.history.append(("Uploaded File", result))
        else:
            st.error("Could not extract text from the uploaded file.")
    elif user_topic:
        user_input = f"{task_type.lower()} on {user_topic}"
        result = generate_response(user_input, task_type.lower())
        st.session_state.history.append((user_input, result))
    else:
        st.warning("Please enter a topic or upload a file.")

#OUTPUT
for query, reply in reversed(st.session_state.history):
    st.markdown(f"""
    <div class="response-card">
        <p><strong>You:</strong> {query}</p>
        <p><strong>{custom_svg_icon('assets/artificial-bot-intelligence-svgrepo-com.svg')} AI:</strong><br>{reply}</p>
    </div>
    """, unsafe_allow_html=True)

#SIDEBAR 
if st.session_state.topics:
    st.sidebar.markdown("<h4>Topics Revised</h4>", unsafe_allow_html=True)
    for t in st.session_state.topics:
        st.sidebar.markdown(f"<p>✅ {t}</p>", unsafe_allow_html=True)