from sqlalchemy import Column, Integer, String, ForeignKey
from app.core.database import Base

class PeriodoEscolar(Base):
    __tablename__ = "periodos_escolares"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nombre = Column(String(50), nullable=False)  # Ej: "Trimestre 1", "Unidad 1"
    anio_lectivo_id = Column(Integer, ForeignKey("anios_lectivos.id"), nullable=False)
    estado = Column(String(20), default="Abierto")  # "Abierto" o "Cerrado"