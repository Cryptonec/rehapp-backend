from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import sqlalchemy

from db import engine
import models
from routers import auth, students, diagnoses, modules, saved_groups, bkds, bkds_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up – creating tables if needed…")
    models.Base.metadata.create_all(bind=engine)
    with engine.connect() as conn:
        conn.execute(sqlalchemy.text(
            "ALTER TABLE kurumlar "
            "ADD COLUMN IF NOT EXISTS bkds_email VARCHAR(200), "
            "ADD COLUMN IF NOT EXISTS bkds_password VARCHAR(256)"
        ))
        conn.commit()
    logger.info("DB migration OK.")
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

app.include_router(auth.router,             prefix="/api")
app.include_router(students.router,         prefix="/api")
app.include_router(diagnoses.router,        prefix="/api")
app.include_router(modules.router,          prefix="/api")
app.include_router(saved_groups.router,     prefix="/api")
app.include_router(bkds.router,             prefix="/bkds",  tags=["BKDS"])
app.include_router(bkds_settings.router,    prefix="/kurum", tags=["Kurum"])


@app.get("/api/health")
def health():
    return {"status": "ok"}
