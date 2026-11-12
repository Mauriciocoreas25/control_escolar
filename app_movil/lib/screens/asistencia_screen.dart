import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../models/models.dart';
import '../services/api_service.dart';
import '../theme/app_theme.dart';
import 'login_screen.dart';

class AsistenciaScreen extends StatefulWidget {
  final Asignatura? selectedCourse;

  const AsistenciaScreen({super.key, this.selectedCourse});

  @override
  State<AsistenciaScreen> createState() => _AsistenciaScreenState();
}

class _AsistenciaScreenState extends State<AsistenciaScreen> {
  Institucion? _institucion;
  List<Asignatura> _asignaturas = [];
  Asignatura? _cursoActivo;
  List<Estudiante> _estudiantes = [];
  final Map<int, String> _asistenciaEstado = {}; // estudianteId -> 'Presente', 'Ausente', 'Justificado'
  DateTime _fechaSeleccionada = DateTime.now();
  bool _isLoading = true;
  bool _isSaving = false;
  Map<String, dynamic>? _currentUser;

  @override
  void initState() {
    super.initState();
    _initData();
  }

  @override
  void didUpdateWidget(covariant AsistenciaScreen oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.selectedCourse != null && widget.selectedCourse?.id != _cursoActivo?.id) {
      final matchingCourse = _asignaturas.firstWhere(
        (a) => a.id == widget.selectedCourse!.id,
        orElse: () => widget.selectedCourse!,
      );
      _cambiarCurso(matchingCourse);
    }
  }

  Future<void> _initData() async {
    setState(() => _isLoading = true);
    final user = await ApiService.getCurrentUser();
    if (user == null) {
      if (!mounted) return;
      Navigator.pushAndRemoveUntil(
        context,
        MaterialPageRoute(builder: (_) => const LoginScreen()),
        (route) => false,
      );
      return;
    }
    final inst = await ApiService.getInstitucion();
    final docenteNombre = user['nombre'];
    final rol = user['rol']?.toString().toLowerCase() ?? 'profesor';

    List<Asignatura> asignaturas = [];
    if (rol == 'director' || rol == 'administrador') {
      asignaturas = await ApiService.getAsignaturas();
    } else if (docenteNombre != null && docenteNombre.toString().isNotEmpty) {
      asignaturas = await ApiService.getAsignaturas(profesorNombre: docenteNombre);
    }

    Asignatura? activo;
    if (widget.selectedCourse != null) {
      activo = asignaturas.firstWhere(
        (a) => a.id == widget.selectedCourse!.id,
        orElse: () => widget.selectedCourse!,
      );
    } else if (asignaturas.isNotEmpty) {
      activo = asignaturas.first;
    }

    List<Estudiante> estudiantes = [];
    if (activo != null) {
      estudiantes = await ApiService.getEstudiantes(gradoSeccion: activo.gradoSeccion);
    }

    _asistenciaEstado.clear();
    for (var e in estudiantes) {
      _asistenciaEstado[e.id] = 'Presente';
    }

    if (!mounted) return;
    setState(() {
      _currentUser = user;
      _institucion = inst;
      _asignaturas = asignaturas;
      _cursoActivo = activo;
      _estudiantes = estudiantes;
      _isLoading = false;
    });
  }

  Future<void> _cambiarCurso(Asignatura nuevoCurso) async {
    setState(() {
      _isLoading = true;
      _cursoActivo = nuevoCurso;
    });

    final estudiantes = await ApiService.getEstudiantes(gradoSeccion: nuevoCurso.gradoSeccion);

    _asistenciaEstado.clear();
    for (var e in estudiantes) {
      _asistenciaEstado[e.id] = 'Presente';
    }

    if (!mounted) return;
    setState(() {
      _estudiantes = estudiantes;
      _isLoading = false;
    });
  }

  int get _presentesCount => _asistenciaEstado.values.where((v) => v == 'Presente').length;
  int get _ausentesCount => _asistenciaEstado.values.where((v) => v == 'Ausente').length;
  int get _justificadosCount => _asistenciaEstado.values.where((v) => v == 'Justificado').length;

  void _marcarTodos(String estado) {
    setState(() {
      for (var e in _estudiantes) {
        _asistenciaEstado[e.id] = estado;
      }
    });
  }

  Future<void> _guardarAsistencia() async {
    if (_cursoActivo == null || _estudiantes.isEmpty) return;

    setState(() => _isSaving = true);
    final fechaStr = DateFormat('yyyy-MM-dd').format(_fechaSeleccionada);

    int guardados = 0;
    for (var e in _estudiantes) {
      final estado = _asistenciaEstado[e.id] ?? 'Presente';
      final ok = await ApiService.registrarAsistencia(
        estudianteId: e.id,
        asignaturaId: _cursoActivo!.id,
        fecha: fechaStr,
        estado: estado,
      );
      if (ok) guardados++;
    }

    if (!mounted) return;
    setState(() => _isSaving = false);

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        backgroundColor: AppTheme.primaryNavy,
        content: Text(
          '¡Asistencia registrada exitosamente! ($guardados alumnos guardados)',
          style: const TextStyle(fontWeight: FontWeight.w700),
        ),
      ),
    );
  }

  Future<void> _confirmLogout() async {
    final docenteNombre = _currentUser?['nombre'] ?? 'Docente Autorizado';
    final confirm = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(18)),
        title: Row(
          children: const [
            Icon(Icons.logout_rounded, color: Color(0xFFDC2626), size: 22),
            SizedBox(width: 8),
            Text('Cerrar Sesión', style: TextStyle(fontWeight: FontWeight.w800, fontSize: 16)),
          ],
        ),
        content: Text(
          '¿Desea cerrar la sesión de $docenteNombre y volver al ingreso institucional?',
          style: const TextStyle(fontSize: 13, color: AppTheme.primaryDark),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('Cancelar', style: TextStyle(color: Color(0xFF64748B), fontWeight: FontWeight.w600)),
          ),
          ElevatedButton(
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFFDC2626),
              foregroundColor: Colors.white,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
            ),
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text('Cerrar Sesión', style: TextStyle(fontWeight: FontWeight.w700)),
          ),
        ],
      ),
    );

    if (confirm == true) {
      await ApiService.logout();
      if (!mounted) return;
      Navigator.pushAndRemoveUntil(
        context,
        MaterialPageRoute(builder: (_) => const LoginScreen()),
        (route) => false,
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final docenteNombre = _currentUser?['nombre'] ?? 'Docente Autorizado';
    final nombreEscuela = _institucion?.nombre ?? 'Complejo Educativo Santa Sofía';
    final fechaFormatted = DateFormat('EEEE, d MMMM yyyy', 'es').format(_fechaSeleccionada);

    return Scaffold(
      backgroundColor: Colors.transparent,
      body: AmbientBackground(
        child: SafeArea(
          child: _isLoading
              ? const Center(child: CircularProgressIndicator(color: AppTheme.primaryNavy))
              : Column(
                  children: [
                    Expanded(
                      child: SingleChildScrollView(
                        padding: const EdgeInsets.fromLTRB(18, 14, 18, 20),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            // Encabezado Superior
                            Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                Expanded(
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      Text(
                                        nombreEscuela.toUpperCase(),
                                        maxLines: 1,
                                        overflow: TextOverflow.ellipsis,
                                        style: const TextStyle(
                                          fontSize: 11,
                                          fontWeight: FontWeight.w800,
                                          color: AppTheme.primaryNavy,
                                          letterSpacing: 0.6,
                                        ),
                                      ),
                                      const SizedBox(height: 2),
                                      const Text(
                                        'Pase de Asistencia',
                                        style: TextStyle(
                                          fontSize: 21,
                                          fontWeight: FontWeight.w900,
                                          color: AppTheme.primaryDark,
                                          letterSpacing: -0.5,
                                        ),
                                      ),
                                    ],
                                  ),
                                ),
                                Row(
                                  children: [
                                    IconButton(
                                      icon: const Icon(Icons.refresh_rounded, size: 21, color: AppTheme.primaryDark),
                                      onPressed: _initData,
                                      tooltip: 'Actualizar',
                                    ),
                                    IconButton(
                                      icon: const Icon(Icons.logout_rounded, size: 21, color: Color(0xFFDC2626)),
                                      onPressed: _confirmLogout,
                                      tooltip: 'Salir',
                                    ),
                                  ],
                                ),
                              ],
                            ),

                            const SizedBox(height: 16),

                            // Tarjeta Glassmorphic de Control y Curso
                            GlassContainer(
                              borderRadius: 20,
                              blur: 18,
                              padding: const EdgeInsets.all(18),
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  // Selector de Fecha
                                  Row(
                                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                    children: [
                                      const Text(
                                        'CURSO ACTIVO & FECHA',
                                        style: TextStyle(
                                          fontSize: 10.5,
                                          fontWeight: FontWeight.w800,
                                          letterSpacing: 0.6,
                                          color: AppTheme.primaryNavy,
                                        ),
                                      ),
                                      InkWell(
                                        onTap: () async {
                                          final picked = await showDatePicker(
                                            context: context,
                                            initialDate: _fechaSeleccionada,
                                            firstDate: DateTime(2025),
                                            lastDate: DateTime(2030),
                                          );
                                          if (picked != null) {
                                            setState(() => _fechaSeleccionada = picked);
                                          }
                                        },
                                        borderRadius: BorderRadius.circular(10),
                                        child: Container(
                                          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                                          decoration: BoxDecoration(
                                            color: Colors.white,
                                            borderRadius: BorderRadius.circular(10),
                                            border: Border.all(color: AppTheme.borderSubtle),
                                          ),
                                          child: Row(
                                            mainAxisSize: MainAxisSize.min,
                                            children: [
                                              const Icon(Icons.calendar_today_rounded, size: 13, color: AppTheme.primaryNavy),
                                              const SizedBox(width: 5),
                                              Text(
                                                DateFormat('dd/MM/yyyy').format(_fechaSeleccionada),
                                                style: const TextStyle(fontSize: 11.5, fontWeight: FontWeight.w800, color: AppTheme.primaryDark),
                                              ),
                                            ],
                                          ),
                                        ),
                                      ),
                                    ],
                                  ),

                                  const SizedBox(height: 10),

                                  // Selector de Curso
                                  if (_asignaturas.isNotEmpty)
                                    DropdownButtonHideUnderline(
                                      child: DropdownButton<Asignatura>(
                                        value: _asignaturas.any((a) => a.id == _cursoActivo?.id) ? _asignaturas.firstWhere((a) => a.id == _cursoActivo?.id) : (_asignaturas.isNotEmpty ? _asignaturas.first : null),
                                        isDense: true,
                                        isExpanded: true,
                                        icon: const Icon(Icons.keyboard_arrow_down_rounded, color: AppTheme.primaryNavy),
                                        items: _asignaturas.map((a) {
                                          return DropdownMenuItem<Asignatura>(
                                            value: a,
                                            child: Text(
                                              '${a.nombre} — ${a.gradoSeccion}',
                                              style: const TextStyle(
                                                fontSize: 15,
                                                fontWeight: FontWeight.w800,
                                                color: AppTheme.primaryDark,
                                                letterSpacing: -0.2,
                                              ),
                                            ),
                                          );
                                        }).toList(),
                                        onChanged: (nueva) {
                                          if (nueva != null) _cambiarCurso(nueva);
                                        },
                                      ),
                                    )
                                  else
                                    const Text(
                                      'No tiene asignaturas asignadas',
                                      style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold),
                                    ),

                                  const SizedBox(height: 6),
                                  Text(
                                    'Docente a cargo: $docenteNombre',
                                    style: const TextStyle(fontSize: 12, color: Color(0xFF64748B), fontWeight: FontWeight.w500),
                                  ),

                                  // Aula si existe
                                  if (_cursoActivo != null && _cursoActivo!.aulaCodigo != null && _cursoActivo!.aulaCodigo!.isNotEmpty) ...[
                                    const SizedBox(height: 8),
                                    Container(
                                      padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 4),
                                      decoration: BoxDecoration(
                                        color: const Color(0xFFF0FDF4),
                                        borderRadius: BorderRadius.circular(8),
                                        border: Border.all(color: const Color(0xFFBBF7D0)),
                                      ),
                                      child: Row(
                                        mainAxisSize: MainAxisSize.min,
                                        children: [
                                          const Icon(Icons.meeting_room_rounded, size: 13, color: Color(0xFF15803D)),
                                          const SizedBox(width: 5),
                                          Flexible(
                                            child: Text(
                                              'Aula Asignada: ${_cursoActivo!.aulaCodigo} (${_cursoActivo!.aulaNombre ?? ''})',
                                              style: const TextStyle(
                                                fontSize: 11.5,
                                                fontWeight: FontWeight.w800,
                                                color: Color(0xFF15803D),
                                              ),
                                              overflow: TextOverflow.ellipsis,
                                            ),
                                          ),
                                        ],
                                      ),
                                    ),
                                  ],

                                  const SizedBox(height: 14),
                                  const Divider(height: 1, color: AppTheme.borderSubtle),
                                  const SizedBox(height: 12),

                                  // Resumen Rápido de Contadores
                                  Row(
                                    children: [
                                      _buildGlassStatMini('Total', '${_estudiantes.length}', const Color(0xFF334155), const Color(0xFFF1F5F9)),
                                      const SizedBox(width: 6),
                                      _buildGlassStatMini('Presentes', '$_presentesCount', AppTheme.statusPresente, const Color(0xFFECFDF5)),
                                      const SizedBox(width: 6),
                                      _buildGlassStatMini('Ausentes', '$_ausentesCount', AppTheme.statusAusente, const Color(0xFFFEF2F2)),
                                      const SizedBox(width: 6),
                                      _buildGlassStatMini('Justificados', '$_justificadosCount', AppTheme.statusJustificado, const Color(0xFFFFFBEB)),
                                    ],
                                  ),
                                ],
                              ),
                            ),

                            const SizedBox(height: 16),

                            // Fila de Acción Rápida
                            Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    const Text(
                                      'Alumnos de la Sección',
                                      style: TextStyle(
                                        fontSize: 14.5,
                                        fontWeight: FontWeight.w800,
                                        color: AppTheme.primaryDark,
                                      ),
                                    ),
                                    Text(
                                      fechaFormatted,
                                      style: const TextStyle(fontSize: 11, color: Color(0xFF64748B)),
                                    ),
                                  ],
                                ),
                                InkWell(
                                  onTap: () => _marcarTodos('Presente'),
                                  borderRadius: BorderRadius.circular(10),
                                  child: Container(
                                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                                    decoration: BoxDecoration(
                                      gradient: AppTheme.emeraldGradient,
                                      borderRadius: BorderRadius.circular(10),
                                      boxShadow: [
                                        BoxShadow(
                                          color: const Color(0xFF059669).withOpacity(0.25),
                                          blurRadius: 8,
                                          offset: const Offset(0, 2),
                                        ),
                                      ],
                                    ),
                                    child: Row(
                                      mainAxisSize: MainAxisSize.min,
                                      children: const [
                                        Icon(Icons.done_all_rounded, size: 14, color: Colors.white),
                                        SizedBox(width: 4),
                                        Text(
                                          'Marcar Todos P',
                                          style: TextStyle(fontSize: 11, fontWeight: FontWeight.w800, color: Colors.white),
                                        ),
                                      ],
                                    ),
                                  ),
                                ),
                              ],
                            ),

                            const SizedBox(height: 12),

                            // Lista de Estudiantes
                            if (_estudiantes.isEmpty)
                              GlassContainer(
                                borderRadius: 18,
                                padding: const EdgeInsets.all(32),
                                child: const Center(
                                  child: Text(
                                    'No hay estudiantes registrados en esta sección.',
                                    style: TextStyle(fontSize: 13, color: Color(0xFF94A3B8)),
                                  ),
                                ),
                              )
                            else
                              ListView.separated(
                                shrinkWrap: true,
                                physics: const NeverScrollableScrollPhysics(),
                                itemCount: _estudiantes.length,
                                separatorBuilder: (_, __) => const SizedBox(height: 8),
                                itemBuilder: (context, index) {
                                  final est = _estudiantes[index];
                                  final estado = _asistenciaEstado[est.id] ?? 'Presente';
                                  return _buildStudentAttendanceRow(est, estado, index + 1);
                                },
                              ),

                            const SizedBox(height: 85),
                          ],
                        ),
                      ),
                    ),

                    // Barra Inferior Flotante Glassmorphic para Guardar
                    Container(
                      padding: const EdgeInsets.fromLTRB(16, 10, 16, 88),
                      decoration: BoxDecoration(
                        color: Colors.white.withOpacity(0.85),
                        borderRadius: const BorderRadius.vertical(top: Radius.circular(20)),
                        border: Border.all(color: Colors.white.withOpacity(0.70)),
                        boxShadow: [
                          BoxShadow(
                            color: Colors.black.withOpacity(0.04),
                            blurRadius: 16,
                            offset: const Offset(0, -4),
                          ),
                        ],
                      ),
                      child: SafeArea(
                        top: false,
                        child: Container(
                          width: double.infinity,
                          height: 48,
                          decoration: BoxDecoration(
                            gradient: (_isSaving || _estudiantes.isEmpty) ? null : AppTheme.buttonGradient,
                            color: (_isSaving || _estudiantes.isEmpty) ? const Color(0xFFCBD5E1) : null,
                            borderRadius: BorderRadius.circular(14),
                            boxShadow: (_isSaving || _estudiantes.isEmpty)
                                ? null
                                : [
                                    BoxShadow(
                                      color: const Color(0xFF2563EB).withOpacity(0.35),
                                      blurRadius: 14,
                                      offset: const Offset(0, 4),
                                    ),
                                  ],
                          ),
                          child: Material(
                            color: Colors.transparent,
                            child: InkWell(
                              borderRadius: BorderRadius.circular(14),
                              onTap: (_isSaving || _estudiantes.isEmpty) ? null : _guardarAsistencia,
                              child: Center(
                                child: _isSaving
                                    ? const SizedBox(
                                        width: 22,
                                        height: 22,
                                        child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                                      )
                                    : Row(
                                        mainAxisAlignment: MainAxisAlignment.center,
                                        children: const [
                                          Icon(Icons.save_rounded, color: Colors.white, size: 18),
                                          SizedBox(width: 8),
                                          Text(
                                            'Guardar Asistencia de Hoy',
                                            style: TextStyle(
                                              color: Colors.white,
                                              fontSize: 14,
                                              fontWeight: FontWeight.w800,
                                            ),
                                          ),
                                        ],
                                      ),
                              ),
                            ),
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
        ),
      ),
    );
  }

  Widget _buildGlassStatMini(String label, String value, Color color, Color bg) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 6, horizontal: 4),
        decoration: BoxDecoration(
          color: bg,
          borderRadius: BorderRadius.circular(10),
          border: Border.all(color: color.withOpacity(0.25)),
        ),
        child: Column(
          children: [
            Text(
              value,
              style: TextStyle(fontSize: 15, fontWeight: FontWeight.w900, color: color),
            ),
            Text(
              label,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: TextStyle(fontSize: 10, fontWeight: FontWeight.w700, color: color),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildStudentAttendanceRow(Estudiante est, String estadoActual, int correlativo) {
    return GlassContainer(
      borderRadius: 14,
      blur: 12,
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
      child: Row(
        children: [
          Container(
            width: 26,
            height: 26,
            decoration: BoxDecoration(
              color: const Color(0xFFF1F5F9),
              borderRadius: BorderRadius.circular(8),
            ),
            alignment: Alignment.center,
            child: Text(
              '$correlativo',
              style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w800, color: Color(0xFF64748B)),
            ),
          ),
          const SizedBox(width: 12),

          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  est.nombreCompleto,
                  style: const TextStyle(fontSize: 13.5, fontWeight: FontWeight.w800, color: AppTheme.primaryDark),
                ),
                Text(
                  'NIE: ${est.nie} • ${est.gradoSeccion}',
                  style: const TextStyle(fontSize: 10.5, fontFamily: 'monospace', color: Color(0xFF64748B), fontWeight: FontWeight.w500),
                ),
              ],
            ),
          ),
          const SizedBox(width: 10),

          // Segmentos P / A / J con Animación y Colores Vivos
          Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              _buildAttendanceButton(
                est.id,
                label: 'P',
                estado: 'Presente',
                color: AppTheme.statusPresente,
                gradient: AppTheme.emeraldGradient,
                isSelected: estadoActual == 'Presente',
              ),
              const SizedBox(width: 5),
              _buildAttendanceButton(
                est.id,
                label: 'A',
                estado: 'Ausente',
                color: AppTheme.statusAusente,
                gradient: AppTheme.roseGradient,
                isSelected: estadoActual == 'Ausente',
              ),
              const SizedBox(width: 5),
              _buildAttendanceButton(
                est.id,
                label: 'J',
                estado: 'Justificado',
                color: AppTheme.statusJustificado,
                gradient: AppTheme.amberGradient,
                isSelected: estadoActual == 'Justificado',
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildAttendanceButton(
    int estudianteId, {
    required String label,
    required String estado,
    required Color color,
    required LinearGradient gradient,
    required bool isSelected,
  }) {
    return InkWell(
      onTap: () {
        setState(() {
          _asistenciaEstado[estudianteId] = estado;
        });
      },
      borderRadius: BorderRadius.circular(8),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        width: 32,
        height: 32,
        decoration: BoxDecoration(
          gradient: isSelected ? gradient : null,
          color: isSelected ? null : Colors.white,
          borderRadius: BorderRadius.circular(8),
          border: Border.all(
            color: isSelected ? Colors.transparent : color.withOpacity(0.35),
            width: 1.2,
          ),
          boxShadow: isSelected
              ? [
                  BoxShadow(
                    color: color.withOpacity(0.35),
                    blurRadius: 8,
                    offset: const Offset(0, 2),
                  ),
                ]
              : null,
        ),
        alignment: Alignment.center,
        child: Text(
          label,
          style: TextStyle(
            fontSize: 12.5,
            fontWeight: FontWeight.w900,
            color: isSelected ? Colors.white : color,
          ),
        ),
      ),
    );
  }
}
