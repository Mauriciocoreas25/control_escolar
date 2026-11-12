import 'dart:ui';
import 'package:flutter/material.dart';
import '../models/models.dart';
import '../services/api_service.dart';
import '../theme/app_theme.dart';
import 'asistencia_screen.dart';
import 'cursos_screen.dart';
import 'grados_screen.dart';
import 'horario_docente_screen.dart';
import 'login_screen.dart';

class MainNavigationScreen extends StatefulWidget {
  const MainNavigationScreen({super.key});

  @override
  State<MainNavigationScreen> createState() => _MainNavigationScreenState();
}

class _MainNavigationScreenState extends State<MainNavigationScreen> {
  int _currentIndex = 0;
  Asignatura? _selectedCourseForAction;
  Map<String, dynamic>? _currentUser;
  Map<String, dynamic>? _profesorPerfil;
  Institucion? _institucion;
  String? _docenteFotoUrl;

  @override
  void initState() {
    super.initState();
    _loadUser();
  }

  Future<void> _loadUser() async {
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
    setState(() => _currentUser = user);

    try {
      final userId = user['id'] as int?;
      if (userId != null) {
        final prefs = await SharedPreferences.getInstance();
        final savedFoto = prefs.getString('docente_foto_$userId');
        final perfil = await ApiService.getProfesorPerfil(userId);
        final inst = await ApiService.getInstitucion();
        if (mounted) {
          setState(() {
            _docenteFotoUrl = savedFoto;
            _profesorPerfil = perfil;
            _institucion = inst;
          });
        }
      }
    } catch (e) {
      debugPrint('Error al cargar datos del perfil: ');
    }
  }

  void _onNavigateTab(int index, {Asignatura? asignatura}) {
    setState(() {
      _currentIndex = index;
      _selectedCourseForAction = asignatura;
    });
  }

  Future<void> _handleLogout() async {
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
        content: const Text(
          '¿Está seguro de que desea salir del Portal Móvil Docente?',
          style: TextStyle(fontSize: 13, color: AppTheme.primaryDark),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('Cancelar', style: TextStyle(color: Color(0xFF64748B), fontWeight: FontWeight.w600)),
          ),
          ElevatedButton(
            style: ElevatedButton.styleFrom(
              backgroundColor: AppTheme.statusAusente,
              foregroundColor: Colors.white,
              elevation: 0,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
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
      Navigator.pushReplacement(
        context,
        MaterialPageRoute(builder: (_) => const LoginScreen()),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final screens = [
      CursosScreen(onNavigateTab: _onNavigateTab),
      HorarioDocenteScreen(onNavigateTab: _onNavigateTab),
      AsistenciaScreen(selectedCourse: _selectedCourseForAction),
      GradosScreen(selectedCourse: _selectedCourseForAction),
      _buildPerfilScreen(),
    ];

    return Scaffold(
      extendBody: true,
      body: IndexedStack(index: _currentIndex, children: screens),
      drawer: Drawer(
        backgroundColor: Colors.white,
        child: SafeArea(
          child: Column(
            children: [
              // Cabecera con Degradado y Glass Card
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(22),
                decoration: const BoxDecoration(
                  gradient: AppTheme.primaryGradient,
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Container(
                      width: 52,
                      height: 52,
                      decoration: BoxDecoration(
                        color: Colors.white.withOpacity(0.18),
                        borderRadius: BorderRadius.circular(14),
                        border: Border.all(color: Colors.white.withOpacity(0.35)),
                      ),
                      alignment: Alignment.center,
                      child: const Icon(Icons.school_rounded, color: Colors.white, size: 28),
                    ),
                    const SizedBox(height: 14),
                    Text(
                      _currentUser?['nombre'] ?? 'Docente Autorizado',
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 16,
                        fontWeight: FontWeight.w800,
                        letterSpacing: -0.3,
                      ),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      _currentUser?['correo'] ?? 'docente@santasofia.edu.sv',
                      style: const TextStyle(color: Color(0xFF93C5FD), fontSize: 12),
                    ),
                    const SizedBox(height: 10),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                      decoration: BoxDecoration(
                        color: Colors.white.withOpacity(0.15),
                        borderRadius: BorderRadius.circular(20),
                        border: Border.all(color: Colors.white.withOpacity(0.25)),
                      ),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: const [
                          Icon(Icons.verified_rounded, color: Color(0xFF38BDF8), size: 13),
                          SizedBox(width: 5),
                          Text(
                            'Docente Activo 2026',
                            style: TextStyle(color: Colors.white, fontSize: 11, fontWeight: FontWeight.w700),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),

              const SizedBox(height: 12),

              _buildDrawerItem(
                icon: Icons.auto_stories_outlined,
                activeIcon: Icons.auto_stories,
                title: 'Mis Cursos Asignados',
                index: 0,
              ),
              _buildDrawerItem(
                icon: Icons.calendar_month_outlined,
                activeIcon: Icons.calendar_month,
                title: 'Mi Horario Semanal',
                index: 1,
              ),
              _buildDrawerItem(
                icon: Icons.checklist_rtl_outlined,
                activeIcon: Icons.checklist_rtl,
                title: 'Pase de Asistencia',
                index: 2,
              ),
              _buildDrawerItem(
                icon: Icons.assignment_turned_in_outlined,
                activeIcon: Icons.assignment_turned_in,
                title: 'Registro de Calificaciones',
                index: 3,
              ),
              _buildDrawerItem(
                icon: Icons.person_outline_rounded,
                activeIcon: Icons.person_rounded,
                title: 'Mi Perfil Docente',
                index: 4,
              ),



              const Spacer(),

              Padding(
                padding: const EdgeInsets.all(16.0),
                child: SizedBox(
                  width: double.infinity,
                  child: OutlinedButton.icon(
                    onPressed: _handleLogout,
                    icon: const Icon(Icons.logout_rounded, size: 18, color: AppTheme.statusAusente),
                    label: const Text(
                      'Cerrar Sesión',
                      style: TextStyle(color: AppTheme.statusAusente, fontWeight: FontWeight.w700, fontSize: 13),
                    ),
                    style: OutlinedButton.styleFrom(
                      side: const BorderSide(color: Color(0xFFFECDD3)),
                      backgroundColor: const Color(0xFFFFF1F2),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                      padding: const EdgeInsets.symmetric(vertical: 12),
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),

      // Barra de Navegación Flotante con Glassmorphism
      bottomNavigationBar: Container(
        margin: const EdgeInsets.fromLTRB(16, 0, 16, 16),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(24),
          boxShadow: [
            BoxShadow(
              color: const Color(0xFF0F172A).withOpacity(0.08),
              blurRadius: 24,
              offset: const Offset(0, 8),
            ),
          ],
        ),
        child: ClipRRect(
          borderRadius: BorderRadius.circular(24),
          child: BackdropFilter(
            filter: ImageFilter.blur(sigmaX: 18, sigmaY: 18),
            child: Container(
              height: 68,
              decoration: BoxDecoration(
                color: Colors.white.withOpacity(0.88),
                borderRadius: BorderRadius.circular(24),
                border: Border.all(
                  color: Colors.white.withOpacity(0.70),
                  width: 1.5,
                ),
              ),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceAround,
                children: [
                  _buildNavItem(0, Icons.auto_stories_outlined, Icons.auto_stories, 'Cursos'),
                  _buildNavItem(1, Icons.calendar_month_outlined, Icons.calendar_month, 'Horario'),
                  _buildNavItem(2, Icons.checklist_rtl_outlined, Icons.checklist_rtl, 'Asistencia'),
                  _buildNavItem(3, Icons.assignment_turned_in_outlined, Icons.assignment_turned_in, 'Notas'),
                  _buildNavItem(4, Icons.person_outline_rounded, Icons.person_rounded, 'Perfil'),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildDrawerItem({
    required IconData icon,
    required IconData activeIcon,
    required String title,
    required int index,
  }) {
    final isSelected = _currentIndex == index;
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 12, vertical: 3),
      decoration: BoxDecoration(
        color: isSelected ? const Color(0xFFEFF6FF) : Colors.transparent,
        borderRadius: BorderRadius.circular(10),
      ),
      child: ListTile(
        dense: true,
        leading: Icon(
          isSelected ? activeIcon : icon,
          color: isSelected ? AppTheme.primaryNavy : const Color(0xFF64748B),
          size: 21,
        ),
        title: Text(
          title,
          style: TextStyle(
            fontSize: 13,
            fontWeight: isSelected ? FontWeight.w800 : FontWeight.w600,
            color: isSelected ? AppTheme.primaryNavy : const Color(0xFF334155),
          ),
        ),
        onTap: () {
          Navigator.pop(context);
          _onNavigateTab(index);
        },
      ),
    );
  }

  Widget _buildNavItem(int index, IconData icon, IconData activeIcon, String label) {
    final isSelected = _currentIndex == index;

    return InkWell(
      onTap: () => setState(() => _currentIndex = index),
      borderRadius: BorderRadius.circular(16),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 250),
        curve: Curves.easeOutCubic,
        padding: EdgeInsets.symmetric(
          horizontal: isSelected ? 16 : 10,
          vertical: 8,
        ),
        decoration: BoxDecoration(
          gradient: isSelected ? AppTheme.buttonGradient : null,
          borderRadius: BorderRadius.circular(16),
          boxShadow: isSelected
              ? [
                  BoxShadow(
                    color: const Color(0xFF2563EB).withOpacity(0.30),
                    blurRadius: 10,
                    offset: const Offset(0, 3),
                  ),
                ]
              : null,
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              isSelected ? activeIcon : icon,
              size: 20,
              color: isSelected ? Colors.white : const Color(0xFF64748B),
            ),
            if (isSelected) ...[
              const SizedBox(width: 6),
              Text(
                label,
                style: const TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.w800,
                  fontSize: 12,
                  letterSpacing: -0.2,
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildProfileInfoRow({
    required IconData icon,
    required Color iconColor,
    required String title,
    required String value,
  }) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 7.0),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: iconColor.withOpacity(0.12),
              borderRadius: BorderRadius.circular(10),
            ),
            child: Icon(icon, size: 18, color: iconColor),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: const TextStyle(
                    fontSize: 11,
                    fontWeight: FontWeight.w600,
                    color: Color(0xFF64748B),
                    letterSpacing: 0.2,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  value,
                  style: const TextStyle(
                    fontSize: 13.5,
                    fontWeight: FontWeight.w700,
                    color: AppTheme.primaryDark,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  void _showChangePasswordDialog() {
    final newPassCtrl = TextEditingController();
    final confirmPassCtrl = TextEditingController();
    bool obscureNew = true;
    bool obscureConfirm = true;
    bool isSubmitting = false;

    showDialog(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (context, setDialogState) => AlertDialog(
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
          title: Row(
            children: const [
              Icon(Icons.lock_reset_rounded, color: AppTheme.primaryNavy, size: 22),
              SizedBox(width: 10),
              Text('Cambiar Contraseña', style: TextStyle(fontWeight: FontWeight.w800, fontSize: 16)),
            ],
          ),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Ingrese su nueva contraseña de acceso institucional para la plataforma docente.',
                  style: TextStyle(fontSize: 12.5, color: Color(0xFF64748B)),
                ),
                const SizedBox(height: 16),
                TextField(
                  controller: newPassCtrl,
                  obscureText: obscureNew,
                  decoration: InputDecoration(
                    labelText: 'Nueva Contraseña',
                    hintText: 'Mínimo 4 caracteres',
                    prefixIcon: const Icon(Icons.key_rounded, size: 20),
                    suffixIcon: IconButton(
                      icon: Icon(obscureNew ? Icons.visibility_outlined : Icons.visibility_off_outlined, size: 20),
                      onPressed: () => setDialogState(() => obscureNew = !obscureNew),
                    ),
                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                    contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
                  ),
                ),
                const SizedBox(height: 14),
                TextField(
                  controller: confirmPassCtrl,
                  obscureText: obscureConfirm,
                  decoration: InputDecoration(
                    labelText: 'Confirmar Contraseña',
                    hintText: 'Repita la nueva contraseña',
                    prefixIcon: const Icon(Icons.check_circle_outline_rounded, size: 20),
                    suffixIcon: IconButton(
                      icon: Icon(obscureConfirm ? Icons.visibility_outlined : Icons.visibility_off_outlined, size: 20),
                      onPressed: () => setDialogState(() => obscureConfirm = !obscureConfirm),
                    ),
                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                    contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
                  ),
                ),
              ],
            ),
          ),
          actionsPadding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
          actions: [
            TextButton(
              onPressed: isSubmitting ? null : () => Navigator.pop(ctx),
              child: const Text('Cancelar', style: TextStyle(color: Color(0xFF64748B), fontWeight: FontWeight.w600)),
            ),
            ElevatedButton(
              style: ElevatedButton.styleFrom(
                backgroundColor: AppTheme.primaryNavy,
                foregroundColor: Colors.white,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 10),
              ),
              onPressed: isSubmitting
                  ? null
                  : () async {
                      final newPass = newPassCtrl.text.trim();
                      final confirmPass = confirmPassCtrl.text.trim();

                      if (newPass.isEmpty || confirmPass.isEmpty) {
                        ScaffoldMessenger.of(context).showSnackBar(
                          const SnackBar(content: Text('Por favor complete ambos campos.'), backgroundColor: Colors.orange),
                        );
                        return;
                      }
                      if (newPass.length < 4) {
                        ScaffoldMessenger.of(context).showSnackBar(
                          const SnackBar(content: Text('La contraseña debe tener al menos 4 caracteres.'), backgroundColor: Colors.orange),
                        );
                        return;
                      }
                      if (newPass != confirmPass) {
                        ScaffoldMessenger.of(context).showSnackBar(
                          const SnackBar(content: Text('Las contraseñas no coinciden.'), backgroundColor: Colors.redAccent),
                        );
                        return;
                      }

                      setDialogState(() => isSubmitting = true);
                      final userId = _currentUser?['id'];
                      if (userId == null) {
                        setDialogState(() => isSubmitting = false);
                        return;
                      }

                      final res = await ApiService.updatePassword(userId, newPass);
                      setDialogState(() => isSubmitting = false);

                      if (res['success'] == true) {
                        if (!mounted) return;
                        Navigator.pop(ctx);
                        ScaffoldMessenger.of(context).showSnackBar(
                          const SnackBar(
                            content: Row(
                              children: [
                                Icon(Icons.check_circle_rounded, color: Colors.white),
                                SizedBox(width: 8),
                                Expanded(child: Text('Contraseña actualizada correctamente.')),
                              ],
                            ),
                            backgroundColor: Color(0xFF059669),
                          ),
                        );
                      } else {
                        ScaffoldMessenger.of(context).showSnackBar(
                          SnackBar(
                            content: Text(res['message'] ?? 'Error al actualizar contraseña.'),
                            backgroundColor: Colors.redAccent,
                          ),
                        );
                      }
                    },
              child: isSubmitting
                  ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                  : const Text('Guardar', style: TextStyle(fontWeight: FontWeight.bold)),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildPerfilScreen() {
    final nombre = _currentUser?['nombre'] ?? 'Docente Autorizado';
    final correo = _currentUser?['correo'] ?? 'docente@santasofia.edu.sv';
    final rol = _currentUser?['rol'] ?? 'Docente Titular';
    final especialidad = _profesorPerfil?['especialidad'] ?? 'Docencia General';
    final telefono = _profesorPerfil?['telefono'] ?? 'No registrado';

    return Scaffold(
      backgroundColor: Colors.transparent,
      body: AmbientBackground(
        child: SafeArea(
          child: SingleChildScrollView(
            padding: const EdgeInsets.fromLTRB(20, 20, 20, 100),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    const Text(
                      'Mi Perfil',
                      style: TextStyle(
                        fontSize: 20,
                        fontWeight: FontWeight.w800,
                        color: AppTheme.primaryDark,
                        letterSpacing: -0.4,
                      ),
                    ),
                    IconButton(
                      icon: const Icon(Icons.logout_rounded, color: Color(0xFFDC2626)),
                      tooltip: 'Cerrar Sesión',
                      onPressed: _handleLogout,
                    ),
                  ],
                ),

                const SizedBox(height: 18),

                // Tarjeta de Identidad Personal
                GlassContainer(
                  borderRadius: 24,
                  blur: 20,
                  padding: const EdgeInsets.all(22),
                  child: Column(
                    children: [
                      Container(
                        width: 76,
                        height: 76,
                        decoration: BoxDecoration(
                          gradient: AppTheme.buttonGradient,
                          shape: BoxShape.circle,
                          boxShadow: [
                            BoxShadow(
                              color: const Color(0xFF2563EB).withOpacity(0.35),
                              blurRadius: 20,
                              offset: const Offset(0, 8),
                            ),
                          ],
                        ),
                        alignment: Alignment.center,
                        child: Text(
                          nombre.length >= 2 ? nombre.substring(0, 2).toUpperCase() : 'DOC',
                          style: const TextStyle(
                            fontSize: 24,
                            fontWeight: FontWeight.w900,
                            color: Colors.white,
                            letterSpacing: -0.5,
                          ),
                        ),
                      ),
                      const SizedBox(height: 14),
                      Text(
                        nombre,
                        textAlign: TextAlign.center,
                        style: const TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.w800,
                          color: AppTheme.primaryDark,
                          letterSpacing: -0.3,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        correo,
                        style: const TextStyle(fontSize: 13, color: Color(0xFF64748B), fontWeight: FontWeight.w500),
                      ),
                      const SizedBox(height: 12),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 5),
                        decoration: BoxDecoration(
                          color: const Color(0xFFEFF6FF),
                          borderRadius: BorderRadius.circular(20),
                          border: Border.all(color: const Color(0xFFBFDBFE)),
                        ),
                        child: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            const Icon(Icons.badge_rounded, size: 14, color: Color(0xFF2563EB)),
                            const SizedBox(width: 5),
                            Text(
                              rol,
                              style: const TextStyle(fontSize: 11.5, fontWeight: FontWeight.w800, color: Color(0xFF1D4ED8)),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),

                const SizedBox(height: 18),

                // Tarjeta de Información Personal y Profesional del Docente
                GlassContainer(
                  borderRadius: 20,
                  padding: const EdgeInsets.all(20),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: const [
                          Icon(Icons.person_outline_rounded, size: 18, color: AppTheme.primaryNavy),
                          SizedBox(width: 8),
                          Text(
                            'INFORMACIÓN DEL DOCENTE',
                            style: TextStyle(
                              fontSize: 11,
                              fontWeight: FontWeight.w800,
                              color: AppTheme.primaryNavy,
                              letterSpacing: 0.6,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 14),
                      _buildProfileInfoRow(
                        icon: Icons.person_rounded,
                        iconColor: const Color(0xFF2563EB),
                        title: 'Nombre Completo',
                        value: nombre,
                      ),
                      const Divider(height: 12, color: Color(0xFFE2E8F0)),
                      _buildProfileInfoRow(
                        icon: Icons.alternate_email_rounded,
                        iconColor: const Color(0xFF0284C7),
                        title: 'Correo Electrónico',
                        value: correo,
                      ),
                      const Divider(height: 12, color: Color(0xFFE2E8F0)),
                      _buildProfileInfoRow(
                        icon: Icons.menu_book_rounded,
                        iconColor: const Color(0xFF7C3AED),
                        title: 'Especialidad Académica',
                        value: especialidad,
                      ),
                      const Divider(height: 12, color: Color(0xFFE2E8F0)),
                      _buildProfileInfoRow(
                        icon: Icons.phone_android_rounded,
                        iconColor: const Color(0xFF059669),
                        title: 'Teléfono de Contacto',
                        value: telefono,
                      ),
                    ],
                  ),
                ),

                const SizedBox(height: 18),

                // Tarjeta de Seguridad (Cambio de Contraseña)
                GlassContainer(
                  borderRadius: 20,
                  padding: const EdgeInsets.all(18),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: const [
                          Icon(Icons.security_rounded, size: 18, color: AppTheme.primaryNavy),
                          SizedBox(width: 8),
                          Text(
                            'SEGURIDAD DE LA CUENTA',
                            style: TextStyle(
                              fontSize: 11,
                              fontWeight: FontWeight.w800,
                              color: AppTheme.primaryNavy,
                              letterSpacing: 0.6,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 14),
                      Material(
                        color: Colors.transparent,
                        child: InkWell(
                          borderRadius: BorderRadius.circular(14),
                          onTap: _showChangePasswordDialog,
                          child: Container(
                            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
                            decoration: BoxDecoration(
                              color: const Color(0xFFF8FAFC),
                              borderRadius: BorderRadius.circular(14),
                              border: Border.all(color: const Color(0xFFE2E8F0)),
                            ),
                            child: Row(
                              children: [
                                Container(
                                  padding: const EdgeInsets.all(10),
                                  decoration: BoxDecoration(
                                    color: const Color(0xFF1E293B).withOpacity(0.08),
                                    borderRadius: BorderRadius.circular(10),
                                  ),
                                  child: const Icon(Icons.lock_reset_rounded, size: 20, color: AppTheme.primaryNavy),
                                ),
                                const SizedBox(width: 12),
                                Expanded(
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: const [
                                      Text(
                                        'Cambiar Contraseña',
                                        style: TextStyle(fontSize: 13.5, fontWeight: FontWeight.w700, color: AppTheme.primaryDark),
                                      ),
                                      SizedBox(height: 2),
                                      Text(
                                        'Actualice su clave de acceso personal',
                                        style: TextStyle(fontSize: 11.5, color: Color(0xFF64748B)),
                                      ),
                                    ],
                                  ),
                                ),
                                const Icon(Icons.arrow_forward_ios_rounded, size: 15, color: Color(0xFF94A3B8)),
                              ],
                            ),
                          ),
                        ),
                      ),
                    ],
                  ),
                ),

                const SizedBox(height: 20),

                // Botón de Cierre de Sesión
                Container(
                  height: 48,
                  decoration: BoxDecoration(
                    gradient: AppTheme.roseGradient,
                    borderRadius: BorderRadius.circular(14),
                    boxShadow: [
                      BoxShadow(
                        color: const Color(0xFFDC2626).withOpacity(0.3),
                        blurRadius: 14,
                        offset: const Offset(0, 4),
                      ),
                    ],
                  ),
                  child: Material(
                    color: Colors.transparent,
                    child: InkWell(
                      borderRadius: BorderRadius.circular(14),
                      onTap: _handleLogout,
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: const [
                          Icon(Icons.logout_rounded, color: Colors.white, size: 18),
                          SizedBox(width: 8),
                          Text(
                            'Cerrar Sesión Móvil',
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

                ],
            ),
          ),
        ),
      ),
    );
  }

  void _showChangePhotoDialog(int userId) {
    final textController = TextEditingController(text: _docenteFotoUrl ?? '');
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(18)),
        title: const Text(
          'Foto de Perfil del Docente',
          style: TextStyle(fontWeight: FontWeight.w800, fontSize: 16),
        ),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                'Ingrese el enlace web (URL) de la fotografía institucional o seleccione una predefinida:',
                style: TextStyle(fontSize: 12, color: Color(0xFF64748B)),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: textController,
                style: const TextStyle(fontSize: 13),
                decoration: InputDecoration(
                  hintText: 'https://ejemplo.com/docente.jpg',
                  prefixIcon: const Icon(Icons.link_rounded, size: 18),
                  contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
                ),
              ),
              const SizedBox(height: 16),
              const Text(
                'Fotografías institucionales sugeridas:',
                style: TextStyle(fontSize: 11, fontWeight: FontWeight.w700, color: Color(0xFF475569)),
              ),
              const SizedBox(height: 8),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                children: [
                  _buildAvatarChoice('https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150', textController),
                  _buildAvatarChoice('https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150', textController),
                  _buildAvatarChoice('https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=150', textController),
                  _buildAvatarChoice('https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=150', textController),
                ],
              ),
            ],
          ),
        ),
        actions: [
          if (_docenteFotoUrl != null && _docenteFotoUrl!.isNotEmpty)
            TextButton(
              onPressed: () async {
                final prefs = await SharedPreferences.getInstance();
                await prefs.remove('docente_foto_$userId');
                if (mounted) {
                  setState(() => _docenteFotoUrl = null);
                }
                Navigator.pop(ctx);
              },
              child: const Text('Restablecer', style: TextStyle(color: Color(0xFFDC2626), fontWeight: FontWeight.w700, fontSize: 12)),
            ),
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Cancelar', style: TextStyle(color: Color(0xFF64748B), fontWeight: FontWeight.w600, fontSize: 12)),
          ),
          ElevatedButton(
            onPressed: () async {
              final newUrl = textController.text.trim();
              final prefs = await SharedPreferences.getInstance();
              if (newUrl.isNotEmpty) {
                await prefs.setString('docente_foto_$userId', newUrl);
                if (mounted) {
                  setState(() => _docenteFotoUrl = newUrl);
                }
              } else {
                await prefs.remove('docente_foto_$userId');
                if (mounted) {
                  setState(() => _docenteFotoUrl = null);
                }
              }
              Navigator.pop(ctx);
              if (mounted) {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(
                    content: Text('Foto de perfil actualizada correctamente'),
                    behavior: SnackBarBehavior.floating,
                  ),
                );
              }
            },
            style: ElevatedButton.styleFrom(
              backgroundColor: AppTheme.primaryBlue,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
            ),
            child: const Text('Guardar', style: TextStyle(color: Colors.white, fontWeight: FontWeight.w700, fontSize: 12)),
          ),
        ],
      ),
    );
  }

  Widget _buildAvatarChoice(String url, TextEditingController controller) {
    return InkWell(
      onTap: () {
        controller.text = url;
      },
      borderRadius: BorderRadius.circular(20),
      child: ClipOval(
        child: Image.network(
          url,
          width: 40,
          height: 40,
          fit: BoxFit.cover,
          errorBuilder: (_, __, ___) => const Icon(Icons.person, size: 28),
        ),
      ),
    );
  }
}
