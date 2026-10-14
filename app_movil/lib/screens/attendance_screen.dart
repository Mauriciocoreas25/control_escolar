import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../models/models.dart';
import '../services/api_service.dart';
import '../theme/app_theme.dart';

class AttendanceScreen extends StatefulWidget {
  final Asignatura? selectedCourse;

  const AttendanceScreen({super.key, this.selectedCourse});

  @override
  State<AttendanceScreen> createState() => _AttendanceScreenState();
}

class _AttendanceScreenState extends State<AttendanceScreen> {
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

  Future<void> _initData() async {
    setState(() => _isLoading = true);
    final user = await ApiService.getCurrentUser();
    final asignaturas = await ApiService.getAsignaturas();

    Asignatura? activo = widget.selectedCourse;
    if (activo == null && asignaturas.isNotEmpty) {
      activo = asignaturas.first;
    }

    List<Estudiante> estudiantes = [];
    if (activo != null) {
      estudiantes = await ApiService.getEstudiantes(gradoSeccion: activo.gradoSeccion);
    } else {
      estudiantes = await ApiService.getEstudiantes();
    }

    // Inicializar todos en 'Presente' por defecto
    for (var e in estudiantes) {
      _asistenciaEstado[e.id] = 'Presente';
    }

    if (!mounted) return;
    setState(() {
      _currentUser = user;
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

  Future<void> _guardarAsistencia() async {
    if (_cursoActivo == null) return;

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
          '¡Asistencia guardada con éxito! ($guardados alumnos registrados)',
          style: const TextStyle(fontWeight: FontWeight.w600),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final docenteNombre = _currentUser?['nombre'] ?? 'Prof. Carlos Juan Pérez';
    final fechaFormatted = DateFormat('EEEE, d MMMM yyyy', 'es').format(_fechaSeleccionada);

    return Scaffold(
      backgroundColor: AppTheme.background,
      appBar: AppBar(
        title: const Text('Pase de Asistencia'),
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : Column(
              children: [
                Expanded(
                  child: SingleChildScrollView(
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        // Top Header Overview Card (Figma)
                        Container(
                          padding: const EdgeInsets.all(16),
                          decoration: BoxDecoration(
                            color: Colors.white,
                            borderRadius: BorderRadius.circular(14),
                            border: Border.all(color: AppTheme.borderSubtle),
                          ),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Row(
                                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                children: [
                                  const Text(
                                    'Colegio San Martín',
                                    style: TextStyle(
                                      fontSize: 12,
                                      fontWeight: FontWeight.w700,
                                      color: AppTheme.primaryNavy,
                                    ),
                                  ),
                                  // Selector de fecha
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
                                    child: Container(
                                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                                      decoration: BoxDecoration(
                                        color: const Color(0xFFF1F5F9),
                                        borderRadius: BorderRadius.circular(6),
                                      ),
                                      child: Row(
                                        mainAxisSize: MainAxisSize.min,
                                        children: [
                                          const Icon(Icons.calendar_today, size: 12, color: Color(0xFF475569)),
                                          const SizedBox(width: 4),
                                          Text(
                                            DateFormat('dd/MM/yyyy').format(_fechaSeleccionada),
                                            style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w700),
                                          ),
                                        ],
                                      ),
                                    ),
                                  ),
                                ],
                              ),
                              const SizedBox(height: 8),

                              // Dropdown de Curso / Sección
                              if (_asignaturas.isNotEmpty)
                                DropdownButtonHideUnderline(
                                  child: DropdownButton<Asignatura>(
                                    value: _cursoActivo,
                                    isDense: true,
                                    isExpanded: true,
                                    items: _asignaturas.map((a) {
                                      return DropdownMenuItem<Asignatura>(
                                        value: a,
                                        child: Text(
                                          '${a.nombre} — ${a.gradoSeccion}',
                                          style: const TextStyle(
                                            fontSize: 15,
                                            fontWeight: FontWeight.w800,
                                            color: AppTheme.primaryDark,
                                          ),
                                        ),
                                      );
                                    }).toList(),
                                    onChanged: (nueva) {
                                      if (nueva != null) _cambiarCurso(nueva);
                                    },
                                  ),
                                ),

                              const SizedBox(height: 4),
                              Text(
                                'Docente a cargo: $docenteNombre',
                                style: const TextStyle(fontSize: 12, color: Color(0xFF64748B)),
                              ),

                              const SizedBox(height: 14),
                              const Divider(height: 1, color: AppTheme.borderSubtle),
                              const SizedBox(height: 12),

                              // Quick Attendance Pill Summary Counter (Figma)
                              Row(
                                children: [
                                  Text(
                                    '${_estudiantes.length} Estudiantes',
                                    style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w700, color: Color(0xFF334155)),
                                  ),
                                  const Spacer(),
                                  _buildCounterPill('$_presentesCount Pres.', AppTheme.statusPresente, AppTheme.statusPresenteBg),
                                  const SizedBox(width: 6),
                                  _buildCounterPill('$_ausentesCount Aus.', AppTheme.statusAusente, AppTheme.statusAusenteBg),
                                  const SizedBox(width: 6),
                                  _buildCounterPill('$_justificadosCount Just.', AppTheme.statusJustificado, AppTheme.statusJustificadoBg),
                                ],
                              ),
                            ],
                          ),
                        ),

                        const SizedBox(height: 16),

                        // Título de la lista
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            const Text(
                              'Padrón de Alumnos',
                              style: TextStyle(
                                fontSize: 14,
                                fontWeight: FontWeight.w700,
                                color: AppTheme.primaryDark,
                              ),
                            ),
                            Text(
                              fechaFormatted,
                              style: const TextStyle(fontSize: 11, color: Color(0xFF64748B)),
                            ),
                          ],
                        ),

                        const SizedBox(height: 10),

                        // Lista de estudiantes con botones
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

                        const SizedBox(height: 80), // Espacio para el botón flotante
                      ],
                    ),
                  ),
                ),

                // Sticky Bottom Save Area (Figma)
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    boxShadow: [
                      BoxShadow(
                        color: Colors.black.withOpacity(0.05),
                        blurRadius: 10,
                        offset: const Offset(0, -4),
                      ),
                    ],
                  ),
                  child: SafeArea(
                    child: SizedBox(
                      width: double.infinity,
                      height: 48,
                      child: ElevatedButton(
                        onPressed: _isSaving ? null : _guardarAsistencia,
                        style: ElevatedButton.styleFrom(
                          backgroundColor: AppTheme.primaryNavy,
                          foregroundColor: Colors.white,
                          elevation: 0,
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                        ),
                        child: _isSaving
                            ? const SizedBox(width: 22, height: 22, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                            : const Text(
                                'Guardar Asistencia Oficial',
                                style: TextStyle(fontSize: 14, fontWeight: FontWeight.w700),
                              ),
                      ),
                    ),
                  ),
                ),
              ],
            ),
    );
  }

  Widget _buildCounterPill(String text, Color color, Color bg) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(6),
        border: Border.all(color: color.withOpacity(0.3)),
      ),
      child: Text(
        text,
        style: TextStyle(fontSize: 10, fontWeight: FontWeight.w700, color: color),
      ),
    );
  }

  Widget _buildStudentAttendanceRow(Estudiante est, String estadoActual, int correlativo) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: AppTheme.borderSubtle),
      ),
      child: Row(
        children: [
          // Número correlativo
          SizedBox(
            width: 24,
            child: Text(
              '$correlativo.',
              style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: Color(0xFF94A3B8)),
            ),
          ),

          // Nombre del alumno y NIE
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  est.nombreCompleto,
                  style: const TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.w700,
                    color: AppTheme.primaryDark,
                  ),
                ),
                Text(
                  'NIE: ${est.nie}',
                  style: const TextStyle(
                    fontSize: 10,
                    fontFamily: 'monospace',
                    color: Color(0xFF64748B),
                  ),
                ),
              ],
            ),
          ),

          const SizedBox(width: 8),

          // Botones Presente / Ausente / Justificado
          Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              _buildAttendanceStateButton(
                label: 'P',
                title: 'Presente',
                color: AppTheme.statusPresente,
                bg: AppTheme.statusPresenteBg,
                isSelected: estadoActual == 'Presente',
                onTap: () => setState(() => _asistenciaEstado[est.id] = 'Presente'),
              ),
              const SizedBox(width: 4),
              _buildAttendanceStateButton(
                label: 'A',
                title: 'Ausente',
                color: AppTheme.statusAusente,
                bg: AppTheme.statusAusenteBg,
                isSelected: estadoActual == 'Ausente',
                onTap: () => setState(() => _asistenciaEstado[est.id] = 'Ausente'),
              ),
              const SizedBox(width: 4),
              _buildAttendanceStateButton(
                label: 'J',
                title: 'Justificado',
                color: AppTheme.statusJustificado,
                bg: AppTheme.statusJustificadoBg,
                isSelected: estadoActual == 'Justificado',
                onTap: () => setState(() => _asistenciaEstado[est.id] = 'Justificado'),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildAttendanceStateButton({
    required String label,
    required String title,
    required Color color,
    required Color bg,
    required bool isSelected,
    required VoidCallback onTap,
  }) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(6),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 150),
        width: 34,
        height: 32,
        alignment: Alignment.center,
        decoration: BoxDecoration(
          color: isSelected ? color : const Color(0xFFF8FAFC),
          borderRadius: BorderRadius.circular(6),
          border: Border.all(
            color: isSelected ? color : const Color(0xFFE2E8F0),
            width: 1.2,
          ),
        ),
        child: Text(
          label,
          style: TextStyle(
            fontSize: 12,
            fontWeight: FontWeight.w800,
            color: isSelected ? Colors.white : const Color(0xFF64748B),
          ),
        ),
      ),
    );
  }
}
