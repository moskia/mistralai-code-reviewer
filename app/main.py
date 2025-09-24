import logging
from fastapi import FastAPI
from dotenv import load_dotenv

load_dotenv()
from app.routes import router  # noqa

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("app.log"), logging.StreamHandler()],
)

app = FastAPI(title="CodeReviewer", version="1.0.0")
app.include_router(router)

