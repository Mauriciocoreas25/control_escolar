from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.models.asignatura import Asignatura
from app.schemas.schemas import AsignaturaCreate, AsignaturaResponse

router = APIRouter(prefix="/asignaturas", tags=["Asignaturas"])

@router.get("/", response_model=List[AsignaturaResponse])
def listar_asignaturas(db: Session = Depends(get_db)):
    return db.query(Asignatura).all()

@router.post("/", response_model=AsignaturaResponse)
def crear_asignatura(asignatura_data: AsignaturaCreate, db: Session = Depends(get_db)):
    db_asignatura = db.query(Asignatura).filter(Asignatura.codigo == asignatura_data.codigo).first()
    if db_asignatura:
        raise HTTPException(status_code=400, detail="El codigo de asignatura ya esta registrado")
    nuevo = Asignatura(**asignatura_data.dict())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo

@router.patch("/{asignatura_id}", response_model=AsignaturaResponse)
def actualizar_asignatura(asignatura_id: int, asignatura_data: AsignaturaCreate, db: Session = Depends(get_db)):
    db_asignatura = db.query(Asignatura).filter(Asignatura.id == asignatura_id).first()
    if not db_asignatura:
        raise HTTPException(status_code=404, detail="Asignatura no encontrada")
    
    for key, value in asignatura_data.dict().items():
        setattr(db_asignatura, key, value)
    
    db.commit()
    db.refresh(db_asignatura)
    return db_asignatura

@router.delete("/{asignatura_id}")
def eliminar_asignatura(asignatura_id: int, db: Session = Depends(get_db)):
    db_asignatura = db.query(Asignatura).filter(Asignatura.id == asignatura_id).first()
    if not db_asignatura:
        raise HTTPException(status_code=404, detail="Asignatura no encontrada")
    
    db.delete(db_asignatura)
    db.commit()
    return {"mensaje": "Asignatura eliminada correctamente"}