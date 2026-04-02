"""
rehapp-backend/routers/bkds.py
SSO bridge: Rehapp → bkds-takip
"""
import os
import httpx
from fastapi import APIRouter, Depends, HTTPException
from auth import get_current_kurum
import models

router = APIRouter()

BKDS_APP_URL   = os.environ.get("BKDS_APP_URL", "https://bkds.rehapp.com.tr")
BKDS_SSO_SECRET = os.environ.get("BKDS_SSO_SECRET", "")


@router.get("/sso-url")
async def get_sso_url(kurum: models.Kurum = Depends(get_current_kurum)):
    """
    Streamlit bu endpoint'i çağırır.
    bkds-takip'ten tek kullanımlık SSO URL alır, döndürür.
    """
    if not BKDS_SSO_SECRET:
        raise HTTPException(status_code=500, detail="BKDS_SSO_SECRET tanımlı değil")

    org_slug = str(kurum.id)

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                f"{BKDS_APP_URL}/api/sso",
                json={
                    "org_slug": org_slug,
                    "secret":   BKDS_SSO_SECRET,
                    "kurum_ad": kurum.ad,
                },
            )
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"bkds-takip hatası: {e.response.text}")
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"bkds-takip erişilemiyor: {str(e)}")

    redirect_url = data.get("redirect_url")
    if not redirect_url:
        raise HTTPException(status_code=502, detail="bkds-takip geçersiz yanıt döndürdü")

    return {"redirect_url": redirect_url}
