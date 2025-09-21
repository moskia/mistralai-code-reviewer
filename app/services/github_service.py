from app.utils import fetch_repo_contents, fetch_file_contents
import logging
import os
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
if not GITHUB_TOKEN:
    raise ValueError("GITHUB_TOKEN not found in environment variables")


def check_if_cool(repo_url):  
    """Check if the repo belongs to your GitHub or has special keywords."""
    username = repo_url.split("/")[3]
    if username.lower() == "moskia":
        return True
    if any(keyword in repo_url.lower() for keyword in ["ai", "security", "cloud"]):
        return True
    return False


def fetch_repo_and_generate_message(repo_url):
    logger.info(f"Fetching repository: {repo_url}")
    api_url = repo_url.replace("https://github.com", "https://api.github.com/repos")
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}

    try:
        repo_files = fetch_repo_contents(f"{api_url}/contents", headers)
    except Exception as e:
        logger.error(f"Error fetching repository: {repo_url}, Error: {e}")
        raise e

    file_contents = fetch_file_contents(repo_files, headers)
    logger.debug(f"Response: {file_contents}")

    # Build the message
    message = f"📂 Repository Analysis for {repo_url}\n\n"

    message += "📁 Files Retrieved:\n"
    message += "\n".join(file["path"] for file in repo_files) + "\n\n"

    message += "📝 File Contents (preview):\n"
    for file_path, content in file_contents.items():
        if file_path.endswith(".py"):
            message += f"🐍 Python File: {file_path}\n{content[:200]}...\n\n"
        elif file_path == "Dockerfile":
            message += f"🐳 Dockerfile Detected: {file_path}\n{content[:200]}...\n\n"
        elif file_path.lower() == "readme.md":
            message += f"📖 README Found!\n{content[:200]}...\n\n"
        else:
            message += f"📄 {file_path}\n{content[:200]}...\n\n"

    # Simple scoring system
    score = 0
    if "README.md" in file_contents:
        score += 1
    if "requirements.txt" in file_contents or "pyproject.toml" in file_contents:
        score += 1
    if any(f.endswith(".py") for f in file_contents):
        score += 2
    if "Dockerfile" in file_contents:
        score += 1

    message += f"📊 Repo Quality Score: {score}/5\n"

    # Add personalized note
    if check_if_cool(repo_url):
        message += "\n🌟 This repo is special! Made by a cool developer or matches key topics. Extra credit given!"

    return message

