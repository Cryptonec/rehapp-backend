from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from db import get_db
import models, schemas
from auth import get_current_kurum

router = APIRouter(prefix="/diagnoses", tags=["diagnoses"])


@router.get("", response_model=list[schemas.DiagnosisOut])
def list_diagnoses(
    kurum: models.Kurum = Depends(get_current_kurum),
    db: Session = Depends(get_db),
):
    return db.query(models.Diagnosis).filter(models.Diagnosis.kurum_id == kurum.id).all()


@router.post("", response_model=schemas.DiagnosisOut, status_code=201)
def create_diagnosis(
    body: schemas.DiagnosisCreate,
    kurum: models.Kurum = Depends(get_current_kurum),
    db: Session = Depends(get_db),
):
    d = models.Diagnosis(kurum_id=kurum.id, name=body.name)
    db.add(d)
    db.commit()
    db.refresh(d)
    return d


@router.delete("/{diagnosis_id}", status_code=204)
def delete_diagnosis(
    diagnosis_id: int,
    kurum: models.Kurum = Depends(get_current_kurum),
    db: Session = Depends(get_db),
):
    d = db.query(models.Diagnosis).filter(
        models.Diagnosis.id == diagnosis_id,
        models.Diagnosis.kurum_id == kurum.id,
    ).first()
    if not d:
        raise HTTPException(status_code=404, detail="Tanı bulunamadı")
    db.delete(d)
    db.commit()
