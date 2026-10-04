import os
import random

from flask import Flask, render_template, request, redirect, url_for, session
from dotenv import load_dotenv
from pymongo import MongoClient
from google import genai
import markdown
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
ai_client = genai.Client(api_key=api_key)

client = MongoClient("mongodb://localhost:27017/")
db = client["ai_student_assistant"]

chat_collection = db["chat_history"]
quiz_collection = db["quiz_results"]

print("MongoDB connected!")

app = Flask(__name__)

app.secret_key = os.getenv(
    "FLASK_SECRET_KEY",
    "student-assistant-secret-key"
)
def get_ai_answer(question):
    try:

        prompt = f"""
You are Typhoon, an AI Student Learning Assistant.

Answer the student's question clearly and accurately.

Use simple language suitable for a college student.
Keep the response concise.
Use bullet points when useful.
Give a short example when it helps.

Student's question:
{question}
"""

        response = ai_client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=prompt
        )

        return markdown.markdown(
    response.text,
    extensions=["fenced_code", "nl2br"]
)

    except Exception as e:

        print("Gemini API Error:", e)

        return "Sorry, I couldn't connect to the AI service right now. Please try again."
@app.route("/", methods=["GET", "POST"])
def home():
    answer = ""
    if request.method == "POST":
        question = request.form.get("question", "").strip()

        if not question:
            return redirect(url_for("home"))   
        answer = get_ai_answer(question)
        chat_collection.insert_one({
    "question": question,
    "answer": answer
})
    chat_history = list(chat_collection.find())

    return render_template(
        "index.html",
        answer=answer,
        chat_history=chat_history
    )
@app.route("/clear")
def clear_history():
    chat_collection.delete_many({})
    return redirect("/")

@app.route("/dashboard")
def dashboard():

    chat_count = chat_collection.count_documents({})

    quiz_attempts = quiz_collection.count_documents({})

    latest_quiz = quiz_collection.find_one(
        {},
        sort=[("_id", -1)]
    )

    latest_score = "-"

    if latest_quiz:
        latest_score = f"{latest_quiz['score']} / {latest_quiz['total']}"

    return render_template(
        "dashboard.html",
        chat_count=chat_count,
        quiz_attempts=quiz_attempts,
        latest_score=latest_score
    )
quiz_questions = [

    {
        "question": "What is Python?",
        "options": {
            "A": "A database",
            "B": "A programming language",
            "C": "A web browser",
            "D": "An operating system"
        },
        "answer": "B"
    },

    {
        "question": "What is a loop used for in Python?",
        "options": {
            "A": "Creating a database",
            "B": "Designing a webpage",
            "C": "Repeating a block of code",
            "D": "Connecting to the internet"
        },
        "answer": "C"
    },

    {
        "question": "What is Flask?",
        "options": {
            "A": "A Python web framework",
            "B": "A database",
            "C": "An operating system",
            "D": "A web browser"
        },
        "answer": "A"
    },

    {
        "question": "What is MongoDB?",
        "options": {
            "A": "A programming language",
            "B": "A web browser",
            "C": "An operating system",
            "D": "A NoSQL database"
        },
        "answer": "D"
    },

    {
        "question": "What is an API used for?",
        "options": {
            "A": "Creating computer hardware",
            "B": "Allowing software systems to communicate",
            "C": "Designing logos",
            "D": "Writing documents"
        },
        "answer": "B"
    },

    {
        "question": "What is HTML used for?",
        "options": {
            "A": "Storing database records",
            "B": "Running an operating system",
            "C": "Creating and structuring web pages",
            "D": "Managing computer hardware"
        },
        "answer": "C"
    },

    {
        "question": "What is CSS used for?",
        "options": {
            "A": "Styling and designing web pages",
            "B": "Storing data",
            "C": "Creating databases",
            "D": "Running Python programs"
        },
        "answer": "A"
    },

    {
        "question": "What is JavaScript mainly used for?",
        "options": {
            "A": "Creating database tables",
            "B": "Installing operating systems",
            "C": "Managing computer memory",
            "D": "Making web pages interactive"
        },
        "answer": "D"
    },

    {
        "question": "What is a database?",
        "options": {
            "A": "A programming language",
            "B": "A system used to store and manage data",
            "C": "A web browser",
            "D": "A computer game"
        },
        "answer": "B"
    },

    {
        "question": "What does web development involve?",
        "options": {
            "A": "Only repairing computers",
            "B": "Only creating hardware",
            "C": "Creating websites and web applications",
            "D": "Only installing software"
        },
        "answer": "C"
    },

    {
        "question": "Which keyword is used to define a function in Python?",
        "options": {
            "A": "def",
            "B": "function",
            "C": "func",
            "D": "define"
        },
        "answer": "A"
    },

    {
        "question": "Which data type stores True or False?",
        "options": {
            "A": "String",
            "B": "List",
            "C": "Integer",
            "D": "Boolean"
        },
        "answer": "D"
    },

    {
        "question": "Which symbol is used for a comment in Python?",
        "options": {
            "A": "//",
            "B": "#",
            "C": "/*",
            "D": "<!--"
        },
        "answer": "B"
    },

    {
        "question": "What does CRUD stand for?",
        "options": {
            "A": "Copy, Run, Upload, Download",
            "B": "Create, Run, Use, Display",
            "C": "Create, Read, Update, Delete",
            "D": "Connect, Read, Upload, Delete"
        },
        "answer": "C"
    },

    {
        "question": "Which HTTP method is commonly used to submit form data?",
        "options": {
            "A": "POST",
            "B": "GET",
            "C": "READ",
            "D": "SEND"
        },
        "answer": "A"
    }

]
@app.route("/quiz", methods=["GET", "POST"])
def quiz():

    result = ""
    score = 0
    feedback = []

    # =========================
    # START NEW QUIZ
    # =========================

    if request.method == "GET":

        selected_questions = random.sample(
            quiz_questions,
            10
        )

        session["quiz_questions"] = selected_questions

        return render_template(
            "quiz.html",
            result="",
            score=0,
            feedback=[],
            quiz_questions=selected_questions
        )

    # =========================
    # SUBMIT QUIZ
    # =========================

    selected_questions = session.get(
        "quiz_questions",
        []
    )

    # Safety check
    if not selected_questions:
        return redirect(url_for("quiz"))

    for i, question in enumerate(
        selected_questions,
        start=1
    ):

        user_answer = request.form.get(
            f"answer{i}"
        )

        if user_answer == question["answer"]:

            score += 1

            feedback.append(
                (
                    "correct",
                    f"Question {i} - Correct "
                )
            )

        else:

            correct_answer = question["answer"]

            correct_option = question["options"][
                correct_answer
            ]

            feedback.append(
                (
                    "wrong",
                    f"Question {i} - Wrong | "
                    f"Correct answer: "
                    f"{correct_answer}. "
                    f"{correct_option}"
                )
            )

    total_questions = len(selected_questions)

    result = (
        f"You scored {score} "
        f"out of {total_questions}"
    )

    # =========================
    # SAVE RESULT TO MONGODB
    # =========================

    quiz_collection.insert_one({
        "score": score,
        "total": total_questions
    })

    # =========================
    # RESULT MESSAGE
    # =========================

    if score == total_questions:

        result += " - Excellent! "

    elif score >= total_questions / 2:

        result += " - Good job! "

    else:

        result += " - Keep practicing! "


    return render_template(
        "quiz.html",
        result=result,
        score=score,
        feedback=feedback,
        quiz_questions=selected_questions
    )
if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)