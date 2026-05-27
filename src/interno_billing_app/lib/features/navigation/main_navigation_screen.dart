import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:easy_localization/easy_localization.dart';
import 'package:interno_billing_app/features/home/presentation/home_screen.dart';
import 'package:interno_billing_app/features/home/presentation/create_ticket_screen.dart';
import 'package:interno_billing_app/features/home/presentation/tickets_screen.dart';
import 'package:interno_billing_app/features/scanner/presentation/scanner_screen.dart';
import 'package:interno_billing_app/features/scanner/presentation/bloc/scanner_bloc.dart';

class MainNavigationScreen extends StatefulWidget {
  const MainNavigationScreen({super.key});

  @override
  State<MainNavigationScreen> createState() => _MainNavigationScreenState();
}

class _MainNavigationScreenState extends State<MainNavigationScreen> {
  int _currentIndex = 0;

  // Tabs 0 (Ventas) and 1 (Recibos) share the same ScannerScreen instance.
  static const _physicalSlots = [0, 0, 1, 2, 3];

  final ValueNotifier<bool> _scannerActive = ValueNotifier(true);

  late final List<Widget> _physicalScreens;

  @override
  void initState() {
    super.initState();
    _physicalScreens = [
      ScannerScreen(isTabMode: true, isActiveNotifier: _scannerActive),
      const TicketsScreen(),
      const CreateTicketScreen(),
      const HomeScreen(),
    ];
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) return;
      final mode = context.read<ScannerBloc>().state.mode;
      if (mode == ScannerMode.entry) {
        setState(() => _currentIndex = 1);
      }
    });
  }

  @override
  void dispose() {
    _scannerActive.dispose();
    super.dispose();
  }

  void _onTabTapped(int index) {
    setState(() => _currentIndex = index);
    _scannerActive.value = index == 0 || index == 1;
    final bloc = context.read<ScannerBloc>();
    if (index == 0) bloc.add(ModeSelected(ScannerMode.sale));
    if (index == 1) bloc.add(ModeSelected(ScannerMode.entry));
  }

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    final scaffoldBg = Theme.of(context).scaffoldBackgroundColor;

    return Scaffold(
      body: IndexedStack(
        index: _physicalSlots[_currentIndex],
        children: _physicalScreens,
      ),
      bottomNavigationBar: Container(
        decoration: BoxDecoration(
          border: Border(top: BorderSide(color: Theme.of(context).dividerColor)),
        ),
        child: BottomNavigationBar(
          currentIndex: _currentIndex,
          onTap: _onTabTapped,
          backgroundColor: scaffoldBg,
          selectedItemColor: cs.primary,
          unselectedItemColor: cs.onSurface.withValues(alpha: 0.35),
          type: BottomNavigationBarType.fixed,
          showSelectedLabels: true,
          showUnselectedLabels: true,
          selectedLabelStyle: const TextStyle(fontSize: 10, fontWeight: FontWeight.bold),
          unselectedLabelStyle: const TextStyle(fontSize: 10),
          items: [
            BottomNavigationBarItem(icon: const Icon(Icons.point_of_sale_outlined), label: 'nav.sales'.tr()),
            BottomNavigationBarItem(icon: const Icon(Icons.receipt_long_outlined), label: 'nav.receipts'.tr()),
            BottomNavigationBarItem(icon: const Icon(Icons.confirmation_number_outlined), label: 'nav.tickets'.tr()),
            BottomNavigationBarItem(icon: const Icon(Icons.support_agent_outlined), label: 'nav.support'.tr()),
            BottomNavigationBarItem(icon: const Icon(Icons.person_outline), label: 'nav.user'.tr()),
          ],
        ),
      ),
    );
  }
}
