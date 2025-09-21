from fastapi import APIRouter
import logging
from app.models import ReviewRequest, ReviewResponse
from app.services.ai_service import generate_review
from app.services.github_service import fetch_repo_and_generate_message


router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/review")
async def review_code(request: ReviewRequest):
    logger.info("Received review request")
    repo_contents = fetch_repo_and_generate_message(request.github_repo_url)
    review = await generate_review(
            assignment_description=request.assignment_description,
            repo_contents=repo_contents,
            candidate_level=request.candidate_level,
            )
    response = ReviewResponse(
            files_found = [
                file.lstrip("- ").strip() for file in review.split("--start--")[1].split("--end--")[0].split("\n")[1:] if file.strip()
                ],
            result=review.split("--end--")[1].strip(),
            )
    return response
