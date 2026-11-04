from django.db import models
from django.contrib.auth.models import User

class PerfilUsuario(models.Model):
    ROLES = [
        ('Director', 'Director General'),
        ('Secretaria', 'Secretaría Académica'),
        ('Profesor', 'Docente'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    rol = models.CharField(max_length=20, choices=ROLES, default='Secretaria')
    telefono = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.rol})"

class ConfiguracionInstitucion(models.Model):
    nombre = models.CharField(max_length=200, default="Complejo Educativo Santa Sofía")
    codigo_mined = models.CharField(max_length=50, default="10234")
    anio_lectivo = models.CharField(max_length=10, default="2026")
    regimen = models.CharField(max_length=50, default="4 Períodos Anuales")
    director_nombre = models.CharField(max_length=150, default="Lic. Roberto Antonio Mendoza")
    direccion = models.CharField(max_length=250, default="Barrio El Centro, San Salvador, El Salvador")

    telefono = models.CharField(max_length=50, default="2222-3333")
    logo = models.ImageField(upload_to='institucion/', blank=True, null=True)

    def __str__(self):
        return self.nombre

    @classmethod
    def get_activa(cls):
        obj, created = cls.objects.get_or_create(id=1)
        return obj
