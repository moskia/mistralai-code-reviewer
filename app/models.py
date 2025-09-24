from typing import List, Optional, Literal
from pydantic import BaseModel, Field

class ReviewRequest(BaseModel):
    assignment_description: str = Field(..., description="Assignment description")
    github_repo_url: str = Field(..., description="GitHub repo URL")
    candidate_level: Literal["Junior", "Mid", "Senior"] = Field(..., description="Candidate level")

class Finding(BaseModel):
    file: Optional[str] = None
    line: Optional[int] = None
    severity: Literal["low", "medium", "high"]
    issue: str
    suggestion: str

class ReviewResponse(BaseModel):
    files_found: List[str]
    rating_out_of_5: int
    summary: str
    findings: List[Finding]
    conclusion: str
    truncated: bool = False
    included_files: int = 0
    total_bytes: int = 0
    raw_text: Optional[str] = None

