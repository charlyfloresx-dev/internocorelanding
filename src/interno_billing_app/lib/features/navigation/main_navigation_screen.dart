import 'package:flutter/material.dart';
import 'package:interno_billing_app/features/home/presentation/home_screen.dart';
import 'package:interno_billing_app/features/home/presentation/inbox_screen.dart';
import 'package:interno_billing_app/features/home/presentation/tickets_screen.dart';
import 'package:interno_billing_app/features/home/presentation/sales_screen.dart';
import 'package:interno_billing_app/features/home/presentation/receipts_screen.dart';

class MainNavigationScreen extends StatefulWidget {
  const MainNavigationScreen({super.key});

  @override
  State<MainNavigationScreen> createState() => _MainNavigationScreenState();
}

class _MainNavigationScreenState extends State<MainNavigationScreen> {
  int _currentIndex = 0;

  final List<Widget> _screens = [
    const SalesScreen(),
    const ReceiptsScreen(),
    const TicketsScreen(),
    const InboxScreen(), // Using Inbox as Support for now
    const HomeScreen(),  // This is the "Usuario" screen
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: IndexedStack(
        index: _currentIndex,
        children: _screens,
      ),
      bottomNavigationBar: Container(
        decoration: BoxDecoration(
          border: Border(top: BorderSide(color: Colors.white.withValues(alpha: 0.05))),
        ),
        child: BottomNavigationBar(
          currentIndex: _currentIndex,
          onTap: (index) => setState(() => _currentIndex = index),
          backgroundColor: Colors.black,
          selectedItemColor: Colors.white,
          unselectedItemColor: Colors.white24,
          type: BottomNavigationBarType.fixed,
          showSelectedLabels: true,
          showUnselectedLabels: true,
          selectedLabelStyle: const TextStyle(fontSize: 10, fontWeight: FontWeight.bold),
          unselectedLabelStyle: const TextStyle(fontSize: 10),
          items: const [
            BottomNavigationBarItem(icon: Icon(Icons.point_of_sale_outlined), label: 'Ventas'),
            BottomNavigationBarItem(icon: Icon(Icons.receipt_long_outlined), label: 'Recibos'),
            BottomNavigationBarItem(icon: Icon(Icons.confirmation_number_outlined), label: 'Tickets'),
            BottomNavigationBarItem(icon: Icon(Icons.support_agent_outlined), label: 'Soporte'),
            BottomNavigationBarItem(icon: Icon(Icons.person_outline), label: 'Usuario'),
          ],
        ),
      ),
    );
  }
}
