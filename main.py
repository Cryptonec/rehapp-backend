from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from db import engine
import models
from routers import auth, students, diagnoses, modules, saved_groups
from routers import bkds

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up – creating tables if needed…")
    models.Base.metadata.create_all(bind=engine)
    yield
    logger.info("Shutting down.")


app = FastAPI(title="Rehapp API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router,         prefix="/api")
app.include_router(students.router,     prefix="/api")
app.include_router(diagnoses.router,    prefix="/api")
app.include_router(modules.router,      prefix="/api")
app.include_router(saved_groups.router, prefix="/api")
app.include_router(bkds.router,         prefix="/bkds", tags=["BKDS"])


@app.api_route("/api/health", methods=["GET", "HEAD"])
def health():
    return {"status": "ok"}
