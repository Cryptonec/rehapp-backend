import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from db import get_db
import models

# ── Config ─────────────────────────────────────────────────────────────────

SECRET_KEY = os.environ.get("JWT_SECRET", "CHANGE_ME_IN_PRODUCTION")
ALGORITHM  = os.environ.get("JWT_ALGO",   "HS256")
EXPIRE_MIN = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")


# ── Helpers ────────────────────────────────────────────────────────────────

def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=EXPIRE_MIN))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# ── Dependency: aktif kurum ────────────────────────────────────────────────

def get_current_kurum(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> models.Kurum:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Kimlik doğrulanamadı",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        kurum_id: int = payload.get("sub")
        if kurum_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    kurum = db.query(models.Kurum).filter(models.Kurum.id == int(kurum_id)).first()
    if kurum is None or not kurum.approved:
        raise credentials_exception
    return kurum
