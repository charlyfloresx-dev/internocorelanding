import 'dart:async';
import 'package:dio/dio.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// RTR Semaphore Interceptor
///
/// Handles 401 responses by silently rotating the RTR refresh token.
/// Uses a [Completer<String>] as a semaphore: only one refresh call fires at
/// a time; concurrent 401s queue on the completer and get the new token when
/// the primary refresh completes. On failure, completeError() propagates to
/// all waiters so they fail immediately instead of hanging.
///
/// Flow:
///   N requests expire simultaneously → all get 401
///   → First one starts refresh (sets _refreshCompleter)
///   → Others await _refreshCompleter.future
///   → Primary completes → all retry with new token
///   → Primary fails → all fail → tokens cleared → user sees 401
class AuthInterceptor extends Interceptor {
  final Dio _dio;
  final SharedPreferences _prefs;

  bool _isRefreshing = false;
  Completer<String>? _refreshCompleter;

  AuthInterceptor({required Dio dio, required SharedPreferences prefs})
      : _dio = dio,
        _prefs = prefs;

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) async {
    if (err.response?.statusCode != 401) {
      handler.next(err);
      return;
    }

    final path = err.requestOptions.path;
    // Never attempt refresh for auth endpoints — prevents infinite loops
    final isAuthEndpoint = path.contains('/auth/login') ||
        path.contains('/auth/refresh') ||
        path.contains('/auth/select-company') ||
        path.contains('/auth/collaborator-login');
    // Skip already-retried requests
    final isRetried = err.requestOptions.extra['_retried'] == true;

    if (isAuthEndpoint || isRetried) {
      handler.next(err);
      return;
    }

    try {
      final String newToken;

      if (_isRefreshing) {
        // Queued branch: wait for the primary refresh to finish
        newToken = await _refreshCompleter!.future;
      } else {
        // Primary branch: own the refresh cycle
        final completer = Completer<String>();
        _refreshCompleter = completer;
        _isRefreshing = true;

        try {
          newToken = await _doRefresh();
          completer.complete(newToken);
        } catch (e) {
          completer.completeError(e); // unblocks all waiters with an error
          rethrow;
        } finally {
          _isRefreshing = false;
          _refreshCompleter = null;
        }
      }

      // Retry the original request with the new access token
      err.requestOptions.headers['Authorization'] = 'Bearer $newToken';
      err.requestOptions.extra['_retried'] = true;
      final response = await _dio.fetch(err.requestOptions);
      handler.resolve(response);
    } catch (_) {
      // Refresh failed: clear both tokens so next login is forced
      await _prefs.remove('access_token');
      await _prefs.remove('refresh_token');
      // Pass the original 401 error upstream — BLoC/UI handles logout
      handler.next(err);
    }
  }

  Future<String> _doRefresh() async {
    final refreshToken = _prefs.getString('refresh_token');
    if (refreshToken == null || refreshToken.isEmpty) {
      throw DioException(
        requestOptions: RequestOptions(path: 'auth/refresh'),
        error: 'No refresh token stored',
        type: DioExceptionType.unknown,
      );
    }

    // POST auth/refresh goes through MultiTenantInterceptor (adds stale AT header —
    // harmless, the endpoint extracts company_id from the HMAC-sealed refresh token).
    // ResilienceInterceptor applies transient-error retries (helpful for RDS failover).
    // AuthInterceptor.onError skips /auth/refresh endpoints — no infinite loop.
    final response = await _dio.post(
      'auth/refresh',
      data: {'refresh_token': refreshToken},
    );

    final data = response.data['data'] as Map<String, dynamic>;
    final newAccessToken = data['access_token'] as String;
    final newRefreshToken = data['refresh_token'] as String;

    await _prefs.setString('access_token', newAccessToken);
    await _prefs.setString('refresh_token', newRefreshToken);

    return newAccessToken;
  }
}
