from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.models.grado_seccion import GradoSeccion
from app.models.aula import Aula
from app.schemas.schemas import GradoSeccionCreate, GradoSeccionResponse

router = APIRouter(prefix="/secciones", tags=["Secciones"])

@router.get("/", response_model=List[GradoSeccionResponse])
def listar_secciones(anio_lectivo: Optional[int] = None, db: Session = Depends(get_db)):
    query = db.query(GradoSeccion, Aula.codigo, Aula.nombre)\
              .outerjoin(Aula, GradoSeccion.aula_base_id == Aula.id)
    if anio_lectivo:
        query = query.filter(GradoSeccion.anio_lectivo == anio_lectivo)
    
    resultados = query.order_by(GradoSeccion.grado.asc(), GradoSeccion.seccion.asc()).all()
    respuestas = []
    for gs, aula_codigo, aula_nombre in resultados:
        respuestas.append(GradoSeccionResponse(
            id=gs.id,
            grado=gs.grado,
            seccion=gs.seccion,
            anio_lectivo=gs.anio_lectivo,
            aula_base_id=gs.aula_base_id,
            aula_codigo=aula_codigo,
            aula_nombre=aula_nombre
        ))
    return respuestas

@router.post("/", response_model=GradoSeccionResponse, status_code=status.HTTP_201_CREATED)
def crear_seccion(seccion_data: GradoSeccionCreate, db: Session = Depends(get_db)):
    existente = db.query(GradoSeccion).filter(
        GradoSeccion.grado == seccion_data.grado.strip(),
        GradoSeccion.seccion == seccion_data.seccion.strip().upper(),
        GradoSeccion.anio_lectivo == seccion_data.anio_lectivo
    ).first()
    if existente:
        raise HTTPException(status_code=400, detail=f"La sección '{seccion_data.grado} {seccion_data.seccion}' ya existe para el año {seccion_data.anio_lectivo}.")

    if seccion_data.aula_base_id:
        aula = db.query(Aula).filter(Aula.id == seccion_data.aula_base_id).first()
        if not aula:
            raise HTTPException(status_code=404, detail="El aula base especificada no existe.")
        
        # Validar regla de negocio: un aula base no puede pertenecer a dos secciones en el mismo ciclo
        ocupada = db.query(GradoSeccion).filter(
            GradoSeccion.aula_base_id == seccion_data.aula_base_id,
            GradoSeccion.anio_lectivo == seccion_data.anio_lectivo
        ).first()
        if ocupada:
            raise HTTPException(status_code=400, detail=f"El aula '{aula.codigo}' ya está asignada como aula base a '{ocupada.grado} {ocupada.seccion}'.")

    nueva = GradoSeccion(
        grado=seccion_data.grado.strip(),
        seccion=seccion_data.seccion.strip().upper(),
        anio_lectivo=seccion_data.anio_lectivo,
        aula_base_id=seccion_data.aula_base_id
    )
    db.add(nueva)
    db.commit()
    db.refresh(nueva)

    aula_info = db.query(Aula).filter(Aula.id == nueva.aula_base_id).first() if nueva.aula_base_id else None
    return GradoSeccionResponse(
        id=nueva.id,
        grado=nueva.grado,
        seccion=nueva.seccion,
        anio_lectivo=nueva.anio_lectivo,
        aula_base_id=nueva.aula_base_id,
        aula_codigo=aula_info.codigo if aula_info else None,
        aula_nombre=aula_info.nombre if aula_info else None
    )

@router.patch("/{seccion_id}/aula-base")
def asignar_aula_base(seccion_id: int, aula_base_id: Optional[int] = None, db: Session = Depends(get_db)):
    seccion = db.query(GradoSeccion).filter(GradoSeccion.id == seccion_id).first()
    if not seccion:
        raise HTTPException(status_code=404, detail="Sección no encontrada")

    if aula_base_id:
        aula = db.query(Aula).filter(Aula.id == aula_base_id).first()
        if not aula:
            raise HTTPException(status_code=404, detail="El aula seleccionada no existe")

        ocupada = db.query(GradoSeccion).filter(
            GradoSeccion.aula_base_id == aula_base_id,
            GradoSeccion.anio_lectivo == seccion.anio_lectivo,
            GradoSeccion.id != seccion_id
        ).first()
        if ocupada:
            raise HTTPException(status_code=400, detail=f"El aula '{aula.codigo}' ya está asignada a la sección '{ocupada.grado} {ocupada.seccion}' para el año {seccion.anio_lectivo}.")

    seccion.aula_base_id = aula_base_id
    db.commit()
    db.refresh(seccion)

    aula_info = db.query(Aula).filter(Aula.id == seccion.aula_base_id).first() if seccion.aula_base_id else None
    return {
        "mensaje": "Aula base actualizada con éxito",
        "seccion_id": seccion.id,
        "aula_base_id": seccion.aula_base_id,
        "aula_codigo": aula_info.codigo if aula_info else None,
        "aula_nombre": aula_info.nombre if aula_info else None
    }
