from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from db import get_db
import models, schemas
from auth import (
    hash_password, verify_password, create_access_token, get_current_kurum
)

router = APIRouter(tags=["auth"])


@router.post("/register", response_model=schemas.TokenResponse)
def register(body: schemas.KurumRegister, db: Session = Depends(get_db)):
    if db.query(models.Kurum).filter(models.Kurum.email == body.email).first():
        raise HTTPException(status_code=400, detail="Bu e-posta zaten kayıtlı")

    kurum = models.Kurum(
        ad=body.ad,
        email=body.email,
        hashed_password=hash_password(body.password),
    )
    db.add(kurum)
    db.commit()
    db.refresh(kurum)

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
