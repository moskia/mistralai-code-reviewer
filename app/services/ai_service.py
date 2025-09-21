from mistralai import Mistral
import logging
import os
import asyncio

logger = logging.getLogger(__name__)

# Load API key from environment
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
if not MISTRAL_API_KEY:
    raise ValueError("MISTRAL_API_KEY not found in environment variables")

# Configurable model (fallback to mistral-large-latest if not set)
MISTRAL_MODEL = os.getenv("MISTRAL_MODEL", "mistral-large-latest")

# Shared client
client = Mistral(api_key=MISTRAL_API_KEY)


async def generate_review(assignment_description: str, repo_contents: str, candidate_level: str) -> str:
    """
    Generate a code review using Mistral AI.
    Handles large repo contents, errors, and keeps FastAPI async-safe.
    """

    # Truncate repo contents if too long
    MAX_CONTENT_LENGTH = 20000
    if len(repo_contents) > MAX_CONTENT_LENGTH:
        logger.warning("Repo contents too large, truncating before sending to Mistral.")
        repo_contents = repo_contents[:MAX_CONTENT_LENGTH] + "\n... [truncated] ..."

    # Build prompt in safe string concatenation
    prompt_intro = f"You are a senior software engineer tasked with reviewing a coding assignment submitted by a {candidate_level}-level candidate.\n" \
                   "Provide a thorough analysis of the repository and assess the code quality based on industry best practices.\n" \
                   "Check how well the task aligns with the assignment description.\n\n"

    prompt_assignment = f"## Details of the Assignment:\n" \
                        f"- **Assignment Description**: {assignment_description}\n" \
                        f"- **Candidate Level**: {candidate_level}\n\n"

    prompt_instructions = (
        "### Instructions:\n"
        "1. **Identify and list the files in the repository**.\n"
        "2. **Analyze the code for the following criteria**:\n"
        "   - Code organization and structure\n"
        "   - Readability (variable names, comments, and documentation)\n"
        "   - Code quality (best practices, performance, modularity)\n"
        "   - Error handling and edge-case management\n"
        "   - Use of testing (unit tests or integration tests)\n"
        "3. **Identify any potential issues or areas for improvement** in the codebase.\n"
        "4. **Provide a rating out of 5** based on the candidate's level and the code's quality.\n"
        "5. Write a **conclusion** summarizing the overall evaluation.\n\n"
    )

    prompt_format = (
        "Respond in the structured format below:\n"
        "## Review Results\n"
        "**Found Files**:\n"
        "--start--\n"
        "- <file1>\n"
        "- <file2>\n"
        "--end--\n"
        "**Downsides/Comments**:\n"
        "1. <Comment on file1>\n"
        "2. <Comment on file2>\n\n"
        "**Rating**:\n"
        f"<Rating>/5 (for {candidate_level}-level)\n\n"
        "**Conclusion**:\n"
        "<Your conclusion>\n\n"
    )

    prompt_repo = f"## Repo Contents:\n{repo_contents}\n\nBegin the review."

    # Combine all parts safely
    prompt = prompt_intro + prompt_assignment + prompt_instructions + prompt_format + prompt_repo

    logger.info(f"Prompt prepared. Sending to Mistral model: {MISTRAL_MODEL}")

    try:
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: client.chat.complete(
                model=MISTRAL_MODEL,
                messages=[
                    {"role": "system", "content": "You are a skilled software engineer providing a code review."},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=2000,
                temperature=0.7,
            )
        )

        return response.choices[0].message.content

    except Exception as e:
        logger.error(f"Mistral API call failed: {e}")
        return "⚠️ Error: Unable to generate review at this time. Please try again later."

