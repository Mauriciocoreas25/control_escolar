from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base

class GradoSeccion(Base):
    __tablename__ = "grados_secciones"
    __table_args__ = (
        UniqueConstraint("grado", "seccion", "anio_lectivo", name="uk_grado_seccion"),
        UniqueConstraint("aula_base_id", "anio_lectivo", name="uk_aula_base_anio"),
        {"extend_existing": True}
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    grado = Column(String(50), nullable=False)
    seccion = Column(String(10), nullable=False)
    anio_lectivo = Column(Integer, nullable=False)
    aula_base_id = Column(Integer, ForeignKey("aulas.id"), nullable=True)

    aula_base = relationship("Aula")
