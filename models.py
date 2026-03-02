from sqlalchemy import (
    Column, Integer, String, Boolean, Date, DateTime, Text, ForeignKey, Table
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db import Base


# ── Many-to-many ara tabloları ─────────────────────────────────────────────

student_diagnoses = Table(
    "student_diagnoses",
    Base.metadata,
    Column("student_id",   Integer, ForeignKey("students.id",   ondelete="CASCADE"), primary_key=True),
    Column("diagnosis_id", Integer, ForeignKey("diagnoses.id",  ondelete="CASCADE"), primary_key=True),
)

student_modules = Table(
    "student_modules",
    Base.metadata,
    Column("student_id", Integer, ForeignKey("students.id",  ondelete="CASCADE"), primary_key=True),
    Column("module_id",  Integer, ForeignKey("modules.id",   ondelete="CASCADE"), primary_key=True),
)


# ── Kurumlar ───────────────────────────────────────────────────────────────

class Kurum(Base):
    __tablename__ = "kurumlar"

    id              = Column(Integer, primary_key=True, index=True)
    ad              = Column(String(200), nullable=False)
    email           = Column(String(200), unique=True, nullable=False, index=True)
    hashed_password = Column(String(256), nullable=False)
    approved        = Column(Boolean, default=True)
    created_at      = Column(DateTime(timezone=True), server_default=func.now())

    students      = relationship("Student",    back_populates="kurum", cascade="all, delete-orphan")
    diagnoses     = relationship("Diagnosis",  back_populates="kurum", cascade="all, delete-orphan")
    modules       = relationship("Module",     back_populates="kurum", cascade="all, delete-orphan")
    saved_groups  = relationship("SavedGroup", back_populates="kurum", cascade="all, delete-orphan")


# ── Öğrenciler ─────────────────────────────────────────────────────────────

class Student(Base):
    __tablename__ = "students"

    id          = Column(Integer, primary_key=True, index=True)
    kurum_id    = Column(Integer, ForeignKey("kurumlar.id", ondelete="CASCADE"), nullable=False)
    name        = Column(String(200), nullable=False)
    dob         = Column(Date, nullable=True)
    rapor_bitis = Column(Date, nullable=True)

    kurum      = relationship("Kurum", back_populates="students")
    diagnoses  = relationship("Diagnosis", secondary=student_diagnoses, back_populates="students")
    modules    = relationship("Module",    secondary=student_modules,   back_populates="students")


# ── Tanılar ────────────────────────────────────────────────────────────────

class Diagnosis(Base):
    __tablename__ = "diagnoses"

    id       = Column(Integer, primary_key=True, index=True)
    kurum_id = Column(Integer, ForeignKey("kurumlar.id", ondelete="CASCADE"), nullable=False)
    name     = Column(String(200), nullable=False)

    kurum    = relationship("Kurum",    back_populates="diagnoses")
    students = relationship("Student",  secondary=student_diagnoses, back_populates="diagnoses")


# ── Modüller ───────────────────────────────────────────────────────────────

class Module(Base):
    __tablename__ = "modules"

    id       = Column(Integer, primary_key=True, index=True)
    kurum_id = Column(Integer, ForeignKey("kurumlar.id", ondelete="CASCADE"), nullable=False)
    name     = Column(String(200), nullable=False)

    kurum    = relationship("Kurum",   back_populates="modules")
    students = relationship("Student", secondary=student_modules, back_populates="modules")


# ── Kaydedilen Gruplar ────────────────────────────────────────────────────

class SavedGroup(Base):
    __tablename__ = "saved_groups"

    id         = Column(Integer, primary_key=True, index=True)
    kurum_id   = Column(Integer, ForeignKey("kurumlar.id", ondelete="CASCADE"), nullable=False)
    ogrenciler = Column(Text, nullable=False)        # "Ali | Ayşe | …"
    moduller   = Column(Text, nullable=False)        # "DİL / …"
    saat       = Column(String(50),  nullable=True)
    notlar     = Column(Text,        nullable=True)
    liste_adi  = Column(String(200), nullable=False, default="")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    kurum = relationship("Kurum", back_populates="saved_groups")
