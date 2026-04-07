"""
rehapp-backend/routers/bkds.py
Rehapp → bkds-takip SSO bridge
MEB BKDS kimlik bilgilerini JWT payload'una ekler.
"""
import os
import time
import hashlib
import base64
import json
from fastapi import APIRouter, Depends
import models
from auth import get_current_kurum

router = APIRouter()

BKDS_APP_URL    = os.environ.get("BKDS_APP_URL", "https://bkds-takip.onrender.com").rstrip("/")
BKDS_SSO_SECRET = os.environ.get("BKDS_SSO_SECRET", "")


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _make_sso_jwt(kurum: models.Kurum) -> str:
    header  = _b64url(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    payload = _b64url(json.dumps({
        "sub":          str(kurum.id),
        "email":        kurum.email,
        "name":         kurum.ad,
        "role":         "admin",
        "org_id":       str(kurum.id),
        "org_slug":     str(kurum.id),
        "meb_username": kurum.bkds_email    or "",
        "meb_password": kurum.bkds_password or "",
        "iat":          int(time.time()),
        "exp":          int(time.time()) + 600,
    }, ensure_ascii=False).encode())

    data = f"{header}.{payload}"
    sig  = _b64url(hashlib.sha256((BKDS_SSO_SECRET + data).encode()).digest())
    return f"{data}.{sig}"


@router.get("/sso-url")
def get_sso_url(kurum: models.Kurum = Depends(get_current_kurum)):
    if not BKDS_SSO_SECRET:
        return {"error": "BKDS_SSO_SECRET tanimli degil", "redirect_url": None}

    token        = _make_sso_jwt(kurum)
    redirect_url = f"{BKDS_APP_URL}/api/sso?token={token}"
    return {"redirect_url": redirect_url}
