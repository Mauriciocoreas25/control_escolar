from sqlalchemy import Column, Integer, Float, String, Text, ForeignKey
from app.core.database import Base

class ActividadEvaluativa(Base):
    __tablename__ = "actividades_evaluativas"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    asignatura_id = Column(Integer, ForeignKey("asignaturas.id"), nullable=False)
    periodo_id = Column(Integer, ForeignKey("periodos_escolares.id"), nullable=False)
    nombre = Column(String(150), nullable=False)
    tipo = Column(String(50), nullable=False, default="Examen") # 'Examen', 'Tarea', 'Guía', 'Laboratorio', 'Proyecto'
    ponderacion = Column(Float, nullable=False, default=0.0) # Porcentaje ej: 35.0
    fecha = Column(String(20), nullable=True)
    descripcion = Column(Text, nullable=True)
