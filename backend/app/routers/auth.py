from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.profesor import Usuario
from app.schemas.schemas import UsuarioLogin, UsuarioResponse

router = APIRouter(prefix="/auth", tags=["Autenticación"])

@router.post("/login")
def login(login_data: UsuarioLogin, db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.correo == login_data.correo.strip()).first()
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas: El correo no está registrado."
        )

    # Verificación de contraseña (compatible con texto plano o hash para el prototipo)
    if usuario.password_hash != login_data.password.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas: Contraseña inválida."
        )

    # Verificación de autorización por la Dirección
    if not usuario.estado:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado: Esta cuenta ha sido suspendida o no está autorizada por la Dirección."
        )

    return {
        "status": "success",
        "mensaje": f"Bienvenido(a), {usuario.nombre}",
        "token": f"bearer-token-{usuario.id}-{usuario.rol.lower()}",
        "usuario": {
            "id": usuario.id,
            "nombre": usuario.nombre,
            "correo": usuario.correo,
            "rol": usuario.rol,
            "estado": usuario.estado
        }
    }

@router.get("/me/{usuario_id}", response_model=UsuarioResponse)
def get_current_user(usuario_id: int, db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return usuario
