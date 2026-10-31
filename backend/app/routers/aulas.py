from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.models.aula import Aula
from app.schemas.schemas import AulaCreate, AulaResponse

router = APIRouter(prefix="/aulas", tags=["Aulas"])

@router.get("/", response_model=List[AulaResponse])
def listar_aulas(tipo: Optional[str] = None, estado: Optional[bool] = None, db: Session = Depends(get_db)):
    query = db.query(Aula)
    if tipo:
        query = query.filter(Aula.tipo == tipo)
    if estado is not None:
        query = query.filter(Aula.estado == estado)
    return query.order_by(Aula.codigo.asc()).all()

@router.post("/", response_model=AulaResponse, status_code=status.HTTP_201_CREATED)
def crear_aula(aula_data: AulaCreate, db: Session = Depends(get_db)):
    existente = db.query(Aula).filter(Aula.codigo == aula_data.codigo.strip()).first()
    if existente:
        raise HTTPException(status_code=400, detail=f"El código de aula '{aula_data.codigo}' ya está registrado.")
    
    nuevo_aula = Aula(
        codigo=aula_data.codigo.strip().upper(),
        nombre=aula_data.nombre.strip(),
        tipo=aula_data.tipo,
        capacidad=aula_data.capacidad,
        ubicacion=aula_data.ubicacion.strip() if aula_data.ubicacion else None,
        estado=aula_data.estado
    )
    db.add(nuevo_aula)
    db.commit()
    db.refresh(nuevo_aula)
    return nuevo_aula

@router.patch("/{aula_id}", response_model=AulaResponse)
def actualizar_aula(aula_id: int, aula_data: AulaCreate, db: Session = Depends(get_db)):
    aula = db.query(Aula).filter(Aula.id == aula_id).first()
    if not aula:
        raise HTTPException(status_code=404, detail="Aula no encontrada")
    
    if aula_data.codigo.strip().upper() != aula.codigo:
        otro = db.query(Aula).filter(Aula.codigo == aula_data.codigo.strip().upper(), Aula.id != aula_id).first()
        if otro:
            raise HTTPException(status_code=400, detail=f"El código '{aula_data.codigo}' ya está en uso.")
        aula.codigo = aula_data.codigo.strip().upper()

    aula.nombre = aula_data.nombre.strip()
    aula.tipo = aula_data.tipo
    aula.capacidad = aula_data.capacidad
    aula.ubicacion = aula_data.ubicacion.strip() if aula_data.ubicacion else None
    if aula_data.estado is not None:
        aula.estado = aula_data.estado

    db.commit()
    db.refresh(aula)
    return aula

@router.delete("/{aula_id}")
def eliminar_aula(aula_id: int, db: Session = Depends(get_db)):
    aula = db.query(Aula).filter(Aula.id == aula_id).first()
    if not aula:
        raise HTTPException(status_code=404, detail="Aula no encontrada")
    
    # Validar si tiene secciones base asignadas o asignaciones especiales
    from app.models.grado_seccion import GradoSeccion
    from app.models.horario import Horario
    secciones_asignadas = db.query(GradoSeccion).filter(GradoSeccion.aula_base_id == aula_id).count()
    if secciones_asignadas > 0:
        raise HTTPException(status_code=400, detail="No se puede eliminar: el aula está asignada como aula base a una sección activa.")
    
    horarios_asignados = db.query(Horario).filter(Horario.aula_especial_id == aula_id).count()
    if horarios_asignados > 0:
        raise HTTPException(status_code=400, detail="No se puede eliminar: el aula está asignada como aula especial en horarios de clase.")

    db.delete(aula)
    db.commit()
    return {"mensaje": f"Aula '{aula.codigo}' eliminada exitosamente"}
