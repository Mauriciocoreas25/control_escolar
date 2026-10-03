from sqlalchemy import Column, Integer, String, Date, ForeignKey
from app.core.database import Base

class Asistencia(Base):
    __tablename__ = "asistencias"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    estudiante_id = Column(Integer, ForeignKey("estudiantes.id"), nullable=False)
    fecha = Column(Date, nullable=False)
    estado = Column(String(20), nullable=False)  # "Presente", "Ausente", "Tarde"
    observacion = Column(String(150), nullable=True)