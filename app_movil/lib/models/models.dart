class Institucion {
  final int id;
  final String nombre;
  final String codigoMined;
  final String anioLectivo;
  final String regimen;
  final String directorNombre;
  final String telefono;
  final String direccion;

  Institucion({
    required this.id,
    required this.nombre,
    required this.codigoMined,
    required this.anioLectivo,
    required this.regimen,
    required this.directorNombre,
    required this.telefono,
    required this.direccion,
  });

  factory Institucion.fromJson(Map<String, dynamic> json) {
    return Institucion(
      id: json['id'] ?? 1,
      nombre: json['nombre'] ?? 'Centro Educativo',
      codigoMined: json['codigo_mined'] ?? '',
      anioLectivo: json['anio_lectivo'] ?? '2026',
      regimen: json['regimen'] ?? 'Régimen Trimestral',
      directorNombre: json['director_nombre'] ?? '',
      telefono: json['telefono'] ?? '',
      direccion: json['direccion'] ?? '',
    );
  }
}

class Docente {
  final int id;
  final String nombre;
  final String correo;
  final String especialidad;
  final String telefono;

  Docente({
    required this.id,
    required this.nombre,
    required this.correo,
    required this.especialidad,
    required this.telefono,
  });

  factory Docente.fromJson(Map<String, dynamic> json) {
    return Docente(
      id: json['id'] ?? 0,
      nombre: json['nombre'] ?? '',
      correo: json['correo'] ?? '',
      especialidad: json['especialidad'] ?? 'General',
      telefono: json['telefono'] ?? '',
    );
  }
}

class Asignatura {
  final int id;
  final String codigo;
  final String nombre;
  final String gradoSeccion;
  final String profesorNombre;
  final String descripcion;
  final String? aulaCodigo;
  final String? aulaNombre;

  Asignatura({
    required this.id,
    required this.codigo,
    required this.nombre,
    required this.gradoSeccion,
    required this.profesorNombre,
    required this.descripcion,
    this.aulaCodigo,
    this.aulaNombre,
  });

  factory Asignatura.fromJson(Map<String, dynamic> json) {
    return Asignatura(
      id: json['id'] ?? 0,
      codigo: json['codigo'] ?? '',
      nombre: json['nombre'] ?? '',
      gradoSeccion: json['grado_seccion'] ?? 'General',
      profesorNombre: json['profesor_nombre'] ?? 'Sin asignar',
      descripcion: json['descripcion'] ?? '',
      aulaCodigo: json['aula_codigo'],
      aulaNombre: json['aula_nombre'],
    );
  }

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is Asignatura && runtimeType == other.runtimeType && id == other.id;

  @override
  int get hashCode => id.hashCode;
}

class Estudiante {
  final int id;
  final String nie;
  final String nombreCompleto;
  final String gradoSeccion;
  final String encargado;
  final String telefono;

  Estudiante({
    required this.id,
    required this.nie,
    required this.nombreCompleto,
    required this.gradoSeccion,
    required this.encargado,
    required this.telefono,
  });

  factory Estudiante.fromJson(Map<String, dynamic> json) {
    return Estudiante(
      id: json['id'] ?? 0,
      nie: json['nie']?.toString() ?? '',
      nombreCompleto: json['nombre_completo'] ?? '',
      gradoSeccion: json['grado_seccion'] ?? '',
      encargado: json['encargado'] ?? '',
      telefono: json['telefono'] ?? '',
    );
  }
}

class Asistencia {
  final int id;
  final int estudianteId;
  final int asignaturaId;
  final String fecha;
  final String estado; // 'Presente', 'Ausente', 'Justificado'
  final String observaciones;

  Asistencia({
    required this.id,
    required this.estudianteId,
    required this.asignaturaId,
    required this.fecha,
    required this.estado,
    required this.observaciones,
  });

  factory Asistencia.fromJson(Map<String, dynamic> json) {
    return Asistencia(
      id: json['id'] ?? 0,
      estudianteId: json['estudiante_id'] ?? 0,
      asignaturaId: json['asignatura_id'] ?? 0,
      fecha: json['fecha'] ?? '',
      estado: json['estado'] ?? 'Presente',
      observaciones: json['observaciones'] ?? '',
    );
  }
}

class Calificacion {
  final int id;
  final int estudianteId;
  final int asignaturaId;
  final int periodoId;
  final double nota;
  final String tipoEvaluacion;

  Calificacion({
    required this.id,
    required this.estudianteId,
    required this.asignaturaId,
    required this.periodoId,
    required this.nota,
    required this.tipoEvaluacion,
  });

  factory Calificacion.fromJson(Map<String, dynamic> json) {
    return Calificacion(
      id: json['id'] ?? 0,
      estudianteId: json['estudiante_id'] ?? 0,
      asignaturaId: json['asignatura_id'] ?? 0,
      periodoId: json['periodo_id'] ?? 1,
      nota: (json['nota'] is num) ? (json['nota'] as num).toDouble() : 0.0,
      tipoEvaluacion: json['tipo_evaluacion'] ?? 'Actividad 1: Examen Parcial',
    );
  }
}

class Periodo {
  final int id;
  final String nombre;
  final int anioLectivoId;
  final String estado; // 'Abierto' o 'Cerrado'

  Periodo({
    required this.id,
    required this.nombre,
    required this.anioLectivoId,
    required this.estado,
  });

  factory Periodo.fromJson(Map<String, dynamic> json) {
    return Periodo(
      id: json['id'] ?? 0,
      nombre: json['nombre'] ?? '',
      anioLectivoId: json['anio_lectivo_id'] ?? 1,
      estado: json['estado'] ?? 'Abierto',
    );
  }

  bool get estaAbierto => estado.toLowerCase() == 'abierto';

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is Periodo && runtimeType == other.runtimeType && id == other.id;

  @override
  int get hashCode => id.hashCode;
}


class ActividadEvaluativa {
  final int id;
  final int asignaturaId;
  final int periodoId;
  final String nombre;
  final String tipo; // 'Examen', 'Tarea', 'Guía', 'Laboratorio', 'Proyecto'
  final double ponderacion;
  final String? fecha;
  final String? descripcion;

  ActividadEvaluativa({
    required this.id,
    required this.asignaturaId,
    required this.periodoId,
    required this.nombre,
    required this.tipo,
    required this.ponderacion,
    this.fecha,
    this.descripcion,
  });

  factory ActividadEvaluativa.fromJson(Map<String, dynamic> json) {
    return ActividadEvaluativa(
      id: json['id'] ?? 0,
      asignaturaId: json['asignatura_id'] ?? 0,
      periodoId: json['periodo_id'] ?? 0,
      nombre: json['nombre'] ?? '',
      tipo: json['tipo'] ?? 'Examen',
      ponderacion: (json['ponderacion'] is num) ? (json['ponderacion'] as num).toDouble() : 0.0,
      fecha: json['fecha'],
      descripcion: json['descripcion'],
    );
  }

  String get displayName => '$nombre (${ponderacion.toStringAsFixed(0)}%)';
}

class HorarioClase {
  final int id;
  final int gradoSeccionId;
  final int materiaId;
  final int profesorId;
  final int anioLectivoId;
  final String diaSemana;
  final String horaInicio;
  final String horaFin;
  final String gradoSeccion;
  final String materiaNombre;
  final String profesorNombre;
  final String aulaCodigo;
  final String aulaNombre;
  final bool esAulaEspecial;

  HorarioClase({
    required this.id,
    required this.gradoSeccionId,
    required this.materiaId,
    required this.profesorId,
    required this.anioLectivoId,
    required this.diaSemana,
    required this.horaInicio,
    required this.horaFin,
    required this.gradoSeccion,
    required this.materiaNombre,
    required this.profesorNombre,
    required this.aulaCodigo,
    required this.aulaNombre,
    this.esAulaEspecial = false,
  });

  factory HorarioClase.fromJson(Map<String, dynamic> json) {
    return HorarioClase(
      id: json['id'] ?? 0,
      gradoSeccionId: json['grado_seccion_id'] ?? 0,
      materiaId: json['materia_id'] ?? 0,
      profesorId: json['profesor_id'] ?? 0,
      anioLectivoId: json['anio_lectivo_id'] ?? 1,
      diaSemana: json['dia_semana'] ?? '',
      horaInicio: json['hora_inicio'] ?? '',
      horaFin: json['hora_fin'] ?? '',
      gradoSeccion: json['grado_seccion'] ?? '',
      materiaNombre: json['materia_nombre'] ?? '',
      profesorNombre: json['profesor_nombre'] ?? '',
      aulaCodigo: json['aula_codigo'] ?? '',
      aulaNombre: json['aula_nombre'] ?? '',
      esAulaEspecial: json['es_aula_especial'] ?? false,
    );
  }

  String get rangoHoras {
    final ini = horaInicio.length >= 5 ? horaInicio.substring(0, 5) : horaInicio;
    final fin = horaFin.length >= 5 ? horaFin.substring(0, 5) : horaFin;
    return '$ini - $fin';
  }
}

