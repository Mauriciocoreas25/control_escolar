from sqlalchemy import Column, Integer, String
from app.core.database import Base

class AnioLectivo(Base):
    __tablename__ = "anios_lectivos"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    anio = Column(String(10), unique=True, nullable=False)
    estado = Column(String(20), default="Activo")
    descripcion = Column(String(150), nullable=True)