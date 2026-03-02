from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from db import get_db
import models, schemas
from auth import get_current_kurum

router = APIRouter(prefix="/modules", tags=["modules"])


@router.get("", response_model=list[schemas.ModuleOut])
def list_modules(
    kurum: models.Kurum = Depends(get_current_kurum),
    db: Session = Depends(get_db),
):
    return db.query(models.Module).filter(models.Module.kurum_id == kurum.id).all()


@router.post("", response_model=schemas.ModuleOut, status_code=201)
def create_module(
    body: schemas.ModuleCreate,
    kurum: models.Kurum = Depends(get_current_kurum),
    db: Session = Depends(get_db),
):
    m = models.Module(kurum_id=kurum.id, name=body.name)
    db.add(m)
    db.commit()
    db.refresh(m)
    return m


@router.delete("/{module_id}", status_code=204)
def delete_module(
    module_id: int,
    kurum: models.Kurum = Depends(get_current_kurum),
    db: Session = Depends(get_db),
):
    m = db.query(models.Module).filter(
        models.Module.id == module_id,
        models.Module.kurum_id == kurum.id,
    ).first()
    if not m:
        raise HTTPException(status_code=404, detail="Modül bulunamadı")
    db.delete(m)
    db.commit()
