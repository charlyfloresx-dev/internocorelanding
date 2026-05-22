import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';
import '../models/draft_sale.dart';

class LocalDraftRepository {
  final SharedPreferences _prefs;
  static const String _key = 'current_draft_sale';

  LocalDraftRepository(this._prefs);

  Future<bool> saveDraft(DraftSale draft) async {
    try {
      final jsonStr = json.encode(draft.toJson());
      return await _prefs.setString(_key, jsonStr);
    } catch (e) {
      return false;
    }
  }

  DraftSale? loadDraft() {
    try {
      final jsonStr = _prefs.getString(_key);
      if (jsonStr != null) {
        final decoded = json.decode(jsonStr) as Map<String, dynamic>;
        return DraftSale.fromJson(decoded);
      }
    } catch (e) {
      // Fail-silent
    }
    return null;
  }

  Future<bool> clearDraft() async {
    try {
      return await _prefs.remove(_key);
    } catch (e) {
      return false;
    }
  }
}
