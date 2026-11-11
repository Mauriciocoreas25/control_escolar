from sqlalchemy import Column, Integer, String
from app.core.database import Base

class Estudiante(Base):
    __tablename__ = "estudiantes"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nie = Column(String(50), unique=True, index=True, nullable=False)
    nombre_completo = Column(String(150), nullable=False)
    grado_seccion = Column(String(50), nullable=False)
    encargado = Column(String(150), nullable=True)
    telefono = Column(String(20), nullable=True)
    fecha_nacimiento = Column(String(50), nullable=True, default="No especificada")
    direccion = Column(String(255), nullable=True, default="No especificada")
    alergias = Column(String(255), nullable=True, default="Ninguna conocida")
    condiciones_medicas = Column(String(255), nullable=True, default="Ninguna reportada")
