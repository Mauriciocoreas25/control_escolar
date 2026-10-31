from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.models.actividad_evaluativa import ActividadEvaluativa
from app.schemas.schemas import ActividadEvaluativaCreate, ActividadEvaluativaResponse

router = APIRouter(prefix="/actividades", tags=["Actividades Evaluativas"])

@router.get("/", response_model=List[ActividadEvaluativaResponse])
def listar_actividades(
    asignatura_id: Optional[int] = Query(None),
    periodo_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(ActividadEvaluativa)
    if asignatura_id is not None:
        query = query.filter(ActividadEvaluativa.asignatura_id == asignatura_id)
    if periodo_id is not None:
        query = query.filter(ActividadEvaluativa.periodo_id == periodo_id)
    
    actividades = query.order_by(ActividadEvaluativa.id.asc()).all()
    return actividades

@router.post("/", response_model=ActividadEvaluativaResponse)
def crear_actividad(actividad_data: ActividadEvaluativaCreate, db: Session = Depends(get_db)):
    nueva = ActividadEvaluativa(**actividad_data.dict())
    db.add(nueva)
    db.commit()
    db.refresh(nueva)
    return nueva

@router.delete("/{actividad_id}")
def eliminar_actividad(actividad_id: int, db: Session = Depends(get_db)):
    act = db.query(ActividadEvaluativa).filter(ActividadEvaluativa.id == actividad_id).first()
    if not act:
        raise HTTPException(status_code=404, detail="Actividad evaluativa no encontrada")
    db.delete(act)
    db.commit()
    return {"message": "Actividad eliminada correctamente", "id": actividad_id}
