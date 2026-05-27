import 'package:get_it/get_it.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:dio/dio.dart';
import 'package:interno_billing_app/core/database/local_database.dart';
import 'package:interno_billing_app/core/network/connection_status_provider.dart';
import 'package:interno_billing_app/core/network/connectivity_service.dart';
import 'package:interno_billing_app/core/network/multi_tenant_interceptor.dart';
import 'package:interno_billing_app/core/network/resilience_interceptor.dart';
import 'package:interno_billing_app/core/services/product_sync_service.dart';
import 'package:interno_billing_app/features/auth/data/auth_repository.dart';
import 'package:interno_billing_app/features/scanner/data/repositories/product_repository.dart';
import 'package:interno_billing_app/features/scanner/data/repositories/sale_repository.dart';
import 'package:interno_billing_app/features/scanner/data/repositories/partner_repository.dart';
import 'package:interno_billing_app/features/scanner/data/repositories/local_draft_repository.dart';
import 'package:interno_billing_app/features/home/data/ticket_repository.dart';
import 'package:interno_billing_app/features/home/data/document_repository.dart';
import 'package:interno_billing_app/features/home/presentation/bloc/tickets_bloc.dart';

final sl = GetIt.instance;

Future<void> init() async {
  // ── Core ──────────────────────────────────────────────────────────────────
  final prefs = await SharedPreferences.getInstance();
  sl.registerSingleton<SharedPreferences>(prefs);

  final dio = Dio(BaseOptions(
    baseUrl: prefs.getString('api_url') ?? 'http://10.0.2.2:8000/api/v1/',
    connectTimeout: const Duration(seconds: 5),
    receiveTimeout: const Duration(seconds: 5),
  ));

  sl.registerSingleton<Dio>(dio);
  sl.registerSingleton<ConnectionStatusProvider>(ConnectionStatusProvider());

  dio.interceptors.addAll([
    MultiTenantInterceptor(prefs),
    ResilienceInterceptor(dio: dio),
    LogInterceptor(requestBody: true, responseBody: true),
  ]);

  // ── Offline-First: Local Database (Drift/SQLite) ──────────────────────────
  final localDb = AppLocalDatabase();
  sl.registerSingleton<AppLocalDatabase>(localDb);

  // ── Connectivity Service ──────────────────────────────────────────────────
  final connectivity = ConnectivityService();
  sl.registerSingleton<ConnectivityService>(connectivity);

  // ── Repositories ──────────────────────────────────────────────────────────
  sl.registerLazySingleton(() => AuthRepository(sl(), sl()));
  sl.registerLazySingleton(() => ProductRepository(sl(), sl(), sl(), sl()));
  sl.registerLazySingleton(() => SaleRepository(sl(), sl()));
  sl.registerLazySingleton(() => PartnerRepository(sl(), sl()));
  sl.registerLazySingleton(() => LocalDraftRepository(sl()));
  sl.registerLazySingleton(() => TicketRepository(sl(), sl()));
  sl.registerLazySingleton(() => DocumentRepository(sl()));

  // ── Blocs ──────────────────────────────────────────────────────────────────
  sl.registerFactory(() => TicketsBloc(ticketRepository: sl()));

  // ── Sync Services ─────────────────────────────────────────────────────────
  sl.registerLazySingleton(() => ProductSyncService(sl(), sl(), sl()));
}
