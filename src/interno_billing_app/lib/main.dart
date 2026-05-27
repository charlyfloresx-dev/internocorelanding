import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:easy_localization/easy_localization.dart';
import 'package:provider/provider.dart';
import 'package:interno_billing_app/core/di/injection.dart' as di;
import 'package:interno_billing_app/core/theme/app_theme.dart';
import 'package:interno_billing_app/core/theme/theme_notifier.dart';
import 'package:interno_billing_app/core/network/connection_status_provider.dart';
import 'package:interno_billing_app/features/auth/presentation/setup_screen.dart';
import 'package:interno_billing_app/features/scanner/presentation/bloc/scanner_bloc.dart';
import 'package:interno_billing_app/features/home/presentation/bloc/tickets_bloc.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await EasyLocalization.ensureInitialized();
  await di.init();

  runApp(
    EasyLocalization(
      supportedLocales: const [Locale('en'), Locale('es')],
      path: 'assets/translations',
      fallbackLocale: const Locale('es'),
      child: const InternoApp(),
    ),
  );
}

class InternoApp extends StatelessWidget {
  const InternoApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => di.sl<ConnectionStatusProvider>()),
        ChangeNotifierProvider(create: (_) => ThemeNotifier(di.sl())),
      ],
      child: Consumer<ThemeNotifier>(
        builder: (context, themeNotifier, _) => MultiBlocProvider(
          providers: [
            BlocProvider(
              create: (context) => ScannerBloc(
                repository: di.sl(),
                saleRepository: di.sl(),
                localDraftRepository: di.sl(),
              ),
            ),
            BlocProvider(
              create: (context) => di.sl<TicketsBloc>()..add(LoadTickets()),
            ),
          ],
          child: MaterialApp(
            title: 'InternoCore',
            theme: AppTheme.lightTheme,
            darkTheme: AppTheme.darkTheme,
            themeMode: themeNotifier.mode,
            debugShowCheckedModeBanner: false,
            localizationsDelegates: context.localizationDelegates,
            supportedLocales: context.supportedLocales,
            locale: context.locale,
            home: const SetupScreen(),
          ),
        ),
      ),
    );
  }
}
