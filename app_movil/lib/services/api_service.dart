import 'dart:convert';
import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import '../models/models.dart';

class ApiService {
  static const String defaultServerUrl = 'http://130.131.113.202:8001';
  static String? _customBaseUrl;
  static Future<void> init() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final saved = prefs.getString('custom_server_url');
      if (saved != null && saved.trim().isNotEmpty) {
        _customBaseUrl = saved.trim();
      }
    } catch (e) {
      debugPrint('Error al inicializar ApiService: $e');
    }
  }

  static String get baseUrl {
    if (_customBaseUrl != null && _customBaseUrl!.isNotEmpty) {
      return _customBaseUrl!;
    }
    if (kIsWeb) {
      return defaultServerUrl;
    }
    if (Platform.isAndroid) {
      // 10.0.2.2 es el alias de localhost para el emulador Android
      return defaultServerUrl;
    }
    return defaultServerUrl;
  }

  static Future<void> setBaseUrl(String url) async {
    _customBaseUrl = url.trim();
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString('custom_server_url', _customBaseUrl!);
    } catch (e) {
      debugPrint('Error al guardar custom_server_url: $e');
    }
  }

  // ==================== INSTITUCIÓN ====================
  static Future<Institucion> getInstitucion() async {
    try {
      final res = await http.get(Uri.parse('$baseUrl/institucion/')).timeout(const Duration(seconds: 5));
      if (res.statusCode == 200) {
        final data = jsonDecode(utf8.decode(res.bodyBytes));
        return Institucion.fromJson(data);
      }
    } catch (e) {
      debugPrint('Error al consultar institución desde la API: $e');
    }
    return Institucion(
      id: 1,
      nombre: 'Complejo Educativo Santa Sofía',
      codigoMined: '10234',
      anioLectivo: '2026',
      regimen: '4 Períodos Anuales',
      directorNombre: 'Lic. Roberto Antonio Mendoza',
      telefono: '2222-3333',
      direccion: 'Barrio El Centro, San Salvador, El Salvador',
    );
  }

  // ==================== SESIÓN / AUTH ====================
  static Future<Map<String, dynamic>> login(String correo, String password) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/auth/login'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'correo': correo.trim(),
          'password': password.trim(),
        }),
      ).timeout(const Duration(seconds: 5));

      if (response.statusCode == 200) {
        final data = jsonDecode(utf8.decode(response.bodyBytes));
        final prefs = await SharedPreferences.getInstance();
        await prefs.setString('user_data', jsonEncode(data));
        return {'success': true, 'data': data};
      } else {
        final error = jsonDecode(utf8.decode(response.bodyBytes));
        return {'success': false, 'message': error['detail'] ?? 'Credenciales incorrectas'};
      }
    } catch (e) {
      return {'success': false, 'message': 'No se pudo conectar con el servidor ($baseUrl). Verifique la conexión institucional.'};
    }
  }

  static Future<Map<String, dynamic>?> getCurrentUser({bool validateOnline = true}) async {
    final prefs = await SharedPreferences.getInstance();
    final str = prefs.getString('user_data');
    if (str == null) return null;

    Map<String, dynamic> userMap;
    try {
      final map = jsonDecode(str);
      if (map is Map<String, dynamic> && map.containsKey('usuario') && map['usuario'] is Map<String, dynamic>) {
        userMap = Map<String, dynamic>.from(map['usuario']);
      } else if (map is Map<String, dynamic>) {
        userMap = Map<String, dynamic>.from(map);
      } else {
        await logout();
        return null;
      }
    } catch (e) {
      await logout();
      return null;
    }

    if (validateOnline) {
      final userId = userMap['id'];
      if (userId != null) {
        try {
          final res = await http.get(Uri.parse('$baseUrl/auth/me/$userId')).timeout(const Duration(seconds: 4));
          if (res.statusCode == 404 || res.statusCode == 401 || res.statusCode == 403) {
            // El usuario fue eliminado o suspendido en el servidor
            debugPrint('Sesión invalidada por el servidor (código ${res.statusCode}). Cerrando sesión local...');
            await logout();
            return null;
          } else if (res.statusCode == 200) {
            final freshData = jsonDecode(utf8.decode(res.bodyBytes));
            userMap = Map<String, dynamic>.from(freshData);
            final map = jsonDecode(str);
            if (map is Map<String, dynamic> && map.containsKey('usuario')) {
              map['usuario'] = userMap;
              await prefs.setString('user_data', jsonEncode(map));
            }
          }
        } catch (e) {
          debugPrint('Aviso: Validación de sesión offline temporal: $e');
        }
      }
    }

    return userMap;
  }

  static Future<void> logout() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('user_data');
  }

  // ==================== ASIGNATURAS / CURSOS ====================
  static Future<List<Asignatura>> getAsignaturas({String? profesorNombre}) async {
    try {
      String url = '$baseUrl/asignaturas/';
      if (profesorNombre != null && profesorNombre.isNotEmpty) {
        url += '?profesor_nombre=${Uri.encodeComponent(profesorNombre)}';
      }
      final res = await http.get(Uri.parse(url)).timeout(const Duration(seconds: 5));
      if (res.statusCode == 200) {
        final List list = jsonDecode(utf8.decode(res.bodyBytes));
        return list.map((j) => Asignatura.fromJson(j)).toList();
      }
    } catch (e) {
      debugPrint('Error al obtener asignaturas: $e');
    }
    return [];
  }

  // ==================== ESTUDIANTES ====================
  static Future<List<Estudiante>> getEstudiantes({String? gradoSeccion}) async {
    try {
      String url = '$baseUrl/estudiantes/';
      if (gradoSeccion != null && gradoSeccion.isNotEmpty) {
        url += '?grado_seccion=${Uri.encodeComponent(gradoSeccion)}';
      }
      final res = await http.get(Uri.parse(url)).timeout(const Duration(seconds: 5));
      if (res.statusCode == 200) {
        final List list = jsonDecode(utf8.decode(res.bodyBytes));
        return list.map((j) => Estudiante.fromJson(j)).toList();
      }
    } catch (e) {
      debugPrint('Error al obtener estudiantes: $e');
    }
    return [];
  }

  // ==================== ASISTENCIAS ====================
  static Future<List<Asistencia>> getAsistencias({int? asignaturaId, String? fecha}) async {
    try {
      final res = await http.get(Uri.parse('$baseUrl/asistencias/')).timeout(const Duration(seconds: 5));
      if (res.statusCode == 200) {
        final List list = jsonDecode(utf8.decode(res.bodyBytes));
        List<Asistencia> asistencias = list.map((j) => Asistencia.fromJson(j)).toList();
        if (asignaturaId != null) {
          asistencias = asistencias.where((a) => a.asignaturaId == asignaturaId).toList();
        }
        if (fecha != null) {
          asistencias = asistencias.where((a) => a.fecha == fecha).toList();
        }
        return asistencias;
      }
    } catch (e) {
      debugPrint('Error al obtener asistencias: $e');
    }
    return [];
  }

  static Future<bool> registrarAsistencia({
    required int estudianteId,
    required int asignaturaId,
    required String fecha,
    required String estado,
    String observaciones = '',
  }) async {
    try {
      final res = await http.post(
        Uri.parse('$baseUrl/asistencias/'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'estudiante_id': estudianteId,
          'asignatura_id': asignaturaId,
          'fecha': fecha,
          'estado': estado,
          'observaciones': observaciones,
        }),
      ).timeout(const Duration(seconds: 5));
      return res.statusCode == 200 || res.statusCode == 201;
    } catch (e) {
      debugPrint('Error al guardar asistencia: $e');
      return false;
    }
  }

  // ==================== CALIFICACIONES ====================
  static Future<List<Calificacion>> getCalificaciones({
    int? asignaturaId,
    int? periodoId,
    String? tipoEvaluacion,
  }) async {
    try {
      final queryParams = <String, String>{};
      if (asignaturaId != null) queryParams['asignatura_id'] = asignaturaId.toString();
      if (periodoId != null) queryParams['periodo_id'] = periodoId.toString();
      if (tipoEvaluacion != null && tipoEvaluacion.isNotEmpty) {
        queryParams['tipo_evaluacion'] = tipoEvaluacion;
      }

      final uri = Uri.parse('$baseUrl/calificaciones/').replace(
        queryParameters: queryParams.isNotEmpty ? queryParams : null,
      );
      final res = await http.get(uri).timeout(const Duration(seconds: 5));
      if (res.statusCode == 200) {
        final List list = jsonDecode(utf8.decode(res.bodyBytes));
        return list.map((j) => Calificacion.fromJson(j)).toList();
      }
    } catch (e) {
      debugPrint('Error al obtener calificaciones: $e');
    }
    return [];
  }

  static Future<bool> registrarCalificacion({
    required int estudianteId,
    required int asignaturaId,
    required int periodoId,
    required double nota,
    required String tipoEvaluacion,
  }) async {
    try {
      final res = await http.post(
        Uri.parse('$baseUrl/calificaciones/'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'estudiante_id': estudianteId,
          'asignatura_id': asignaturaId,
          'periodo_id': periodoId,
          'nota': nota,
          'tipo_evaluacion': tipoEvaluacion,
        }),
      ).timeout(const Duration(seconds: 5));
      return res.statusCode == 200 || res.statusCode == 201;
    } catch (e) {
      debugPrint('Error al registrar calificación: $e');
      return false;
    }
  }

  // ==================== PERÍODOS ====================
  static Future<List<Periodo>> getPeriodos() async {
    try {
      final res = await http.get(Uri.parse('$baseUrl/periodos/')).timeout(const Duration(seconds: 5));
      if (res.statusCode == 200) {
        final List list = jsonDecode(utf8.decode(res.bodyBytes));
        return list.map((j) => Periodo.fromJson(j)).toList();
      }
    } catch (e) {
      debugPrint('Error al obtener períodos: $e');
    }
    return [];
  }

  // ==================== ACTIVIDADES EVALUATIVAS ====================
  static Future<List<ActividadEvaluativa>> getActividades({
    int? asignaturaId,
    int? periodoId,
  }) async {
    try {
      final queryParams = <String, String>{};
      if (asignaturaId != null) queryParams['asignatura_id'] = asignaturaId.toString();
      if (periodoId != null) queryParams['periodo_id'] = periodoId.toString();

      final uri = Uri.parse('$baseUrl/actividades/').replace(
        queryParameters: queryParams.isNotEmpty ? queryParams : null,
      );
      final res = await http.get(uri).timeout(const Duration(seconds: 5));
      if (res.statusCode == 200) {
        final List list = jsonDecode(utf8.decode(res.bodyBytes));
        return list.map((j) => ActividadEvaluativa.fromJson(j)).toList();
      }
    } catch (e) {
      debugPrint('Error al obtener actividades evaluativas: $e');
    }
    return [];
  }

  static Future<ActividadEvaluativa?> crearActividad({
    required int asignaturaId,
    required int periodoId,
    required String nombre,
    required String tipo,
    required double ponderacion,
    String? fecha,
    String? descripcion,
  }) async {
    try {
      final res = await http.post(
        Uri.parse('$baseUrl/actividades/'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'asignatura_id': asignaturaId,
          'periodo_id': periodoId,
          'nombre': nombre,
          'tipo': tipo,
          'ponderacion': ponderacion,
          'fecha': fecha,
          'descripcion': descripcion,
        }),
      ).timeout(const Duration(seconds: 5));
      if (res.statusCode == 200 || res.statusCode == 201) {
        final data = jsonDecode(utf8.decode(res.bodyBytes));
        return ActividadEvaluativa.fromJson(data);
      }
    } catch (e) {
      debugPrint('Error al crear actividad evaluativa: $e');
    }
    return null;
  }

  static Future<bool> eliminarActividad(int actividadId) async {
    try {
      final res = await http.delete(
        Uri.parse('$baseUrl/actividades/$actividadId'),
      ).timeout(const Duration(seconds: 5));
      return res.statusCode == 200;
    } catch (e) {
      debugPrint('Error al eliminar actividad evaluativa: $e');
      return false;
    }
  }

  // ==================== HORARIOS DE CLASE ====================
  static Future<List<HorarioClase>> getHorarios({
    int? profesorId,
    String? profesorNombre,
    String? diaSemana,
  }) async {
    try {
      String url = '$baseUrl/horarios/';
      final qp = <String, String>{};
      if (profesorId != null) qp['profesor_id'] = profesorId.toString();
      if (diaSemana != null && diaSemana.isNotEmpty) qp['dia_semana'] = diaSemana;
      if (qp.isNotEmpty) {
        url += '?${Uri(queryParameters: qp).query}';
      }
      final res = await http.get(Uri.parse(url)).timeout(const Duration(seconds: 5));
      if (res.statusCode == 200) {
        final List list = jsonDecode(utf8.decode(res.bodyBytes));
        var items = list.map((j) => HorarioClase.fromJson(j)).toList();
        if (profesorNombre != null && profesorNombre.trim().isNotEmpty) {
          final normProf = profesorNombre.toLowerCase().trim();
          items = items.where((h) => h.profesorNombre.toLowerCase().contains(normProf)).toList();
        }
        return items;
      }
    } catch (e) {
      debugPrint('Error al obtener horarios de clase: $e');
    }
    return [];
  }
}
