import 'package:flutter/material.dart';
import 'package:interno_billing_app/core/theme/app_theme.dart';

class InboxScreen extends StatelessWidget {
  const InboxScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      appBar: AppBar(
        backgroundColor: Colors.black,
        title: const Text('BANDEJA DE ENTRADA', style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold, letterSpacing: 1)),
        actions: [
          IconButton(icon: const Icon(Icons.archive_outlined), onPressed: () {}),
        ],
      ),
      body: Column(
        children: [
          // ── Filters ──────────────────────────────────────────────────────
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            child: Row(
              children: [
                _buildFilterChip('Todo', true),
                _buildFilterChip('Mensajes', false),
                _buildFilterChip('Alertas', false),
                _buildFilterChip('Actualizaciones', false),
              ],
            ),
          ),
          
          const SizedBox(height: 16),
          
          // ── Notification List ─────────────────────────────────────────────
          Expanded(
            child: ListView(
              children: [
                _buildSectionHeader('HOY'),
                _buildNotificationItem(
                  icon: Icons.book_outlined,
                  title: 'Inicia tu experiencia y mejora tu seguridad en planta',
                  time: 'Hace 4 horas',
                  isRead: false,
                ),
                const SizedBox(height: 16),
                _buildSectionHeader('ANTERIORES'),
                _buildNotificationItem(
                  icon: Icons.emoji_events_outlined,
                  title: '¡Recibiste un bono de productividad!',
                  time: 'Ayer',
                  isRead: true,
                ),
                _buildNotificationItem(
                  icon: Icons.warning_amber_rounded,
                  title: 'Mantenimiento preventivo en Almacén A-12',
                  time: 'Hace 3 días',
                  isRead: true,
                ),
                _buildNotificationItem(
                  icon: Icons.campaign_outlined,
                  title: 'Nuevos protocolos de despacho industrial',
                  time: 'Hace 4 días',
                  isRead: true,
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildFilterChip(String label, bool isActive) {
    return Container(
      margin: const EdgeInsets.only(right: 8),
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      decoration: BoxDecoration(
        color: isActive ? Colors.white : const Color(0xFF1A1A1A),
        borderRadius: BorderRadius.circular(20),
      ),
      child: Text(
        label,
        style: TextStyle(
          color: isActive ? Colors.black : Colors.white70,
          fontWeight: FontWeight.bold,
          fontSize: 12,
        ),
      ),
    );
  }

  Widget _buildSectionHeader(String title) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: Text(
        title,
        style: const TextStyle(color: Colors.white54, fontSize: 14, fontWeight: FontWeight.bold),
      ),
    );
  }

  Widget _buildNotificationItem({
    required IconData icon,
    required String title,
    required String time,
    required bool isRead,
  }) {
    return ListTile(
      leading: Container(
        padding: const EdgeInsets.all(10),
        decoration: const BoxDecoration(color: Color(0xFF1A1A1A), shape: BoxShape.circle),
        child: Icon(icon, color: Colors.white, size: 24),
      ),
      title: Text(
        title,
        style: TextStyle(
          color: Colors.white,
          fontSize: 15,
          fontWeight: isRead ? FontWeight.normal : FontWeight.bold,
        ),
      ),
      subtitle: Text(time, style: const TextStyle(color: Colors.white38, fontSize: 12)),
      trailing: !isRead ? const Icon(Icons.circle, color: InternoColors.cyan, size: 8) : null,
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
    );
  }
}
