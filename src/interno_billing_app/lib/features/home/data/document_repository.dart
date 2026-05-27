import 'package:dio/dio.dart';
import 'package:interno_billing_app/features/home/data/models/document_models.dart';

class DocumentRepository {
  final Dio _dio;

  DocumentRepository(this._dio);

  Future<List<InventoryDocumentRow>> listDocuments({
    String? documentType,
    int limit = 50,
    int offset = 0,
  }) async {
    final queryParams = <String, dynamic>{
      'limit': limit,
      'offset': offset,
      'document_type': documentType,
    }..removeWhere((_, v) => v == null);

    final response = await _dio.get(
      'inventory/documents',
      queryParameters: queryParams,
    );

    if (response.statusCode == 200 && response.data['status'] == 'success') {
      final List<dynamic> data = response.data['data'] as List<dynamic>;
      return data
          .map((json) => InventoryDocumentRow.fromJson(json as Map<String, dynamic>))
          .toList();
    }
    return [];
  }
}
