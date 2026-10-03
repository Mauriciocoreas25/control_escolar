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

@router.delete("/{anio_id}")
def eliminar_anio(anio_id: int, db: Session = Depends(get_db)):
    db_anio = db.query(AnioLectivo).filter(AnioLectivo.id == anio_id).first()
    if not db_anio:
        raise HTTPException(status_code=404, detail="Año lectivo no encontrado")
    db.delete(db_anio)
    db.commit()
    return {"mensaje": "Año lectivo eliminado correctamente"}