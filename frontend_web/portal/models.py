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
    nombre = models.CharField(max_length=200, default="Complejo Educativo San Bartolomé")
    codigo_mined = models.CharField(max_length=50, default="10245")
    anio_lectivo = models.CharField(max_length=10, default="2026")
    regimen = models.CharField(max_length=50, default="Régimen Trimestral")
    director_nombre = models.CharField(max_length=150, default="Lic. Roberto Mendoza")
    direccion = models.CharField(max_length=250, default="San Bartolomé Perulapía, Cuscatlán")
    telefono = models.CharField(max_length=50, default="2222-3333")

    def __str__(self):
        return self.nombre

    @classmethod
    def get_activa(cls):
        obj, created = cls.objects.get_or_create(id=1)
        return obj
