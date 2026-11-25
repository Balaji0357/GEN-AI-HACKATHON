# MathReview AI – Enhanced Edition

## Features
- Student/teacher registration and sign-in (local SQLite; PBKDF2 password hashing)
- Student dashboard and learning history
- Teacher error-intelligence dashboard
- Typed solution parser and Python/SymPy arithmetic verification
- Error replay and what-if branch
- Mistake reasoning and verified numerical evidence
- Handwritten image transcription using an OpenAI vision-capable model (student must confirm OCR)
- Searchable question library with 30 built-in questions across topics and difficulty
- Adaptive practice generator and personalized error pattern summary
- CSV export

## Run in VS Code (Windows PowerShell)
```powershell
cd mathreview_ai
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
copy .env.example .env
# Edit .env and add OPENAI_API_KEY
streamlit run app.py
```

If you already created a virtual environment in the parent folder, activate that environment first and then run `python -m pip install -r requirements.txt` from this project folder.

## Demo teacher account
- Email: `teacher@mathreview.ai`
- Password: `Teacher@123`

Create student accounts from the registration tab. The demo teacher account is seeded automatically in the local SQLite database.

## API configuration
`.env`:
```env
OPENAI_API_KEY=your_actual_api_key
OPENAI_MODEL=gpt-4o-mini
OPENAI_VISION_MODEL=gpt-4o-mini
```
The API is optional for typed fallback parsing and template explanations, but required for AI-based handwriting transcription and richer LLM parsing.

## Important limitations
- OCR output must be checked by the student before verification.
- Arithmetic verification supports restricted numeric expressions; it does not prove that the selected operation correctly models the word problem.
- Error categories are heuristic learning signals, not validated diagnoses.
- Error replay is a best-effort text-based propagation demonstration, not a general symbolic dependency solver.
- This is a local hackathon prototype. For public deployment, use a production identity provider, HTTPS, rate limiting, role approval, secure secrets, database backups and privacy controls.
