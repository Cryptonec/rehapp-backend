from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import os, logging

from db import get_db
import models, schemas
from auth import hash_password, verify_password, create_access_token, get_current_kurum

logger = logging.getLogger(__name__)
router = APIRouter(tags=["auth"])
ADMIN_EMAIL = "necmettinakgun@gmail.com"


def _mail(to: list, subject: str, html: str):
    api_key = os.environ.get("RESEND_API_KEY", "")
    if not api_key:
        logger.warning("RESEND_API_KEY yok — mail atlandı.")
        return
    try:
        import resend
        resend.api_key = api_key
        resend.Emails.send({
            "from": "Rehapp <noreply@rehapp.com.tr>",
            "to": to,
            "subject": subject,
            "html": html,
        })
        logger.info(f"Mail gönderildi: {to}")
    except Exception as e:
        logger.error(f"Resend hata: {e}")


@router.post("/register", response_model=schemas.TokenResponse)
def register(body: schemas.KurumRegister, db: Session = Depends(get_db)):
    if db.query(models.Kurum).filter(models.Kurum.email == body.email).first():
        raise HTTPException(status_code=400, detail="Bu e-posta zaten kayıtlı")

    kurum = models.Kurum(
        ad=body.ad,
        email=body.email,
        hashed_password=hash_password(body.password),
        approved=False,
    )
    db.add(kurum)
    db.commit()
    db.refresh(kurum)

    _mail(
        to=[ADMIN_EMAIL],
        subject=f"[Rehapp] Yeni Kayıt: {body.ad}",
        html=f"<p><strong>Kurum:</strong> {body.ad}<br><strong>Mail:</strong> {body.email}</p>",
    )
    _mail(
        to=[body.email],
        subject="Rehapp — Kaydınız Alındı",
        html=f"<p>Merhaba {body.ad}, kaydınız alındı. Onay sonrası giriş yapabilirsiniz.</p>",
    )

    token = create_access_token({"sub": str(kurum.id)})
    return schemas.TokenResponse(
        access_token=token,
        token_type="bearer",
        kurum_id=kurum.id,
        kurum_ad=kurum.ad,
    )


@router.post("/login", response_model=schemas.TokenResponse)
def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    kurum = db.query(models.Kurum).filter(models.Kurum.email == form.username).first()
    if not kurum or not verify_password(form.password, kurum.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-posta veya şifre yanlış",
        )
    if not kurum.approved:
        raise HTTPException(status_code=403, detail="Hesabınız henüz onaylanmamış")

    token = create_access_token({"sub": str(kurum.id)})
    return schemas.TokenResponse(
        access_token=token,
        token_type="bearer",
        kurum_id=kurum.id,
        kurum_ad=kurum.ad,
    )


@router.get("/me", response_model=schemas.MeResponse)
def me(kurum: models.Kurum = Depends(get_current_kurum)):
    return schemas.MeResponse(kurum_id=kurum.id, kurum_ad=kurum.ad, email=kurum.email)


def _require_admin(kurum: models.Kurum):
    if kurum.email != ADMIN_EMAIL:
        raise HTTPException(status_code=403, detail="Yetkisiz erişim")


@router.get("/admin/kurumlar")
def admin_list(
    db: Session = Depends(get_db),
    kurum: models.Kurum = Depends(get_current_kurum),
):
    _require_admin(kurum)
    return [
        {
            "id": k.id,
            "ad": k.ad,
            "email": k.email,
            "approved": k.approved,
            "created_at": k.created_at.isoformat() if k.created_at else None,
            "son_giris": k.son_giris.isoformat() if getattr(k, "son_giris", None) else None,
        }
        for k in db.query(models.Kurum).order_by(models.Kurum.id).all()
    ]


@router.post("/admin/kurumlar/{kid}/onayla")
def admin_onayla(
    kid: int,
    db: Session = Depends(get_db),
    kurum: models.Kurum = Depends(get_current_kurum),
):
    _require_admin(kurum)
    k = db.query(models.Kurum).filter(models.Kurum.id == kid).first()
    if not k:
        raise HTTPException(status_code=404, detail="Kurum bulunamadı")
    k.approved = True
    db.commit()
    _mail(
        to=[k.email],
        subject="Rehapp Hesabınız Onaylandı",
        html=f"<p>Merhaba {k.ad}, hesabınız onaylandı! <a href='https://rehapp.com.tr'>Giriş yapın</a></p>",
    )
    return {"ok": True}


@router.post("/admin/kurumlar/{kid}/pasif")
def admin_pasif(
    kid: int,
    db: Session = Depends(get_db),
    kurum: models.Kurum = Depends(get_current_kurum),
):
    _require_admin(kurum)
    k = db.query(models.Kurum).filter(models.Kurum.id == kid).first()
    if not k:
        raise HTTPException(status_code=404, detail="Kurum bulunamadı")
    k.approved = False
    db.commit()
    return {"ok": True}