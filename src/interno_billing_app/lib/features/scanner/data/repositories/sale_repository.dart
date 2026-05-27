import 'package:dio/dio.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:interno_billing_app/features/scanner/data/models/sale_request.dart';
import 'package:interno_billing_app/features/scanner/data/models/inventory_document_request.dart';

class SaleRepository {
  final Dio _dio;
  final SharedPreferences _prefs;

  SaleRepository(this._dio, this._prefs);

  Future<Map<String, dynamic>> checkout(SaleRequest request) async {
    try {
      final token = _prefs.getString('access_token') ?? '';
      final companyId = _prefs.getString('company_id') ?? '';

      final response = await _dio.post(
        'pos/checkout',
        data: request.toJson(),
        queryParameters: {'company_id': companyId},
      );
      return response.data as Map<String, dynamic>;
    } catch (e) {
      rethrow;
    }
  }

  Future<Map<String, dynamic>> createDocument(InventoryDocumentRequest request) async {
    try {
      final token = _prefs.getString('access_token') ?? '';
      final companyId = _prefs.getString('company_id') ?? '';

      final response = await _dio.post(
        'inventory/documents',
        data: request.toJson(),
        queryParameters: {'company_id': companyId},
        options: Options(
          headers: {
            'X-Client-Request-ID': request.correlationId,
          },
        ),
      );
      return response.data as Map<String, dynamic>;
    } catch (e) {
      rethrow;
    }
  }
}
