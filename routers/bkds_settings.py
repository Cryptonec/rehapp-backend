from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from db import get_db
from auth import get_current_kurum
from models import Kurum
from schemas import BkdsCredentialsUpdate, BkdsCredentialsOut

router = APIRouter()


@router.get("/bkds-credentials", response_model=BkdsCredentialsOut)
def get_bkds_credentials(kurum: Kurum = Depends(get_current_kurum)):
    return BkdsCredentialsOut(
        bkds_email=kurum.bkds_email,
        bkds_configured=bool(kurum.bkds_email and kurum.bkds_password),
    )


@router.patch("/bkds-credentials", response_model=BkdsCredentialsOut)
def update_bkds_credentials(
    body: BkdsCredentialsUpdate,
    kurum: Kurum = Depends(get_current_kurum),
    db: Session = Depends(get_db),
):
    if body.bkds_email is not None:
        kurum.bkds_email = body.bkds_email.strip() or None
    if body.bkds_password is not None:
        kurum.bkds_password = body.bkds_password or None
    db.commit()
    db.refresh(kurum)
    return BkdsCredentialsOut(
        bkds_email=kurum.bkds_email,
        bkds_configured=bool(kurum.bkds_email and kurum.bkds_password),
    )
