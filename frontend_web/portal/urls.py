from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('', views.dashboard, name='dashboard'),

    # Estudiantes
    path('estudiantes/', views.estudiantes_list, name='estudiantes_list'),
    path('estudiantes/nuevo/', views.estudiante_create, name='estudiante_create'),
    path('estudiantes/<int:id>/editar/', views.estudiante_update, name='estudiante_update'),
    path('estudiantes/<int:id>/eliminar/', views.estudiante_delete, name='estudiante_delete'),

    # Docentes
    path('docentes/', views.docentes_list, name='docentes_list'),
    path('docentes/nuevo/', views.docente_create, name='docente_create'),
    path('docentes/<int:id>/eliminar/', views.docente_delete, name='docente_delete'),

    # Asignaturas / Carga Académica
    path('carga-academica/', views.carga_academica, name='carga_academica'),
    path('asignaturas/nueva/', views.asignatura_create, name='asignatura_create'),
    path('asignaturas/<int:id>/eliminar/', views.asignatura_delete, name='asignatura_delete'),

    # Ciclos y Periodos
    path('periodos/', views.periodos_list, name='periodos_list'),
    path('periodos/nuevo/', views.periodo_create, name='periodo_create'),
    path('periodos/<int:id>/toggle/', views.periodo_toggle, name='periodo_toggle'),
    path('periodos/<int:id>/eliminar/', views.periodo_delete, name='periodo_delete'),
    path('ciclos/nuevo/', views.anio_create, name='anio_create'),
    path('ciclos/<int:id>/eliminar/', views.anio_delete, name='anio_delete'),

    # Boletas y Ajustes
    path('boletas/', views.boletas_view, name='boletas_view'),
    path('ajustes/', views.ajustes_view, name='ajustes_view'),

    # Gestión y Autorización de Usuarios
    path('usuarios/', views.usuarios_list, name='usuarios_list'),
    path('usuarios/nuevo/', views.usuario_create, name='usuario_create'),
    path('usuarios/<int:id>/toggle-estado/', views.usuario_toggle_estado, name='usuario_toggle_estado'),
    path('usuarios/<int:id>/password/', views.usuario_update_password, name='usuario_update_password'),
    path('usuarios/<int:id>/eliminar/', views.usuario_delete, name='usuario_delete'),
]
