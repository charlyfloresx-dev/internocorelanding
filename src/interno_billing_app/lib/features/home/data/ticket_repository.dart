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

  Future<List<TicketAction>> getTicketActions(String ticketId) async {
    try {
      final response = await _dio.get('tickets/$ticketId/actions');
      if (response.statusCode == 200 && response.data['status'] == 'success') {
        final List<dynamic> data = response.data['data'];
        return data.map((json) => TicketAction.fromJson(json)).toList();
      }
      return [];
    } catch (e) {
      return [];
    }
  }

  Future<TicketAction?> createAction(
    String ticketId, {
    required String description,
    String? assignedToId,
    DateTime? commitDate,
  }) async {
    try {
      final body = <String, dynamic>{'description': description};
      if (assignedToId != null) body['assigned_to_id'] = assignedToId;
      if (commitDate != null) body['commit_date'] = commitDate.toUtc().toIso8601String();
      final response = await _dio.post('tickets/$ticketId/actions', data: body);
      if (response.statusCode == 200 && response.data['status'] == 'success') {
        return TicketAction.fromJson(response.data['data']);
      }
      return null;
    } catch (e) {
      return null;
    }
  }

  Future<bool> closeAction(String ticketId, String actionId) async {
    try {
      final response = await _dio.patch('tickets/$ticketId/actions/$actionId/close');
      return response.statusCode == 200;
    } catch (e) {
      return false;
    }
  }

  Future<List<Department>> getDepartments() async {
    try {
      final response = await _dio.get(
        'hcm/departments/',
        queryParameters: {'is_active': true, 'limit': 100},
      );
      if (response.statusCode == 200 && response.data['status'] == 'success') {
        final List<dynamic> data = response.data['data'];
        return data.map((json) => Department.fromJson(json)).toList();
      }
      return [];
    } catch (_) {
      return [];
    }
  }
}
