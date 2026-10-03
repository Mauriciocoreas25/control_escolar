from pydantic import BaseModel
from datetime import date
from typing import Optional
class EstudianteCreate(BaseModel):
    nie: str
    nombre_completo: str
    grado_seccion: str
    encargado: Optional[str] = None
    telefono: Optional[str] = None
class EstudianteResponse(EstudianteCreate):
    id: int
    class Config:
        from_attributes = True
class AnioLectivoCreate(BaseModel):
    anio: str
    estado: Optional[str] = "Activo"
    descripcion: Optional[str] = None

class AnioLectivoResponse(AnioLectivoCreate):
    id: int
    class Config:
        from_attributes = True
class AsignaturaCreate(BaseModel):
    nombre: str
    codigo: str
    grado_seccion: Optional[str] = "General"
    profesor_nombre: Optional[str] = "Sin asignar"
    descripcion: Optional[str] = None

class AsignaturaResponse(AsignaturaCreate):
    id: int
    class Config:
        from_attributes = True
class PeriodoCreate(BaseModel):
    nombre: str
    anio_lectivo_id: int
    estado: Optional[str] = "Abierto"

class PeriodoResponse(PeriodoCreate):
    id: int
    class Config:
        from_attributes = True
class AsistenciaCreate(BaseModel):
    estudiante_id: int
    fecha: date
    estado: str  # Ej: "Presente", "Ausente", "Tarde"
    observacion: Optional[str] = None

class AsistenciaResponse(AsistenciaCreate):
    id: int
    class Config:
        from_attributes = True
class CalificacionCreate(BaseModel):
    estudiante_id: int
    asignatura_id: int
    periodo_id: int
    nota: float

class CalificacionResponse(CalificacionCreate):
    id: int
    class Config:
        from_attributes = True

class ProfesorCreate(BaseModel):
    nombre: str
    correo: str
    telefono: Optional[str] = None
    especialidad: Optional[str] = None
    password: Optional[str] = "docente123"

class ProfesorResponse(BaseModel):
    id: int
    usuario_id: int
    nombre: str
    correo: str
    telefono: Optional[str] = None
    especialidad: Optional[str] = None
    class Config:
        from_attributes = True

class UsuarioLogin(BaseModel):
    correo: str
    password: str

class UsuarioCreate(BaseModel):
    nombre: str
    correo: str
    password: str
    rol: str = "Profesor"
    estado: Optional[bool] = True

class UsuarioResponse(BaseModel):
    id: int
    nombre: str
    correo: str
    rol: str
    estado: bool
    class Config:
        from_attributes = True

class UsuarioPasswordUpdate(BaseModel):
    password: str
