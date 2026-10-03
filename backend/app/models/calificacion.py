from sqlalchemy import Column, Integer, Float, ForeignKey
from app.core.database import Base

class Calificacion(Base):
    __tablename__ = "calificaciones"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    estudiante_id = Column(Integer, ForeignKey("estudiantes.id"), nullable=False)
    asignatura_id = Column(Integer, ForeignKey("asignaturas.id"), nullable=False)
    periodo_id = Column(Integer, ForeignKey("periodos_escolares.id"), nullable=False)
    nota = Column(Float, nullable=False)  # Ej: 8.5, 10.0