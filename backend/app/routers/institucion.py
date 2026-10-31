from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from app.core.database import get_db
from app.models.institucion import Institucion

router = APIRouter(prefix="/institucion", tags=["Institucion"])

class InstitucionSchema(BaseModel):
    id: Optional[int] = 1
    nombre: str
    codigo_mined: str
    anio_lectivo: str
    regimen: str
    director_nombre: str
    telefono: str
    direccion: str

    class Config:
        from_attributes = True

@router.get("/", response_model=InstitucionSchema)
def obtener_institucion(db: Session = Depends(get_db)):
    inst = db.query(Institucion).filter(Institucion.id == 1).first()
    if not inst:
        inst = Institucion(
            id=1,
            nombre="Complejo Educativo Santa Sofía",
            codigo_mined="10234",
            anio_lectivo="2026",
            regimen="Régimen Trimestral",
            director_nombre="Lic. Roberto Antonio Mendoza",
            telefono="2222-3333",
            direccion="Barrio El Centro, San Salvador, El Salvador"
        )
        db.add(inst)
        db.commit()
        db.refresh(inst)
    return inst

@router.put("/", response_model=InstitucionSchema)
def actualizar_institucion(data: InstitucionSchema, db: Session = Depends(get_db)):
    inst = db.query(Institucion).filter(Institucion.id == 1).first()
    if not inst:
        inst = Institucion(id=1, **data.dict(exclude={"id"}))
        db.add(inst)
    else:
        for k, v in data.dict(exclude={"id"}).items():
            setattr(inst, k, v)
    db.commit()
    db.refresh(inst)
    return inst
