"""
rehapp-backend/routers/bkds.py
SSO bridge: Rehapp → bkds-takip  (JWT tabanlı, HTTP çağrısı yok)
"""
import os
import json
import time
import hashlib
import base64
from fastapi import APIRouter, Depends, HTTPException
from auth import get_current_kurum
import models

router = APIRouter()

BKDS_APP_URL    = os.environ.get("BKDS_APP_URL",    "https://bkds.rehapp.com.tr")
BKDS_SSO_SECRET = os.environ.get("BKDS_SSO_SECRET", "")


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _make_jwt(payload: dict, secret: str) -> str:
    header  = _b64url(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    body    = _b64url(json.dumps(payload).encode())
    data    = f"{header}.{body}"
    sig     = hashlib.sha256((secret + data).encode("utf-8")).digest()
    return f"{data}.{_b64url(sig)}"


@router.get("/sso-url")
async def get_sso_url(kurum: models.Kurum = Depends(get_current_kurum)):
    if not BKDS_SSO_SECRET:
        raise HTTPException(status_code=500, detail="BKDS_SSO_SECRET tanımlı değil")

    if not kurum.bkds_email or not kurum.bkds_password:
        raise HTTPException(
            status_code=422,
            detail="BKDS giriş bilgileri tanımlı değil. Yönetim → BKDS bölümünden girin.",
        )

    payload = {
        "org_slug":     str(kurum.id),
        "meb_username": kurum.bkds_email,
        "meb_password": kurum.bkds_password,
        "role":         "admin",
        "exp":          int(time.time()) + 600,
    }
    token        = _make_jwt(payload, BKDS_SSO_SECRET)
    redirect_url = f"{BKDS_APP_URL}/api/sso?token={token}"

    return {"redirect_url": redirect_url}
