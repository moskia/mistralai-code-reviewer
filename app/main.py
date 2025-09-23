from fastapi import FastAPI
import logging

from dotenv import load_dotenv
load_dotenv()

from app.routes import router



logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("app.log")
            ],
        )

app = FastAPI(
        title="CodeReviewer",
        description="An API to review codes using SDK",
        version="1.0.0",
        )


app.include_router(router)
