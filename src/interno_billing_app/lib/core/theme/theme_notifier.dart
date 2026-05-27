import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

class ThemeNotifier extends ChangeNotifier {
  static const _key = 'app_theme_mode';

  ThemeMode _mode;
  final SharedPreferences _prefs;

  ThemeNotifier(this._prefs)
      : _mode = _prefs.getString(_key) == 'light' ? ThemeMode.light : ThemeMode.dark;

  ThemeMode get mode => _mode;
  bool get isDark => _mode == ThemeMode.dark;

  void setMode(ThemeMode mode) {
    if (_mode == mode) return;
    _mode = mode;
    _prefs.setString(_key, mode == ThemeMode.light ? 'light' : 'dark');
    notifyListeners();
  }
}
