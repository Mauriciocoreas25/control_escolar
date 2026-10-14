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

  Asignatura({
    required this.id,
    required this.codigo,
    required this.nombre,
    required this.gradoSeccion,
    required this.profesorNombre,
    required this.descripcion,
  });

  factory Asignatura.fromJson(Map<String, dynamic> json) {
    return Asignatura(
      id: json['id'] ?? 0,
      codigo: json['codigo'] ?? '',
      nombre: json['nombre'] ?? '',
      gradoSeccion: json['grado_seccion'] ?? 'General',
      profesorNombre: json['profesor_nombre'] ?? 'Sin asignar',
      descripcion: json['descripcion'] ?? '',
    );
  }
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
}
