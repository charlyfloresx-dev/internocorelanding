import 'package:dio/dio.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:interno_billing_app/features/scanner/data/models/sale_request.dart';
import 'package:interno_billing_app/features/scanner/data/models/inventory_document_request.dart';

class SaleRepository {
  final Dio _dio;
  final SharedPreferences _prefs;

  SaleRepository(this._dio, this._prefs);

  Future<void> checkout(SaleRequest request) async {
    try {
      final token = _prefs.getString('access_token') ?? '';
      final companyId = _prefs.getString('company_id') ?? '';

      await _dio.post(
        'pos/checkout',
        data: request.toJson(),
        queryParameters: {'company_id': companyId},
      );
    } catch (e) {
      rethrow;
    }
  }

  Future<void> createDocument(InventoryDocumentRequest request) async {
    try {
      final token = _prefs.getString('access_token') ?? '';
      final companyId = _prefs.getString('company_id') ?? '';

      await _dio.post(
        'inventory/documents',
        data: request.toJson(),
        queryParameters: {'company_id': companyId},
      );
    } catch (e) {
      rethrow;
    }
  }
}
