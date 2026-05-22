import 'package:flutter/foundation.dart';

enum SentinelConnectionStatus { stable, reconnecting, offline }

class ConnectionStatusProvider extends ChangeNotifier {
  SentinelConnectionStatus _status = SentinelConnectionStatus.stable;
  
  SentinelConnectionStatus get status => _status;

  void updateStatus(SentinelConnectionStatus newStatus) {
    if (_status != newStatus) {
      _status = newStatus;
      notifyListeners();
    }
  }
}
