from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.models.anio_lectivo import AnioLectivo
from app.schemas.schemas import AnioLectivoCreate, AnioLectivoResponse

router = APIRouter(prefix="/anios-lectivos", tags=["Años Lectivos"])

@router.get("/", response_model=List[AnioLectivoResponse])
def listar_anios(db: Session = Depends(get_db)):
    return db.query(AnioLectivo).all()

@router.post("/", response_model=AnioLectivoResponse)
def crear_anio(anio_data: AnioLectivoCreate, db: Session = Depends(get_db)):
    db_anio = db.query(AnioLectivo).filter(AnioLectivo.anio == anio_data.anio).first()
    if db_anio:
        raise HTTPException(status_code=400, detail="Este año lectivo ya esta registrado")
    nuevo = AnioLectivo(**anio_data.dict())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo

@router.patch("/{anio_id}/estado")
def actualizar_estado_anio(anio_id: int, payload: dict, db: Session = Depends(get_db)):
    db_anio = db.query(AnioLectivo).filter(AnioLectivo.id == anio_id).first()
    if not db_anio:
        raise HTTPException(status_code=404, detail="Año lectivo no encontrado")
    nuevo_estado = payload.get("estado", "Activo")
    db_anio.estado = nuevo_estado
    db.commit()
    db.refresh(db_anio)
    return {"mensaje": f"Estado del ciclo actualizado a {nuevo_estado}", "id": db_anio.id, "estado": db_anio.estado}

@router.delete("/{anio_id}")
def eliminar_anio(anio_id: int, db: Session = Depends(get_db)):
    from app.models.periodo import PeriodoEscolar
    db_anio = db.query(AnioLectivo).filter(AnioLectivo.id == anio_id).first()
    if not db_anio:
        raise HTTPException(status_code=404, detail="Año lectivo no encontrado")
    
    # Validar períodos asociados
    periodos = db.query(PeriodoEscolar).filter(PeriodoEscolar.anio_lectivo_id == anio_id).all()
    if periodos:
        from app.models.calificacion import Calificacion
        periodo_ids = [p.id for p in periodos]
        califs = db.query(Calificacion).filter(Calificacion.periodo_id.in_(periodo_ids)).count()
        if califs > 0:
            raise HTTPException(
                status_code=400,
                detail="No se puede eliminar este ciclo escolar porque contiene calificaciones oficiales registradas. Puede cambiar su estado a 'Cerrado / Finalizado'."
            )
        for p in periodos:
            db.delete(p)
    
    db.delete(db_anio)
    db.commit()
    return {"mensaje": "Año lectivo eliminado correctamente"}
