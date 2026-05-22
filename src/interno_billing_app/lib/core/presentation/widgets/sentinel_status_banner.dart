import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:interno_billing_app/core/network/connection_status_provider.dart';
import 'package:interno_billing_app/core/theme/app_theme.dart';

class SentinelStatusBanner extends StatelessWidget {
  const SentinelStatusBanner({super.key});

  @override
  Widget build(BuildContext context) {
    return Consumer<ConnectionStatusProvider>(
      builder: (context, provider, child) {
        if (provider.status == SentinelConnectionStatus.stable) {
          return const SizedBox.shrink();
        }

        final bool isOffline = provider.status == SentinelConnectionStatus.offline;
        
        return Container(
          width: double.infinity,
          padding: const EdgeInsets.symmetric(vertical: 8),
          color: isOffline ? Colors.red : InternoColors.warning,
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(
                isOffline ? Icons.wifi_off : Icons.sync,
                color: Colors.black,
                size: 16,
              ),
              const SizedBox(width: 8),
              Text(
                isOffline ? 'MODO OFFLINE ACTIVADO' : 'RECONECTANDO CON EL SERVIDOR...',
                style: const TextStyle(
                  color: Colors.black,
                  fontWeight: FontWeight.bold,
                  fontSize: 12,
                  letterSpacing: 1,
                ),
              ),
            ],
          ),
        );
      },
    );
  }
}
