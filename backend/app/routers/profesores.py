from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.models.profesor import Profesor, Usuario
from app.schemas.schemas import ProfesorCreate, ProfesorResponse

router = APIRouter(prefix="/profesores", tags=["Profesores"])

@router.get("/", response_model=List[ProfesorResponse])
def listar_profesores(db: Session = Depends(get_db)):
    profes = db.query(Profesor).all()
    resultado = []
    for p in profes:
        u = db.query(Usuario).filter(Usuario.id == p.usuario_id).first()
        resultado.append({
            "id": p.id,
            "usuario_id": p.usuario_id,
            "nombre": u.nombre if u else "Docente",
            "correo": u.correo if u else "sin_correo",
            "telefono": p.telefono,
            "especialidad": p.especialidad
        })
    return resultado

@router.post("/", response_model=ProfesorResponse)
def crear_profesor(prof_data: ProfesorCreate, db: Session = Depends(get_db)):
    # Check if email is already used
    existe_usuario = db.query(Usuario).filter(Usuario.correo == prof_data.correo).first()
    if existe_usuario:
        raise HTTPException(status_code=400, detail="El correo ya se encuentra registrado")

    # Create Usuario
    nuevo_usuario = Usuario(
        nombre=prof_data.nombre,
        correo=prof_data.correo,
        password_hash=prof_data.password or "docente123",
        rol="Profesor",
        estado=True
    )
    db.add(nuevo_usuario)
    db.commit()
    db.refresh(nuevo_usuario)

    # Create Profesor
    nuevo_prof = Profesor(
        usuario_id=nuevo_usuario.id,
        telefono=prof_data.telefono,
        especialidad=prof_data.especialidad
    )
    db.add(nuevo_prof)
    db.commit()
    db.refresh(nuevo_prof)

    return {
        "id": nuevo_prof.id,
        "usuario_id": nuevo_usuario.id,
        "nombre": nuevo_usuario.nombre,
        "correo": nuevo_usuario.correo,
        "telefono": nuevo_prof.telefono,
        "especialidad": nuevo_prof.especialidad
    }

@router.delete("/{profesor_id}")
def eliminar_profesor(profesor_id: int, db: Session = Depends(get_db)):
    prof = db.query(Profesor).filter(Profesor.id == profesor_id).first()
    if not prof:
        raise HTTPException(status_code=404, detail="Profesor no encontrado")

    usuario_id = prof.usuario_id
    db.delete(prof)
    
    # Also delete the associated user if it exists
    u = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if u:
        db.delete(u)

    db.commit()
    return {"mensaje": "Profesor eliminado correctamente"}
