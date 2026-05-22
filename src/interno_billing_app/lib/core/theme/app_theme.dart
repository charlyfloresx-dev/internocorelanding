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
  static ThemeData get darkTheme {
    return ThemeData(
      brightness: Brightness.dark,
      scaffoldBackgroundColor: Colors.black,
      colorScheme: const ColorScheme.dark(
        primary: InternoColors.cyan,
        secondary: InternoColors.success,
        surface: InternoColors.surfaceDark,
      ),
      fontFamily: 'Inter',
      useMaterial3: true,
    );
  }
}
