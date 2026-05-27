import 'package:flutter/material.dart';

class InternoColors {
  static const Color cyan = Color(0xFF00E5FF);
  static const Color success = Color(0xFF00C853);
  static const Color error = Color(0xFFFF1744);
  static const Color warning = Color(0xFFFFD600);
  static const Color textPrimary = Colors.white;
  static const Color textSecondary = Colors.white60;
  static const Color bgDark = Color(0xFF000000);
  static const Color surfaceDark = Color(0xFF111111);
  static const Color lightBg = Color(0xFFF8FAFC);
  static const Color lightBorder = Color(0xFFE2E8F0);
}

class AppTheme {
  // Dark — industrial black / cyan (matches Angular .dark vars)
  static ThemeData get darkTheme {
    return ThemeData(
      brightness: Brightness.dark,
      scaffoldBackgroundColor: const Color(0xFF050B14),
      colorScheme: const ColorScheme.dark(
        primary: InternoColors.cyan,
        secondary: InternoColors.success,
        surface: Color(0xFF0A1628),
        onSurface: Color(0xFFF8FAFC),
      ),
      fontFamily: 'Inter',
      useMaterial3: true,
    );
  }

  // Light — slate/white (matches Angular light vars: surface-bg #f1f5f9, primary #0284c7)
  static ThemeData get lightTheme {
    return ThemeData(
      brightness: Brightness.light,
      scaffoldBackgroundColor: const Color(0xFFF1F5F9),
      colorScheme: const ColorScheme.light(
        primary: Color(0xFF0284C7),
        secondary: Color(0xFF00C853),
        surface: Colors.white,
        onSurface: Color(0xFF0F172A),
        onPrimary: Colors.white,
      ),
      fontFamily: 'Inter',
      useMaterial3: true,
      appBarTheme: const AppBarTheme(
        backgroundColor: Colors.white,
        foregroundColor: Color(0xFF0F172A),
        surfaceTintColor: Colors.transparent,
        elevation: 0,
      ),
      bottomNavigationBarTheme: const BottomNavigationBarThemeData(
        backgroundColor: Colors.white,
        selectedItemColor: Color(0xFF0284C7),
        unselectedItemColor: Color(0xFF94A3B8),
      ),
      cardColor: Colors.white,
      dividerColor: const Color(0xFFCBD5E1),
    );
  }
}
