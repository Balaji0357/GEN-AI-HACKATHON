
import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
from core.database import init_db, register_user, authenticate, save_attempt, get_attempts, get_users
from core.parser import parse_solution
from core.verifier import verify_steps
from core.replay import build_replay
from core.learning import misconception_report, explanation, generate_challenge, classify_error
from core.ocr import read_handwritten_solution
from core.question_bank import QUESTIONS

st.set_page_config(page_title="MathReview AI", page_icon="🧮", layout="wide", initial_sidebar_state="expanded")
init_db()

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');
html, body, [class*="css"] {font-family:'DM Sans',sans-serif}
[data-testid="stAppViewContainer"] {background:#f5f7fb}
[data-testid="stSidebar"] {background:#101d35}
[data-testid="stSidebar"] * {color:#edf3ff !important}
.block-container {max-width:1450px;padding-top:1.4rem;padding-bottom:3rem}
.hero {padding:1.55rem 1.8rem;border-radius:22px;background:linear-gradient(115deg,#101d35,#174a83 65%,#167e83);color:#fff;margin-bottom:1.15rem;box-shadow:0 12px 30px rgba(20,45,80,.12)}
.hero h1 {font-family:Manrope,sans-serif;color:#fff;font-size:2.15rem;margin:0}
.hero p {color:#d8e7f7;margin:.45rem 0 0;font-size:1rem}
.eyebrow {text-transform:uppercase;letter-spacing:.13em;font-size:.72rem;font-weight:700;color:#b6d7f3}
.section-title {font-family:Manrope,sans-serif;color:#172b49;font-weight:800;font-size:1.3rem;margin:.25rem 0 .75rem}
.metric-card {background:#fff;border:1px solid #e6ebf2;border-radius:16px;padding:1rem 1.1rem;min-height:112px}
.metric-label {color:#66758b;font-size:.82rem;font-weight:600}
.metric-value {font-family:Manrope,sans-serif;color:#142b4a;font-size:1.8rem;font-weight:800;margin-top:.25rem}
.metric-note {color:#8b98a9;font-size:.75rem}
.panel {background:#fff;border:1px solid #e6ebf2;border-radius:18px;padding:1.15rem 1.25rem;margin-bottom:.8rem}
div.stButton>button[kind="primary"] {background:linear-gradient(90deg,#1764a5,#168d91);border:0;border-radius:11px;font-weight:700;min-height:2.8rem}
div.stButton>button {border-radius:10px}
[data-testid="stTextArea"] textarea,[data-testid="stTextInput"] input {border-radius:10px}
.small-muted {color:#77869a;font-size:.86rem}
</style>
""", unsafe_allow_html=True)

def metric(label, value, note=""):
    st.markdown(f"<div class='metric-card'><div class='metric-label'>{label}</div><div class='metric-value'>{value}</div><div class='metric-note'>{note}</div></div>", unsafe_allow_html=True)

def login_screen():
    st.markdown("<div class='hero'><div class='eyebrow'>AI-powered learning workspace</div><h1>🧮 MathReview AI</h1><p>Understand every mistake. Verify every calculation. Improve with every attempt.</p></div>", unsafe_allow_html=True)
    left, right = st.columns([1.05, 1], gap="large")
    with left:
        st.markdown("### A smarter way to learn mathematics")
        st.write("Review typed or handwritten work, investigate calculation mistakes, and receive practice tailored to your learning needs.")
        for title, desc in [
            ("✍️ Handwritten analyzer","Upload a photo of your working and confirm the extracted equations."),
            ("🔎 Intelligent error detection","Find the exact step where the arithmetic differs."),
            ("🧠 Mistake reasoning","Understand the likely source of the mistake."),
            ("📈 Personal learning profile","Track recurring patterns across your attempts."),
            ("🎯 Adaptive practice","Get new questions based on topics that need attention.")
        ]:
            st.markdown(f"**{title}**  \n<span class='small-muted'>{desc}</span>", unsafe_allow_html=True)
    with right:
        tab1, tab2 = st.tabs(["Sign in", "Create account"])
        with tab1:
            with st.form("login_form"):
                email = st.text_input("Email", placeholder="you@example.com")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Sign in", type="primary", use_container_width=True)
            if submitted:
                user = authenticate(email, password)
                if user:
                    st.session_state.user = user
                    st.rerun()
                else:
                    st.error("Email or password is incorrect.")
            st.info("Demo teacher: teacher@mathreview.ai  |  Password: Teacher@123")
        with tab2:
            with st.form("register_form"):
                name = st.text_input("Full name")
                new_email = st.text_input("Email address")
                new_password = st.text_input("Password (minimum 8 characters)", type="password")
                role = st.selectbox("Account type", ["student", "teacher"])
                create = st.form_submit_button("Create account", type="primary", use_container_width=True)
            if create:
                ok, message = register_user(name, new_email, new_password, role)
                (st.success if ok else st.error)(message)

if "user" not in st.session_state:
    login_screen()
    st.stop()

user = st.session_state.user
uid = str(user["id"])
attempts = get_attempts(uid)
all_attempts = get_attempts() if user["role"] in ("teacher", "admin") else attempts
df = pd.DataFrame(attempts) if attempts else pd.DataFrame()
page_options = ["Dashboard", "Math Solver & Reviewer", "Handwritten Analyzer", "Question Library",
                "Error Investigation", "My Learning Profile", "Adaptive Practice", "Learning History"]
if user["role"] in ("teacher", "admin"):
    page_options += ["Teacher Dashboard"]
page_options += ["Settings & About"]



# NAVIGATION STATE
if st.session_state.get("quick_nav"):
    target_page = st.session_state.pop("quick_nav")
    if target_page in page_options:
        st.session_state["page_nav"] = target_page

if "page_nav" not in st.session_state:
    st.session_state["page_nav"] = "Dashboard"

# SIDEBAR
with st.sidebar:
    st.markdown("## 🧮 MathReview AI")
    st.caption("INTELLIGENT LEARNING WORKSPACE")
    st.divider()

    st.markdown(f"**{user['name']}**")
    st.caption(f"{user['role'].title()} account")

    page = st.radio(
        "WORKSPACE",
        page_options,
        key="page_nav"
    )

    st.divider()
    st.caption(
        "Arithmetic verified by Python/SymPy. "
        "AI reasoning suggestions are labelled separately."
    )

    if st.button("Sign out", use_container_width=True):
        st.session_state.pop("user", None)
        st.session_state.pop("last_review", None)
        st.session_state.pop("page_nav", None)
        st.rerun()



def run_review(problem, solution):
    with st.spinner("Parsing and independently checking the solution..."):
        parsed = parse_solution(problem, solution)
        verification = verify_steps(parsed.get("steps", []))
        replay = build_replay(parsed.get("steps", []), verification)
        explanation_text, explanation_source = explanation(problem, parsed.get("steps", []), verification)
        save_attempt(uid, problem, solution, parsed.get("topic", "other"), verification)
    st.session_state.last_review = {"parsed": parsed, "verification": verification, "replay": replay,
                                    "explanation": explanation_text, "explanation_source": explanation_source,
                                    "problem": problem, "solution": solution}
    st.rerun()

def render_review(review):
    parsed, verification, replay = review["parsed"], review["verification"], review["replay"]
    st.markdown("### Review results")
    a,b,c,d = st.columns(4)
    a.metric("Steps identified", len(verification))
    b.metric("Arithmetic errors", sum(v["status"]=="error" for v in verification))
    c.metric("Verified steps", sum(v["status"]=="correct" for v in verification))
    d.metric("Needs review", sum(v["status"]=="unverifiable" for v in verification))
    rows=[]
    for v in verification:
        rows.append({"Step":v["step_id"],"Expression":v["expression"],"Student answer":v["claimed_result"],
                     "Verified answer":v["actual_result"] or "—",
                     "Status":{"correct":"Verified","error":"Arithmetic error","unverifiable":"Unverifiable"}[v["status"]],
                     "Earlier error dependency":"Yes" if v.get("depends_on_earlier_error") else "No"})
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    st.caption("A later step can be arithmetically correct while depending on an earlier incorrect value.")
    t1,t2,t3,t4 = st.tabs(["Error Replay", "Mistake Reasoning", "Verified Evidence", "Extracted Steps"])
    with t1:
        st.write("Original and corrected calculation paths. Review substitutions for complex expressions.")
        for r in replay:
            with st.container(border=True):
                st.markdown(f"**Step {r['step_id']}**")
                st.write(f"Original: `{r['original_expression']}` = `{r['student_claim']}`")
                if r.get("corrected_expression") != r.get("original_expression") or r.get("original_status")=="error":
                    st.success(f"Corrected branch: `{r.get('corrected_expression')}` → **{r.get('replay_value') or r.get('verified_value') or 'Needs manual review'}**")
    with t2:
        st.info(review["explanation"])
        st.caption(review["explanation_source"])
        errors=[v for v in verification if v["status"]=="error"]
        if errors:
            category=classify_error(errors[0]["expression"])
            st.markdown(f"**Likely practice concept:** {category}")
            st.write("This is a suggested learning category based on the expression, not a definitive diagnosis.")
    with t3:
        st.write("These are the code-calculated values used as numerical evidence.")
        st.dataframe(pd.DataFrame([{"Step":v["step_id"],"Expression":v["expression"],"Claim":v["claimed_result"],
                                    "Code result":v["actual_result"],"Status":v["status"]} for v in verification]),
                     use_container_width=True, hide_index=True)
    with t4:
        st.json(parsed)

if page == "Dashboard":
    st.markdown(f"<div class='hero'><div class='eyebrow'>Your learning overview</div><h1>Welcome back, {user['name'].split()[0]} 👋</h1><p>Your mathematics progress, practice recommendations and recent activity in one place.</p></div>", unsafe_allow_html=True)
    total = len(attempts)
    steps = int(df.total_steps.sum()) if total else 0
    errors = int(df.errors.sum()) if total else 0
    verified = max(steps-errors-(int(df.unverifiable.sum()) if total else 0),0)
    c1,c2,c3,c4=st.columns(4)
    with c1: metric("Practice attempts",total,"All saved reviews")
    with c2: metric("Steps reviewed",steps,"Expressions processed")
    with c3: metric("Errors found",errors,"Across your attempts")
    with c4: metric("Verified steps",verified,"Arithmetic matches")
    left,right=st.columns([1.35,1])
    with left:
        st.markdown("<div class='section-title'>Learning activity</div>",unsafe_allow_html=True)
        if total:
            chart=df.copy()
            chart["created_at"]=pd.to_datetime(chart["created_at"],errors="coerce")
            trend=chart.groupby(chart["created_at"].dt.date,as_index=False).agg(attempts=("id","count"),errors=("errors","sum"))
            st.plotly_chart(px.line(trend,x="created_at",y="attempts",markers=True,title="Your practice sessions"),use_container_width=True)
        else:
            st.info("Your activity chart will appear after your first solution review.")
    with right:
        st.markdown("<div class='section-title'>Recommended next step</div>",unsafe_allow_html=True)
        if total:
            findings,msg=misconception_report(attempts)
            st.info(msg)
            if findings: st.write(f"Practise next: **{findings[0]['category']}**")
        else:
            st.write("Start with a question from the Question Library or review your own working.")
        if st.button("Start a practice session",type="primary",use_container_width=True):
            st.session_state.quick_nav="Adaptive Practice"; st.rerun()
    st.markdown("### Quick actions")
    q1,q2,q3=st.columns(3)
    with q1:
        if st.button("✍️ Review a solution",use_container_width=True): st.session_state.quick_nav="Math Solver & Reviewer"; st.rerun()
    with q2:
        if st.button("📷 Upload handwriting",use_container_width=True): st.session_state.quick_nav="Handwritten Analyzer"; st.rerun()
    with q3:
        if st.button("🎯 Practise weak topics",use_container_width=True): st.session_state.quick_nav="Adaptive Practice"; st.rerun()

elif page == "Math Solver & Reviewer":
    st.markdown("<div class='section-title'>Math Solver & Reviewer</div>",unsafe_allow_html=True)
    st.write("Enter the question and the student's own working. The system checks arithmetic separately from reasoning.")
    c1,c2=st.columns(2)
    with c1: problem=st.text_area("Mathematical question",height=180,placeholder="A shop sells 12 notebooks at ₹15 each. Find the total cost.")
    with c2: solution=st.text_area("Student's working",height=180,placeholder="12 * 15 = 170\n170 + 20 = 190")
    if st.button("Review my solution",type="primary",use_container_width=True):
        if problem.strip() and solution.strip(): run_review(problem,solution)
        else: st.warning("Enter both the question and attempted solution.")
    if st.session_state.get("last_review"): render_review(st.session_state.last_review)

elif page == "Handwritten Analyzer":
    st.markdown("<div class='section-title'>Handwritten Solution Analyzer</div>",unsafe_allow_html=True)
    st.write("Upload a clear photo or scan of handwritten mathematical work. AI transcribes it; you confirm the text before arithmetic verification.")
    upload=st.file_uploader("Upload handwritten solution",type=["png","jpg","jpeg","webp"])
    problem=st.text_area("Original mathematical question",height=100)
    if upload:
        st.image(upload,caption="Uploaded work",use_container_width=True)
        if st.button("Recognize handwritten steps",type="primary"):
            text,notice=read_handwritten_solution(upload.getvalue(),upload.type or "image/png")
            if text:
                st.session_state.ocr_text=text
                st.success(notice)
            else: st.error(notice)
    if "ocr_text" in st.session_state:
        transcribed=st.text_area("Confirm or correct the recognized steps",value=st.session_state.ocr_text,height=220)
        st.caption("Do not proceed until the recognized numbers and operators match the handwriting.")
        if st.button("Verify these handwritten steps",type="primary"):
            if problem.strip() and transcribed.strip(): run_review(problem,transcribed)
            else: st.warning("Enter the original question and confirm the transcription.")
    if st.session_state.get("last_review"): render_review(st.session_state.last_review)

elif page == "Question Library":
    st.markdown("<div class='section-title'>Question Library</div>",unsafe_allow_html=True)
    topics=sorted(set(q[0] for q in QUESTIONS))
    f1,f2,f3=st.columns(3)
    topic=f1.selectbox("Topic",["All"]+topics)
    level=f2.selectbox("Difficulty",["All","Beginner","Intermediate","Advanced"])
    search=f3.text_input("Search questions")
    filtered=[q for q in QUESTIONS if (topic=="All" or q[0]==topic) and (level=="All" or q[1]==level) and search.lower() in q[2].lower()]
    st.caption(f"{len(filtered)} questions available in this filtered view • {len(QUESTIONS)} built-in questions")
    if filtered:
        labels=[f"{i+1}. [{q[0]} · {q[1]}] {q[2]}" for i,q in enumerate(filtered)]
        selected=st.selectbox("Choose a question",labels)
        chosen=filtered[labels.index(selected)]
        st.markdown(f"<div class='panel'><b>{chosen[0]} · {chosen[1]}</b><br><br>{chosen[2]}</div>",unsafe_allow_html=True)
        answer=st.text_input("Your answer / working (example: 7 * 12 = 84)")
        if st.button("Check my answer",type="primary"):
            if answer.strip(): run_review(chosen[2],answer)
            else: st.warning("Enter your working.")
    else: st.info("No questions match those filters.")

elif page == "Error Investigation":
    st.markdown("<div class='section-title'>Error Investigation</div>",unsafe_allow_html=True)
    review=st.session_state.get("last_review")
    if review: render_review(review)
    else: st.info("Review a solution first. Its detected errors and explanations will appear here.")

elif page == "My Learning Profile":
    st.markdown("<div class='section-title'>Personalized Learning Profile</div>",unsafe_allow_html=True)
    if not attempts: st.info("Complete a few exercises to build your personal learning profile.")
    else:
        findings,message=misconception_report(attempts)
        a,b,c=st.columns(3)
        with a: metric("Attempts",len(attempts))
        with b: metric("Arithmetic errors",int(df.errors.sum()))
        with c: metric("Topics practised",df.topic.nunique())
        st.info(message)
        if findings:
            st.dataframe(pd.DataFrame(findings).rename(columns={"category":"Practice area","count":"Recorded errors","tip":"Recommended action"}),use_container_width=True,hide_index=True)
            st.plotly_chart(px.bar(pd.DataFrame(findings),x="category",y="count",title="Your recurring error patterns"),use_container_width=True)
        st.caption("Patterns are learning signals, not a formal diagnosis. Confirm them with additional practice.")

elif page == "Adaptive Practice":
    st.markdown("<div class='section-title'>Adaptive Practice Generator</div>",unsafe_allow_html=True)
    findings,_=misconception_report(attempts)
    suggested=findings[0]["category"] if findings else "Multiplication"
    categories=["Multiplication","Addition","Subtraction and signs","Division and fractions","Percentage calculations","Ratios"]
    category=st.selectbox("Choose a practice area",categories,index=categories.index(suggested) if suggested in categories else 0)
    st.write("Generate a targeted question based on your learning profile or choose a topic manually.")
    if st.button("Generate a practice question",type="primary"):
        q,expr,ans,hint=generate_challenge(category)
        st.session_state.practice={"q":q,"expr":expr,"ans":ans,"hint":hint,"category":category}
    if st.session_state.get("practice"):
        p=st.session_state.practice
        st.markdown(f"<div class='panel'><b>Topic: {p['category']}</b><br><br>{p['q']}</div>",unsafe_allow_html=True)
        with st.expander("Need a hint?"): st.write(p["hint"])
        user_answer=st.text_input("Your answer",key="adaptive_answer")
        if st.button("Check practice answer"):
            from core.verifier import numeric_equal
            if numeric_equal(user_answer,p["ans"]): st.success("Correct! Great work.")
            else: st.error("Not quite. Recheck your operation and try again.")
        with st.expander("Show worked answer"): st.code(f"{p['expr']} = {p['ans']}")

elif page == "Learning History":
    st.markdown("<div class='section-title'>Learning History</div>",unsafe_allow_html=True)
    if attempts:
        hist=pd.DataFrame(attempts)
        st.dataframe(hist[["created_at","problem","topic","total_steps","errors","unverifiable"]],use_container_width=True,hide_index=True)
        st.download_button("Download my learning history (CSV)",hist.to_csv(index=False).encode("utf-8"),"my_mathreview_history.csv","text/csv")
    else: st.info("No saved attempts yet.")

elif page == "Teacher Dashboard":
    st.markdown("<div class='section-title'>Teacher Error Intelligence Dashboard</div>",unsafe_allow_html=True)
    users=get_users()
    all_df=pd.DataFrame(all_attempts)
    if all_df.empty:
        st.info("No student attempts have been recorded yet.")
    else:
        students=all_df.student_id.nunique()
        a,b,c,d=st.columns(4)
        with a: metric("Learner accounts",len([u for u in users if u["role"]=="student"]))
        with b: metric("Attempts",len(all_df))
        with c: metric("Arithmetic errors",int(all_df.errors.sum()))
        with d: metric("Unverifiable steps",int(all_df.unverifiable.sum()))
        left,right=st.columns(2)
        with left:
            cats=all_df.dropna(subset=["category"]).groupby("category",as_index=False).size()
            if not cats.empty: st.plotly_chart(px.bar(cats,x="category",y="size",title="Common error categories"),use_container_width=True)
        with right:
            per=all_df.groupby("student_id",as_index=False).agg(attempts=("id","count"),errors=("errors","sum"))
            st.plotly_chart(px.bar(per,x="student_id",y="errors",title="Recorded errors by learner"),use_container_width=True)
        st.dataframe(all_df[["created_at","student_id","problem","topic","total_steps","errors","category"]],use_container_width=True,hide_index=True)
        st.download_button("Export class report CSV",all_df.to_csv(index=False).encode("utf-8"),"mathreview_class_report.csv","text/csv")
    if user["role"]=="admin":
        st.markdown("### Account directory")
        st.dataframe(pd.DataFrame(users),use_container_width=True,hide_index=True)

else:
    st.markdown("<div class='section-title'>Settings & About</div>",unsafe_allow_html=True)
    st.markdown(f"**Signed in as:** {user['name']}  \n**Email:** {user['email']}  \n**Role:** {user['role']}")
    st.markdown("""
**Verification policy**
- Python/SymPy checks supported arithmetic expressions independently.
- AI transcription and explanations can make mistakes; confirm handwritten OCR before checking.
- Operation choice and word-problem interpretation are not mathematically proven by the arithmetic verifier.
- The local SQLite database stores accounts and learning attempts on this computer.
- The demo teacher account is intended only for local testing. Change or disable demo credentials before deployment.
""")

st.divider()
st.caption("MathReview AI · PS 76 · SDG 4 Quality Education | Arithmetic verified by code; explanations generated by AI.")
