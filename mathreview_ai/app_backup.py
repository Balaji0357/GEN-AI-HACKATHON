
import streamlit as st
import pandas as pd
import plotly.express as px
import re

from core.database import (
    init_db, register_user, authenticate, save_attempt,
    get_attempts, get_users
)
from core.parser import parse_solution
from core.verifier import verify_steps, numeric_equal
from core.replay import build_replay
from core.learning import (
    misconception_report, explanation, generate_challenge,
    classify_error
)
from core.ocr import read_handwritten_solution
from core.question_bank import QUESTIONS


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="MathReview AI",
    page_icon="🧮",
    layout="wide",
    initial_sidebar_state="expanded"
)

init_db()


# ============================================================
# CUSTOM DESIGN
# ============================================================

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

[data-testid="stAppViewContainer"] {
    background: #f4f7fb;
}

[data-testid="stSidebar"] {
    background: #101d35;
}

[data-testid="stSidebar"] * {
    color: #edf3ff !important;
}

.block-container {
    max-width: 1450px;
    padding-top: 1.4rem;
    padding-bottom: 3rem;
}

.hero {
    padding: 1.6rem 1.8rem;
    border-radius: 20px;
    background: linear-gradient(115deg,#101d35,#174a83 65%,#167e83);
    color: white;
    margin-bottom: 1.3rem;
    box-shadow: 0 12px 30px rgba(20,45,80,.12);
}

.hero h1 {
    font-family: Manrope,sans-serif;
    color: white;
    font-size: 2.1rem;
    margin: 0;
}

.hero p {
    color: #d8e7f7;
    margin: .45rem 0 0;
}

.eyebrow {
    text-transform: uppercase;
    letter-spacing: .13em;
    font-size: .72rem;
    font-weight: 700;
    color: #b6d7f3;
}

.section-title {
    font-family: Manrope,sans-serif;
    color: #172b49;
    font-weight: 800;
    font-size: 1.4rem;
    margin: .3rem 0 .8rem;
}

.metric-card {
    background: white;
    border: 1px solid #e6ebf2;
    border-radius: 16px;
    padding: 1rem 1.1rem;
    min-height: 112px;
}

.metric-label {
    color: #66758b;
    font-size: .82rem;
    font-weight: 600;
}

.metric-value {
    font-family: Manrope,sans-serif;
    color: #142b4a;
    font-size: 1.8rem;
    font-weight: 800;
    margin-top: .25rem;
}

.metric-note {
    color: #8b98a9;
    font-size: .75rem;
}

.panel {
    background: white;
    border: 1px solid #e6ebf2;
    border-radius: 16px;
    padding: 1.2rem;
    margin-bottom: .8rem;
}

div.stButton > button[kind="primary"] {
    background: linear-gradient(90deg,#1764a5,#168d91);
    border: 0;
    border-radius: 10px;
    font-weight: 700;
    min-height: 2.7rem;
}

div.stButton > button {
    border-radius: 9px;
}

[data-testid="stTextArea"] textarea,
[data-testid="stTextInput"] input {
    border-radius: 10px;
}

.small-muted {
    color: #77869a;
    font-size: .86rem;
}

</style>
""", unsafe_allow_html=True)


# ============================================================
# REUSABLE FUNCTIONS
# ============================================================

def metric(label, value, note=""):
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


def navigate(page_name):
    st.session_state.quick_nav = page_name
    st.rerun()


# ============================================================
# LOGIN AND REGISTRATION
# ============================================================

def login_screen():

    st.markdown("""
    <div class="hero">
        <div class="eyebrow">AI-powered mathematics learning</div>
        <h1>🧮 MathReview AI</h1>
        <p>
        Understand every mistake. Verify every calculation.
        Improve with every attempt.
        </p>
    </div>
    """, unsafe_allow_html=True)

    left, right = st.columns([1.1, 1], gap="large")

    with left:

        st.markdown("## A smarter way to learn mathematics")

        st.write(
            "Review typed or handwritten mathematical work, "
            "investigate calculation mistakes and receive "
            "practice tailored to your learning needs."
        )

        features = [
            ("✍️ Handwritten Analyzer",
             "Upload handwritten mathematical work."),
            ("🔎 Error Detection",
             "Identify incorrect arithmetic steps."),
            ("🧠 Mistake Reasoning",
             "Understand why an answer may be incorrect."),
            ("📈 Learning Profile",
             "Track your mathematical progress."),
            ("🎯 Adaptive Practice",
             "Practise topics that need improvement.")
        ]

        for title, description in features:
            st.markdown(
                f"**{title}**  \n"
                f"<span class='small-muted'>{description}</span>",
                unsafe_allow_html=True
            )

    with right:

        tab1, tab2 = st.tabs(["Sign In", "Create Account"])

        with tab1:

            with st.form("login_form"):

                email = st.text_input("Email address")
                password = st.text_input(
                    "Password",
                    type="password"
                )

                submitted = st.form_submit_button(
                    "Sign In",
                    type="primary",
                    use_container_width=True
                )

            if submitted:

                user = authenticate(email, password)

                if user:
                    st.session_state.user = user
                    st.rerun()
                else:
                    st.error("Incorrect email or password.")

            st.info(
                "Demo teacher account: teacher@mathreview.ai\n\n"
                "Password: Teacher@123"
            )

        with tab2:

            with st.form("register_form"):

                name = st.text_input("Full name")
                new_email = st.text_input("Email address")

                new_password = st.text_input(
                    "Password (minimum 8 characters)",
                    type="password"
                )

                role = st.selectbox(
                    "Account type",
                    ["student", "teacher"]
                )

                create = st.form_submit_button(
                    "Create Account",
                    type="primary",
                    use_container_width=True
                )

            if create:

                ok, message = register_user(
                    name,
                    new_email,
                    new_password,
                    role
                )

                if ok:
                    st.success(message)
                else:
                    st.error(message)


# ============================================================
# LOGIN CHECK
# ============================================================

if "user" not in st.session_state:
    login_screen()
    st.stop()


user = st.session_state.user

uid = str(user["id"])

attempts = get_attempts(uid)

all_attempts = (
    get_attempts()
    if user["role"] in ("teacher", "admin")
    else attempts
)

df = pd.DataFrame(attempts) if attempts else pd.DataFrame()


# ============================================================
# NAVIGATION
# ============================================================

page_options = [
    "Dashboard",
    "Math Solver & Reviewer",
    "Handwritten Analyzer",
    "Question Library",
    "Error Investigation",
    "My Learning Profile",
    "Adaptive Practice",
    "Learning History"
]

if user["role"] in ("teacher", "admin"):
    page_options += [
        "Teacher Dashboard",
        "Question Management"
    ]

page_options += ["Settings & About"]


# Apply dashboard quick navigation before creating radio widget.
if st.session_state.get("quick_nav"):

    target_page = st.session_state.pop("quick_nav")

    if target_page in page_options:
        st.session_state["page_nav"] = target_page


if (
    "page_nav" not in st.session_state
    or st.session_state["page_nav"] not in page_options
):
    st.session_state["page_nav"] = "Dashboard"


with st.sidebar:

    st.markdown("## 🧮 MathReview AI")

    st.caption("INTELLIGENT LEARNING WORKSPACE")

    st.divider()

    st.markdown(f"**{user['name']}**")

    st.caption(f"{user['role'].title()} account")

    st.divider()

    st.markdown("### Navigation")

    page = st.radio(
        "WORKSPACE",
        page_options,
        key="page_nav",
        label_visibility="collapsed"
    )

    st.divider()

    st.caption(
        "Python/SymPy independently checks supported "
        "arithmetic expressions. AI explanations are "
        "shown separately."
    )

    if st.button("🚪 Sign Out", use_container_width=True):

        st.session_state.pop("user", None)
        st.session_state.pop("last_review", None)
        st.session_state.pop("page_nav", None)

        st.rerun()


# ============================================================
# SOLUTION REVIEW ENGINE
# ============================================================

def run_review(problem, solution):

    with st.spinner(
        "Parsing and independently checking your solution..."
    ):

        parsed = parse_solution(problem, solution)

        steps = parsed.get("steps", [])

        verification = verify_steps(steps)

        replay = build_replay(steps, verification)

        explanation_text, explanation_source = explanation(
            problem,
            steps,
            verification
        )

        save_attempt(
            uid,
            problem,
            solution,
            parsed.get("topic", "other"),
            verification
        )

    st.session_state.last_review = {
        "parsed": parsed,
        "verification": verification,
        "replay": replay,
        "explanation": explanation_text,
        "explanation_source": explanation_source,
        "problem": problem,
        "solution": solution
    }

    st.rerun()


# ============================================================
# REVIEW RESULTS
# ============================================================

def render_review(review):

    parsed = review["parsed"]
    verification = review["verification"]
    replay = review["replay"]

    st.markdown("### 📊 Review Results")

    a, b, c, d = st.columns(4)

    with a:
        st.metric("Steps Identified", len(verification))

    with b:
        st.metric(
            "Arithmetic Errors",
            sum(v["status"] == "error" for v in verification)
        )

    with c:
        st.metric(
            "Verified Steps",
            sum(v["status"] == "correct" for v in verification)
        )

    with d:
        st.metric(
            "Needs Review",
            sum(v["status"] == "unverifiable" for v in verification)
        )

    rows = []

    for v in verification:

        rows.append({
            "Step": v["step_id"],
            "Expression": v["expression"],
            "Student Answer": v["claimed_result"],
            "Verified Answer": v["actual_result"] or "—",
            "Status": {
                "correct": "Verified",
                "error": "Arithmetic Error",
                "unverifiable": "Unverifiable"
            }.get(v["status"], v["status"]),
            "Depends on Earlier Error": (
                "Yes"
                if v.get("depends_on_earlier_error")
                else "No"
            )
        })

    st.dataframe(
        pd.DataFrame(rows),
        use_container_width=True,
        hide_index=True
    )

    st.caption(
        "A later step can be arithmetically correct while "
        "depending on an earlier incorrect value."
    )

    t1, t2, t3, t4 = st.tabs([
        "Error Replay",
        "Mistake Reasoning",
        "Verified Evidence",
        "Extracted Steps"
    ])

    with t1:

        st.write(
            "Compare the original and corrected calculation paths."
        )

        if not replay:
            st.info("No replay steps are available.")

        for r in replay:

            with st.container(border=True):

                st.markdown(f"**Step {r['step_id']}**")

                st.write(
                    f"Original: `{r['original_expression']}` "
                    f"= `{r['student_claim']}`"
                )

                if (
                    r.get("corrected_expression")
                    != r.get("original_expression")
                    or r.get("original_status") == "error"
                ):

                    st.success(
                        "Corrected branch: "
                        f"`{r.get('corrected_expression')}` "
                        "→ "
                        f"**{r.get('replay_value') or r.get('verified_value') or 'Needs manual review'}**"
                    )

    with t2:

        st.info(review["explanation"])

        st.caption(review["explanation_source"])

        errors = [
            v for v in verification
            if v["status"] == "error"
        ]

        if errors:

            category = classify_error(
                errors[0]["expression"]
            )

            st.markdown(
                f"**Likely practice concept:** {category}"
            )

            st.caption(
                "This is a suggested practice category, "
                "not a definitive diagnosis."
            )

    with t3:

        st.write(
            "Numerical evidence produced by the independent "
            "calculation engine."
        )

        evidence = [
            {
                "Step": v["step_id"],
                "Expression": v["expression"],
                "Claim": v["claimed_result"],
                "Code Result": v["actual_result"],
                "Status": v["status"]
            }
            for v in verification
        ]

        st.dataframe(
            pd.DataFrame(evidence),
            use_container_width=True,
            hide_index=True
        )

    with t4:

        st.json(parsed)


# ============================================================
# DASHBOARD
# ============================================================

if page == "Dashboard":

    first_name = user["name"].split()[0]

    st.markdown(
        f"""
        <div class="hero">
            <div class="eyebrow">Your Learning Overview</div>
            <h1>Welcome back, {first_name} 👋</h1>
            <p>
            Your mathematics progress, practice recommendations
            and recent activity in one place.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    total = len(attempts)

    steps = int(df["total_steps"].sum()) if total else 0

    errors = int(df["errors"].sum()) if total else 0

    unverifiable = (
        int(df["unverifiable"].sum())
        if total else 0
    )

    verified = max(steps - errors - unverifiable, 0)

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        metric("Practice Attempts", total, "Saved reviews")

    with c2:
        metric("Steps Reviewed", steps, "Expressions processed")

    with c3:
        metric("Errors Found", errors, "Across your attempts")

    with c4:
        metric("Verified Steps", verified, "Arithmetic matches")

    left, right = st.columns([1.4, 1])

    with left:

        st.markdown(
            '<div class="section-title">Learning Activity</div>',
            unsafe_allow_html=True
        )

        if total:

            chart = df.copy()

            chart["created_at"] = pd.to_datetime(
                chart["created_at"],
                errors="coerce"
            )

            trend = (
                chart.dropna(subset=["created_at"])
                .groupby(chart["created_at"].dt.date)
                .size()
                .reset_index(name="attempts")
            )

            if not trend.empty:

                trend.columns = ["Date", "Attempts"]

                st.plotly_chart(
                    px.line(
                        trend,
                        x="Date",
                        y="Attempts",
                        markers=True,
                        title="Your Practice Sessions"
                    ),
                    use_container_width=True
                )

        else:

            st.info(
                "Your activity chart will appear "
                "after your first solution review."
            )

    with right:

        st.markdown(
            '<div class="section-title">Recommended Next Step</div>',
            unsafe_allow_html=True
        )

        if total:

            findings, message = misconception_report(attempts)

            st.info(message)

            if findings:
                st.write(
                    f"Practise next: **{findings[0]['category']}**"
                )

        else:

            st.write(
                "Start with a question from the Question Library "
                "or review your own working."
            )

        if st.button(
            "Start a Practice Session",
            type="primary",
            use_container_width=True
        ):

            navigate("Adaptive Practice")

    st.markdown("### Quick Actions")

    q1, q2, q3 = st.columns(3)

    with q1:

        if st.button(
            "✍️ Review a Solution",
            use_container_width=True
        ):
            navigate("Math Solver & Reviewer")

    with q2:

        if st.button(
            "📷 Upload Handwriting",
            use_container_width=True
        ):
            navigate("Handwritten Analyzer")

    with q3:

        if st.button(
            "🎯 Practise Weak Topics",
            use_container_width=True
        ):
            navigate("Adaptive Practice")


# ============================================================
# MATH SOLVER AND REVIEWER
# ============================================================

elif page == "Math Solver & Reviewer":

    st.markdown(
        '<div class="section-title">Math Solver & Reviewer</div>',
        unsafe_allow_html=True
    )

    st.write(
        "Enter a mathematical question or expression. "
        "Calculate supported arithmetic expressions or "
        "review your own step-by-step working."
    )

    input_mode = st.radio(
        "Choose Input Method",
        [
            "Natural Language",
            "Mathematical Expression"
        ],
        horizontal=True,
        key="math_input_mode"
    )

    problem = st.text_area(
        "Mathematical Question",
        height=100,
        placeholder=(
            "Example: Find 20% of 450."
        ),
        key="math_problem"
    )

    st.markdown("### Mathematical Keyboard")

    symbols = [
        "+", "-", "*", "/", "=",
        "(", ")", "**", "sqrt(", "pi",
        "sin(", "cos(", "tan(", "log("
    ]

    if "math_expression" not in st.session_state:
        st.session_state.math_expression = ""

    cols = st.columns(7)

    for i, symbol in enumerate(symbols):

        with cols[i % 7]:

            if st.button(
                symbol,
                key=f"symbol_{i}",
                use_container_width=True
            ):

                st.session_state.math_expression += symbol
                st.rerun()

    expression = st.text_input(
        "Mathematical Expression",
        key="math_expression",
        placeholder="Example: 25 * 4 + 10"
    )

    c1, c2 = st.columns(2)

    with c1:

        if st.button(
            "Clear Expression",
            use_container_width=True
        ):

            st.session_state.math_expression = ""
            st.rerun()

    with c2:

        if st.button(
            "Use Expression as Question",
            use_container_width=True
        ):

            if expression.strip():

                st.session_state.math_problem = expression
                st.rerun()

    st.divider()

    st.markdown("### Student's Working")

    solution = st.text_area(
        "Enter your solution step by step",
        height=170,
        placeholder=(
            "Example:\n"
            "20 / 100 = 0.2\n"
            "0.2 * 450 = 90"
        ),
        key="math_solution"
    )

    left, right = st.columns(2)

    with left:

        if st.button(
            "Review My Working",
            type="primary",
            use_container_width=True
        ):

            if problem.strip() and solution.strip():

                run_review(problem, solution)

            else:

                st.warning(
                    "Enter both the question and your working."
                )

    with right:

        if st.button(
            "Calculate Expression",
            use_container_width=True
        ):

            if not expression.strip():

                st.warning("Enter an expression first.")

            else:

                # This calculator intentionally accepts only
                # basic arithmetic characters.
                safe_expression = expression.replace("^", "**")

                if not re.fullmatch(
                    r"[0-9\s+\-*/().]+",
                    safe_expression
                ):

                    st.error(
                        "For this calculator, enter only numbers, "
                        "brackets and +, -, *, / or ^ operators."
                    )

                else:

                    try:

                        from sympy import sympify

                        result = sympify(
                            safe_expression,
                            evaluate=True
                        )

                        if result.is_number:

                            st.success(
                                f"Calculated Result: {result}"
                            )

                            st.code(
                                f"{expression} = {result}"
                            )

                        else:

                            st.warning(
                                "This expression could not be "
                                "evaluated as a numerical result."
                            )

                    except Exception:

                        st.error(
                            "Invalid mathematical expression. "
                            "Please check the operators and brackets."
                        )

    st.caption(
        "The calculator handles basic numerical expressions. "
        "It is not a general-purpose symbolic solver. "
        "Use Review My Working for step-by-step verification."
    )

    if st.session_state.get("last_review"):
        render_review(st.session_state.last_review)


# ============================================================
# HANDWRITTEN ANALYZER
# ============================================================

elif page == "Handwritten Analyzer":

    st.markdown(
        '<div class="section-title">Handwritten Solution Analyzer</div>',
        unsafe_allow_html=True
    )

    st.write(
        "Upload a clear image of handwritten mathematics. "
        "Confirm the extracted steps before verification."
    )

    upload = st.file_uploader(
        "Upload Handwritten Solution",
        type=["png", "jpg", "jpeg", "webp"]
    )

    problem = st.text_area(
        "Original Mathematical Question",
        height=100,
        key="handwritten_problem"
    )

    if upload:

        st.image(
            upload,
            caption="Uploaded Handwritten Work",
            use_container_width=True
        )

        if st.button(
            "Recognize Handwritten Steps",
            type="primary"
        ):

            with st.spinner("Reading handwritten mathematics..."):

                text, notice = read_handwritten_solution(
                    upload.getvalue(),
                    upload.type or "image/png"
                )

            if text:

                st.session_state.ocr_text = text
                st.success(notice)

            else:

                st.error(notice)

    if "ocr_text" in st.session_state:

        transcribed = st.text_area(
            "Confirm or Correct Recognized Steps",
            value=st.session_state.ocr_text,
            height=200,
            key="confirmed_ocr"
        )

        st.warning(
            "Check all recognized numbers and operators "
            "before proceeding."
        )

        if st.button(
            "Verify Handwritten Steps",
            type="primary"
        ):

            if problem.strip() and transcribed.strip():

                run_review(problem, transcribed)

            else:

                st.warning(
                    "Enter the original question and confirm "
                    "the recognized steps."
                )

    if st.session_state.get("last_review"):
        render_review(st.session_state.last_review)


# ============================================================
# QUESTION LIBRARY
# ============================================================

elif page == "Question Library":

    st.markdown(
        '<div class="section-title">Question Library</div>',
        unsafe_allow_html=True
    )

    st.write(
        "Explore mathematics questions by topic and difficulty."
    )

    topics = sorted(set(q[0] for q in QUESTIONS))

    f1, f2, f3 = st.columns(3)

    topic = f1.selectbox(
        "Topic",
        ["All"] + topics
    )

    level = f2.selectbox(
        "Difficulty",
        ["All", "Beginner", "Intermediate", "Advanced"]
    )

    search = f3.text_input(
        "Search Questions"
    )

    if "bookmarks" not in st.session_state:
        st.session_state.bookmarks = []

    filtered = [
        q for q in QUESTIONS
        if (topic == "All" or q[0] == topic)
        and (level == "All" or q[1] == level)
        and search.lower() in q[2].lower()
    ]

    only_bookmarks = st.checkbox(
        "Show bookmarked questions only"
    )

    if only_bookmarks:

        filtered = [
            q for q in filtered
            if q[2] in st.session_state.bookmarks
        ]

    st.caption(
        f"{len(filtered)} questions available in this view "
        f"· {len(QUESTIONS)} built-in questions"
    )

    if filtered:

        labels = [
            f"{i+1}. [{q[0]} · {q[1]}] {q[2]}"
            for i, q in enumerate(filtered)
        ]

        selected = st.selectbox(
            "Choose a Question",
            labels
        )

        chosen = filtered[labels.index(selected)]

        st.markdown(
            f"""
            <div class="panel">
                <b>{chosen[0]} · {chosen[1]}</b>
                <br><br>
                {chosen[2]}
            </div>
            """,
            unsafe_allow_html=True
        )

        is_bookmarked = (
            chosen[2] in st.session_state.bookmarks
        )

        if st.button(
            "★ Remove Bookmark"
            if is_bookmarked
            else "☆ Bookmark Question"
        ):

            if is_bookmarked:

                st.session_state.bookmarks.remove(chosen[2])

            else:

                st.session_state.bookmarks.append(chosen[2])

            st.rerun()

        answer = st.text_area(
            "Your Answer / Working",
            placeholder="Example: 7 * 12 = 84",
            height=120
        )

        if st.button(
            "Check My Answer",
            type="primary",
            use_container_width=True
        ):

            if answer.strip():

                run_review(chosen[2], answer)

            else:

                st.warning("Enter your working first.")

        if st.button("Load Another Random Question"):

            import random

            random_question = random.choice(filtered)

            st.session_state.selected_random_question = (
                random_question[2]
            )

            st.info(
                f"Random question: {random_question[2]}"
            )

    else:

        st.info(
            "No questions match your selected filters."
        )


# ============================================================
# ERROR INVESTIGATION
# ============================================================

elif page == "Error Investigation":

    st.markdown(
        '<div class="section-title">Error Investigation</div>',
        unsafe_allow_html=True
    )

    review = st.session_state.get("last_review")

    if review:

        render_review(review)

    else:

        st.info(
            "Review a solution first. Its detected errors, "
            "evidence and explanations will appear here."
        )

        if st.button("Go to Math Solver"):

            navigate("Math Solver & Reviewer")


# ============================================================
# PERSONALIZED LEARNING PROFILE
# ============================================================

elif page == "My Learning Profile":

    st.markdown(
        '<div class="section-title">My Learning Profile</div>',
        unsafe_allow_html=True
    )

    if not attempts:

        st.info(
            "Complete a few exercises to build your "
            "personal learning profile."
        )

        if st.button("Start Learning"):

            navigate("Question Library")

    else:

        findings, message = misconception_report(attempts)

        a, b, c = st.columns(3)

        with a:
            metric("Attempts", len(attempts))

        with b:
            metric(
                "Arithmetic Errors",
                int(df["errors"].sum())
            )

        with c:
            metric(
                "Topics Practised",
                df["topic"].nunique()
            )

        st.info(message)

        if findings:

            learning_df = pd.DataFrame(findings)

            learning_df = learning_df.rename(
                columns={
                    "category": "Practice Area",
                    "count": "Recorded Errors",
                    "tip": "Recommended Action"
                }
            )

            st.dataframe(
                learning_df,
                use_container_width=True,
                hide_index=True
            )

            st.plotly_chart(
                px.bar(
                    pd.DataFrame(findings),
                    x="category",
                    y="count",
                    title="Recurring Error Patterns"
                ),
                use_container_width=True
            )

        st.caption(
            "Patterns are learning signals, not a formal diagnosis."
        )

        if st.button("Practise My Weak Areas"):

            navigate("Adaptive Practice")


# ============================================================
# ADAPTIVE PRACTICE
# ============================================================

elif page == "Adaptive Practice":

    st.markdown(
        '<div class="section-title">Adaptive Practice Generator</div>',
        unsafe_allow_html=True
    )

    findings, _ = misconception_report(attempts)

    suggested = (
        findings[0]["category"]
        if findings
        else "Multiplication"
    )

    categories = [
        "Multiplication",
        "Addition",
        "Subtraction and signs",
        "Division and fractions",
        "Percentage calculations",
        "Ratios"
    ]

    category = st.selectbox(
        "Choose a Practice Area",
        categories,
        index=(
            categories.index(suggested)
            if suggested in categories
            else 0
        )
    )

    st.write(
        "Generate a targeted question based on your "
        "learning profile or choose a topic manually."
    )

    if st.button(
        "Generate Practice Question",
        type="primary"
    ):

        q, expr, ans, hint = generate_challenge(category)

        st.session_state.practice = {
            "q": q,
            "expr": expr,
            "ans": ans,
            "hint": hint,
            "category": category
        }

        st.session_state.pop("adaptive_answer", None)

    if st.session_state.get("practice"):

        p = st.session_state.practice

        st.markdown(
            f"""
            <div class="panel">
                <b>Topic: {p['category']}</b>
                <br><br>
                {p['q']}
            </div>
            """,
            unsafe_allow_html=True
        )

        with st.expander("Need a Hint?"):

            st.write(p["hint"])

        user_answer = st.text_input(
            "Your Answer",
            key="adaptive_answer"
        )

        if st.button(
            "Check Practice Answer",
            type="primary"
        ):

            if not user_answer.strip():

                st.warning("Enter your answer.")

            elif numeric_equal(user_answer, p["ans"]):

                st.success("Correct! Great work.")

                st.session_state.practice_correct = True

            else:

                st.error(
                    "Not quite. Recheck your operation and try again."
                )

                st.session_state.practice_correct = False

        with st.expander("Show Worked Answer"):

            st.code(
                f"{p['expr']} = {p['ans']}"
            )

        if st.button("Generate Next Question"):

            st.session_state.pop("practice", None)
            st.session_state.pop("adaptive_answer", None)
            st.rerun()


# ============================================================
# LEARNING HISTORY
# ============================================================

elif page == "Learning History":

    st.markdown(
        '<div class="section-title">Learning History</div>',
        unsafe_allow_html=True
    )

    if attempts:

        hist = pd.DataFrame(attempts)

        columns = [
            "created_at",
            "problem",
            "topic",
            "total_steps",
            "errors",
            "unverifiable"
        ]

        st.dataframe(
            hist[columns],
            use_container_width=True,
            hide_index=True
        )

        st.download_button(
            "⬇ Download Learning History (CSV)",
            hist.to_csv(index=False).encode("utf-8"),
            "my_mathreview_history.csv",
            "text/csv",
            use_container_width=True
        )

    else:

        st.info("No saved attempts yet.")


# ============================================================
# TEACHER DASHBOARD
# ============================================================

elif page == "Teacher Dashboard":

    st.markdown(
        '<div class="section-title">Teacher Error Intelligence Dashboard</div>',
        unsafe_allow_html=True
    )

    users = get_users()

    all_df = pd.DataFrame(all_attempts)

    if all_df.empty:

        st.info(
            "No student attempts have been recorded yet."
        )

    else:

        a, b, c, d = st.columns(4)

        with a:

            metric(
                "Learner Accounts",
                len([
                    u for u in users
                    if u["role"] == "student"
                ])
            )

        with b:

            metric("Total Attempts", len(all_df))

        with c:

            metric(
                "Arithmetic Errors",
                int(all_df["errors"].sum())
            )

        with d:

            metric(
                "Unverifiable Steps",
                int(all_df["unverifiable"].sum())
            )

        left, right = st.columns(2)

        with left:

            cats = (
                all_df.dropna(subset=["category"])
                .groupby("category")
                .size()
                .reset_index(name="Count")
            )

            if not cats.empty:

                st.plotly_chart(
                    px.bar(
                        cats,
                        x="category",
                        y="Count",
                        title="Common Error Categories"
                    ),
                    use_container_width=True
                )

        with right:

            per = (
                all_df.groupby("student_id")
                .agg(
                    attempts=("id", "count"),
                    errors=("errors", "sum")
                )
                .reset_index()
            )

            st.plotly_chart(
                px.bar(
                    per,
                    x="student_id",
                    y="errors",
                    title="Recorded Errors by Learner"
                ),
                use_container_width=True
            )

        st.markdown("### Student Attempts")

        st.dataframe(
            all_df[
                [
                    "created_at",
                    "student_id",
                    "problem",
                    "topic",
                    "total_steps",
                    "errors",
                    "category"
                ]
            ],
            use_container_width=True,
            hide_index=True
        )

        st.download_button(
            "Export Class Report CSV",
            all_df.to_csv(index=False).encode("utf-8"),
            "mathreview_class_report.csv",
            "text/csv"
        )

    if user["role"] == "admin":

        st.markdown("### Account Directory")

        st.dataframe(
            pd.DataFrame(users),
            use_container_width=True,
            hide_index=True
        )


# ============================================================
# QUESTION MANAGEMENT
# ============================================================

elif page == "Question Management":

    st.markdown(
        '<div class="section-title">Question Management</div>',
        unsafe_allow_html=True
    )

    st.info(
        "This section currently provides question-bank viewing. "
        "Adding, editing and deleting questions requires a "
        "persistent question-management database."
    )

    question_df = pd.DataFrame(
        [
            {
                "Topic": q[0],
                "Difficulty": q[1],
                "Question": q[2]
            }
            for q in QUESTIONS
        ]
    )

    st.dataframe(
        question_df,
        use_container_width=True,
        hide_index=True
    )

    st.download_button(
        "Export Question Bank CSV",
        question_df.to_csv(index=False).encode("utf-8"),
        "mathreview_question_bank.csv",
        "text/csv"
    )


# ============================================================
# SETTINGS AND ABOUT
# ============================================================

elif page == "Settings & About":

    st.markdown(
        '<div class="section-title">Settings & About</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        f"""
        **Signed in as:** {user['name']}

        **Email:** {user['email']}

        **Role:** {user['role']}
        """
    )

    st.divider()

    st.markdown("### Verification Policy")

    st.markdown("""
    - Python/SymPy independently checks supported arithmetic expressions.
    - AI transcription and explanations can make mistakes.
    - Confirm handwritten OCR before checking.
    - Operation choice and word-problem interpretation are not
      mathematically proven by the arithmetic verifier.
    - SQLite stores accounts and learning attempts locally.
    - The demo teacher account is intended only for local testing.
    """)

    st.markdown("### Project Information")

    st.write("**Project:** MathReview AI")

    st.write("**Problem Statement:** Mathematical calculation review.")

    st.write("**Category:** Education and Skill Development")

    st.write("**SDG:** SDG 4 – Quality Education")


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "MathReview AI · PS 76 · SDG 4 Quality Education "
    "| AI explains, Python verifies, and students learn."
)
