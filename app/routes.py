import json, re, logging
from typing import Any, Tuple
from fastapi import APIRouter, HTTPException
from app.models import ReviewRequest, ReviewResponse, Finding
from app.services.github_service import fetch_repo_and_generate_message
from app.services.ai_service import generate_review

router = APIRouter()
logger = logging.getLogger(__name__)

def _parse_ai_json(text: str) -> Tuple[bool, Any]:
    if not isinstance(text, str) or not text.strip():
        return False, "empty"
    raw = text.strip()
    if raw.startswith("```"):
        raw = raw.strip("`").replace("json\n", "").replace("JSON\n", "").strip()
    try:
        obj = json.loads(raw)
        if isinstance(obj, str): obj = json.loads(obj)
        if isinstance(obj, dict): return True, obj
    except: pass
    try:
        m = re.search(r"\{.*\}", raw, flags=re.DOTALL)
        if m:
            obj = json.loads(m.group(0))
            if isinstance(obj, dict): return True, obj
    except: pass
    return False, "parse failed"

@router.post("/review", response_model=ReviewResponse)
async def review_code(request: ReviewRequest):
    try:
        repo_contents = fetch_repo_and_generate_message(request.github_repo_url)
        ai_text = await generate_review(
            assignment_description=request.assignment_description,
            repo_contents=repo_contents,
            candidate_level=request.candidate_level,
        )
    except HTTPException: raise
    except Exception as e:
        logger.exception("Unhandled error in /review")
        raise HTTPException(status_code=502, detail=str(e))

    ok, parsed = _parse_ai_json(ai_text)
    if ok:
        data = parsed
        files_found = list(map(str, data.get("files_found", [])))
        rating = int(data.get("rating_out_of_5", 0) or 0)
        summary = str(data.get("summary", "") or "")
        truncated = "truncated" in repo_contents.lower()
        if truncated:
            summary = "(Note: analysis truncated)\n" + summary
        conclusion = str(data.get("conclusion", "") or "")
        findings = [Finding(**f) for f in (data.get("findings", []) or []) if isinstance(f, dict)]

        logger.info("Review: %d files (truncated=%s). Examples: %s",
                    len(files_found), truncated, files_found[:5])

        return ReviewResponse(
            files_found=files_found,
            rating_out_of_5=rating,
            summary=summary,
            findings=findings,
            conclusion=conclusion,
            truncated=truncated,
            included_files=len(files_found),
            total_bytes=len(repo_contents.encode("utf-8")),
        )

    logger.warning("AI JSON parse failed: %s", parsed)
    return ReviewResponse(
        files_found=[], rating_out_of_5=0,
        summary="Model returned unstructured text.",
        findings=[], conclusion="", raw_text=ai_text
    )

