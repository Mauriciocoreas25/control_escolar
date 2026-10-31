from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.models.calificacion import Calificacion
from app.schemas.schemas import CalificacionCreate, CalificacionResponse

router = APIRouter(prefix="/calificaciones", tags=["Calificaciones"])

@router.get("/", response_model=List[CalificacionResponse])
def listar_calificaciones(
    asignatura_id: Optional[int] = Query(None),
    periodo_id: Optional[int] = Query(None),
    estudiante_id: Optional[int] = Query(None),
    tipo_evaluacion: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(Calificacion)
    if asignatura_id is not None:
        query = query.filter(Calificacion.asignatura_id == asignatura_id)
    if periodo_id is not None:
        query = query.filter(Calificacion.periodo_id == periodo_id)
    if estudiante_id is not None:
        query = query.filter(Calificacion.estudiante_id == estudiante_id)
    if tipo_evaluacion:
        query = query.filter(Calificacion.tipo_evaluacion == tipo_evaluacion)
    return query.all()

@router.post("/", response_model=CalificacionResponse)
def registrar_calificacion(calificacion_data: CalificacionCreate, db: Session = Depends(get_db)):
    # Buscar si ya existe una calificación para el estudiante, materia, periodo y actividad
    query = db.query(Calificacion).filter(
        Calificacion.estudiante_id == calificacion_data.estudiante_id,
        Calificacion.asignatura_id == calificacion_data.asignatura_id,
        Calificacion.periodo_id == calificacion_data.periodo_id
    )
    if calificacion_data.tipo_evaluacion:
        query = query.filter(Calificacion.tipo_evaluacion == calificacion_data.tipo_evaluacion)

    existente = query.first()
    if existente:
        existente.nota = calificacion_data.nota
        if calificacion_data.tipo_evaluacion:
            existente.tipo_evaluacion = calificacion_data.tipo_evaluacion
        db.commit()
        db.refresh(existente)
        return existente

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