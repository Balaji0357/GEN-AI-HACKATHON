import os, json
from dotenv import load_dotenv

load_dotenv()


def ask_json(system_prompt: str, user_prompt: str):
    """Return parsed JSON from OpenAI. Returns None when no key/API is available."""
    key = os.getenv("OPENAI_API_KEY", "").strip()
    if not key or key == "your_api_key_here":
        return None
    try:
        from openai import OpenAI
        client = OpenAI(api_key=key)
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            temperature=0.1,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return json.loads(response.choices[0].message.content)
    except Exception:
        return None


def ask_text(system_prompt: str, user_prompt: str):
    key = os.getenv("OPENAI_API_KEY", "").strip()
    if not key or key == "your_api_key_here":
        return None
    try:
        from openai import OpenAI
        client = OpenAI(api_key=key)
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            temperature=0.2,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return response.choices[0].message.content
    except Exception:
        return None
