import 'package:dio/dio.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:interno_billing_app/domain/entities/partner.dart';

class PartnerRepository {
  final Dio _dio;
  final SharedPreferences _prefs;

  PartnerRepository(this._dio, this._prefs);

  Future<List<Partner>> getPartners({String? type}) async {
    try {
      final token = _prefs.getString('access_token') ?? '';
      final companyId = _prefs.getString('company_id') ?? '';

      final response = await _dio.get(
        'partners',
        queryParameters: {
          if (type != null) 'type': type,
        },
        options: Options(headers: {'Authorization': 'Bearer $token'}),
      );

      if (response.statusCode == 200 && response.data['status'] == 'success') {
        final List data = response.data['data'];
        return data.map((json) => Partner.fromJson(json)).toList();
      }
      return [];
    } catch (e) {
      print('getPartners error: $e');
      return [];
    }
  }

  Future<List<Partner>> searchPartners(String query, {String? type}) async {
    try {
      final token = _prefs.getString('access_token') ?? '';
      final companyId = _prefs.getString('company_id') ?? '';

      final response = await _dio.get(
        'partners/search',
        queryParameters: {
          'q': query,
          'company_id': companyId,
          if (type != null) 'type': type,
        },
        options: Options(headers: {'Authorization': 'Bearer $token'}),
      );

      if (response.data['status'] == 'success') {
        final List data = response.data['data'];
        return data.map((json) => Partner.fromJson(json)).toList();
      }
      return [];
    } catch (e) {
      rethrow;
    }
  }
}
