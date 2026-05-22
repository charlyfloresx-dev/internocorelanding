import 'package:dio/dio.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:interno_billing_app/features/home/data/models/ticket_models.dart';

class TicketRepository {
  final Dio _dio;
  final SharedPreferences _prefs;

  TicketRepository(this._dio, this._prefs);

  Future<List<Ticket>> getTickets() async {
    try {
      final response = await _dio.get('tickets/mine');
      if (response.statusCode == 200 && response.data['status'] == 'success') {
        final List<dynamic> data = response.data['data'];
        return data.map((json) => Ticket.fromJson(json)).toList();
      }
      return [];
    } catch (e) {
      return [];
    }
  }

  Future<Ticket?> createTicket(TicketCreateRequest request) async {
    try {
      final companyId = _prefs.getString('company_id');
      if (companyId == null) {
        throw Exception('Company ID not found in session');
      }

      final response = await _dio.post(
        'tickets/',
        data: request.toJson(companyId),
      );

      if (response.statusCode == 200 && response.data['status'] == 'success') {
        return Ticket.fromJson(response.data['data']);
      }
      return null;
    } catch (e) {
      return null;
    }
  }

  Future<List<TicketComment>> getTicketComments(String ticketId) async {
    try {
      final response = await _dio.get('tickets/$ticketId/comments');
      if (response.statusCode == 200 && response.data['status'] == 'success') {
        final List<dynamic> data = response.data['data'];
        return data.map((json) => TicketComment.fromJson(json)).toList();
      }
      return [];
    } catch (e) {
      return [];
    }
  }

  Future<TicketComment?> addComment(String ticketId, String content) async {
    try {
      final response = await _dio.post(
        'tickets/$ticketId/comments',
        data: {'content': content},
      );
      if (response.statusCode == 200 && response.data['status'] == 'success') {
        return TicketComment.fromJson(response.data['data']);
      }
      return null;
    } catch (e) {
      return null;
    }
  }
}
