from sqlalchemy import Column, Integer, String
from app.core.database import Base
class Estudiante(Base):
    __tablename__ = "estudiantes"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nie = Column(String(50), unique=True, index=True, nullable=False)
    nombre_completo = Column(String(150), nullable=False)
    grado_seccion = Column(String(50), nullable=False)
    encargado = Column(String(150), nullable=True)
    telefono = Column(String(20), nullable=True)
