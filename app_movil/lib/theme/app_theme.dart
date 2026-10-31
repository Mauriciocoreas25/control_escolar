import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

class AppTheme {
  // Colores Institucionales
  static const Color primaryNavy = Color(0xFF1E3A8A); // Royal Blue 900
  static const Color primaryDark = Color(0xFF0F172A); // Slate 900
  static const Color primaryCobalt = Color(0xFF1D4ED8); // Blue 700
  static const Color accentBlue = Color(0xFF2563EB); // Blue 600
  static const Color accentCyan = Color(0xFF06B6D4); // Cyan 500
  static const Color lightBlue = Color(0xFFF0F7FF); // Ice Blue 50

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

  // Degradados Premium
  static const LinearGradient primaryGradient = LinearGradient(
    colors: [Color(0xFF0F172A), Color(0xFF1E3A8A), Color(0xFF2563EB)],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );

  static const LinearGradient buttonGradient = LinearGradient(
    colors: [Color(0xFF1E3A8A), Color(0xFF2563EB), Color(0xFF38BDF8)],
    begin: Alignment.centerLeft,
    end: Alignment.centerRight,
  );

  static const LinearGradient accentGradient = LinearGradient(
    colors: [Color(0xFF2563EB), Color(0xFF06B6D4)],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );

  static const LinearGradient emeraldGradient = LinearGradient(
    colors: [Color(0xFF059669), Color(0xFF10B981)],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );

  static const LinearGradient roseGradient = LinearGradient(
    colors: [Color(0xFFDC2626), Color(0xFFF43F5E)],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );

  static const LinearGradient amberGradient = LinearGradient(
    colors: [Color(0xFFD97706), Color(0xFFFBBF24)],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );

  static const LinearGradient verdeLimonGradient = LinearGradient(
    colors: [Color(0xFF65A30D), Color(0xFF84CC16)],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );

  static const LinearGradient celesteGradient = LinearGradient(
    colors: [Color(0xFF0284C7), Color(0xFF38BDF8)],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );

  static LinearGradient glassCardGradient = LinearGradient(
    colors: [
      Colors.white.withOpacity(0.92),
      Colors.white.withOpacity(0.75),
    ],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );

  static LinearGradient darkGlassGradient = LinearGradient(
    colors: [
      Colors.white.withOpacity(0.14),
      Colors.white.withOpacity(0.04),
    ],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );

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
      ),
      textTheme: textTheme,
      appBarTheme: AppBarTheme(
        backgroundColor: Colors.transparent,
        elevation: 0,
        centerTitle: false,
        iconTheme: const IconThemeData(color: primaryDark),
        titleTextStyle: GoogleFonts.plusJakartaSans(
          color: primaryDark,
          fontSize: 18,
          fontWeight: FontWeight.w800,
          letterSpacing: -0.3,
        ),
      ),
      cardTheme: CardThemeData(
        color: cardSurface,
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
          side: const BorderSide(color: borderSubtle, width: 1),
        ),
      ),
    );
  }
}

/// Contenedor Glassmorphism con desenfoque de fondo y borde iluminado
class GlassContainer extends StatelessWidget {
  final Widget child;
  final double? width;
  final double? height;
  final EdgeInsetsGeometry? padding;
  final EdgeInsetsGeometry? margin;
  final double borderRadius;
  final double blur;
  final Color? color;
  final Gradient? gradient;
  final Border? border;
  final List<BoxShadow>? boxShadow;

  const GlassContainer({
    super.key,
    required this.child,
    this.width,
    this.height,
    this.padding,
    this.margin,
    this.borderRadius = 18,
    this.blur = 16,
    this.color,
    this.gradient,
    this.border,
    this.boxShadow,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      width: width,
      height: height,
      margin: margin,
      child: ClipRRect(
        borderRadius: BorderRadius.circular(borderRadius),
        child: BackdropFilter(
          filter: ImageFilter.blur(sigmaX: blur, sigmaY: blur),
          child: Container(
            padding: padding,
            decoration: BoxDecoration(
              color: color ?? Colors.white.withOpacity(0.80),
              gradient: gradient,
              borderRadius: BorderRadius.circular(borderRadius),
              border: border ??
                  Border.all(
                    color: Colors.white.withOpacity(0.65),
                    width: 1.2,
                  ),
              boxShadow: boxShadow ??
                  [
                    BoxShadow(
                      color: const Color(0xFF0F172A).withOpacity(0.06),
                      blurRadius: 20,
                      offset: const Offset(0, 8),
                    ),
                  ],
            ),
            child: child,
          ),
        ),
      ),
    );
  }
}

/// Fondo ambiental con orbes luminosos en degradado para resaltar el efecto Glassmorphism
class AmbientBackground extends StatelessWidget {
  final Widget child;
  final bool isDark;

  const AmbientBackground({
    super.key,
    required this.child,
    this.isDark = false,
  });

  @override
  Widget build(BuildContext context) {
    final size = MediaQuery.of(context).size;

    return Stack(
      children: [
        // Color Base
        Container(
          color: isDark ? const Color(0xFF090D16) : const Color(0xFFF8FAFC),
        ),

        // Orbe Luminoso Superior Derecho
        Positioned(
          top: -size.width * 0.25,
          right: -size.width * 0.2,
          child: Container(
            width: size.width * 0.9,
            height: size.width * 0.9,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              gradient: RadialGradient(
                colors: isDark
                    ? [
                        const Color(0xFF2563EB).withOpacity(0.40),
                        const Color(0xFF06B6D4).withOpacity(0.15),
                        Colors.transparent,
                      ]
                    : [
                        const Color(0xFF60A5FA).withOpacity(0.25),
                        const Color(0xFF93C5FD).withOpacity(0.10),
                        Colors.transparent,
                      ],
              ),
            ),
          ),
        ),

        // Orbe Luminoso Inferior Izquierdo (Verdecito Tierno / Limón Suave)
        Positioned(
          bottom: -size.width * 0.25,
          left: -size.width * 0.2,
          child: Container(
            width: size.width * 0.85,
            height: size.width * 0.85,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              gradient: RadialGradient(
                colors: isDark
                    ? [
                        const Color(0xFF059669).withOpacity(0.35),
                        const Color(0xFF1E3A8A).withOpacity(0.15),
                        Colors.transparent,
                      ]
                    : [
                        const Color(0xFFD9F99D).withOpacity(0.35),
                        const Color(0xFFBAE6FD).withOpacity(0.15),
                        Colors.transparent,
                      ],
              ),
            ),
          ),
        ),

        // Orbe Centro-Derecha Sutil
        Positioned(
          top: size.height * 0.45,
          right: -size.width * 0.35,
          child: Container(
            width: size.width * 0.7,
            height: size.width * 0.7,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              gradient: RadialGradient(
                colors: isDark
                    ? [
                        const Color(0xFF0EA5E9).withOpacity(0.20),
                        Colors.transparent,
                      ]
                    : [
                        const Color(0xFFBAE6FD).withOpacity(0.20),
                        Colors.transparent,
                      ],
              ),
            ),
          ),
        ),

        // Contenido Principal
        child,
      ],
    );
  }
}
