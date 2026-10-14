import 'package:flutter/material.dart';
import '../models/models.dart';
import '../services/api_service.dart';
import '../theme/app_theme.dart';
import 'attendance_screen.dart';
import 'courses_screen.dart';
import 'grades_screen.dart';
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

  @override
  void initState() {
    super.initState();
    _loadUser();
  }

  Future<void> _loadUser() async {
    final user = await ApiService.getCurrentUser();
    setState(() => _currentUser = user);
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
        title: const Text('Cerrar Sesión', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
        content: const Text('¿Está seguro de que desea salir de la aplicación?', style: TextStyle(fontSize: 13)),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('Cancelar'),
          ),
          ElevatedButton(
            style: ElevatedButton.styleFrom(
              backgroundColor: AppTheme.statusAusente,
              foregroundColor: Colors.white,
            ),
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text('Cerrar Sesión'),
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
      CoursesScreen(onNavigateTab: _onNavigateTab),
      AttendanceScreen(selectedCourse: _selectedCourseForAction),
      GradesScreen(selectedCourse: _selectedCourseForAction),
    ];

    return Scaffold(
      body: screens[_currentIndex],
      drawer: Drawer(
        child: SafeArea(
          child: Column(
            children: [
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(20),
                color: AppTheme.primaryNavy,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Container(
                      width: 50,
                      height: 50,
                      decoration: BoxDecoration(
                        color: Colors.white,
                        borderRadius: BorderRadius.circular(12),
                      ),
                      alignment: Alignment.center,
                      child: const Text(
                        'DOC',
                        style: TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.w800,
                          color: AppTheme.primaryNavy,
                        ),
                      ),
                    ),
                    const SizedBox(height: 12),
                    Text(
                      _currentUser?['nombre'] ?? 'Prof. Carlos Juan Pérez',
                      style: const TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.bold),
                    ),
                    Text(
                      _currentUser?['correo'] ?? 'docente@santabartolome.edu.sv',
                      style: const TextStyle(color: Color(0xFF93C5FD), fontSize: 12),
                    ),
                    const SizedBox(height: 6),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                      decoration: BoxDecoration(
                        color: Colors.white.withOpacity(0.15),
                        borderRadius: BorderRadius.circular(6),
                      ),
                      child: const Text(
                        'Docente Autorizado',
                        style: TextStyle(color: Colors.white, fontSize: 10, fontWeight: FontWeight.bold),
                      ),
                    ),
                  ],
                ),
              ),

              ListTile(
                leading: const Icon(Icons.school_outlined, color: AppTheme.primaryNavy),
                title: const Text('Mis Cursos Asignados', style: TextStyle(fontSize: 13, fontWeight: FontWeight.w600)),
                selected: _currentIndex == 0,
                onTap: () {
                  Navigator.pop(context);
                  _onNavigateTab(0);
                },
              ),
              ListTile(
                leading: const Icon(Icons.fact_check_outlined, color: AppTheme.primaryNavy),
                title: const Text('Pase de Asistencia', style: TextStyle(fontSize: 13, fontWeight: FontWeight.w600)),
                selected: _currentIndex == 1,
                onTap: () {
                  Navigator.pop(context);
                  _onNavigateTab(1);
                },
              ),
              ListTile(
                leading: const Icon(Icons.assignment_turned_in_outlined, color: AppTheme.primaryNavy),
                title: const Text('Registro de Notas', style: TextStyle(fontSize: 13, fontWeight: FontWeight.w600)),
                selected: _currentIndex == 2,
                onTap: () {
                  Navigator.pop(context);
                  _onNavigateTab(2);
                },
              ),

              const Divider(),

              ListTile(
                leading: const Icon(Icons.info_outline, color: Color(0xFF64748B)),
                title: const Text('Configuración Servidor API', style: TextStyle(fontSize: 13)),
                subtitle: Text(ApiService.baseUrl, style: const TextStyle(fontSize: 11)),
                onTap: () {
                  Navigator.pop(context);
                  _showServerConfigDialog();
                },
              ),

              const Spacer(),

              ListTile(
                leading: const Icon(Icons.logout, color: AppTheme.statusAusente),
                title: const Text('Cerrar Sesión', style: TextStyle(fontSize: 13, color: AppTheme.statusAusente, fontWeight: FontWeight.w700)),
                onTap: _handleLogout,
              ),
              const SizedBox(height: 12),
            ],
          ),
        ),
      ),
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _currentIndex,
        onTap: (index) => setState(() => _currentIndex = index),
        items: const [
          BottomNavigationBarItem(
            icon: Icon(Icons.book_outlined),
            activeIcon: Icon(Icons.book),
            label: 'Mis Cursos',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.check_circle_outline),
            activeIcon: Icon(Icons.check_circle),
            label: 'Asistencia',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.edit_note_outlined),
            activeIcon: Icon(Icons.edit_note),
            label: 'Notas',
          ),
        ],
      ),
    );
  }

  void _showServerConfigDialog() {
    final controller = TextEditingController(text: ApiService.baseUrl);
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Servidor API FastAPI', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'IP/Host del Backend (puerto 8001):',
              style: TextStyle(fontSize: 12, color: Color(0xFF64748B)),
            ),
            const SizedBox(height: 8),
            TextField(
              controller: controller,
              decoration: const InputDecoration(
                border: OutlineInputBorder(),
                isDense: true,
                hintText: 'http://10.0.2.2:8001',
              ),
            ),
          ],
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cancelar')),
          ElevatedButton(
            onPressed: () {
              ApiService.setBaseUrl(controller.text.trim());
              Navigator.pop(ctx);
              ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(content: Text('Servidor actualizado a: ${controller.text.trim()}')),
              );
            },
            child: const Text('Guardar'),
          ),
        ],
      ),
    );
  }
}
