from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.models.periodo import PeriodoEscolar
from app.schemas.schemas import PeriodoCreate, PeriodoResponse

router = APIRouter(prefix="/periodos", tags=["Periodos Escolares"])

@router.get("/", response_model=List[PeriodoResponse])
def listar_periodos(db: Session = Depends(get_db)):
    return db.query(PeriodoEscolar).all()

@router.post("/", response_model=PeriodoResponse)
def crear_periodo(periodo_data: PeriodoCreate, db: Session = Depends(get_db)):
    nuevo = PeriodoEscolar(**periodo_data.dict())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo

@router.patch("/{periodo_id}", response_model=PeriodoResponse)
def cambiar_estado_periodo(periodo_id: int, periodo_data: PeriodoCreate, db: Session = Depends(get_db)):
    db_periodo = db.query(PeriodoEscolar).filter(PeriodoEscolar.id == periodo_id).first()
    if not db_periodo:
        raise HTTPException(status_code=404, detail="Periodo no encontrado")
    
    for key, value in periodo_data.dict().items():
        setattr(db_periodo, key, value)
    
    db.commit()
    db.refresh(db_periodo)
    return db_periodo

@router.delete("/{periodo_id}")
def eliminar_periodo(periodo_id: int, db: Session = Depends(get_db)):
    db_periodo = db.query(PeriodoEscolar).filter(PeriodoEscolar.id == periodo_id).first()
    if not db_periodo:
        raise HTTPException(status_code=404, detail="Periodo no encontrado")
    db.delete(db_periodo)
    db.commit()
    return {"mensaje": "Periodo eliminado correctamente"}