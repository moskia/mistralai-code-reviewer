import os, logging, json
from mistralai import Mistral

logger = logging.getLogger(__name__)

MISTRAL_MODEL = os.getenv("MISTRAL_MODEL", "mistral-large-latest")
_client = None

def _get_client() -> Mistral:
    global _client
    if _client is None:
        api_key = os.getenv("MISTRAL_API_KEY")
        if not api_key:
            raise RuntimeError("Missing MISTRAL_API_KEY. Add it to .env")
        _client = Mistral(api_key=api_key)
    return _client

JSON_SCHEMA_INSTRUCTIONS = """
You are a code reviewer. Return ONLY JSON matching this schema:

{
  "files_found": ["path/to/file1"],
  "rating_out_of_5": 1-5,
  "summary": "overview",
  "findings": [
    {"file": "path", "line": 123, "severity": "low|medium|high", "issue": "text", "suggestion": "text"}
  ],
  "conclusion": "short summary"
}
"""

async def generate_review(assignment_description: str, repo_contents: str, candidate_level: str) -> str:
    client = _get_client()
    system_prompt = (
        "You are a strict, helpful code reviewer. "
        "Focus first on application code, then config/docs if room. "
        "Be concise, actionable, security-focused."
    )
    user_prompt = (
        f"ASSIGNMENT:\n{assignment_description}\n\n"
        f"CANDIDATE LEVEL: {candidate_level}\n\n"
        f"REPO CONTENT (may be truncated):\n{repo_contents}\n\n"
        f"{JSON_SCHEMA_INSTRUCTIONS}"
    )
    resp = client.chat.complete(
        model=MISTRAL_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
    )
    text = resp.choices[0].message.content.strip()
    if text.startswith("```"):
        text = text.strip("`").replace("json\n", "").replace("JSON\n", "").strip()
    try:
        json.loads(text)
    except Exception:
        logger.warning("AI returned non-JSON; will pass raw text")
    return text

