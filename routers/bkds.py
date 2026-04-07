"""
rehapp-backend/routers/bkds.py
Rehapp → bkds-takip SSO bridge
"""
import os
import httpx
from fastapi import APIRouter, Depends, HTTPException
import models
from auth import get_current_kurum

router = APIRouter()

BKDS_APP_URL    = os.environ.get("BKDS_APP_URL", "https://bkds-takip.onrender.com").rstrip("/")
BKDS_SSO_SECRET = os.environ.get("BKDS_SSO_SECRET", "")


@router.get("/sso-url")
def get_sso_url(kurum: models.Kurum = Depends(get_current_kurum)):
    """
    Streamlit bu endpoint'i çağırır.
    bkds-takip'e email+şifre+org_slug göndererek tek kullanımlık SSO URL alır.
    """
    if not BKDS_SSO_SECRET:
        raise HTTPException(status_code=500, detail="BKDS_SSO_SECRET tanımlı değil")

    if not kurum.bkds_email or not kurum.bkds_password:
        raise HTTPException(status_code=400, detail="BKDS kimlik bilgileri girilmemiş")

    try:
        resp = httpx.post(
            f"{BKDS_APP_URL}/api/sso/rehapp",
            json={
                "email":          kurum.bkds_email,
                "password":       kurum.bkds_password,
                "org_slug":       str(kurum.id),
                "rehapp_secret":  BKDS_SSO_SECRET,
            },
            timeout=15,
        )
        data = resp.json()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"bkds-takip bağlantı hatası: {exc}")

    if resp.status_code != 200:
        detail = data.get("error", "bilinmeyen hata")
        raise HTTPException(status_code=resp.status_code, detail=f"bkds-takip: {detail}")

    redirect_url = data.get("redirect_url")
    if not redirect_url:
        raise HTTPException(status_code=502, detail="bkds-takip redirect_url döndürmedi")

    return {"redirect_url": redirect_url}

