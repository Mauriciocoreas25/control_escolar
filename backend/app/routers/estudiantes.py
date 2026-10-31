from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.models.models import Estudiante
from app.schemas.schemas import EstudianteCreate, EstudianteResponse

router = APIRouter(prefix="/estudiantes", tags=["Estudiantes"])

@router.get("/", response_model=List[EstudianteResponse])
def listar_estudiantes(grado_seccion: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Estudiante)
    if grado_seccion:
        variante = grado_seccion.replace("º", "°") if "º" in grado_seccion else grado_seccion.replace("°", "º")
        query = query.filter(
            (Estudiante.grado_seccion == grado_seccion) |
            (Estudiante.grado_seccion == variante) |
            (Estudiante.grado_seccion.ilike(f"%{grado_seccion.strip()}%"))
        )
    return query.all()

@router.post("/", response_model=EstudianteResponse)
def crear_estudiante(estudiante: EstudianteCreate, db: Session = Depends(get_db)):
    db_estudiante = db.query(Estudiante).filter(Estudiante.nie == estudiante.nie).first()
    if db_estudiante:
        raise HTTPException(status_code=400, detail="El NIE ya esta registrado")
    nuevo = Estudiante(**estudiante.dict())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo

@router.patch("/{estudiante_id}", response_model=EstudianteResponse)
def actualizar_estudiante(estudiante_id: int, estudiante_data: EstudianteCreate, db: Session = Depends(get_db)):
    db_estudiante = db.query(Estudiante).filter(Estudiante.id == estudiante_id).first()
    if not db_estudiante:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")
    
    for key, value in estudiante_data.dict().items():
        setattr(db_estudiante, key, value)
    
    db.commit()
    db.refresh(db_estudiante)
    return db_estudiante

@router.delete("/{estudiante_id}")
def eliminar_estudiante(estudiante_id: int, db: Session = Depends(get_db)):
    db_estudiante = db.query(Estudiante).filter(Estudiante.id == estudiante_id).first()
    if not db_estudiante:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")
    
    db.delete(db_estudiante)
    db.commit()
    return {"mensaje": "Estudiante eliminado correctamente"}