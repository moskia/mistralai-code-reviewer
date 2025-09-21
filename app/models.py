from pydantic import BaseModel, HttpUrl, Field, field_validator
from typing import List
import logging

logger = logging.getLogger(__name__)

class ReviewRequest(BaseModel):
    assignment_description: str = Field(..., min_length=10, max_length=1000, description="Description of the assignment")
    github_repo_url: HttpUrl = Field(..., description="Valid GitHub repository URL")
    candidate_level: str = Field(..., pattern="^(Junior|Middle|Senior)$", description="Candidate level must be Junior, Mid, or Senior")

    @field_validator("assignment_description")
    def validate_assignment_description(cls, value):
        value = str(value)
        if len(value.strip()) < 10:
            logger.error("Assignment description must be at least 10 characters long")
            raise ValueError("Assignment description must be at least 10 characters long")
        return value

    @field_validator("github_repo_url")
    def validate_github_url(cls, value):
        value = str(value)
        if not value.startswith("https://github.com/"):
            logger.error("GitHub repository URL must start with 'https://github.com/'")
            raise ValueError("GitHub repository URL must start with 'https://github.com/'")
        return value
    
class ReviewResponse(BaseModel):
    files_found: List[str] = Field(..., description="List of files found in the repository")
    result: str = Field(..., description="Result of the review")
