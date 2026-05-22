import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:equatable/equatable.dart';
import 'package:interno_billing_app/features/home/data/models/ticket_models.dart';
import 'package:interno_billing_app/features/home/data/ticket_repository.dart';

// --- Events ---
abstract class TicketsEvent extends Equatable {
  const TicketsEvent();
  @override
  List<Object> get props => [];
}

class LoadTickets extends TicketsEvent {}

class CreateTicket extends TicketsEvent {
  final TicketCreateRequest request;
  const CreateTicket(this.request);

  @override
  List<Object> get props => [request];
}

class LoadTicketComments extends TicketsEvent {
  final String ticketId;
  const LoadTicketComments(this.ticketId);

  @override
  List<Object> get props => [ticketId];
}

class AddTicketComment extends TicketsEvent {
  final String ticketId;
  final String content;

  const AddTicketComment({required this.ticketId, required this.content});

  @override
  List<Object> get props => [ticketId, content];
}

// --- States ---
abstract class TicketsState extends Equatable {
  const TicketsState();
  @override
  List<Object?> get props => [];
}

class TicketsInitial extends TicketsState {}

class TicketsLoading extends TicketsState {}

class TicketsLoaded extends TicketsState {
  final List<Ticket> tickets;
  const TicketsLoaded(this.tickets);

  @override
  List<Object> get props => [tickets];
}

class TicketCommentsLoaded extends TicketsState {
  final Ticket ticket;
  final List<TicketComment> comments;
  
  const TicketCommentsLoaded(this.ticket, this.comments);

  @override
  List<Object> get props => [ticket, comments];
}

class TicketActionSuccess extends TicketsState {
  final String message;
  const TicketActionSuccess(this.message);

  @override
  List<Object> get props => [message];
}

class TicketsError extends TicketsState {
  final String message;
  const TicketsError(this.message);

  @override
  List<Object> get props => [message];
}

// --- BLoC ---
class TicketsBloc extends Bloc<TicketsEvent, TicketsState> {
  final TicketRepository ticketRepository;
  
  List<Ticket> _currentTickets = [];
  List<Ticket> get currentTickets => _currentTickets;

  TicketsBloc({required this.ticketRepository}) : super(TicketsInitial()) {
    on<LoadTickets>(_onLoadTickets);
    on<CreateTicket>(_onCreateTicket);
    on<LoadTicketComments>(_onLoadTicketComments);
    on<AddTicketComment>(_onAddTicketComment);
  }

  Future<void> _onLoadTickets(LoadTickets event, Emitter<TicketsState> emit) async {
    emit(TicketsLoading());
    try {
      _currentTickets = await ticketRepository.getTickets();
      emit(TicketsLoaded(_currentTickets));
    } catch (e) {
      emit(const TicketsError('Error al cargar tickets'));
    }
  }

  Future<void> _onCreateTicket(CreateTicket event, Emitter<TicketsState> emit) async {
    emit(TicketsLoading());
    try {
      final newTicket = await ticketRepository.createTicket(event.request);
      if (newTicket != null) {
        _currentTickets.insert(0, newTicket);
        emit(const TicketActionSuccess('Ticket creado exitosamente'));
        emit(TicketsLoaded(_currentTickets));
      } else {
        emit(const TicketsError('No se pudo crear el ticket'));
        emit(TicketsLoaded(_currentTickets));
      }
    } catch (e) {
      emit(const TicketsError('Error al crear ticket'));
      emit(TicketsLoaded(_currentTickets));
    }
  }

  Future<void> _onLoadTicketComments(LoadTicketComments event, Emitter<TicketsState> emit) async {
    emit(TicketsLoading());
    try {
      final ticket = _currentTickets.firstWhere((t) => t.id == event.ticketId);
      final comments = await ticketRepository.getTicketComments(event.ticketId);
      emit(TicketCommentsLoaded(ticket, comments));
    } catch (e) {
      emit(const TicketsError('Error al cargar comentarios'));
      emit(TicketsLoaded(_currentTickets));
    }
  }

  Future<void> _onAddTicketComment(AddTicketComment event, Emitter<TicketsState> emit) async {
    final currentState = state;
    if (currentState is TicketCommentsLoaded) {
      try {
        final newComment = await ticketRepository.addComment(event.ticketId, event.content);
        if (newComment != null) {
          final updatedComments = List<TicketComment>.from(currentState.comments)..add(newComment);
          emit(TicketCommentsLoaded(currentState.ticket, updatedComments));
        } else {
          emit(const TicketsError('No se pudo enviar el mensaje'));
          emit(currentState);
        }
      } catch (e) {
        emit(const TicketsError('Error al enviar mensaje'));
        emit(currentState);
      }
    }
  }
}
