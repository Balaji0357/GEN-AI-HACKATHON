
import sqlite3, json, hashlib, secrets
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "mathreview.db"

def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con

def _hash_password(password, salt=None):
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 260_000).hex()
    return salt, digest

def init_db():
    with connect() as con:
        con.execute("""CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            salt TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'student',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )""")
        con.execute("""CREATE TABLE IF NOT EXISTS attempts (
          id INTEGER PRIMARY KEY AUTOINCREMENT, student_id TEXT NOT NULL,
          problem TEXT NOT NULL, solution TEXT NOT NULL, topic TEXT,
          total_steps INTEGER, errors INTEGER, unverifiable INTEGER,
          category TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP,
          verification_json TEXT)""")
        # Seed a demo teacher account for local hackathon demonstrations.
        row = con.execute("SELECT id FROM users WHERE email=?", ("teacher@mathreview.ai",)).fetchone()
        if not row:
            salt, digest = _hash_password("Teacher@123")
            con.execute("INSERT INTO users(name,email,salt,password_hash,role) VALUES(?,?,?,?,?)",
                        ("Demo Teacher", "teacher@mathreview.ai", salt, digest, "teacher"))

def register_user(name, email, password, role="student"):
    email = email.strip().lower()
    if not name.strip() or "@" not in email or len(password) < 8:
        return False, "Enter a name, valid email, and password with at least 8 characters."
    if role not in ("student", "teacher"):
        role = "student"
    salt, digest = _hash_password(password)
    try:
        with connect() as con:
            con.execute("INSERT INTO users(name,email,salt,password_hash,role) VALUES(?,?,?,?,?)",
                        (name.strip(), email, salt, digest, role))
        return True, "Account created. Please sign in."
    except sqlite3.IntegrityError:
        return False, "An account with this email already exists."

def authenticate(email, password):
    with connect() as con:
        row = con.execute("SELECT * FROM users WHERE email=?", (email.strip().lower(),)).fetchone()
    if not row:
        return None
    _, digest = _hash_password(password, row["salt"])
    if secrets.compare_digest(digest, row["password_hash"]):
        return {"id": row["id"], "name": row["name"], "email": row["email"], "role": row["role"]}
    return None

def save_attempt(student_id, problem, solution, topic, verification):
    errors = [v for v in verification if v["status"] == "error"]
    unver = [v for v in verification if v["status"] == "unverifiable"]
    category = None
    if errors:
        from .learning import classify_error
        category = classify_error(errors[0].get("expression", ""), errors[0].get("text", ""))
    with connect() as con:
        con.execute("""INSERT INTO attempts(student_id,problem,solution,topic,total_steps,errors,
                       unverifiable,category,verification_json) VALUES(?,?,?,?,?,?,?,?,?)""",
          (str(student_id), problem, solution, topic, len(verification), len(errors),
           len(unver), category, json.dumps(verification)))

def get_attempts(student_id=None):
    with connect() as con:
        if student_id is not None:
            rows = con.execute("SELECT * FROM attempts WHERE student_id=? ORDER BY created_at DESC",
                               (str(student_id),)).fetchall()
        else:
            rows = con.execute("SELECT * FROM attempts ORDER BY created_at DESC").fetchall()
    return [dict(r) for r in rows]

def get_users():
    with connect() as con:
        rows = con.execute("SELECT id,name,email,role,created_at FROM users ORDER BY created_at DESC").fetchall()
    return [dict(r) for r in rows]
