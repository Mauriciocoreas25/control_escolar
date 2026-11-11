import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../models/models.dart';
import '../services/api_service.dart';
import '../theme/app_theme.dart';
import 'login_screen.dart';

class GradosScreen extends StatefulWidget {
  final Asignatura? selectedCourse;

  const GradosScreen({super.key, this.selectedCourse});

  @override
  State<GradosScreen> createState() => _GradosScreenState();
}

class _GradosScreenState extends State<GradosScreen> {
  Institucion? _institucion;
  List<Asignatura> _asignaturas = [];
  Asignatura? _cursoActivo;
  List<Periodo> _periodos = [];
  Periodo? _periodoActivo;
  List<Estudiante> _estudiantes = [];
  final Map<int, TextEditingController> _controllers = {};

  List<ActividadEvaluativa> _actividadesBD = [];
  String _actividadSeleccionada = 'Actividad 1: Examen Parcial (35%)';
  bool _isLoading = true;
  bool _isSaving = false;
  Map<String, dynamic>? _currentUser;

  final List<String> _actividadesEstandar = [
    'Actividad 1: Examen Parcial (35%)',
    'Actividad 2: Guías y Tareas (35%)',
    'Actividad 3: Proyecto Aplicado (30%)',
    'Evaluación de Recuperación (100%)',
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

  Future<void> _cargarActividadesYNotas() async {
    if (_cursoActivo == null || _periodoActivo == null) return;

    final acts = await ApiService.getActividades(
      asignaturaId: _cursoActivo!.id,
      periodoId: _periodoActivo!.id,
    );
    _actividadesBD = acts;

    final todasOpciones = _listaNombresActividades;
    if (!todasOpciones.contains(_actividadSeleccionada)) {
      _actividadSeleccionada = todasOpciones.isNotEmpty ? todasOpciones.first : 'Actividad 1: Examen Parcial (35%)';
    }

    final califs = await ApiService.getCalificaciones(
      asignaturaId: _cursoActivo!.id,
      periodoId: _periodoActivo!.id,
      tipoEvaluacion: _actividadSeleccionada,
    );

    final Map<int, double> notasExistentes = {
      for (var c in califs) c.estudianteId: c.nota,
    };

    for (var e in _estudiantes) {
      final notaGuardada = notasExistentes[e.id];
      final valorTexto = notaGuardada != null ? notaGuardada.toStringAsFixed(1) : '';
      if (_controllers.containsKey(e.id)) {
        _controllers[e.id]!.text = valorTexto;
      } else {
        _controllers[e.id] = TextEditingController(text: valorTexto);
      }
    }
  }

  List<String> get _listaNombresActividades {
    final list = <String>[];
    for (var a in _actividadesBD) {
      list.add(a.displayName);
    }
    for (var e in _actividadesEstandar) {
      if (!list.contains(e)) {
        list.add(e);
      }
    }
    return list;
  }

  ActividadEvaluativa? get _actividadBDSeleccionada {
    try {
      return _actividadesBD.firstWhere((a) => a.displayName == _actividadSeleccionada);
    } catch (_) {
      return null;
    }
  }

  Future<void> _cambiarActividad(String nuevaActividad) async {
    if (nuevaActividad == _actividadSeleccionada) return;
    setState(() {
      _actividadSeleccionada = nuevaActividad;
      _isLoading = true;
    });
    await _cargarActividadesYNotas();
    if (!mounted) return;
    setState(() => _isLoading = false);
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

    final periodos = await ApiService.getPeriodos();

    Asignatura? activo;
    if (widget.selectedCourse != null) {
      activo = asignaturas.firstWhere(
        (a) => a.id == widget.selectedCourse!.id,
        orElse: () => widget.selectedCourse!,
      );
    } else if (asignaturas.isNotEmpty) {
      activo = asignaturas.first;
    }

    Periodo? periodo;
    if (periodos.isNotEmpty) {
      periodo = periodos.firstWhere(
        (p) => p.estaAbierto && p.nombre.contains('2026'),
        orElse: () => periodos.firstWhere(
          (p) => p.estaAbierto,
          orElse: () => periodos.first,
        ),
      );
    }

    List<Estudiante> estudiantes = [];
    if (activo != null) {
      estudiantes = await ApiService.getEstudiantes(gradoSeccion: activo.gradoSeccion);
    }

    _currentUser = user;
    _institucion = inst;
    _asignaturas = asignaturas;
    _cursoActivo = activo;
    _periodos = periodos;
    _periodoActivo = periodo;
    _estudiantes = estudiantes;

    _controllers.clear();
    await _cargarActividadesYNotas();

    if (!mounted) return;
    setState(() {
      _isLoading = false;
    });
  }

  Future<void> _cambiarCursoOPeriodo({Asignatura? nuevoCurso, Periodo? nuevoPeriodo}) async {
    final curso = nuevoCurso ?? _cursoActivo;
    final periodo = nuevoPeriodo ?? _periodoActivo;

    setState(() {
      _cursoActivo = curso;
      _periodoActivo = periodo;
      _isLoading = true;
    });

    List<Estudiante> estudiantes = [];
    if (curso != null) {
      estudiantes = await ApiService.getEstudiantes(gradoSeccion: curso.gradoSeccion);
    }

    _estudiantes = estudiantes;
    _controllers.clear();
    await _cargarActividadesYNotas();

    if (!mounted) return;
    setState(() {
      _isLoading = false;
    });
  }

  double get _promedioGeneral {
    if (_estudiantes.isEmpty) return 0.0;
    double suma = 0.0;
    int validos = 0;
    for (var e in _estudiantes) {
      final text = _controllers[e.id]?.text.trim() ?? '';
      if (text.isNotEmpty) {
        final val = double.tryParse(text);
        if (val != null) {
          suma += val;
          validos++;
        }
      }
    }
    return validos > 0 ? (suma / validos) : 0.0;
  }

  Future<void> _mostrarDialogoCrearActividad() async {
    if (_cursoActivo == null || _periodoActivo == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Debe seleccionar un curso y período primero.')),
      );
      return;
    }

    final nombreCtrl = TextEditingController();
    final ponderacionCtrl = TextEditingController(text: '25');
    String tipoSeleccionado = 'Tarea';
    final tiposDisponibles = ['Examen', 'Tarea', 'Guía', 'Laboratorio', 'Proyecto', 'Otro'];

    final res = await showDialog<bool>(
      context: context,
      builder: (ctx) {
        return StatefulBuilder(
          builder: (dialogCtx, setDialogState) {
            return AlertDialog(
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
              title: Row(
                children: const [
                  Icon(Icons.add_task_rounded, color: AppTheme.primaryNavy, size: 24),
                  SizedBox(width: 8),
                  Text('Nueva Evaluación', style: TextStyle(fontWeight: FontWeight.w800, fontSize: 17)),
                ],
              ),
              content: SingleChildScrollView(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Asignatura: ${_cursoActivo!.nombre} (${_cursoActivo!.gradoSeccion})',
                      style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: AppTheme.primaryNavy),
                    ),
                    const SizedBox(height: 16),
                    const Text('Tipo de Actividad:', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: Color(0xFF64748B))),
                    const SizedBox(height: 6),
                    DropdownButtonFormField<String>(
                      value: tipoSeleccionado,
                      decoration: InputDecoration(
                        isDense: true,
                        contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                        border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
                      ),
                      items: tiposDisponibles.map((t) => DropdownMenuItem(value: t, child: Text(t))).toList(),
                      onChanged: (val) {
                        if (val != null) setDialogState(() => tipoSeleccionado = val);
                      },
                    ),
                    const SizedBox(height: 14),
                    const Text('Nombre de la Actividad:', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: Color(0xFF64748B))),
                    const SizedBox(height: 6),
                    TextField(
                      controller: nombreCtrl,
                      decoration: InputDecoration(
                        hintText: 'Ej. Guía #2: Trigonometría, Examen 1',
                        isDense: true,
                        contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                        border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
                      ),
                    ),
                    const SizedBox(height: 14),
                    const Text('Ponderación (%) :', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: Color(0xFF64748B))),
                    const SizedBox(height: 6),
                    TextField(
                      controller: ponderacionCtrl,
                      keyboardType: const TextInputType.numberWithOptions(decimal: true),
                      inputFormatters: [FilteringTextInputFormatter.allow(RegExp(r'^\d{0,3}(\.\d{0,2})?'))],
                      decoration: InputDecoration(
                        hintText: 'Ej. 25, 30, 35',
                        suffixText: '%',
                        isDense: true,
                        contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                        border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
                      ),
                    ),
                  ],
                ),
              ),
              actions: [
                TextButton(
                  onPressed: () => Navigator.pop(ctx, false),
                  child: const Text('Cancelar', style: TextStyle(color: Color(0xFF64748B), fontWeight: FontWeight.w600)),
                ),
                ElevatedButton(
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppTheme.primaryNavy,
                    foregroundColor: Colors.white,
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                  ),
                  onPressed: () {
                    if (nombreCtrl.text.trim().isEmpty) return;
                    Navigator.pop(ctx, true);
                  },
                  child: const Text('Crear Actividad', style: TextStyle(fontWeight: FontWeight.bold)),
                ),
              ],
            );
          },
        );
      },
    );

    if (res == true && nombreCtrl.text.trim().isNotEmpty) {
      final pond = double.tryParse(ponderacionCtrl.text.trim()) ?? 0.0;
      final act = await ApiService.crearActividad(
        asignaturaId: _cursoActivo!.id,
        periodoId: _periodoActivo!.id,
        nombre: '$tipoSeleccionado: ${nombreCtrl.text.trim()}',
        tipo: tipoSeleccionado,
        ponderacion: pond,
      );

      if (act != null) {
        setState(() {
          _actividadSeleccionada = act.displayName;
          _isLoading = true;
        });
        await _cargarActividadesYNotas();
        if (!mounted) return;
        setState(() => _isLoading = false);

        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            backgroundColor: AppTheme.statusPresente,
            content: Text('¡Actividad "${act.nombre}" creada exitosamente!'),
          ),
        );
      }
    }
  }

  Future<void> _eliminarActividadActual() async {
    final act = _actividadBDSeleccionada;
    if (act == null) return;

    final confirm = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(18)),
        title: const Text('¿Eliminar evaluación?', style: TextStyle(fontWeight: FontWeight.w800)),
        content: Text('Se eliminará la actividad "${act.nombre}" de esta asignatura.'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Cancelar')),
          ElevatedButton(
            style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFFDC2626), foregroundColor: Colors.white),
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text('Eliminar'),
          ),
        ],
      ),
    );

    if (confirm == true) {
      setState(() => _isLoading = true);
      await ApiService.eliminarActividad(act.id);
      _actividadSeleccionada = _actividadesEstandar.first;
      await _cargarActividadesYNotas();
      if (!mounted) return;
      setState(() => _isLoading = false);
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Actividad eliminada.')),
      );
    }
  }

  Future<void> _guardarNotas() async {
    if (_cursoActivo == null || _periodoActivo == null || _estudiantes.isEmpty) return;

    setState(() => _isSaving = true);
    int guardados = 0;
    int fallidos = 0;
    for (var e in _estudiantes) {
      final text = _controllers[e.id]?.text.trim() ?? '';
      if (text.isEmpty) continue;
      final nota = double.tryParse(text.replaceAll(',', '.'));
      if (nota == null || nota < 0 || nota > 10) continue;
      final ok = await ApiService.registrarCalificacion(
        estudianteId: e.id,
        asignaturaId: _cursoActivo!.id,
        periodoId: _periodoActivo!.id,
        nota: nota,
        tipoEvaluacion: _actividadSeleccionada,
      );
      if (ok) {
        guardados++;
      } else {
        fallidos++;
      }
    }

    if (!mounted) return;
    setState(() => _isSaving = false);

    if (fallidos > 0 && guardados == 0) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          backgroundColor: Colors.redAccent,
          content: Text('Error al guardar ($fallidos notas no enviadas). Verifique que el servidor (${ApiService.baseUrl}) esté activo.'),
        ),
      );
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          backgroundColor: AppTheme.primaryNavy,
          content: Text('¡Calificaciones guardadas exitosamente! ($guardados notas registradas)'),
        ),
      );
    }
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
    final periodoAbierto = _periodoActivo?.estaAbierto ?? true;
    final esActividadCustom = _actividadBDSeleccionada != null;

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
                                        'Registro de Calificaciones',
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

                            // Tarjeta Glassmorphic de Control Académico y Promedio
                            GlassContainer(
                              borderRadius: 20,
                              blur: 18,
                              padding: const EdgeInsets.all(18),
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Row(
                                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                    children: [
                                      const Text(
                                        'ASIGNATURA & PERÍODO',
                                        style: TextStyle(
                                          fontSize: 10.5,
                                          fontWeight: FontWeight.w800,
                                          letterSpacing: 0.6,
                                          color: AppTheme.primaryNavy,
                                        ),
                                      ),
                                      Container(
                                        padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 4),
                                        decoration: BoxDecoration(
                                          gradient: periodoAbierto ? AppTheme.emeraldGradient : AppTheme.roseGradient,
                                          borderRadius: BorderRadius.circular(12),
                                          boxShadow: [
                                            BoxShadow(
                                              color: (periodoAbierto ? AppTheme.statusPresente : AppTheme.statusAusente).withOpacity(0.3),
                                              blurRadius: 6,
                                              offset: const Offset(0, 2),
                                            ),
                                          ],
                                        ),
                                        child: Text(
                                          periodoAbierto ? 'Período Habilitado' : 'Período Bloqueado',
                                          style: const TextStyle(
                                            fontSize: 10,
                                            fontWeight: FontWeight.w800,
                                            color: Colors.white,
                                          ),
                                        ),
                                      ),
                                    ],
                                  ),

                                  const SizedBox(height: 10),

                                  if (_asignaturas.isNotEmpty)
                                    DropdownButtonHideUnderline(
                                      child: DropdownButton<Asignatura>(
                                        value: _cursoActivo,
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
                                          if (nueva != null) _cambiarCursoOPeriodo(nuevoCurso: nueva);
                                        },
                                      ),
                                    )
                                  else
                                    const Text(
                                      'No tiene asignaturas asignadas',
                                      style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold),
                                    ),

                                  const SizedBox(height: 4),
                                  Text(
                                    'Docente a cargo: $docenteNombre',
                                    style: const TextStyle(fontSize: 12, color: Color(0xFF64748B), fontWeight: FontWeight.w500),
                                  ),

                                  const SizedBox(height: 14),
                                  const Divider(height: 1, color: AppTheme.borderSubtle),
                                  const SizedBox(height: 12),

                                  Row(
                                    children: [
                                      Expanded(
                                        child: Column(
                                          crossAxisAlignment: CrossAxisAlignment.start,
                                          children: [
                                            const Text(
                                              'Período Lectivo',
                                              style: TextStyle(fontSize: 11, fontWeight: FontWeight.w700, color: Color(0xFF64748B)),
                                            ),
                                            const SizedBox(height: 4),
                                            if (_periodos.isNotEmpty)
                                              DropdownButtonHideUnderline(
                                                child: DropdownButton<Periodo>(
                                                  value: _periodoActivo,
                                                  isDense: true,
                                                  items: _periodos.map((p) {
                                                    return DropdownMenuItem<Periodo>(
                                                      value: p,
                                                      child: Text(
                                                        '${p.nombre} (${p.estado})',
                                                        style: const TextStyle(fontSize: 12.5, fontWeight: FontWeight.w800),
                                                      ),
                                                    );
                                                  }).toList(),
                                                  onChanged: (p) {
                                                    if (p != null) _cambiarCursoOPeriodo(nuevoPeriodo: p);
                                                  },
                                                ),
                                              )
                                            else
                                              const Text('Trimestre 1 (Abierto)', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
                                          ],
                                        ),
                                      ),

                                      // Badge de Promedio de la Sección con Glassmorphism y Sombra
                                      Container(
                                        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                                        decoration: BoxDecoration(
                                          gradient: LinearGradient(
                                            colors: [
                                              AppTheme.primaryNavy.withOpacity(0.08),
                                              AppTheme.accentBlue.withOpacity(0.12),
                                            ],
                                          ),
                                          borderRadius: BorderRadius.circular(14),
                                          border: Border.all(color: AppTheme.accentBlue.withOpacity(0.2)),
                                        ),
                                        child: Column(
                                          children: [
                                            const Text(
                                              'Promedio Sección',
                                              style: TextStyle(fontSize: 9.5, fontWeight: FontWeight.w800, color: AppTheme.primaryNavy),
                                            ),
                                            Text(
                                              _promedioGeneral.toStringAsFixed(1),
                                              style: const TextStyle(
                                                fontSize: 20,
                                                fontWeight: FontWeight.w900,
                                                color: AppTheme.primaryNavy,
                                                letterSpacing: -0.5,
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

                            // Selector y Creación de Evaluaciones (Glassmorphic)
                            GlassContainer(
                              borderRadius: 18,
                              blur: 16,
                              padding: const EdgeInsets.all(16),
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Row(
                                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                    children: [
                                      Row(
                                        children: const [
                                          Icon(Icons.assessment_rounded, size: 16, color: AppTheme.primaryNavy),
                                          SizedBox(width: 6),
                                          Text(
                                            'EVALUACIÓN A CALIFICAR',
                                            style: TextStyle(
                                              fontSize: 10.5,
                                              fontWeight: FontWeight.w800,
                                              letterSpacing: 0.6,
                                              color: AppTheme.primaryNavy,
                                            ),
                                          ),
                                        ],
                                      ),
                                      InkWell(
                                        onTap: _mostrarDialogoCrearActividad,
                                        borderRadius: BorderRadius.circular(8),
                                        child: Container(
                                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                                          decoration: BoxDecoration(
                                            color: AppTheme.primaryNavy.withOpacity(0.08),
                                            borderRadius: BorderRadius.circular(8),
                                          ),
                                          child: Row(
                                            mainAxisSize: MainAxisSize.min,
                                            children: const [
                                              Icon(Icons.add_circle_outline_rounded, size: 14, color: AppTheme.primaryNavy),
                                              SizedBox(width: 4),
                                              Text(
                                                '+ Nueva Actividad',
                                                style: TextStyle(fontSize: 11, fontWeight: FontWeight.w800, color: AppTheme.primaryNavy),
                                              ),
                                            ],
                                          ),
                                        ),
                                      ),
                                    ],
                                  ),
                                  const SizedBox(height: 8),
                                  Row(
                                    children: [
                                      Expanded(
                                        child: DropdownButtonHideUnderline(
                                          child: DropdownButton<String>(
                                            value: _actividadSeleccionada,
                                            isDense: true,
                                            isExpanded: true,
                                            icon: const Icon(Icons.keyboard_arrow_down_rounded, color: AppTheme.primaryNavy),
                                            items: _listaNombresActividades.map((act) {
                                              return DropdownMenuItem<String>(
                                                value: act,
                                                child: Text(
                                                  act,
                                                  style: const TextStyle(fontSize: 13.5, fontWeight: FontWeight.w800, color: AppTheme.primaryDark),
                                                  overflow: TextOverflow.ellipsis,
                                                ),
                                              );
                                            }).toList(),
                                            onChanged: (val) {
                                              if (val != null) _cambiarActividad(val);
                                            },
                                          ),
                                        ),
                                      ),
                                      if (esActividadCustom)
                                        IconButton(
                                          icon: const Icon(Icons.delete_outline_rounded, size: 19, color: Color(0xFFDC2626)),
                                          tooltip: 'Eliminar esta evaluación',
                                          visualDensity: VisualDensity.compact,
                                          onPressed: _eliminarActividadActual,
                                        ),
                                    ],
                                  ),
                                ],
                              ),
                            ),

                            const SizedBox(height: 18),

                            // Título de la Lista de Estudiantes
                            Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                const Text(
                                  'Estudiantes del Curso',
                                  style: TextStyle(
                                    fontSize: 14.5,
                                    fontWeight: FontWeight.w800,
                                    color: AppTheme.primaryDark,
                                  ),
                                ),
                                Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                                  decoration: BoxDecoration(
                                    color: const Color(0xFFF1F5F9),
                                    borderRadius: BorderRadius.circular(8),
                                  ),
                                  child: Text(
                                    '${_estudiantes.length} alumnos',
                                    style: const TextStyle(fontSize: 11.5, color: Color(0xFF64748B), fontWeight: FontWeight.w700),
                                  ),
                                ),
                              ],
                            ),

                            const SizedBox(height: 12),

                            if (_estudiantes.isEmpty)
                              GlassContainer(
                                borderRadius: 18,
                                padding: const EdgeInsets.all(32),
                                child: const Center(
                                  child: Text(
                                    'No hay alumnos registrados en esta sección.',
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
                                  return _buildStudentGradeRow(est, index + 1, periodoAbierto);
                                },
                              ),

                            const SizedBox(height: 85),
                          ],
                        ),
                      ),
                    ),

                    // Barra Inferior Flotante Glassmorphic
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
                        child: Column(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                const Text(
                                  'Cálculo dinámico en tiempo real',
                                  style: TextStyle(fontSize: 11, color: Color(0xFF64748B)),
                                ),
                                Text(
                                  periodoAbierto ? "Edición Habilitada" : "Bloqueado",
                                  style: TextStyle(
                                    fontSize: 11,
                                    fontWeight: FontWeight.w800,
                                    color: periodoAbierto ? AppTheme.statusPresente : AppTheme.statusAusente,
                                  ),
                                ),
                              ],
                            ),
                            const SizedBox(height: 8),
                            Container(
                              width: double.infinity,
                              height: 48,
                              decoration: BoxDecoration(
                                gradient: (periodoAbierto && !_isSaving && _estudiantes.isNotEmpty) ? AppTheme.buttonGradient : null,
                                color: (periodoAbierto && !_isSaving && _estudiantes.isNotEmpty) ? null : const Color(0xFFCBD5E1),
                                borderRadius: BorderRadius.circular(14),
                                boxShadow: (periodoAbierto && !_isSaving && _estudiantes.isNotEmpty)
                                    ? [
                                        BoxShadow(
                                          color: const Color(0xFF2563EB).withOpacity(0.35),
                                          blurRadius: 14,
                                          offset: const Offset(0, 4),
                                        ),
                                      ]
                                    : null,
                              ),
                              child: Material(
                                color: Colors.transparent,
                                child: InkWell(
                                  borderRadius: BorderRadius.circular(14),
                                  onTap: (periodoAbierto && !_isSaving && _estudiantes.isNotEmpty) ? _guardarNotas : null,
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
                                                'Guardar Calificaciones',
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
                          ],
                        ),
                      ),
                    ),
                  ],
                ),
        ),
      ),
    );
  }

  Widget _buildStudentGradeRow(
    Estudiante est,
    int correlativo,
    bool periodoAbierto,
  ) {
    final controller = _controllers.putIfAbsent(est.id, () => TextEditingController());
    final text = controller.text.trim();
    final valorNota = double.tryParse(text);
    final tieneNota = valorNota != null;
    final esAprobada = !tieneNota || valorNota >= 6.0;

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
          const SizedBox(width: 12),

          // Casilla de Nota con Borde y Color Inteligente
          SizedBox(
            width: 76,
            child: TextField(
              controller: controller,
              enabled: periodoAbierto,
              keyboardType: const TextInputType.numberWithOptions(decimal: true),
              inputFormatters: [
                FilteringTextInputFormatter.allow(RegExp(r'^\d{0,2}([.,]\d{0,2})?')),
              ],
              textAlign: TextAlign.center,
              style: TextStyle(
                fontSize: 15,
                fontWeight: FontWeight.w900,
                color: !tieneNota
                    ? AppTheme.primaryNavy
                    : (esAprobada ? AppTheme.statusPresente : AppTheme.statusAusente),
              ),
              onChanged: (text) {
                final clean = text.replaceAll(',', '.');
                final numVal = double.tryParse(clean);
                if (numVal != null && numVal > 10.0) {
                  controller.text = '10.0';
                  controller.selection = TextSelection.fromPosition(TextPosition(offset: controller.text.length));
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(
                      content: Text('La calificación máxima permitida es 10.0.'),
                      backgroundColor: Colors.orange,
                      duration: Duration(milliseconds: 1500),
                    ),
                  );
                }
                setState(() {});
              },
              decoration: InputDecoration(
                hintText: '0.0 - 10',
                hintStyle: const TextStyle(
                  color: Color(0xFF94A3B8),
                  fontSize: 11,
                  fontWeight: FontWeight.normal,
                ),
                contentPadding: const EdgeInsets.symmetric(horizontal: 8, vertical: 8),
                isDense: true,
                filled: true,
                fillColor: periodoAbierto ? Colors.white : const Color(0xFFF8FAFC),
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(10),
                  borderSide: BorderSide(
                    color: !tieneNota
                        ? AppTheme.borderSubtle
                        : (esAprobada ? AppTheme.statusPresente : AppTheme.statusAusente),
                    width: 1.5,
                  ),
                ),
                enabledBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(10),
                  borderSide: BorderSide(
                    color: !tieneNota
                        ? AppTheme.borderSubtle
                        : (esAprobada ? AppTheme.statusPresente : AppTheme.statusAusente),
                    width: 1.5,
                  ),
                ),
                focusedBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(10),
                  borderSide: const BorderSide(
                    color: AppTheme.accentBlue,
                    width: 2,
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
