from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from unittest.mock import patch
from portal.models import ConfiguracionInstitucion

class PortalViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Crear usuario superusuario (Director) para acceso administrativo
        self.user = User.objects.create_superuser(
            username='director_test',
            email='director@santasofia.edu.sv',
            password='testpassword123',
            first_name='Director',
            last_name='General'
        )

    def test_01_redireccion_login_sin_autenticacion(self):
        """Usuarios no autenticados son redirigidos a la pantalla de inicio de sesión."""
        urls = [
            reverse('dashboard'),
            reverse('carga_academica'),
            reverse('horarios_view'),
            reverse('calificaciones_consolidado'),
            reverse('boletas_view'),
            reverse('ajustes_view'),
        ]
        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)
            self.assertIn('/login/', response.url)

    @patch('portal.services.api_client.get_estudiantes', return_value=[])
    @patch('portal.services.api_client.get_profesores', return_value=[])
    @patch('portal.services.api_client.get_asignaturas', return_value=[])
    @patch('portal.services.api_client.get_periodos', return_value=[])
    @patch('portal.services.api_client.get_calificaciones', return_value=[])
    @patch('portal.services.api_client.get_secciones', return_value=[])
    def test_02_dashboard_autenticado(self, *mocks):
        """Usuario Director autenticado accede al Dashboard General."""
        self.client.login(username='director_test', password='testpassword123')
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Panel de Control General')

    @patch('portal.services.api_client.get_profesores', return_value=[
        {'id': 1, 'nombre': 'Carlos Alberto Morales', 'correo': 'carlos@santasofia.edu.sv'}
    ])
    @patch('portal.services.api_client.get_asignaturas', return_value=[
        {'id': 1, 'nombre': 'Matemáticas', 'codigo': 'MAT-7A', 'grado_seccion': '7° Grado - Sección A', 'profesor_nombre': 'Carlos Alberto Morales'}
    ])
    def test_03_carga_academica_autenticado(self, *mocks):
        """Módulo de Carga Académica renderiza correctamente con asignaciones."""
        self.client.login(username='director_test', password='testpassword123')
        response = self.client.get(reverse('carga_academica'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Carga Académica Docente')

    @patch('portal.services.api_client.get_secciones', return_value=[
        {'id': 1, 'grado': '7° Grado', 'seccion': 'A', 'turno': 'Matutino', 'aula_base_nombre': 'Aula 101'}
    ])
    @patch('portal.services.api_client.get_aulas', return_value=[
        {'id': 1, 'codigo': 'A-101', 'nombre': 'Aula 101', 'tipo': 'Teorica', 'capacidad': 35}
    ])
    @patch('portal.services.api_client.get_profesores', return_value=[])
    @patch('portal.services.api_client.get_asignaturas', return_value=[])
    @patch('portal.services.api_client.get_horarios', return_value=[])
    @patch('portal.services.api_client.get_anios', return_value=[])
    def test_04_horarios_view_autenticado(self, *mocks):
        """Módulo de Horarios renderiza matriz semanal y gestión de aulas."""
        self.client.login(username='director_test', password='testpassword123')
        response = self.client.get(reverse('horarios_view'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Aulas y Horarios')

    @patch('portal.services.api_client.get_estudiantes', return_value=[
        {'id': 1, 'nie': '12345678', 'nombre_completo': 'Juan Pérez', 'grado_seccion': '7° Grado - Sección A'}
    ])
    @patch('portal.services.api_client.get_asignaturas', return_value=[
        {'id': 1, 'nombre': 'Matemáticas', 'codigo': 'MAT-7A', 'grado_seccion': '7° Grado - Sección A'}
    ])
    @patch('portal.services.api_client.get_periodos', return_value=[
        {'id': 1, 'nombre': 'Trimestre 1'}
    ])
    @patch('portal.services.api_client.get_secciones', return_value=[])
    @patch('portal.services.api_client.get_calificaciones', return_value=[
        {'id': 1, 'estudiante_id': 1, 'asignatura_id': 1, 'periodo_id': 1, 'nota': 8.5}
    ])
    def test_05_calificaciones_consolidado_sin_palabra_oficial(self, *mocks):
        """Consolidado de calificaciones renderiza y NO contiene ninguna palabra 'oficial'."""
        self.client.login(username='director_test', password='testpassword123')
        response = self.client.get(reverse('calificaciones_consolidado'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Consolidado de Calificaciones')
        content_lower = response.content.decode('utf-8').lower()
        self.assertNotIn('sábana oficial', content_lower)
        self.assertNotIn('oficial', content_lower)

    @patch('portal.services.api_client.get_estudiantes', return_value=[
        {'id': 1, 'nie': '12345678', 'nombre_completo': 'Juan Pérez', 'grado_seccion': '7° Grado - Sección A'}
    ])
    @patch('portal.services.api_client.get_asignaturas', return_value=[])
    @patch('portal.services.api_client.get_periodos', return_value=[])
    @patch('portal.services.api_client.get_secciones', return_value=[])
    @patch('portal.services.api_client.get_calificaciones', return_value=[])
    def test_06_boletas_view_autenticado(self, *mocks):
        """Módulo de Boletas renderiza correctamente."""
        self.client.login(username='director_test', password='testpassword123')
        response = self.client.get(reverse('boletas_view'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Boletas de Calificaciones')

    def test_07_ajustes_view_autenticado(self):
        """Módulo de Ajustes Institucionales renderiza formulario de configuración."""
        self.client.login(username='director_test', password='testpassword123')
        response = self.client.get(reverse('ajustes_view'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Ajustes Institucionales')

    def test_08_singleton_configuracion_institucion(self):
        """El modelo ConfiguracionInstitucion opera con el patrón Singleton."""
        inst1 = ConfiguracionInstitucion.get_activa()
        inst1.nombre = 'Complejo Educativo Santa Sofía'
        inst1.save()

        inst2 = ConfiguracionInstitucion.get_activa()
        self.assertEqual(inst1.id, inst2.id)
        self.assertEqual(inst2.nombre, 'Complejo Educativo Santa Sofía')
