import 'package:flutter/material.dart';
import '../models/models.dart';
import '../services/api_service.dart';
import '../theme/app_theme.dart';
import 'login_screen.dart';

class HorarioDocenteScreen extends StatefulWidget {
  final Function(int tabIndex, {Asignatura? asignatura})? onNavigateTab;

  const HorarioDocenteScreen({super.key, this.onNavigateTab});

  @override
  State<HorarioDocenteScreen> createState() => _HorarioDocenteScreenState();
}

class _HorarioDocenteScreenState extends State<HorarioDocenteScreen> {
  final List<String> _diasSemana = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes'];
  String _diaSeleccionado = 'Lunes';

  bool _isLoading = true;
  List<HorarioClase> _todosHorarios = [];
  List<Asignatura> _asignaturasDocente = [];
  Map<String, dynamic>? _currentUser;
  Institucion? _institucion;

  @override
  void initState() {
    super.initState();
    _determinarDiaActual();
    _loadData();
  }

  void _determinarDiaActual() {
    final now = DateTime.now();
    switch (now.weekday) {
      case DateTime.monday:
        _diaSeleccionado = 'Lunes';
        break;
      case DateTime.tuesday:
        _diaSeleccionado = 'Martes';
        break;
      case DateTime.wednesday:
        _diaSeleccionado = 'Miércoles';
        break;
      case DateTime.thursday:
        _diaSeleccionado = 'Jueves';
        break;
      case DateTime.friday:
        _diaSeleccionado = 'Viernes';
        break;
      default:
        _diaSeleccionado = 'Lunes';
        break;
    }
  }

  Future<void> _loadData() async {
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
    final docenteNombre = user['nombre']?.toString() ?? '';
    final rol = user['rol']?.toString().toLowerCase() ?? 'profesor';

    // Obtener asignaturas del docente para enlazar con asistencia/notas
    List<Asignatura> asignaturas = [];
    if (rol == 'director' || rol == 'administrador') {
      asignaturas = await ApiService.getAsignaturas();
    } else if (docenteNombre.isNotEmpty) {
      asignaturas = await ApiService.getAsignaturas(profesorNombre: docenteNombre);
    }

    // Obtener horarios asignados
    List<HorarioClase> horarios = [];
    if (rol == 'director' || rol == 'administrador') {
      horarios = await ApiService.getHorarios();
    } else {
      horarios = await ApiService.getHorarios(profesorNombre: docenteNombre);
    }

    // Orden cronológico por hora de inicio
    horarios.sort((a, b) => a.horaInicio.compareTo(b.horaInicio));

    if (mounted) {
      setState(() {
        _currentUser = user;
        _institucion = inst;
        _asignaturasDocente = asignaturas;
        _todosHorarios = horarios;
        _isLoading = false;
      });
    }
  }

  List<HorarioClase> get _horariosDelDia {
    final normSeleccion = _diaSeleccionado.toLowerCase().replaceAll('é', 'e');
    return _todosHorarios.where((h) {
      final diaNorm = h.diaSemana.toLowerCase().replaceAll('é', 'e');
      return diaNorm == normSeleccion;
    }).toList();
  }

  Asignatura? _encontrarAsignaturaCoincidente(HorarioClase horario) {
    if (_asignaturasDocente.isEmpty) return null;

    final normGrado = horario.gradoSeccion.replaceAll('º', '°').toLowerCase().trim();
    final normMateria = horario.materiaNombre.toLowerCase().trim();

    // 1. Intento por ID exacto de materia
    try {
      final match = _asignaturasDocente.firstWhere((a) => a.id == horario.materiaId);
      return match;
    } catch (_) {}

    // 2. Intento por grado/sección y nombre
    try {
      final match = _asignaturasDocente.firstWhere(
        (a) =>
            a.gradoSeccion.replaceAll('º', '°').toLowerCase().trim() == normGrado &&
            a.nombre.toLowerCase().trim() == normMateria,
      );
      return match;
    } catch (_) {}

    // 3. Intento por coincidencia de nombre
    try {
      final match = _asignaturasDocente.firstWhere(
        (a) => a.nombre.toLowerCase().trim() == normMateria,
      );
      return match;
    } catch (_) {}

    return _asignaturasDocente.isNotEmpty ? _asignaturasDocente.first : null;
  }

  void _mostrarDetalleClase(HorarioClase horario) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (ctx) => _DetalleClaseModal(
        horario: horario,
        asignaturaCoincidente: _encontrarAsignaturaCoincidente(horario),
        onTomarAsistencia: (asig) {
          Navigator.pop(ctx);
          if (widget.onNavigateTab != null) {
            // Tab 2 es Asistencia
            widget.onNavigateTab!(2, asignatura: asig);
          }
        },
        onAsignarNotas: (asig) {
          Navigator.pop(ctx);
          if (widget.onNavigateTab != null) {
            // Tab 3 es Calificaciones
            widget.onNavigateTab!(3, asignatura: asig);
          }
        },
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final docenteNombre = _currentUser?['nombre'] ?? 'Docente';
    final nombreEscuela = _institucion?.nombre ?? 'Complejo Educativo Santa Sofía';
    final anioActivo = _institucion?.anioLectivo ?? '2026';

    return Scaffold(
      backgroundColor: Colors.transparent,
      body: AmbientBackground(
        child: SafeArea(
          child: _isLoading
              ? const Center(child: CircularProgressIndicator(color: AppTheme.primaryNavy))
              : RefreshIndicator(
                  color: AppTheme.primaryNavy,
                  onRefresh: _loadData,
                  child: SingleChildScrollView(
                    physics: const AlwaysScrollableScrollPhysics(),
                    padding: const EdgeInsets.fromLTRB(18, 14, 18, 96),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        // Encabezado
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Row(
                                    children: [
                                      Container(
                                        padding: const EdgeInsets.all(5),
                                        decoration: BoxDecoration(
                                          color: AppTheme.primaryNavy.withOpacity(0.1),
                                          shape: BoxShape.circle,
                                        ),
                                        child: const Icon(Icons.school_rounded, size: 14, color: AppTheme.primaryNavy),
                                      ),
                                      const SizedBox(width: 6),
                                      Expanded(
                                        child: Text(
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
                                      ),
                                    ],
                                  ),
                                  const SizedBox(height: 2),
                                  const Text(
                                    'Mi Horario Semanal',
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
                            IconButton(
                              icon: const Icon(Icons.refresh_rounded, size: 21, color: AppTheme.primaryDark),
                              tooltip: 'Actualizar Horario',
                              onPressed: _loadData,
                            ),
                          ],
                        ),

                        const SizedBox(height: 14),

                        // Tarjeta Resumen del Docente
                        GlassContainer(
                          borderRadius: 20,
                          blur: 18,
                          padding: const EdgeInsets.all(16),
                          child: Row(
                            children: [
                              Container(
                                width: 44,
                                height: 44,
                                decoration: BoxDecoration(
                                  gradient: AppTheme.buttonGradient,
                                  borderRadius: BorderRadius.circular(12),
                                ),
                                alignment: Alignment.center,
                                child: const Icon(Icons.schedule_rounded, color: Colors.white, size: 22),
                              ),
                              const SizedBox(width: 14),
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(
                                      docenteNombre,
                                      maxLines: 1,
                                      overflow: TextOverflow.ellipsis,
                                      style: const TextStyle(
                                        fontSize: 14.5,
                                        fontWeight: FontWeight.w800,
                                        color: AppTheme.primaryDark,
                                      ),
                                    ),
                                    const SizedBox(height: 2),
                                    Text(
                                      '${_todosHorarios.length} bloques asignados • Ciclo $anioActivo',
                                      style: const TextStyle(
                                        fontSize: 11.5,
                                        color: Color(0xFF64748B),
                                        fontWeight: FontWeight.w500,
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                            ],
                          ),
                        ),

                        const SizedBox(height: 16),

                        // Selector de Días de la Semana
                        SizedBox(
                          height: 44,
                          child: ListView.separated(
                            scrollDirection: Axis.horizontal,
                            itemCount: _diasSemana.length,
                            separatorBuilder: (_, __) => const SizedBox(width: 8),
                            itemBuilder: (ctx, idx) {
                              final dia = _diasSemana[idx];
                              final isSelected = _diaSeleccionado == dia;
                              final norm = dia.toLowerCase().replaceAll('é', 'e');
                              final conteo = _todosHorarios.where((h) => h.diaSemana.toLowerCase().replaceAll('é', 'e') == norm).length;

                              return InkWell(
                                onTap: () => setState(() => _diaSeleccionado = dia),
                                borderRadius: BorderRadius.circular(12),
                                child: Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                                  decoration: BoxDecoration(
                                    gradient: isSelected ? AppTheme.primaryGradient : null,
                                    color: isSelected ? null : Colors.white.withOpacity(0.80),
                                    borderRadius: BorderRadius.circular(12),
                                    border: Border.all(
                                      color: isSelected ? Colors.transparent : AppTheme.borderSubtle,
                                      width: 1,
                                    ),
                                    boxShadow: isSelected
                                        ? [
                                            BoxShadow(
                                              color: const Color(0xFF1E3A8A).withOpacity(0.25),
                                              blurRadius: 10,
                                              offset: const Offset(0, 4),
                                            ),
                                          ]
                                        : null,
                                  ),
                                  child: Row(
                                    mainAxisSize: MainAxisSize.min,
                                    children: [
                                      Text(
                                        dia,
                                        style: TextStyle(
                                          fontSize: 12.5,
                                          fontWeight: isSelected ? FontWeight.w800 : FontWeight.w600,
                                          color: isSelected ? Colors.white : AppTheme.primaryDark,
                                        ),
                                      ),
                                      const SizedBox(width: 6),
                                      Container(
                                        padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 1.5),
                                        decoration: BoxDecoration(
                                          color: isSelected ? Colors.white.withOpacity(0.25) : const Color(0xFFF1F5F9),
                                          borderRadius: BorderRadius.circular(8),
                                        ),
                                        child: Text(
                                          '$conteo',
                                          style: TextStyle(
                                            fontSize: 10.5,
                                            fontWeight: FontWeight.w800,
                                            color: isSelected ? Colors.white : const Color(0xFF475569),
                                          ),
                                        ),
                                      ),
                                    ],
                                  ),
                                ),
                              );
                            },
                          ),
                        ),

                        const SizedBox(height: 18),

                        // Subtítulo con el día y conteo
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Text(
                              'Clases de $_diaSeleccionado',
                              style: const TextStyle(
                                fontSize: 14.5,
                                fontWeight: FontWeight.w800,
                                color: AppTheme.primaryDark,
                              ),
                            ),
                            Text(
                              '${_horariosDelDia.length} programadas',
                              style: const TextStyle(
                                fontSize: 12,
                                fontWeight: FontWeight.w600,
                                color: Color(0xFF64748B),
                              ),
                            ),
                          ],
                        ),

                        const SizedBox(height: 12),

                        // Lista de Clases del Día
                        if (_horariosDelDia.isEmpty)
                          GlassContainer(
                            borderRadius: 18,
                            blur: 14,
                            padding: const EdgeInsets.symmetric(vertical: 36, horizontal: 20),
                            child: Center(
                              child: Column(
                                children: [
                                  Container(
                                    padding: const EdgeInsets.all(12),
                                    decoration: BoxDecoration(
                                      color: const Color(0xFFF1F5F9),
                                      shape: BoxShape.circle,
                                    ),
                                    child: const Icon(Icons.event_available_rounded, size: 32, color: Color(0xFF94A3B8)),
                                  ),
                                  const SizedBox(height: 12),
                                  Text(
                                    'Sin clases programadas los $_diaSeleccionado',
                                    style: const TextStyle(
                                      fontSize: 13.5,
                                      fontWeight: FontWeight.w700,
                                      color: Color(0xFF475569),
                                    ),
                                  ),
                                  const SizedBox(height: 4),
                                  const Text(
                                    'Seleccione otro día de la semana para consultar su jornada.',
                                    textAlign: TextAlign.center,
                                    style: TextStyle(
                                      fontSize: 11.5,
                                      color: Color(0xFF94A3B8),
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          )
                        else
                          ListView.separated(
                            shrinkWrap: true,
                            physics: const NeverScrollableScrollPhysics(),
                            itemCount: _horariosDelDia.length,
                            separatorBuilder: (_, __) => const SizedBox(height: 12),
                            itemBuilder: (ctx, idx) {
                              final h = _horariosDelDia[idx];
                              return _buildClassCard(h);
                            },
                          ),
                      ],
                    ),
                  ),
                ),
        ),
      ),
    );
  }

  Widget _buildClassCard(HorarioClase h) {
    final aula = h.aulaNombre.isNotEmpty ? h.aulaNombre : (h.aulaCodigo.isNotEmpty ? h.aulaCodigo : 'Aula Base');

    return GlassContainer(
      borderRadius: 18,
      blur: 16,
      padding: const EdgeInsets.all(16),
      child: InkWell(
        onTap: () => _mostrarDetalleClase(h),
        borderRadius: BorderRadius.circular(18),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Fila Superior: Horario y Aula
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                // Chip de Hora
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 4),
                  decoration: BoxDecoration(
                    color: const Color(0xFFEFF6FF),
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: const Color(0xFFBFDBFE), width: 1),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Icon(Icons.access_time_rounded, size: 12.5, color: Color(0xFF1E40AF)),
                      const SizedBox(width: 4.5),
                      Text(
                        h.rangoHoras,
                        style: const TextStyle(
                          fontSize: 11.5,
                          fontWeight: FontWeight.w800,
                          color: Color(0xFF1E40AF),
                        ),
                      ),
                    ],
                  ),
                ),

                // Chip de Aula
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3.5),
                  decoration: BoxDecoration(
                    color: h.esAulaEspecial ? const Color(0xFFFEF3C7) : const Color(0xFFF1F5F9),
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(
                      color: h.esAulaEspecial ? const Color(0xFFFCD34D) : const Color(0xFFE2E8F0),
                      width: 1,
                    ),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(
                        h.esAulaEspecial ? Icons.science_rounded : Icons.meeting_room_rounded,
                        size: 12,
                        color: h.esAulaEspecial ? const Color(0xFFB45309) : const Color(0xFF64748B),
                      ),
                      const SizedBox(width: 4),
                      Text(
                        aula,
                        style: TextStyle(
                          fontSize: 11,
                          fontWeight: FontWeight.w700,
                          color: h.esAulaEspecial ? const Color(0xFF92400E) : const Color(0xFF475569),
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),

            const SizedBox(height: 12),

            // Nombre de la Materia
            Text(
              h.materiaNombre,
              style: const TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.w900,
                color: AppTheme.primaryDark,
                letterSpacing: -0.3,
              ),
            ),

            const SizedBox(height: 4),

            // Grado y Sección
            Row(
              children: [
                const Icon(Icons.groups_rounded, size: 14, color: Color(0xFF64748B)),
                const SizedBox(width: 5),
                Text(
                  h.gradoSeccion,
                  style: const TextStyle(
                    fontSize: 12.5,
                    fontWeight: FontWeight.w600,
                    color: Color(0xFF475569),
                  ),
                ),
              ],
            ),

            const SizedBox(height: 12),
            const Divider(height: 1, color: AppTheme.borderSubtle),
            const SizedBox(height: 10),

            // Botón Tocar para Ver Estudiantes & Acciones
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text(
                  'Tocar para lista y acciones',
                  style: TextStyle(
                    fontSize: 11.5,
                    fontWeight: FontWeight.w600,
                    color: Color(0xFF2563EB),
                  ),
                ),
                Container(
                  padding: const EdgeInsets.all(4),
                  decoration: BoxDecoration(
                    color: const Color(0xFFEFF6FF),
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: const Icon(Icons.arrow_forward_ios_rounded, size: 11, color: Color(0xFF2563EB)),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

// Modal Detalle de Clase con Lista de Alumnos y Acciones Rápidas
class _DetalleClaseModal extends StatefulWidget {
  final HorarioClase horario;
  final Asignatura? asignaturaCoincidente;
  final Function(Asignatura? asig) onTomarAsistencia;
  final Function(Asignatura? asig) onAsignarNotas;

  const _DetalleClaseModal({
    required this.horario,
    required this.asignaturaCoincidente,
    required this.onTomarAsistencia,
    required this.onAsignarNotas,
  });

  @override
  State<_DetalleClaseModal> createState() => _DetalleClaseModalState();
}

class _DetalleClaseModalState extends State<_DetalleClaseModal> {
  bool _cargandoEstudiantes = true;
  List<Estudiante> _estudiantes = [];

  @override
  void initState() {
    super.initState();
    _cargarEstudiantes();
  }

  Future<void> _cargarEstudiantes() async {
    final list = await ApiService.getEstudiantes(gradoSeccion: widget.horario.gradoSeccion);
    if (mounted) {
      setState(() {
        _estudiantes = list;
        _cargandoEstudiantes = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final h = widget.horario;
    final aula = h.aulaNombre.isNotEmpty ? h.aulaNombre : (h.aulaCodigo.isNotEmpty ? h.aulaCodigo : 'Aula Base');

    return Container(
      height: MediaQuery.of(context).size.height * 0.85,
      decoration: const BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      child: Column(
        children: [
          // Barra de agarre superior
          Container(
            margin: const EdgeInsets.only(top: 10, bottom: 8),
            width: 36,
            height: 4,
            decoration: BoxDecoration(
              color: const Color(0xFFCBD5E1),
              borderRadius: BorderRadius.circular(2),
            ),
          ),

          // Cabecera de la Clase
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Container(
                  width: 48,
                  height: 48,
                  decoration: BoxDecoration(
                    gradient: AppTheme.buttonGradient,
                    borderRadius: BorderRadius.circular(12),
                  ),
                  alignment: Alignment.center,
                  child: const Icon(Icons.school_rounded, color: Colors.white, size: 24),
                ),
                const SizedBox(width: 14),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        h.materiaNombre,
                        style: const TextStyle(
                          fontSize: 16.5,
                          fontWeight: FontWeight.w900,
                          color: AppTheme.primaryDark,
                          letterSpacing: -0.3,
                        ),
                      ),
                      const SizedBox(height: 2),
                      Text(
                        '${h.gradoSeccion} • $aula',
                        style: const TextStyle(
                          fontSize: 12,
                          fontWeight: FontWeight.w600,
                          color: Color(0xFF64748B),
                        ),
                      ),
                      const SizedBox(height: 2),
                      Row(
                        children: [
                          const Icon(Icons.access_time_rounded, size: 12, color: Color(0xFF2563EB)),
                          const SizedBox(width: 4),
                          Text(
                            '${h.diaSemana} • ${h.rangoHoras}',
                            style: const TextStyle(
                              fontSize: 11.5,
                              fontWeight: FontWeight.w700,
                              color: Color(0xFF2563EB),
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
                IconButton(
                  icon: const Icon(Icons.close_rounded, color: Color(0xFF64748B)),
                  onPressed: () => Navigator.pop(context),
                ),
              ],
            ),
          ),

          const Divider(height: 1, color: AppTheme.borderSubtle),

          // Título de la Lista de Estudiantes
          Padding(
            padding: const EdgeInsets.fromLTRB(20, 14, 20, 8),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text(
                  'Estudiantes Registrados',
                  style: TextStyle(
                    fontSize: 13.5,
                    fontWeight: FontWeight.w800,
                    color: AppTheme.primaryDark,
                  ),
                ),
                if (!_cargandoEstudiantes)
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                    decoration: BoxDecoration(
                      color: const Color(0xFFEFF6FF),
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(color: const Color(0xFFBFDBFE)),
                    ),
                    child: Text(
                      '${_estudiantes.length} inscritos',
                      style: const TextStyle(
                        fontSize: 11,
                        fontWeight: FontWeight.w800,
                        color: Color(0xFF1E40AF),
                      ),
                    ),
                  ),
              ],
            ),
          ),

          // Lista de Estudiantes
          Expanded(
            child: _cargandoEstudiantes
                ? const Center(child: CircularProgressIndicator(color: AppTheme.primaryNavy))
                : _estudiantes.isEmpty
                    ? Center(
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: const [
                            Icon(Icons.person_off_rounded, size: 36, color: Color(0xFF94A3B8)),
                            SizedBox(height: 8),
                            Text(
                              'No se encontraron alumnos en esta sección.',
                              style: TextStyle(fontSize: 12.5, color: Color(0xFF64748B), fontWeight: FontWeight.w600),
                            ),
                          ],
                        ),
                      )
                    : ListView.separated(
                        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 6),
                        itemCount: _estudiantes.length,
                        separatorBuilder: (_, __) => const SizedBox(height: 6),
                        itemBuilder: (ctx, idx) {
                          final est = _estudiantes[idx];
                          return Container(
                            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                            decoration: BoxDecoration(
                              color: const Color(0xFFF8FAFC),
                              borderRadius: BorderRadius.circular(10),
                              border: Border.all(color: const Color(0xFFE2E8F0)),
                            ),
                            child: Row(
                              children: [
                                Container(
                                  width: 28,
                                  height: 28,
                                  decoration: BoxDecoration(
                                    color: const Color(0xFFE2E8F0),
                                    shape: BoxShape.circle,
                                  ),
                                  alignment: Alignment.center,
                                  child: Text(
                                    '${idx + 1}',
                                    style: const TextStyle(
                                      fontSize: 11,
                                      fontWeight: FontWeight.w800,
                                      color: Color(0xFF475569),
                                    ),
                                  ),
                                ),
                                const SizedBox(width: 10),
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
                                      const SizedBox(height: 1),
                                      Text(
                                        'NIE: ${est.nie}',
                                        style: const TextStyle(
                                          fontSize: 11,
                                          fontFamily: 'monospace',
                                          color: Color(0xFF2563EB),
                                          fontWeight: FontWeight.w600,
                                        ),
                                      ),
                                    ],
                                  ),
                                ),
                              ],
                            ),
                          );
                        },
                      ),
          ),

          // Barra Inferior de Acciones Directas (Pasar Asistencia & Asignar Notas)
          Container(
            padding: const EdgeInsets.fromLTRB(20, 12, 20, 20),
            decoration: BoxDecoration(
              color: Colors.white,
              border: Border(top: BorderSide(color: AppTheme.borderSubtle)),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withOpacity(0.05),
                  blurRadius: 10,
                  offset: const Offset(0, -4),
                ),
              ],
            ),
            child: Row(
              children: [
                // Botón Pasar Asistencia
                Expanded(
                  child: ElevatedButton.icon(
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFF0F172A),
                      foregroundColor: Colors.white,
                      elevation: 0,
                      padding: const EdgeInsets.symmetric(vertical: 12),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                    ),
                    onPressed: () => widget.onTomarAsistencia(widget.asignaturaCoincidente),
                    icon: const Icon(Icons.checklist_rtl_rounded, size: 18),
                    label: const Text(
                      'Tomar Asistencia',
                      style: TextStyle(fontWeight: FontWeight.w800, fontSize: 12.5),
                    ),
                  ),
                ),

                const SizedBox(width: 10),

                // Botón Asignar Notas
                Expanded(
                  child: Container(
                    decoration: BoxDecoration(
                      gradient: AppTheme.buttonGradient,
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: ElevatedButton.icon(
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.transparent,
                        shadowColor: Colors.transparent,
                        foregroundColor: Colors.white,
                        elevation: 0,
                        padding: const EdgeInsets.symmetric(vertical: 12),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                      ),
                      onPressed: () => widget.onAsignarNotas(widget.asignaturaCoincidente),
                      icon: const Icon(Icons.assignment_turned_in_rounded, size: 18),
                      label: const Text(
                        'Asignar Notas',
                        style: TextStyle(fontWeight: FontWeight.w800, fontSize: 12.5),
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
