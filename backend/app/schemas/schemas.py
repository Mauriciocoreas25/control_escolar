from pydantic import BaseModel, Field
from datetime import date
from typing import Optional
class EstudianteCreate(BaseModel):
    nie: str
    nombre_completo: str
    grado_seccion: str
    encargado: Optional[str] = None
    telefono: Optional[str] = None
    fecha_nacimiento: Optional[str] = None
    direccion: Optional[str] = None
    alergias: Optional[str] = None
    condiciones_medicas: Optional[str] = None

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

class AsignaturaUpdate(BaseModel):
    nombre: Optional[str] = None
    codigo: Optional[str] = None
    grado_seccion: Optional[str] = None
    profesor_nombre: Optional[str] = None
    descripcion: Optional[str] = None

class AsignaturaResponse(AsignaturaCreate):
    id: int
    aula_codigo: Optional[str] = None
    aula_nombre: Optional[str] = None
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
    nota: float = Field(..., ge=0.0, le=10.0, description='Calificación entre 0.0 y 10.0')
    tipo_evaluacion: Optional[str] = "Actividad 1: Examen Parcial (35%)"

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

# ==================== AULAS Y HORARIOS ====================
class AulaCreate(BaseModel):
    codigo: str
    nombre: str
    tipo: Optional[str] = "Estandar"
    capacidad: Optional[int] = None
    ubicacion: Optional[str] = None
    estado: Optional[bool] = True

class AulaResponse(AulaCreate):
    id: int
    class Config:
        from_attributes = True

class GradoSeccionCreate(BaseModel):
    grado: str
    seccion: str
    anio_lectivo: int
    aula_base_id: Optional[int] = None

class GradoSeccionResponse(BaseModel):
    id: int
    grado: str
    seccion: str
    anio_lectivo: int
    aula_base_id: Optional[int] = None
    aula_codigo: Optional[str] = None
    aula_nombre: Optional[str] = None
    class Config:
        from_attributes = True

class HorarioCreate(BaseModel):
    grado_seccion_id: int
    materia_id: int
    profesor_id: int
    anio_lectivo_id: Optional[int] = 1
    dia_semana: str
    hora_inicio: str
    hora_fin: str
    aula_especial_id: Optional[int] = None

class HorarioResponse(BaseModel):
    id: int
    grado_seccion_id: int
    materia_id: int
    profesor_id: int
    anio_lectivo_id: int
    dia_semana: str
    hora_inicio: str
    hora_fin: str
    aula_especial_id: Optional[int] = None
    grado_seccion: Optional[str] = None
    materia_nombre: Optional[str] = None
    profesor_nombre: Optional[str] = None
    aula_codigo: Optional[str] = None
    aula_nombre: Optional[str] = None
    es_aula_especial: bool = False
    class Config:
        from_attributes = True




class ActividadEvaluativaCreate(BaseModel):
    asignatura_id: int
    periodo_id: int
    nombre: str
    tipo: Optional[str] = "Examen"
    ponderacion: Optional[float] = 0.0
    fecha: Optional[str] = None
    descripcion: Optional[str] = None

class ActividadEvaluativaResponse(ActividadEvaluativaCreate):
    id: int
    class Config:
        from_attributes = True
