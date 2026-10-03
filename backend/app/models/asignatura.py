from sqlalchemy import Column, Integer, String
from app.core.database import Base

class Asignatura(Base):
    __tablename__ = "asignaturas"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nombre = Column(String(100), nullable=False)
    codigo = Column(String(20), unique=True, index=True, nullable=False) # Ej: "MAT-101"
    grado_seccion = Column(String(100), nullable=False, default="General")
    profesor_nombre = Column(String(150), nullable=True, default="Sin asignar")
    descripcion = Column(String(150), nullable=True)