import 'package:dio/dio.dart';
import 'package:shared_preferences/shared_preferences.dart';

class MultiTenantInterceptor extends Interceptor {
  final SharedPreferences _prefs;

  MultiTenantInterceptor(this._prefs);

  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    final companyId = _prefs.getString('company_id');
    if (companyId != null && !options.headers.containsKey('X-Company-ID')) {
      options.headers['X-Company-ID'] = companyId;
    }

    final warehouseId = _prefs.getString('warehouse_id');
    if (warehouseId != null && !options.headers.containsKey('X-Warehouse-ID')) {
      options.headers['X-Warehouse-ID'] = warehouseId;
    }

    final userId = _prefs.getString('user_id');
    if (userId != null && !options.headers.containsKey('X-User-ID')) {
      options.headers['X-User-ID'] = userId;
    }
    
    final token = _prefs.getString('access_token');
    if (token != null && !options.headers.containsKey('Authorization')) {
      options.headers['Authorization'] = 'Bearer $token';
    }

    handler.next(options);
  }
}
