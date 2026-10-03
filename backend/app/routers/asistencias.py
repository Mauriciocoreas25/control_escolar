from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.models.asistencia import Asistencia
from app.schemas.schemas import AsistenciaCreate, AsistenciaResponse

router = APIRouter(prefix="/asistencias", tags=["Asistencias"])

@router.get("/", response_model=List[AsistenciaResponse])
def listar_asistencias(db: Session = Depends(get_db)):
    return db.query(Asistencia).all()

@router.post("/", response_model=AsistenciaResponse)
def registrar_asistencia(asistencia_data: AsistenciaCreate, db: Session = Depends(get_db)):
    nuevo = Asistencia(**asistencia_data.dict())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo
@router.patch("/{asistencia_id}", response_model=AsistenciaResponse)
def actualizar_asistencia(asistencia_id: int, asistencia_data: AsistenciaCreate, db: Session = Depends(get_db)):
    db_asistencia = db.query(Asistencia).filter(Asistencia.id == asistencia_id).first()
    if not db_asistencia:
        raise HTTPException(status_code=404, detail="Registro de asistencia no encontrado")
    
    for key, value in asistencia_data.dict().items():
        setattr(db_asistencia, key, value)
    
    db.commit()
    db.refresh(db_asistencia)
    return db_asistencia