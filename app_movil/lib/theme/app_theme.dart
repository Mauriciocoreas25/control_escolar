import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

class AppTheme {
  // Colores Institucionales basados en el Prototipo Figma
  static const Color primaryNavy = Color(0xFF1E3A8A); // Deep Royal Blue
  static const Color primaryDark = Color(0xFF0F172A); // Slate 900
  static const Color accentBlue = Color(0xFF2563EB); // Blue 600
  static const Color lightBlue = Color(0xFFEFF6FF); // Blue 50

  static const Color background = Color(0xFFF8FAFC); // Slate 50
  static const Color cardSurface = Colors.white;
  static const Color borderSubtle = Color(0xFFE2E8F0); // Slate 200

  // Colores de Asistencia y Rendimiento
  static const Color statusPresente = Color(0xFF059669); // Emerald 600
  static const Color statusPresenteBg = Color(0xFFECFDF5); // Emerald 50
  static const Color statusAusente = Color(0xFFDC2626); // Rose 600
  static const Color statusAusenteBg = Color(0xFFFEF2F2); // Rose 50
  static const Color statusJustificado = Color(0xFFD97706); // Amber 600
  static const Color statusJustificadoBg = Color(0xFFFFFBEB); // Amber 50

  static ThemeData get theme {
    final textTheme = GoogleFonts.plusJakartaSansTextTheme();

    return ThemeData(
      useMaterial3: true,
      scaffoldBackgroundColor: background,
      primaryColor: primaryNavy,
      colorScheme: ColorScheme.fromSeed(
        seedColor: primaryNavy,
        primary: primaryNavy,
        secondary: accentBlue,
        surface: cardSurface,
        background: background,
      ),
      textTheme: textTheme,
      appBarTheme: AppBarTheme(
        backgroundColor: Colors.white,
        elevation: 0,
        centerTitle: false,
        iconTheme: const IconThemeData(color: primaryDark),
        titleTextStyle: GoogleFonts.plusJakartaSans(
          color: primaryDark,
          fontSize: 18,
          fontWeight: FontWeight.w700,
        ),
      ),
      cardTheme: CardThemeData(
        color: cardSurface,
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(14),
          side: const BorderSide(color: borderSubtle, width: 1),
        ),
      ),
      bottomNavigationBarTheme: BottomNavigationBarThemeData(
        backgroundColor: Colors.white,
        selectedItemColor: primaryNavy,
        unselectedItemColor: const Color(0xFF64748B),
        selectedLabelStyle: GoogleFonts.plusJakartaSans(
          fontSize: 12,
          fontWeight: FontWeight.w700,
        ),
        unselectedLabelStyle: GoogleFonts.plusJakartaSans(
          fontSize: 12,
          fontWeight: FontWeight.w500,
        ),
        type: BottomNavigationBarType.fixed,
        elevation: 8,
      ),
    );
  }
}
