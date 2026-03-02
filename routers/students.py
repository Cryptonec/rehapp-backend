from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from db import get_db
import models, schemas
from auth import get_current_kurum

router = APIRouter(prefix="/students", tags=["students"])


def _get_student_or_404(student_id: int, kurum: models.Kurum, db: Session):
    s = (
        db.query(models.Student)
        .filter(models.Student.id == student_id, models.Student.kurum_id == kurum.id)
        .first()
    )
    if not s:
        raise HTTPException(status_code=404, detail="Öğrenci bulunamadı")
    return s


@router.get("", response_model=list[schemas.StudentOut])
def list_students(
    kurum: models.Kurum = Depends(get_current_kurum),
    db: Session = Depends(get_db),
):
    return db.query(models.Student).filter(models.Student.kurum_id == kurum.id).all()


@router.post("", response_model=schemas.StudentOut, status_code=201)
def create_student(
    body: schemas.StudentCreate,
    kurum: models.Kurum = Depends(get_current_kurum),
    db: Session = Depends(get_db),
):
    student = models.Student(
        kurum_id=kurum.id,
        name=body.name,
        dob=body.dob,
        rapor_bitis=body.rapor_bitis,
    )
    # Tanı ve modül ilişkileri
    if body.diagnosis_ids:
        diags = db.query(models.Diagnosis).filter(
            models.Diagnosis.id.in_(body.diagnosis_ids),
            models.Diagnosis.kurum_id == kurum.id,
        ).all()
        student.diagnoses = diags
    if body.module_ids:
        mods = db.query(models.Module).filter(
            models.Module.id.in_(body.module_ids),
            models.Module.kurum_id == kurum.id,
        ).all()
        student.modules = mods

    db.add(student)
    db.commit()
    db.refresh(student)
    return student


@router.put("/{student_id}", response_model=schemas.StudentOut)
def update_student(
    student_id: int,
    body: schemas.StudentUpdate,
    kurum: models.Kurum = Depends(get_current_kurum),
    db: Session = Depends(get_db),
):
    student = _get_student_or_404(student_id, kurum, db)

    if body.name is not None:
        student.name = body.name
    if body.dob is not None:
        student.dob = body.dob
    if body.rapor_bitis is not None:
        student.rapor_bitis = body.rapor_bitis
    if body.diagnosis_ids is not None:
        student.diagnoses = db.query(models.Diagnosis).filter(
            models.Diagnosis.id.in_(body.diagnosis_ids),
            models.Diagnosis.kurum_id == kurum.id,
        ).all()
    if body.module_ids is not None:
        student.modules = db.query(models.Module).filter(
            models.Module.id.in_(body.module_ids),
            models.Module.kurum_id == kurum.id,
        ).all()

    db.commit()
    db.refresh(student)
    return student


@router.delete("/{student_id}", status_code=204)
def delete_student(
    student_id: int,
    kurum: models.Kurum = Depends(get_current_kurum),
    db: Session = Depends(get_db),
):
    student = _get_student_or_404(student_id, kurum, db)
    db.delete(student)
    db.commit()
