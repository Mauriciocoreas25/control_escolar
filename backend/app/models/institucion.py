from sqlalchemy import Column, Integer, String
from app.core.database import Base

class Institucion(Base):
    __tablename__ = "institucion_config"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(200), default="Complejo Educativo Santa Sofía")
    codigo_mined = Column(String(50), default="10234")
    anio_lectivo = Column(String(20), default="2026")
    regimen = Column(String(50), default="4 Períodos Anuales")
    director_nombre = Column(String(150), default="Lic. Roberto Antonio Mendoza")
    telefono = Column(String(50), default="2222-3333")
    direccion = Column(String(250), default="Barrio El Centro, San Salvador, El Salvador")
