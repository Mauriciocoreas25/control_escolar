from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.models.asignatura import Asignatura
from app.schemas.schemas import AsignaturaCreate, AsignaturaUpdate, AsignaturaResponse

router = APIRouter(prefix="/asignaturas", tags=["Asignaturas"])

@router.get("/", response_model=List[AsignaturaResponse])
def listar_asignaturas(profesor_nombre: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Asignatura)
    if profesor_nombre:
        limpio = profesor_nombre.replace("Lic. ", "").replace("Prof. ", "").replace("Ing. ", "").strip()
        query = query.filter(
            (Asignatura.profesor_nombre.ilike(f"%{profesor_nombre}%")) |
            (Asignatura.profesor_nombre.ilike(f"%{limpio}%"))
        )
    asignaturas = query.all()

    from app.models.horario import Horario
    from app.models.grado_seccion import GradoSeccion
    from app.models.aula import Aula

    aulas_dict = {a.id: a for a in db.query(Aula).all()}
    secciones = db.query(GradoSeccion).all()
    secciones_map = {}
    for s in secciones:
        clave = f"{s.grado} {s.seccion}".strip().lower()
        secciones_map[clave] = s

    horarios = db.query(Horario).all()
    horarios_map = {h.materia_id: h for h in horarios}

    respuestas = []
    for a in asignaturas:
        aula_cod = None
        aula_nom = None

        h = horarios_map.get(a.id)
        if h and h.aula_especial_id and h.aula_especial_id in aulas_dict:
            aula_obj = aulas_dict[h.aula_especial_id]
            aula_cod = aula_obj.codigo
            aula_nom = aula_obj.nombre
        else:
            clave_sec = (a.grado_seccion or "").strip().lower()
            sec_obj = secciones_map.get(clave_sec)
            if sec_obj and sec_obj.aula_base_id and sec_obj.aula_base_id in aulas_dict:
                aula_obj = aulas_dict[sec_obj.aula_base_id]
                aula_cod = aula_obj.codigo
                aula_nom = aula_obj.nombre

        respuestas.append(AsignaturaResponse(
            id=a.id,
            nombre=a.nombre,
            codigo=a.codigo,
            grado_seccion=a.grado_seccion,
            profesor_nombre=a.profesor_nombre,
            descripcion=a.descripcion,
            aula_codigo=aula_cod,
            aula_nombre=aula_nom
        ))
    return respuestas

@router.post("/", response_model=AsignaturaResponse)
def crear_asignatura(asignatura_data: AsignaturaCreate, db: Session = Depends(get_db)):
    db_asignatura = db.query(Asignatura).filter(Asignatura.codigo == asignatura_data.codigo).first()
    if db_asignatura:
        raise HTTPException(status_code=400, detail="El codigo de asignatura ya esta registrado")
    nuevo = Asignatura(**asignatura_data.dict())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo

@router.patch("/{asignatura_id}", response_model=AsignaturaResponse)
def actualizar_asignatura(asignatura_id: int, asignatura_data: AsignaturaUpdate, db: Session = Depends(get_db)):
    db_asignatura = db.query(Asignatura).filter(Asignatura.id == asignatura_id).first()
    if not db_asignatura:
        raise HTTPException(status_code=404, detail="Asignatura no encontrada")
    
    for key, value in asignatura_data.dict(exclude_unset=True).items():
        if value is not None:
            setattr(db_asignatura, key, value)
    
    db.commit()
    db.refresh(db_asignatura)
    return db_asignatura

@router.delete("/{asignatura_id}")
def eliminar_asignatura(asignatura_id: int, db: Session = Depends(get_db)):
    db_asignatura = db.query(Asignatura).filter(Asignatura.id == asignatura_id).first()
    if not db_asignatura:
        raise HTTPException(status_code=404, detail="Asignatura no encontrada")
    
    db.delete(db_asignatura)
    db.commit()
    return {"mensaje": "Asignatura eliminada correctamente"}