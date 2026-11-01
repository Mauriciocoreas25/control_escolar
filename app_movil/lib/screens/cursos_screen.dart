import 'package:flutter/material.dart';
import '../models/models.dart';
import '../services/api_service.dart';
import '../theme/app_theme.dart';
import 'login_screen.dart';

class CursosScreen extends StatefulWidget {
  final Function(int tabIndex, {Asignatura? asignatura}) onNavigateTab;

  const CursosScreen({super.key, required this.onNavigateTab});

  @override
  State<CursosScreen> createState() => _CursosScreenState();
}

class _CursosScreenState extends State<CursosScreen> {
  Institucion? _institucion;
  List<Asignatura> _asignaturas = [];
  final Map<String, int> _estudiantesPorSeccion = {};
  bool _isLoading = true;
  String _searchQuery = '';
  Map<String, dynamic>? _currentUser;

  @override
  void initState() {
    super.initState();
    _loadData();
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
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Sesión expirada o usuario no registrado en el sistema escolar.'),
          backgroundColor: Colors.redAccent,
        ),
      );
      return;
    }
    final inst = await ApiService.getInstitucion();
    final docenteNombre = user['nombre'];
    final rol = user['rol']?.toString().toLowerCase() ?? 'profesor';

    List<Asignatura> list = [];
    if (rol == 'director' || rol == 'administrador') {
      list = await ApiService.getAsignaturas();
    } else if (docenteNombre != null && docenteNombre.toString().isNotEmpty) {
      list = await ApiService.getAsignaturas(profesorNombre: docenteNombre);
    }

    final todosEstudiantes = await ApiService.getEstudiantes();
    _estudiantesPorSeccion.clear();
    for (var e in todosEstudiantes) {
      _estudiantesPorSeccion[e.gradoSeccion] = (_estudiantesPorSeccion[e.gradoSeccion] ?? 0) + 1;
    }

    if (!mounted) return;
    setState(() {
      _currentUser = user;
      _institucion = inst;
      _asignaturas = list;
      _isLoading = false;
    });
  }

  List<Asignatura> get _filteredCourses {
    if (_searchQuery.isEmpty) return _asignaturas;
    return _asignaturas.where((a) {
      return a.nombre.toLowerCase().contains(_searchQuery.toLowerCase()) ||
          a.gradoSeccion.toLowerCase().contains(_searchQuery.toLowerCase()) ||
          a.codigo.toLowerCase().contains(_searchQuery.toLowerCase()) ||
          (a.aulaNombre != null && a.aulaNombre!.toLowerCase().contains(_searchQuery.toLowerCase()));
    }).toList();
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
          '¿Desea cerrar la sesión de $docenteNombre y volver al inicio?',
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
    final anioActivo = _institucion?.anioLectivo ?? '2026';
    final regimen = _institucion?.regimen ?? 'Régimen Trimestral';

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
                        // Encabezado Superior con Acciones
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
                                    'Mis Cursos Asignados',
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
                                  tooltip: 'Actualizar Catálogo',
                                  onPressed: _loadData,
                                ),
                                IconButton(
                                  icon: const Icon(Icons.logout_rounded, size: 21, color: Color(0xFFDC2626)),
                                  tooltip: 'Salir',
                                  onPressed: _confirmLogout,
                                ),
                              ],
                            ),
                          ],
                        ),

                        const SizedBox(height: 16),

                        // Tarjeta Glassmorphic de Identidad del Docente
                        GlassContainer(
                          borderRadius: 20,
                          blur: 18,
                          padding: const EdgeInsets.all(18),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Row(
                                children: [
                                  Container(
                                    width: 48,
                                    height: 48,
                                    decoration: BoxDecoration(
                                      gradient: AppTheme.buttonGradient,
                                      borderRadius: BorderRadius.circular(14),
                                      boxShadow: [
                                        BoxShadow(
                                          color: const Color(0xFF2563EB).withOpacity(0.35),
                                          blurRadius: 14,
                                          offset: const Offset(0, 4),
                                        ),
                                      ],
                                    ),
                                    alignment: Alignment.center,
                                    child: Text(
                                      docenteNombre.length >= 2 ? docenteNombre.substring(0, 2).toUpperCase() : 'DOC',
                                      style: const TextStyle(
                                        fontSize: 16,
                                        fontWeight: FontWeight.w900,
                                        color: Colors.white,
                                        letterSpacing: -0.5,
                                      ),
                                    ),
                                  ),
                                  const SizedBox(width: 14),
                                  Expanded(
                                    child: Column(
                                      crossAxisAlignment: CrossAxisAlignment.start,
                                      children: [
                                        Text(
                                          docenteNombre,
                                          style: const TextStyle(
                                            fontSize: 16,
                                            fontWeight: FontWeight.w800,
                                            color: AppTheme.primaryDark,
                                            letterSpacing: -0.3,
                                          ),
                                        ),
                                        const SizedBox(height: 2),
                                        Row(
                                          children: const [
                                            Icon(Icons.verified_user_rounded, size: 12, color: AppTheme.statusPresente),
                                            SizedBox(width: 4),
                                            Text(
                                              'Docente Titular Autorizado',
                                              style: TextStyle(
                                                fontSize: 11.5,
                                                color: Color(0xFF64748B),
                                                fontWeight: FontWeight.w600,
                                              ),
                                            ),
                                          ],
                                        ),
                                      ],
                                    ),
                                  ),
                                ],
                              ),

                              const SizedBox(height: 14),
                              const Divider(height: 1, color: AppTheme.borderSubtle),
                              const SizedBox(height: 12),

                              Wrap(
                                spacing: 8,
                                runSpacing: 8,
                                children: [
                                  _buildGlassChip(
                                    icon: Icons.auto_stories_rounded,
                                    label: '${_asignaturas.length} Cursos',
                                    gradient: AppTheme.accentGradient,
                                  ),
                                  _buildGlassChip(
                                    icon: Icons.calendar_today_rounded,
                                    label: 'Ciclo $anioActivo',
                                    gradient: AppTheme.emeraldGradient,
                                  ),
                                  _buildGlassChip(
                                    icon: Icons.timelapse_rounded,
                                    label: regimen,
                                    gradient: AppTheme.amberGradient,
                                  ),
                                ],
                              ),
                            ],
                          ),
                        ),

                        const SizedBox(height: 16),

                        // Barra de Búsqueda Glassmorphic
                        GlassContainer(
                          borderRadius: 16,
                          blur: 14,
                          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 2),
                          child: TextField(
                            onChanged: (val) => setState(() => _searchQuery = val),
                            style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600),
                            decoration: InputDecoration(
                              icon: const Icon(Icons.search_rounded, color: Color(0xFF94A3B8), size: 21),
                              hintText: 'Buscar por sección, materia, código o aula...',
                              hintStyle: const TextStyle(fontSize: 12.5, color: Color(0xFF94A3B8), fontWeight: FontWeight.normal),
                              border: InputBorder.none,
                              isDense: true,
                              contentPadding: const EdgeInsets.symmetric(vertical: 12),
                            ),
                          ),
                        ),

                        const SizedBox(height: 20),

                        // Encabezado de Lista
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            const Text(
                              'Carga Académica',
                              style: TextStyle(
                                fontSize: 15,
                                fontWeight: FontWeight.w800,
                                color: AppTheme.primaryDark,
                                letterSpacing: -0.2,
                              ),
                            ),
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 3),
                              decoration: BoxDecoration(
                                color: AppTheme.primaryNavy.withOpacity(0.08),
                                borderRadius: BorderRadius.circular(10),
                              ),
                              child: Text(
                                '${_filteredCourses.length} asignaturas',
                                style: const TextStyle(
                                  fontSize: 11.5,
                                  color: AppTheme.primaryNavy,
                                  fontWeight: FontWeight.w800,
                                ),
                              ),
                            ),
                          ],
                        ),

                        const SizedBox(height: 12),

                        // Listado de Tarjetas Glassmorphic de Cursos
                        if (_filteredCourses.isEmpty)
                          GlassContainer(
                            borderRadius: 18,
                            padding: const EdgeInsets.all(32),
                            child: Center(
                              child: Column(
                                children: const [
                                  Icon(Icons.search_off_rounded, size: 40, color: Color(0xFF94A3B8)),
                                  SizedBox(height: 10),
                                  Text(
                                    'No se encontraron cursos asignados con los términos de búsqueda.',
                                    textAlign: TextAlign.center,
                                    style: TextStyle(fontSize: 13, color: Color(0xFF64748B), fontWeight: FontWeight.w500),
                                  ),
                                ],
                              ),
                            ),
                          )
                        else
                          ListView.separated(
                            shrinkWrap: true,
                            physics: const NeverScrollableScrollPhysics(),
                            itemCount: _filteredCourses.length,
                            separatorBuilder: (_, __) => const SizedBox(height: 12),
                            itemBuilder: (context, index) {
                              final curso = _filteredCourses[index];
                              return _buildCourseCard(curso);
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

  Widget _buildGlassChip({
    required IconData icon,
    required String label,
    required LinearGradient gradient,
  }) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.70),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: Colors.white),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.03),
            blurRadius: 6,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          ShaderMask(
            shaderCallback: (bounds) => gradient.createShader(bounds),
            child: Icon(icon, size: 13, color: Colors.white),
          ),
          const SizedBox(width: 5),
          Text(
            label,
            style: const TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.w800,
              color: Color(0xFF334155),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildCourseCard(Asignatura curso) {
    final matriculadosReales = _estudiantesPorSeccion[curso.gradoSeccion] ?? 0;
    final aulaAsignada = curso.aulaNombre ?? (curso.aulaCodigo != null ? 'Aula ${curso.aulaCodigo}' : null);

    return GlassContainer(
      borderRadius: 20,
      blur: 16,
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Fila 1: Título y Código
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: Text(
                  curso.nombre,
                  style: const TextStyle(
                    fontSize: 15.5,
                    fontWeight: FontWeight.w800,
                    color: AppTheme.primaryDark,
                    letterSpacing: -0.3,
                  ),
                ),
              ),
              const SizedBox(width: 8),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3.5),
                decoration: BoxDecoration(
                  gradient: AppTheme.primaryGradient,
                  borderRadius: BorderRadius.circular(8),
                  boxShadow: [
                    BoxShadow(
                      color: AppTheme.primaryNavy.withOpacity(0.25),
                      blurRadius: 6,
                      offset: const Offset(0, 2),
                    ),
                  ],
                ),
                child: Text(
                  curso.codigo,
                  style: const TextStyle(
                    fontFamily: 'monospace',
                    fontSize: 11,
                    fontWeight: FontWeight.w800,
                    color: Colors.white,
                  ),
                ),
              ),
            ],
          ),

          const SizedBox(height: 10),

          // Chips de Sección, Aula y Matrícula
          Wrap(
            spacing: 6,
            runSpacing: 6,
            children: [
              // Sección
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3.5),
                decoration: BoxDecoration(
                  color: const Color(0xFFEFF6FF),
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: const Color(0xFFBFDBFE)),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Icon(Icons.group_rounded, size: 12, color: AppTheme.primaryNavy),
                    const SizedBox(width: 4),
                    Text(
                      curso.gradoSeccion,
                      style: const TextStyle(
                        fontSize: 11,
                        fontWeight: FontWeight.w800,
                        color: AppTheme.primaryNavy,
                      ),
                    ),
                  ],
                ),
              ),

              // Salón / Laboratorio
              if (aulaAsignada != null)
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3.5),
                  decoration: BoxDecoration(
                    color: const Color(0xFFF0FDF4),
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: const Color(0xFFBBF7D0)),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Icon(Icons.meeting_room_rounded, size: 12, color: Color(0xFF15803D)),
                      const SizedBox(width: 4),
                      Text(
                        aulaAsignada,
                        style: const TextStyle(
                          fontSize: 11,
                          fontWeight: FontWeight.w800,
                          color: Color(0xFF15803D),
                        ),
                      ),
                    ],
                  ),
                ),

              // Alumnos Matriculados
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3.5),
                decoration: BoxDecoration(
                  color: const Color(0xFFF8FAFC),
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: AppTheme.borderSubtle),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Icon(Icons.person_outline_rounded, size: 12, color: Color(0xFF64748B)),
                    const SizedBox(width: 4),
                    Text(
                      '$matriculadosReales alumnos',
                      style: const TextStyle(
                        fontSize: 11,
                        fontWeight: FontWeight.w600,
                        color: Color(0xFF475569),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),

          const SizedBox(height: 14),

          // Botones de Acción con Degradados
          Row(
            children: [
              // Botón Asistencia (Emerald Gradient)
              Expanded(
                child: Container(
                  height: 38,
                  decoration: BoxDecoration(
                    gradient: AppTheme.emeraldGradient,
                    borderRadius: BorderRadius.circular(10),
                    boxShadow: [
                      BoxShadow(
                        color: const Color(0xFF059669).withOpacity(0.30),
                        blurRadius: 8,
                        offset: const Offset(0, 3),
                      ),
                    ],
                  ),
                  child: Material(
                    color: Colors.transparent,
                    child: InkWell(
                      borderRadius: BorderRadius.circular(10),
                      onTap: () => widget.onNavigateTab(2, asignatura: curso),
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: const [
                          Icon(Icons.checklist_rtl_rounded, size: 16, color: Colors.white),
                          SizedBox(width: 6),
                          Text(
                            'Asistencia',
                            style: TextStyle(
                              color: Colors.white,
                              fontSize: 12,
                              fontWeight: FontWeight.w800,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
              ),

              const SizedBox(width: 10),

              // Botón Calificaciones (Royal Blue Gradient)
              Expanded(
                child: Container(
                  height: 38,
                  decoration: BoxDecoration(
                    gradient: AppTheme.buttonGradient,
                    borderRadius: BorderRadius.circular(10),
                    boxShadow: [
                      BoxShadow(
                        color: const Color(0xFF2563EB).withOpacity(0.30),
                        blurRadius: 8,
                        offset: const Offset(0, 3),
                      ),
                    ],
                  ),
                  child: Material(
                    color: Colors.transparent,
                    child: InkWell(
                      borderRadius: BorderRadius.circular(10),
                      onTap: () => widget.onNavigateTab(3, asignatura: curso),
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: const [
                          Icon(Icons.assignment_turned_in_rounded, size: 16, color: Colors.white),
                          SizedBox(width: 6),
                          Text(
                            'Calificaciones',
                            style: TextStyle(
                              color: Colors.white,
                              fontSize: 12,
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
        ],
      ),
    );
  }
}
