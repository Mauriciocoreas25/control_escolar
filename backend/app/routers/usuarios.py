from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.models.profesor import Usuario, Profesor
from app.schemas.schemas import UsuarioCreate, UsuarioResponse, UsuarioPasswordUpdate

router = APIRouter(prefix="/usuarios", tags=["Gestión de Usuarios"])

@router.get("/", response_model=List[UsuarioResponse])
def listar_usuarios(db: Session = Depends(get_db)):
    return db.query(Usuario).order_by(Usuario.id.asc()).all()

@router.post("/", response_model=UsuarioResponse)
def crear_usuario(usuario_data: UsuarioCreate, db: Session = Depends(get_db)):
    correo = usuario_data.correo.strip().lower()
    existe = db.query(Usuario).filter(Usuario.correo == correo).first()
    if existe:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe un usuario registrado con este correo electrónico."
        )

    nuevo = Usuario(
        nombre=usuario_data.nombre.strip(),
        correo=correo,
        password_hash=usuario_data.password.strip(),
        rol=usuario_data.rol.strip(),
        estado=usuario_data.estado if usuario_data.estado is not None else True
    )
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)

    # Si es profesor, crear automáticamente su registro en la tabla de profesores
    if nuevo.rol == "Profesor":
        nuevo_prof = Profesor(
            usuario_id=nuevo.id,
            telefono="",
            especialidad="Docente General"
        )
        db.add(nuevo_prof)
        db.commit()

    return nuevo

@router.patch("/{usuario_id}/toggle-estado", response_model=UsuarioResponse)
def toggle_estado_usuario(usuario_id: int, db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # Invertir el estado (autorizar / desautorizar)
    usuario.estado = not bool(usuario.estado)
    db.commit()
    db.refresh(usuario)
    return usuario

@router.patch("/{usuario_id}/password")
def actualizar_password(usuario_id: int, data: UsuarioPasswordUpdate, db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    usuario.password_hash = data.password.strip()
    db.commit()
    return {"status": "success", "mensaje": "Contraseña actualizada correctamente"}

@router.delete("/{usuario_id}")
def eliminar_usuario(usuario_id: int, db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # Si es profesor, eliminar registros asociados
    if usuario.rol == "Profesor":
        profesores = db.query(Profesor).filter(Profesor.usuario_id == usuario.id).all()
        for p in profesores:
            db.delete(p)

    db.delete(usuario)
    db.commit()
    return {"status": "success", "mensaje": "Usuario eliminado correctamente"}
