import 'package:dio/dio.dart';
import 'package:shared_preferences/shared_preferences.dart';

class AuthRepository {
  final Dio _dio;
  final SharedPreferences _prefs;

  AuthRepository(this._dio, this._prefs);

  Future<bool> login(String username, String password) async {
    try {
      final response = await _dio.post(
        'auth/login',
        data: {'username': username, 'password': password},
      );

      if (response.statusCode == 200) {
        final data = response.data['data'];
        await _prefs.setString('access_token', data['access_token']);
        return true;
      }
      return false;
    } catch (e) {
      return false;
    }
  }

  Future<List<Map<String, dynamic>>> getCompanies() async {
    try {
      final token = _prefs.getString('access_token') ?? '';
      final response = await _dio.get(
        'companies',
        options: Options(headers: {'Authorization': 'Bearer $token'}),
      );
      if (response.data['status'] == 'success') {
        return List<Map<String, dynamic>>.from(response.data['data']);
      }
      return [];
    } catch (e) {
      return [];
    }
  }

  Future<List<Map<String, dynamic>>> getWarehouses(String companyId) async {
    try {
      final token = _prefs.getString('access_token') ?? '';
      final response = await _dio.get(
        'warehouses',
        queryParameters: {'company_id': companyId},
        options: Options(headers: {'Authorization': 'Bearer $token'}),
      );
      if (response.data['status'] == 'success') {
        return List<Map<String, dynamic>>.from(response.data['data']);
      }
      return [];
    } catch (e) {
      return [];
    }
  }

  Future<void> logout() async {
    await _prefs.remove('access_token');
    await _prefs.remove('company_id');
  }

  bool get isAuthenticated => _prefs.containsKey('access_token');
}
