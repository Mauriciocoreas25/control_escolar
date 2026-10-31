import os
import sys
import unittest

# Asegurar path de backend
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from fastapi import HTTPException
from sqlalchemy import text
from app.core.database import SessionLocal
from app.models.profesor import Usuario, Profesor
from app.models.models import Estudiante
from app.models.periodo import PeriodoEscolar
from app.models.calificacion import Calificacion
from app.models.asistencia import Asistencia
from app.models.asignatura import Asignatura
from app.models.horario import Horario
from app.models.grado_seccion import GradoSeccion
from app.models.aula import Aula
from app.routers.auth import login
from app.routers.estudiantes import listar_estudiantes, crear_estudiante
from app.schemas.schemas import EstudianteCreate, UsuarioLogin

class TestBusinessLogic(unittest.TestCase):
    def setUp(self):
        self.db = SessionLocal()

    def tearDown(self):
        self.db.close()

    # ==========================================
    # 1. PRUEBAS DE AUTENTICACIÓN Y SEGURIDAD RBAC
    # ==========================================
    def test_01_login_docente_exitoso(self):
        """Verifica que un docente activo inicie sesión con token y datos correctos."""
        req = UsuarioLogin(correo="carlos.docente@santasofia.edu.sv", password="docente123")
        res = login(req, db=self.db)
        self.assertEqual(res["status"], "success")
        self.assertIn("token", res)
        self.assertEqual(res["usuario"]["rol"], "Profesor")
        self.assertTrue(res["usuario"]["estado"])

    def test_02_login_director_exitoso(self):
        """Verifica que el Director General inicie sesión y obtenga su rol jerárquico."""
        req = UsuarioLogin(correo="director@santasofia.edu.sv", password="admin123")
        res = login(req, db=self.db)
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["usuario"]["rol"], "Director")
        self.assertTrue(res["usuario"]["estado"])

    def test_03_login_password_invalido_rechazado(self):
        """Verifica que una credencial incorrecta sea rechazada con 401 Unauthorized."""
        req = UsuarioLogin(correo="director@santasofia.edu.sv", password="password_incorrecto_xyz")
        with self.assertRaises(HTTPException) as cm:
            login(req, db=self.db)
        self.assertEqual(cm.exception.status_code, 401)

    def test_04_usuario_suspendido_bloqueado(self):
        """Verifica que una cuenta inactiva/suspendida sea bloqueada con 403 Forbidden."""
        usuario_prueba = self.db.query(Usuario).filter(Usuario.correo.like("%@%")).first()
        if usuario_prueba:
            estado_original = usuario_prueba.estado
            try:
                usuario_prueba.estado = False
                self.db.commit()

                req = UsuarioLogin(correo=usuario_prueba.correo, password=usuario_prueba.password_hash)
                with self.assertRaises(HTTPException) as cm:
                    login(req, db=self.db)
                self.assertEqual(cm.exception.status_code, 403)
            finally:
                usuario_prueba.estado = estado_original
                self.db.commit()

    # ==========================================
    # 2. PRUEBAS DE ESTUDIANTES Y PADRÓN ESCOLAR
    # ==========================================
    def test_05_filtro_estudiantes_por_seccion(self):
        """Verifica que el filtro por grado y sección retorne exclusivamente alumnos de esa sección."""
        estudiantes = listar_estudiantes(grado_seccion="1° Grado - Sección A", db=self.db)
        self.assertGreater(len(estudiantes), 0, "Debe haber estudiantes en 1° Grado - Sección A")
        for est in estudiantes:
            self.assertIn("1", est.grado_seccion)
            self.assertIn("A", est.grado_seccion)

    def test_06_prevencion_nie_duplicado(self):
        """Verifica la regla de integridad de negocio: no se permiten dos alumnos con el mismo NIE."""
        primer_est = self.db.query(Estudiante).first()
        self.assertIsNotNone(primer_est)

        nuevo_duplicado = EstudianteCreate(
            nie=primer_est.nie,
            nombre_completo="Estudiante Duplicado Falso",
            grado_seccion="7° Grado - Sección A",
            encargado="Tutor de Prueba",
            telefono="7777-8888"
        )
        with self.assertRaises(HTTPException) as cm:
            crear_estudiante(nuevo_duplicado, db=self.db)
        self.assertEqual(cm.exception.status_code, 400)
        self.assertIn("NIE ya esta registrado", cm.exception.detail)

    # ==========================================
    # 3. PRUEBAS DE CARGA ACADÉMICA ESPECIALIZADA
    # ==========================================
    def test_07_distribucion_materias_tercer_ciclo(self):
        """Verifica que en 3er Ciclo una materia especializada la imparta el mismo docente a todas las secciones."""
        # Matemáticas en 7mo, 8vo, 9no impartida por Carlos Alberto Morales
        materias_mat = self.db.query(Asignatura).filter(
            Asignatura.codigo.in_(["MAT-7A", "MAT-7B", "MAT-8A", "MAT-8B", "MAT-9A", "MAT-9B"])
        ).all()
        self.assertEqual(len(materias_mat), 6, "Deben existir 6 asignaturas de Matemáticas en 3er ciclo")
        for m in materias_mat:
            self.assertEqual(m.profesor_nombre, "Carlos Alberto Morales")

    def test_08_coherencia_tabla_cargas_academicas(self):
        """Verifica que la tabla relacional cargas_academicas cuente con registros íntegros."""
        total_cargas = self.db.execute(text("SELECT COUNT(*) FROM cargas_academicas")).scalar()
        self.assertGreaterEqual(total_cargas, 120, "Deben existir al menos 120 asignaciones de carga académica")

    # ==========================================
    # 4. PRUEBAS DE INTEGRIDAD DEL HORARIO ROTATIVO
    # ==========================================
    def test_09_sin_colision_docente_mismo_bloque(self):
        """Regla de Oro: Ningún docente puede tener más de una clase en el mismo día y bloque horario."""
        query = text("""
            SELECT profesor_id, dia_semana, hora_inicio, COUNT(*) as colisiones
            FROM horarios
            GROUP BY profesor_id, dia_semana, hora_inicio
            HAVING COUNT(*) > 1
        """)
        colisiones = self.db.execute(query).fetchall()
        self.assertEqual(len(colisiones), 0, f"Se detectaron colisiones de horario para docentes: {colisiones}")

    def test_10_sin_colision_seccion_mismo_bloque(self):
        """Regla de Oro: Ninguna sección puede recibir dos asignaturas simultáneas en el mismo bloque."""
        query = text("""
            SELECT grado_seccion_id, dia_semana, hora_inicio, COUNT(*) as colisiones
            FROM horarios
            GROUP BY grado_seccion_id, dia_semana, hora_inicio
            HAVING COUNT(*) > 1
        """)
        colisiones = self.db.execute(query).fetchall()
        self.assertEqual(len(colisiones), 0, f"Se detectaron colisiones de horario para secciones: {colisiones}")

    def test_11_sin_colision_aula_especial_mismo_bloque(self):
        """Regla de Oro: Ninguna aula especializada (Laboratorio, Taller) puede estar doblemente ocupada."""
        query = text("""
            SELECT aula_especial_id, dia_semana, hora_inicio, COUNT(*) as colisiones
            FROM horarios
            WHERE aula_especial_id IS NOT NULL
            GROUP BY aula_especial_id, dia_semana, hora_inicio
            HAVING COUNT(*) > 1
        """)
        colisiones = self.db.execute(query).fetchall()
        self.assertEqual(len(colisiones), 0, f"Se detectaron colisiones en aulas especiales: {colisiones}")

    # ==========================================
    # 5. PRUEBAS DE CALIFICACIONES Y PERÍODOS
    # ==========================================
    def test_12_escala_calificaciones_valida(self):
        """Verifica que todas las notas en el sistema se ubiquen estrictamente en la escala de 0.00 a 10.00."""
        califs = self.db.query(Calificacion).all()
        self.assertGreater(len(califs), 0, "Deben existir calificaciones registradas en el sistema")
        for c in califs:
            self.assertGreaterEqual(float(c.nota), 0.0)
            self.assertLessEqual(float(c.nota), 10.0)

    def test_13_existencia_periodos_y_regimen_trimestral(self):
        """Verifica que existan los 3 períodos escolares trimestrales para el año activo."""
        periodos = self.db.query(PeriodoEscolar).all()
        self.assertGreaterEqual(len(periodos), 3, "Deben existir al menos 3 períodos trimestrales")
        nombres = [p.nombre for p in periodos]
        self.assertTrue(any("Trimestre 1" in n or "Período 1" in n for n in nombres))

    # ==========================================
    # 6. PRUEBAS DE ASISTENCIA DIARIA
    # ==========================================
    def test_14_estados_asistencia_validos(self):
        """Verifica que los registros de asistencia cumplan con los estados normados."""
        asistencias = self.db.query(Asistencia).all()
        estados_validos = {"Presente", "Ausente", "Justificado", "Tarde"}
        for a in asistencias:
            self.assertIn(a.estado, estados_validos)

    # ==========================================
    # 7. PRUEBA DE REASIGNACIÓN DE DOCENTE
    # ==========================================
    def test_15_reasignacion_docente_actualiza_asignaturas(self):
        """Verifica que al reasignar un docente en una materia, la actualización persista."""
        asig = self.db.query(Asignatura).filter(Asignatura.codigo == "MAT-7A").first()
        self.assertIsNotNone(asig)
        docente_actual = asig.profesor_nombre

        # Probar reasignación a otro docente y retorno al estado original
        docente_nuevo = "Silvia Marlene Rivas" if docente_actual != "Silvia Marlene Rivas" else "Carlos Alberto Morales"
        try:
            asig.profesor_nombre = docente_nuevo
            self.db.commit()

            asig_verif = self.db.query(Asignatura).filter(Asignatura.codigo == "MAT-7A").first()
            self.assertEqual(asig_verif.profesor_nombre, docente_nuevo)
        finally:
            # Revertir
            asig.profesor_nombre = docente_actual
            self.db.commit()

if __name__ == "__main__":
    unittest.main()
