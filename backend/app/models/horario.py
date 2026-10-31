from sqlalchemy import Column, Integer, String, Time, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base

class Horario(Base):
    __tablename__ = "horarios"
    __table_args__ = (
        # A) Ningún docente tiene dos clases a la misma hora
        UniqueConstraint("profesor_id", "dia_semana", "hora_inicio", "hora_fin", "anio_lectivo_id", name="uk_docente_bloque_horario"),
        # B) Ninguna sección recibe dos materias a la misma hora
        UniqueConstraint("grado_seccion_id", "dia_semana", "hora_inicio", "hora_fin", "anio_lectivo_id", name="uk_seccion_bloque_horario"),
        # C) Ninguna aula especial ocupada simultáneamente por dos clases
        UniqueConstraint("aula_especial_id", "dia_semana", "hora_inicio", "hora_fin", "anio_lectivo_id", name="uk_aula_especial_bloque"),
        {"extend_existing": True}
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    grado_seccion_id = Column(Integer, ForeignKey("grados_secciones.id"), nullable=False)
    materia_id = Column(Integer, ForeignKey("asignaturas.id"), nullable=False)
    profesor_id = Column(Integer, ForeignKey("profesores.id"), nullable=False)
    anio_lectivo_id = Column(Integer, ForeignKey("anios_lectivos.id"), nullable=False)
    dia_semana = Column(String(20), nullable=False)  # Lunes, Martes, Miercoles, Jueves, Viernes, Sabado
    hora_inicio = Column(Time, nullable=False)
    hora_fin = Column(Time, nullable=False)
    aula_especial_id = Column(Integer, ForeignKey("aulas.id"), nullable=True)  # Nullable: si es NULL, se usa aula_base_id

    grado_seccion = relationship("GradoSeccion")
    profesor = relationship("Profesor")
    aula_especial = relationship("Aula")
