import 'package:flutter/material.dart';
import '../models/models.dart';
import '../services/api_service.dart';
import '../theme/app_theme.dart';

class GradesScreen extends StatefulWidget {
  final Asignatura? selectedCourse;

  const GradesScreen({super.key, this.selectedCourse});

  @override
  State<GradesScreen> createState() => _GradesScreenState();
}

class _GradesScreenState extends State<GradesScreen> {
  List<Asignatura> _asignaturas = [];
  Asignatura? _cursoActivo;
  List<Periodo> _periodos = [];
  Periodo? _periodoActivo;
  List<Estudiante> _estudiantes = [];
  final Map<int, TextEditingController> _controllers = {};
  String _actividadSeleccionada = 'Actividad 1: Examen Parcial';
  bool _isLoading = true;
  bool _isSaving = false;
  Map<String, dynamic>? _currentUser;

  final List<String> _actividades = [
    'Actividad 1: Examen Parcial (35%)',
    'Actividad 2: Tareas y Guías (35%)',
    'Actividad 3: Proyecto Integrador (30%)',
  ];

  @override
  void initState() {
    super.initState();
    _initData();
  }

  @override
  void dispose() {
    for (var c in _controllers.values) {
      c.dispose();
    }
    super.dispose();
  }

  Future<void> _initData() async {
    setState(() => _isLoading = true);
    final user = await ApiService.getCurrentUser();
    final asignaturas = await ApiService.getAsignaturas();
    final periodos = await ApiService.getPeriodos();

    Asignatura? activo = widget.selectedCourse;
    if (activo == null && asignaturas.isNotEmpty) {
      activo = asignaturas.first;
    }

    Periodo? periodo = periodos.isNotEmpty ? periodos.first : null;

    List<Estudiante> estudiantes = [];
    if (activo != null) {
      estudiantes = await ApiService.getEstudiantes(gradoSeccion: activo.gradoSeccion);
    } else {
      estudiantes = await ApiService.getEstudiantes();
    }

    // Inicializar notas con valores realistas del prototipo Figma
    final sampleGrades = [8.5, 9.2, 5.0, 7.8, 6.5, 10.0, 8.0, 9.5];
    for (int i = 0; i < estudiantes.length; i++) {
      final val = (i < sampleGrades.length) ? sampleGrades[i].toStringAsFixed(1) : '8.0';
      _controllers[estudiantes[i].id] = TextEditingController(text: val);
    }

    if (!mounted) return;
    setState(() {
      _currentUser = user;
      _asignaturas = asignaturas;
      _cursoActivo = activo;
      _periodos = periodos;
      _periodoActivo = periodo;
      _estudiantes = estudiantes;
      _isLoading = false;
    });
  }

  double get _promedioGeneral {
    if (_estudiantes.isEmpty) return 0.0;
    double suma = 0.0;
    int validos = 0;
    for (var e in _estudiantes) {
      final text = _controllers[e.id]?.text ?? '0';
      final val = double.tryParse(text);
      if (val != null) {
        suma += val;
        validos++;
      }
    }
    return validos > 0 ? (suma / validos) : 0.0;
  }

  Future<void> _guardarNotas() async {
    if (_cursoActivo == null || _periodoActivo == null) return;

    if (!_periodoActivo!.estaAbierto) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          backgroundColor: AppTheme.statusAusente,
          content: Text('Acceso Denegado: Este período está cerrado y bloqueado por Dirección General.'),
        ),
      );
      return;
    }

    setState(() => _isSaving = true);
    int guardados = 0;
    for (var e in _estudiantes) {
      final text = _controllers[e.id]?.text ?? '0';
      final nota = double.tryParse(text) ?? 0.0;
      final ok = await ApiService.registrarCalificacion(
        estudianteId: e.id,
        asignaturaId: _cursoActivo!.id,
        periodoId: _periodoActivo!.id,
        nota: nota,
        tipoEvaluacion: _actividadSeleccionada,
      );
      if (ok) guardados++;
    }

    if (!mounted) return;
    setState(() => _isSaving = false);

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        backgroundColor: AppTheme.primaryNavy,
        content: Text('¡$guardados notas guardadas correctamente en la base de datos!'),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final docenteNombre = _currentUser?['nombre'] ?? 'Prof. Carlos Juan Pérez';
    final periodoAbierto = _periodoActivo?.estaAbierto ?? true;

    return Scaffold(
      backgroundColor: AppTheme.background,
      appBar: AppBar(
        title: const Text('Registro de Notas'),
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
                        // Top Header Box / Summary Card (Figma)
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
                                    'REGISTRO DE CALIFICACIONES',
                                    style: TextStyle(
                                      fontSize: 11,
                                      fontWeight: FontWeight.w800,
                                      letterSpacing: 0.5,
                                      color: AppTheme.primaryNavy,
                                    ),
                                  ),
                                  Container(
                                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                                    decoration: BoxDecoration(
                                      color: periodoAbierto ? AppTheme.statusPresenteBg : AppTheme.statusAusenteBg,
                                      borderRadius: BorderRadius.circular(6),
                                      border: Border.all(
                                        color: periodoAbierto ? AppTheme.statusPresente.withOpacity(0.3) : AppTheme.statusAusente.withOpacity(0.3),
                                      ),
                                    ),
                                    child: Text(
                                      periodoAbierto ? 'Período Abierto' : 'Período Bloqueado',
                                      style: TextStyle(
                                        fontSize: 10,
                                        fontWeight: FontWeight.w700,
                                        color: periodoAbierto ? AppTheme.statusPresente : AppTheme.statusAusente,
                                      ),
                                    ),
                                  ),
                                ],
                              ),
                              const SizedBox(height: 8),

                              // Dropdown de Asignatura
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
                                      if (nueva != null) {
                                        setState(() => _cursoActivo = nueva);
                                      }
                                    },
                                  ),
                                ),

                              const SizedBox(height: 4),
                              Text(
                                'Docente: $docenteNombre',
                                style: const TextStyle(fontSize: 12, color: Color(0xFF64748B)),
                              ),

                              const SizedBox(height: 14),
                              const Divider(height: 1, color: AppTheme.borderSubtle),
                              const SizedBox(height: 12),

                              // Selectores de Período y Actividad (Figma)
                              Row(
                                children: [
                                  // Selector Período
                                  Expanded(
                                    child: Column(
                                      crossAxisAlignment: CrossAxisAlignment.start,
                                      children: [
                                        const Text('Período Académico', style: TextStyle(fontSize: 11, fontWeight: FontWeight.w700, color: Color(0xFF64748B))),
                                        const SizedBox(height: 4),
                                        Container(
                                          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 2),
                                          decoration: BoxDecoration(
                                            color: const Color(0xFFF8FAFC),
                                            borderRadius: BorderRadius.circular(8),
                                            border: Border.all(color: AppTheme.borderSubtle),
                                          ),
                                          child: DropdownButtonHideUnderline(
                                            child: DropdownButton<Periodo>(
                                              value: _periodoActivo,
                                              isDense: true,
                                              isExpanded: true,
                                              items: _periodos.map((p) {
                                                return DropdownMenuItem(
                                                  value: p,
                                                  child: Text(p.nombre, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w700)),
                                                );
                                              }).toList(),
                                              onChanged: (p) => setState(() => _periodoActivo = p),
                                            ),
                                          ),
                                        ),
                                      ],
                                    ),
                                  ),
                                  const SizedBox(width: 10),

                                  // Selector Actividad
                                  Expanded(
                                    child: Column(
                                      crossAxisAlignment: CrossAxisAlignment.start,
                                      children: [
                                        const Text('Ponderación Activa', style: TextStyle(fontSize: 11, fontWeight: FontWeight.w700, color: Color(0xFF64748B))),
                                        const SizedBox(height: 4),
                                        Container(
                                          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 2),
                                          decoration: BoxDecoration(
                                            color: const Color(0xFFF8FAFC),
                                            borderRadius: BorderRadius.circular(8),
                                            border: Border.all(color: AppTheme.borderSubtle),
                                          ),
                                          child: DropdownButtonHideUnderline(
                                            child: DropdownButton<String>(
                                              value: _actividadSeleccionada,
                                              isDense: true,
                                              isExpanded: true,
                                              items: _actividades.map((a) {
                                                return DropdownMenuItem(
                                                  value: a,
                                                  child: Text(a.split(':')[0], style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w700)),
                                                );
                                              }).toList(),
                                              onChanged: (a) => setState(() => _actividadSeleccionada = a ?? _actividades.first),
                                            ),
                                          ),
                                        ),
                                      ],
                                    ),
                                  ),
                                ],
                              ),
                            ],
                          ),
                        ),

                        const SizedBox(height: 16),

                        // Header Lista de Estudiantes
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            const Text(
                              'Lista de Calificaciones',
                              style: TextStyle(fontSize: 14, fontWeight: FontWeight.w700, color: AppTheme.primaryDark),
                            ),
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                              decoration: BoxDecoration(
                                color: AppTheme.lightBlue,
                                borderRadius: BorderRadius.circular(6),
                              ),
                              child: Text(
                                'Promedio: ${_promedioGeneral.toStringAsFixed(1)}',
                                style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w800, color: AppTheme.primaryNavy),
                              ),
                            ),
                          ],
                        ),

                        const SizedBox(height: 10),

                        // Lista de estudiantes con input de nota
                        ListView.separated(
                          shrinkWrap: true,
                          physics: const NeverScrollableScrollPhysics(),
                          itemCount: _estudiantes.length,
                          separatorBuilder: (_, __) => const SizedBox(height: 8),
                          itemBuilder: (context, index) {
                            final est = _estudiantes[index];
                            final controller = _controllers[est.id];
                            return _buildStudentGradeRow(est, controller, index + 1, periodoAbierto);
                          },
                        ),

                        const SizedBox(height: 80),
                      ],
                    ),
                  ),
                ),

                // Bottom Action Card (Figma)
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
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            const Text(
                              'Calcula automáticamente el promedio parcial',
                              style: TextStyle(fontSize: 11, color: Color(0xFF64748B)),
                            ),
                            Text(
                              'Promedio: ${_promedioGeneral.toStringAsFixed(1)} / 10',
                              style: TextStyle(
                                fontSize: 12,
                                fontWeight: FontWeight.w800,
                                color: _promedioGeneral >= 6.0 ? AppTheme.statusPresente : AppTheme.statusAusente,
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 8),
                        SizedBox(
                          width: double.infinity,
                          height: 48,
                          child: ElevatedButton(
                            onPressed: (periodoAbierto && !_isSaving) ? _guardarNotas : null,
                            style: ElevatedButton.styleFrom(
                              backgroundColor: AppTheme.primaryNavy,
                              foregroundColor: Colors.white,
                              elevation: 0,
                              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                            ),
                            child: _isSaving
                                ? const SizedBox(width: 22, height: 22, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                                : Text(
                                    periodoAbierto ? 'Guardar Calificaciones Oficiales' : 'Trimestre Cerrado por Dirección',
                                    style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w700),
                                  ),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ],
            ),
    );
  }

  Widget _buildStudentGradeRow(Estudiante est, TextEditingController? controller, int correlativo, bool editable) {
    final notaVal = double.tryParse(controller?.text ?? '') ?? 0.0;
    Color gradeColor = AppTheme.statusPresente;
    Color gradeBg = AppTheme.statusPresenteBg;

    if (notaVal < 6.0) {
      gradeColor = AppTheme.statusAusente;
      gradeBg = AppTheme.statusAusenteBg;
    } else if (notaVal >= 9.5) {
      gradeColor = AppTheme.primaryNavy;
      gradeBg = AppTheme.lightBlue;
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: AppTheme.borderSubtle),
      ),
      child: Row(
        children: [
          SizedBox(
            width: 24,
            child: Text(
              '$correlativo.',
              style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: Color(0xFF94A3B8)),
            ),
          ),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  est.nombreCompleto,
                  style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: AppTheme.primaryDark),
                ),
                Text(
                  'NIE: ${est.nie}',
                  style: const TextStyle(fontSize: 10, fontFamily: 'monospace', color: Color(0xFF64748B)),
                ),
              ],
            ),
          ),
          const SizedBox(width: 10),

          // Input de Nota (Figma)
          Container(
            width: 70,
            height: 38,
            decoration: BoxDecoration(
              color: gradeBg,
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: gradeColor.withOpacity(0.3)),
            ),
            alignment: Alignment.center,
            child: TextField(
              controller: controller,
              enabled: editable,
              keyboardType: const TextInputType.numberWithOptions(decimal: true),
              textAlign: TextAlign.center,
              onChanged: (_) => setState(() {}),
              style: TextStyle(
                fontSize: 14,
                fontWeight: FontWeight.w800,
                color: gradeColor,
              ),
              decoration: const InputDecoration(
                border: InputBorder.none,
                isDense: true,
                contentPadding: EdgeInsets.zero,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
