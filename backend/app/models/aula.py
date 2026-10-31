from sqlalchemy import Column, Integer, String, Boolean
from app.core.database import Base

class Aula(Base):
    __tablename__ = "aulas"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    codigo = Column(String(20), unique=True, index=True, nullable=False)
    nombre = Column(String(100), nullable=False)
    tipo = Column(String(50), nullable=False, default="Estandar")  # Estandar, Laboratorio, Taller, Cancha, etc.
    capacidad = Column(Integer, nullable=True)
    ubicacion = Column(String(150), nullable=True)
    estado = Column(Boolean, default=True)
