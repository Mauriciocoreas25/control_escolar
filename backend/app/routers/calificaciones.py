from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from app.core.database import get_db
from app.models.calificacion import Calificacion
from app.schemas.schemas import CalificacionCreate, CalificacionResponse

router = APIRouter(prefix="/calificaciones", tags=["Calificaciones"])

def _filter_by_tipo(query, tipo_evaluacion: str):
    t_low = tipo_evaluacion.lower()
    if "examen" in t_low or "parcial" in t_low or "actividad 1" in t_low:
        return query.filter(
            or_(
                Calificacion.tipo_evaluacion == tipo_evaluacion,
                Calificacion.tipo_evaluacion.ilike("%examen%"),
                Calificacion.tipo_evaluacion.ilike("%parcial%"),
                Calificacion.tipo_evaluacion.ilike("%actividad 1%")
            )
        )
    elif "tarea" in t_low or "guía" in t_low or "guia" in t_low or "actividad 2" in t_low:
        return query.filter(
            or_(
                Calificacion.tipo_evaluacion == tipo_evaluacion,
                Calificacion.tipo_evaluacion.ilike("%tarea%"),
                Calificacion.tipo_evaluacion.ilike("%gu_a%"),
                Calificacion.tipo_evaluacion.ilike("%actividad 2%")
            )
        )
    elif "proyecto" in t_low or "laboratorio" in t_low or "actividad 3" in t_low:
        return query.filter(
            or_(
                Calificacion.tipo_evaluacion == tipo_evaluacion,
                Calificacion.tipo_evaluacion.ilike("%proyecto%"),
                Calificacion.tipo_evaluacion.ilike("%laboratorio%"),
                Calificacion.tipo_evaluacion.ilike("%actividad 3%")
            )
        )
    return query.filter(Calificacion.tipo_evaluacion == tipo_evaluacion)

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
        query = _filter_by_tipo(query, tipo_evaluacion)
    return query.all()

def _canonical_tipo(tipo: Optional[str]) -> str:
    t = (tipo or "").lower()
    if "1" in t or "parcial" in t or "examen" in t:
        return "Actividad 1: Examen Parcial (35%)"
    elif "2" in t or "tarea" in t or "gu" in t:
        return "Actividad 2: Guías y Tareas (35%)"
    elif "3" in t or "proyecto" in t or "lab" in t:
        return "Actividad 3: Proyecto Aplicado (30%)"
    return "Actividad 1: Examen Parcial (35%)"

@router.post("/", response_model=CalificacionResponse)
def registrar_calificacion(calificacion_data: CalificacionCreate, db: Session = Depends(get_db)):
    if calificacion_data.nota < 0.0 or calificacion_data.nota > 10.0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La calificación debe estar comprendida estrictamente entre 0.0 y 10.0."
        )

    # Normalizar al nombre canónico oficial de la actividad
    can_tipo = _canonical_tipo(calificacion_data.tipo_evaluacion)
    calificacion_data.tipo_evaluacion = can_tipo

    # Buscar registros existentes para ese estudiante, materia, periodo y casilla
    query = db.query(Calificacion).filter(
        Calificacion.estudiante_id == calificacion_data.estudiante_id,
        Calificacion.asignatura_id == calificacion_data.asignatura_id,
        Calificacion.periodo_id == calificacion_data.periodo_id
    )
    query_tipo = _filter_by_tipo(query, can_tipo)
    matches = query_tipo.order_by(Calificacion.id.asc()).all()

    if matches:
        # Prevalece el más reciente
        existente = matches[-1]
        existente.nota = calificacion_data.nota
        existente.tipo_evaluacion = can_tipo
        # Eliminar cualquier duplicado previo de esta misma casilla
        for dup in matches[:-1]:
            db.delete(dup)
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
    if calificacion_data.nota < 0.0 or calificacion_data.nota > 10.0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La calificación debe estar comprendida estrictamente entre 0.0 y 10.0."
        )
    db_calificacion = db.query(Calificacion).filter(Calificacion.id == calificacion_id).first()
    if not db_calificacion:
        raise HTTPException(status_code=404, detail="Calificación no encontrada")
    
    for key, value in calificacion_data.dict().items():
        setattr(db_calificacion, key, value)
    
    db.commit()
    db.refresh(db_calificacion)
    return db_calificacion
