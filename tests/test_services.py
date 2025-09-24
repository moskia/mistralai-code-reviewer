import asyncio
from dotenv import load_dotenv
load_dotenv()
from app.services.ai_service import generate_review

async def main():
    fake_repo = "# Repository Files\n- `main.py`\n```def hello(): pass```"
    result = await generate_review("Build an API", fake_repo, "Junior")
    print(result)

if __name__ == "__main__":
    asyncio.run(main())

