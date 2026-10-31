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
    path('estudiantes/export/pdf/', views.estudiantes_export_pdf, name='estudiantes_export_pdf'),
    path('estudiantes/export/excel/', views.estudiantes_export_excel, name='estudiantes_export_excel'),

    # Docentes
    path('docentes/', views.docentes_list, name='docentes_list'),
    path('docentes/nuevo/', views.docente_create, name='docente_create'),
    path('docentes/<int:id>/eliminar/', views.docente_delete, name='docente_delete'),

    # Asignaturas / Carga Académica
    path('carga-academica/', views.carga_academica, name='carga_academica'),
    path('carga-academica/reasignar-materia/', views.carga_academica_reasignar_materia, name='carga_academica_reasignar_materia'),
    path('asignaturas/nueva/', views.asignatura_create, name='asignatura_create'),
    path('asignaturas/<int:id>/editar/', views.asignatura_update, name='asignatura_update'),
    path('asignaturas/<int:id>/eliminar/', views.asignatura_delete, name='asignatura_delete'),

    # Ciclos y Periodos
    path('periodos/', views.periodos_list, name='periodos_list'),
    path('periodos/nuevo/', views.periodo_create, name='periodo_create'),
    path('periodos/<int:id>/toggle/', views.periodo_toggle, name='periodo_toggle'),
    path('periodos/<int:id>/eliminar/', views.periodo_delete, name='periodo_delete'),
    path('ciclos/nuevo/', views.anio_create, name='anio_create'),
    path('ciclos/<int:id>/toggle/', views.anio_toggle_estado, name='anio_toggle_estado'),
    path('ciclos/<int:id>/eliminar/', views.anio_delete, name='anio_delete'),

    # Aulas, Secciones y Horarios
    path('horarios/', views.aulas_horarios_view, name='horarios_view'),
    path('horarios/nuevo/', views.horario_create, name='horario_create'),
    path('horarios/<int:id>/eliminar/', views.horario_delete, name='horario_delete'),
    path('aulas/nueva/', views.aula_create, name='aula_create'),
    path('aulas/<int:id>/eliminar/', views.aula_delete, name='aula_delete'),
    path('secciones/nueva/', views.seccion_create, name='seccion_create'),
    path('secciones/<int:id>/aula-base/', views.seccion_asignar_aula, name='seccion_asignar_aula'),

    # Boletas y Reportes
    path('boletas/', views.boletas_view, name='boletas_view'),
    path('boletas/export/pdf/', views.boletas_export_pdf, name='boletas_export_pdf'),
    path('boletas/export/excel/', views.boletas_export_excel, name='boletas_export_excel'),
    path('reportes/asistencia/', views.asistencia_consolidado_view, name='asistencia_consolidado'),
    path('reportes/calificaciones/', views.calificaciones_consolidado_view, name='calificaciones_consolidado'),
    path('reportes/calificaciones/export/pdf/', views.calificaciones_export_pdf, name='calificaciones_export_pdf'),
    path('reportes/calificaciones/export/excel/', views.calificaciones_export_excel, name='calificaciones_export_excel'),
    path('ajustes/', views.ajustes_view, name='ajustes_view'),


    # Gestión y Autorización de Usuarios
    path('usuarios/', views.usuarios_list, name='usuarios_list'),
    path('usuarios/nuevo/', views.usuario_create, name='usuario_create'),
    path('usuarios/<int:id>/toggle-estado/', views.usuario_toggle_estado, name='usuario_toggle_estado'),
    path('usuarios/<int:id>/password/', views.usuario_update_password, name='usuario_update_password'),
    path('usuarios/<int:id>/eliminar/', views.usuario_delete, name='usuario_delete'),
]
