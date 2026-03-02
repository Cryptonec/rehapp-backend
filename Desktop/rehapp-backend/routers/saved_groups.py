from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from db import get_db
import models, schemas
from auth import get_current_kurum

router = APIRouter(prefix="/saved-groups", tags=["saved-groups"])


@router.get("", response_model=list[schemas.SavedGroupOut])
def list_saved_groups(
    kurum: models.Kurum = Depends(get_current_kurum),
    db: Session = Depends(get_db),
):
    return (
        db.query(models.SavedGroup)
        .filter(models.SavedGroup.kurum_id == kurum.id)
        .order_by(models.SavedGroup.created_at.desc())
        .all()
    )


@router.post("", response_model=schemas.SavedGroupOut, status_code=201)
def create_saved_group(
    body: schemas.SavedGroupCreate,
    kurum: models.Kurum = Depends(get_current_kurum),
    db: Session = Depends(get_db),
):
    sg = models.SavedGroup(
        kurum_id=kurum.id,
        ogrenciler=body.ogrenciler,
        moduller=body.moduller,
        saat=body.saat,
        notlar=body.notlar,
        liste_adi=body.liste_adi,
    )
    db.add(sg)
    db.commit()
    db.refresh(sg)
    return sg


@router.patch("/{group_id}", response_model=schemas.SavedGroupOut)
def patch_saved_group(
    group_id: int,
    body: schemas.SavedGroupPatch,
    kurum: models.Kurum = Depends(get_current_kurum),
    db: Session = Depends(get_db),
):
    sg = db.query(models.SavedGroup).filter(
        models.SavedGroup.id == group_id,
        models.SavedGroup.kurum_id == kurum.id,
    ).first()
    if not sg:
        raise HTTPException(status_code=404, detail="Kayıtlı grup bulunamadı")
    if body.liste_adi is not None:
        sg.liste_adi = body.liste_adi
    if body.notlar is not None:
        sg.notlar = body.notlar
    db.commit()
    db.refresh(sg)
    return sg


@router.delete("/{group_id}", status_code=204)
def delete_saved_group(
    group_id: int,
    kurum: models.Kurum = Depends(get_current_kurum),
    db: Session = Depends(get_db),
):
    sg = db.query(models.SavedGroup).filter(
        models.SavedGroup.id == group_id,
        models.SavedGroup.kurum_id == kurum.id,
    ).first()
    if not sg:
        raise HTTPException(status_code=404, detail="Kayıtlı grup bulunamadı")
    db.delete(sg)
    db.commit()
