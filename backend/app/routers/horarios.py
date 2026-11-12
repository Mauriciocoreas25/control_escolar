from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, aliased
from typing import List, Optional
from app.core.database import get_db
from app.models.horario import Horario
from app.models.grado_seccion import GradoSeccion
from app.models.profesor import Profesor, Usuario
from app.models.asignatura import Asignatura
from app.models.aula import Aula
from app.schemas.schemas import HorarioCreate, HorarioResponse

router = APIRouter(prefix="/horarios", tags=["Horarios"])

@router.get("/", response_model=List[HorarioResponse])
def listar_horarios(
    grado_seccion_id: Optional[int] = None,
    profesor_id: Optional[int] = None,
    profesor_nombre: Optional[str] = None,
    dia_semana: Optional[str] = None,
    anio_lectivo_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    AulaBase = aliased(Aula)
    AulaEspecial = aliased(Aula)

    query = db.query(
        Horario,
        GradoSeccion.grado,
        GradoSeccion.seccion,
        Usuario.nombre.label("profesor_nombre"),
        AulaBase.codigo.label("aula_base_codigo"),
        AulaBase.nombre.label("aula_base_nombre"),
        AulaEspecial.codigo.label("aula_especial_codigo"),
        AulaEspecial.nombre.label("aula_especial_nombre")
    ).join(GradoSeccion, Horario.grado_seccion_id == GradoSeccion.id)\
     .join(Profesor, Horario.profesor_id == Profesor.id)\
     .join(Usuario, Profesor.usuario_id == Usuario.id)\
     .outerjoin(AulaBase, GradoSeccion.aula_base_id == AulaBase.id)\
     .outerjoin(AulaEspecial, Horario.aula_especial_id == AulaEspecial.id)

    if grado_seccion_id:
        query = query.filter(Horario.grado_seccion_id == grado_seccion_id)
    if profesor_id:
        query = query.filter(Horario.profesor_id == profesor_id)
    if dia_semana:
        query = query.filter(Horario.dia_semana == dia_semana)
    if anio_lectivo_id:
        query = query.filter(Horario.anio_lectivo_id == anio_lectivo_id)
    if profesor_nombre:
        limpio = profesor_nombre.replace("Lic. ", "").replace("Prof. ", "").replace("Ing. ", "").strip()
        query = query.filter((Usuario.nombre.ilike(f"%{profesor_nombre}%")) | (Usuario.nombre.ilike(f"%{limpio}%")))

    # Ordenar por día y hora
    dias_orden = ["Lunes", "Martes", "Miercoles", "Jueves", "Viernes", "Sabado"]
    resultados = query.all()

    # Obtener nombres de materias
    from app.models.asignatura import Asignatura
    materias_dict = {m.id: m.nombre for m in db.query(Asignatura).all()}

    # También verificar si existen materias en la tabla legacy materias
    try:
        from sqlalchemy import text
        legacy_m = db.execute(text("SELECT id, nombre_materia FROM materias")).fetchall()
        for lm in legacy_m:
            if lm[0] not in materias_dict:
                materias_dict[lm[0]] = lm[1]
    except Exception:
        pass

    lista_respuestas = []
    for h, grado, seccion, prof_nom, ab_cod, ab_nom, ae_cod, ae_nom in resultados:
        es_especial = bool(h.aula_especial_id)
        aula_codigo = ae_cod if es_especial else (ab_cod or "Sin aula")
        aula_nombre = ae_nom if es_especial else (ab_nom or "Aula base no asignada")

        m_nombre = materias_dict.get(h.materia_id, f"Materia #{h.materia_id}")

        lista_respuestas.append(HorarioResponse(
            id=h.id,
            grado_seccion_id=h.grado_seccion_id,
            materia_id=h.materia_id,
            profesor_id=h.profesor_id,
            anio_lectivo_id=h.anio_lectivo_id,
            dia_semana=h.dia_semana,
            hora_inicio=str(h.hora_inicio),
            hora_fin=str(h.hora_fin),
            aula_especial_id=h.aula_especial_id,
            grado_seccion=f"{grado} - {seccion}",
            materia_nombre=m_nombre,
            profesor_nombre=prof_nom,
            aula_codigo=aula_codigo,
            aula_nombre=aula_nombre,
            es_aula_especial=es_especial
        ))

    # Ordenar de acuerdo al orden de los días de la semana y hora
    lista_respuestas.sort(key=lambda x: (
        dias_orden.index(x.dia_semana) if x.dia_semana in dias_orden else 99,
        x.hora_inicio
    ))
    return lista_respuestas

@router.post("/", response_model=HorarioResponse, status_code=status.HTTP_201_CREATED)
def crear_bloque_horario(horario_data: HorarioCreate, db: Session = Depends(get_db)):
    # 1. Validar que la sección no tenga dos clases a la misma hora
    conflicto_seccion = db.query(Horario).filter(
        Horario.grado_seccion_id == horario_data.grado_seccion_id,
        Horario.dia_semana == horario_data.dia_semana,
        Horario.hora_inicio == horario_data.hora_inicio,
        Horario.hora_fin == horario_data.hora_fin,
        Horario.anio_lectivo_id == horario_data.anio_lectivo_id
    ).first()
    if conflicto_seccion:
        raise HTTPException(
            status_code=400,
            detail=f"La sección ya tiene asignada una materia el {horario_data.dia_semana} de {horario_data.hora_inicio} a {horario_data.hora_fin}."
        )

    # 2. Validar que el docente no tenga dos clases asignadas a la misma hora
    conflicto_docente = db.query(Horario).filter(
        Horario.profesor_id == horario_data.profesor_id,
        Horario.dia_semana == horario_data.dia_semana,
        Horario.hora_inicio == horario_data.hora_inicio,
        Horario.hora_fin == horario_data.hora_fin,
        Horario.anio_lectivo_id == horario_data.anio_lectivo_id
    ).first()
    if conflicto_docente:
        raise HTTPException(
            status_code=400,
            detail=f"El docente ya tiene otra clase asignada el {horario_data.dia_semana} de {horario_data.hora_inicio} a {horario_data.hora_fin}."
        )

    # 3. Si se especifica aula especial (laboratorio/taller), validar que no esté ocupada
    if horario_data.aula_especial_id:
        conflicto_aula = db.query(Horario).filter(
            Horario.aula_especial_id == horario_data.aula_especial_id,
            Horario.dia_semana == horario_data.dia_semana,
            Horario.hora_inicio == horario_data.hora_inicio,
            Horario.hora_fin == horario_data.hora_fin,
            Horario.anio_lectivo_id == horario_data.anio_lectivo_id
        ).first()
        if conflicto_aula:
            raise HTTPException(
                status_code=400,
                detail=f"El aula especial/laboratorio seleccionada ya está ocupada el {horario_data.dia_semana} en ese bloque horario."
            )

    nuevo_horario = Horario(
        grado_seccion_id=horario_data.grado_seccion_id,
        materia_id=horario_data.materia_id,
        profesor_id=horario_data.profesor_id,
        anio_lectivo_id=horario_data.anio_lectivo_id,
        dia_semana=horario_data.dia_semana,
        hora_inicio=horario_data.hora_inicio,
        hora_fin=horario_data.hora_fin,
        aula_especial_id=horario_data.aula_especial_id
    )
    db.add(nuevo_horario)
    db.commit()
    db.refresh(nuevo_horario)

    # Recuperar datos para la respuesta enriquecida
    gs = db.query(GradoSeccion).filter(GradoSeccion.id == nuevo_horario.grado_seccion_id).first()
    prof = db.query(Profesor).filter(Profesor.id == nuevo_horario.profesor_id).first()
    usr = db.query(Usuario).filter(Usuario.id == prof.usuario_id).first() if prof else None

    aula_esp = db.query(Aula).filter(Aula.id == nuevo_horario.aula_especial_id).first() if nuevo_horario.aula_especial_id else None
    aula_base = db.query(Aula).filter(Aula.id == gs.aula_base_id).first() if gs and gs.aula_base_id else None

    es_especial = bool(nuevo_horario.aula_especial_id)
    return HorarioResponse(
        id=nuevo_horario.id,
        grado_seccion_id=nuevo_horario.grado_seccion_id,
        materia_id=nuevo_horario.materia_id,
        profesor_id=nuevo_horario.profesor_id,
        anio_lectivo_id=nuevo_horario.anio_lectivo_id,
        dia_semana=nuevo_horario.dia_semana,
        hora_inicio=str(nuevo_horario.hora_inicio),
        hora_fin=str(nuevo_horario.hora_fin),
        aula_especial_id=nuevo_horario.aula_especial_id,
        grado_seccion=f"{gs.grado} - {gs.seccion}" if gs else "General",
        materia_nombre=f"Materia #{nuevo_horario.materia_id}",
        profesor_nombre=usr.nombre if usr else "Docente asignado",
        aula_codigo=aula_esp.codigo if es_especial else (aula_base.codigo if aula_base else "Sin aula"),
        aula_nombre=aula_esp.nombre if es_especial else (aula_base.nombre if aula_base else "Aula base no asignada"),
        es_aula_especial=es_especial
    )

@router.delete("/{horario_id}")
def eliminar_bloque_horario(horario_id: int, db: Session = Depends(get_db)):
    h = db.query(Horario).filter(Horario.id == horario_id).first()
    if not h:
        raise HTTPException(status_code=404, detail="Bloque de horario no encontrado")
    db.delete(h)
    db.commit()
    return {"mensaje": "Bloque de horario eliminado con éxito"}
