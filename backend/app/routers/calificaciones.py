from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.models.calificacion import Calificacion
from app.schemas.schemas import CalificacionCreate, CalificacionResponse

router = APIRouter(prefix="/calificaciones", tags=["Calificaciones"])

@router.get("/", response_model=List[CalificacionResponse])
def listar_calificaciones(db: Session = Depends(get_db)):
    return db.query(Calificacion).all()

@router.post("/", response_model=CalificacionResponse)
def registrar_calificacion(calificacion_data: CalificacionCreate, db: Session = Depends(get_db)):
    nuevo = Calificacion(**calificacion_data.dict())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo

@router.patch("/{calificacion_id}", response_model=CalificacionResponse)
def actualizar_calificacion(calificacion_id: int, calificacion_data: CalificacionCreate, db: Session = Depends(get_db)):
    db_calificacion = db.query(Calificacion).filter(Calificacion.id == calificacion_id).first()
    if not db_calificacion:
        raise HTTPException(status_code=404, detail="Calificación no encontrada")
    
    for key, value in calificacion_data.dict().items():
        setattr(db_calificacion, key, value)
    
    db.commit()
    db.refresh(db_calificacion)
    return db_calificacion