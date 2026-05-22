import 'package:dio/dio.dart';
import 'package:uuid/uuid.dart';
import 'package:interno_billing_app/core/network/connection_status_provider.dart';
import 'package:interno_billing_app/core/di/injection.dart';

class ResilienceInterceptor extends Interceptor {
  final int maxRetries = 3;
  final Dio dio;

  ResilienceInterceptor({required this.dio});

  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    final isMutating = ['POST', 'PUT', 'PATCH', 'DELETE'].contains(options.method.toUpperCase());
    
    if (isMutating && !options.headers.containsKey('X-Idempotency-Key')) {
      options.headers['X-Idempotency-Key'] = const Uuid().v4();
    }
    
    handler.next(options);
  }

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) async {
    final isTransient = err.type == DioExceptionType.connectionTimeout || 
                        err.type == DioExceptionType.receiveTimeout ||
                        err.response?.statusCode == 503 ||
                        err.response?.statusCode == 504;
                         
    final responseData = err.response?.data;
    final isReconnecting = responseData is Map && 
                           responseData['meta']?['code'] == 'DATABASE_RECONNECTING';

    if (isReconnecting) {
      sl<ConnectionStatusProvider>().updateStatus(SentinelConnectionStatus.reconnecting);
    } else if (err.type == DioExceptionType.connectionTimeout) {
      sl<ConnectionStatusProvider>().updateStatus(SentinelConnectionStatus.offline);
    }

    if ((isTransient || isReconnecting) && _shouldRetry(err.requestOptions)) {
      final int retryAttempt = (err.requestOptions.extra['retryCount'] ?? 0) + 1;
      
      if (retryAttempt <= maxRetries) {
        final delaySeconds = (2 * retryAttempt); 
        await Future.delayed(Duration(seconds: delaySeconds));

        final options = err.requestOptions;
        options.extra['retryCount'] = retryAttempt;

        try {
          final response = await dio.fetch(options);
          sl<ConnectionStatusProvider>().updateStatus(SentinelConnectionStatus.stable);
          return handler.resolve(response);
        } on DioException catch (retryError) {
          return handler.next(retryError);
        }
      }
    }
    
    handler.next(err);
  }

  bool _shouldRetry(RequestOptions options) {
    return (options.extra['retryCount'] ?? 0) < maxRetries;
  }
}
