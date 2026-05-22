import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:intl/intl.dart';
import 'package:interno_billing_app/core/theme/app_theme.dart';
import 'package:interno_billing_app/features/home/data/models/ticket_models.dart';
import 'package:interno_billing_app/features/home/presentation/bloc/tickets_bloc.dart';
import 'package:interno_billing_app/features/home/presentation/create_ticket_screen.dart';
import 'package:interno_billing_app/features/home/presentation/ticket_chat_screen.dart';

class TicketsScreen extends StatelessWidget {
  const TicketsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      appBar: AppBar(
        backgroundColor: Colors.black,
        title: const Text('TICKETS DE SOPORTE', style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold, letterSpacing: 1)),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh, color: Colors.white),
            onPressed: () => context.read<TicketsBloc>().add(LoadTickets()),
          )
        ],
      ),
      body: BlocConsumer<TicketsBloc, TicketsState>(
        listener: (context, state) {
          if (state is TicketActionSuccess) {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(content: Text(state.message), backgroundColor: InternoColors.success),
            );
          }
        },
        builder: (context, state) {
          List<Ticket> tickets = [];
          if (state is TicketsLoaded) {
            tickets = state.tickets;
          } else if (state is TicketCommentsLoaded) {
            tickets = context.read<TicketsBloc>().currentTickets;
          } else {
            tickets = context.read<TicketsBloc>().currentTickets;
          }

          final pending = tickets.where((t) => t.status != TicketStatus.closed && t.status != TicketStatus.canceled && t.status != TicketStatus.resolved).length;
          final closed = tickets.where((t) => t.status == TicketStatus.closed || t.status == TicketStatus.resolved).length;

          return Padding(
            padding: const EdgeInsets.all(24.0),
            child: Column(
              children: [
                _buildTicketSummary(pending.toString(), closed.toString()),
                const SizedBox(height: 32),
                Expanded(
                  child: state is TicketsLoading && tickets.isEmpty
                      ? const Center(child: CircularProgressIndicator(color: InternoColors.cyan))
                      : tickets.isEmpty
                          ? const Center(child: Text('No hay tickets activos', style: TextStyle(color: Colors.white38)))
                          : ListView.builder(
                              itemCount: tickets.length,
                              itemBuilder: (context, index) {
                                final t = tickets[index];
                                return GestureDetector(
                                  onTap: () {
                                    Navigator.push(
                                      context,
                                      MaterialPageRoute(builder: (_) => TicketChatScreen(ticket: t)),
                                    ).then((_) {
                                      // Reload tickets when back to reflect any status change or we just reload.
                                      context.read<TicketsBloc>().add(LoadTickets());
                                    });
                                  },
                                  child: _buildTicketItem(t),
                                );
                              },
                            ),
                ),
                const SizedBox(height: 16),
                ElevatedButton(
                  onPressed: () {
                    Navigator.push(
                      context,
                      MaterialPageRoute(builder: (_) => const CreateTicketScreen()),
                    );
                  },
                  style: ElevatedButton.styleFrom(
                    backgroundColor: InternoColors.cyan,
                    foregroundColor: Colors.black,
                    minimumSize: const Size(double.infinity, 56),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                  ),
                  child: const Text('CREAR NUEVO TICKET', style: TextStyle(fontWeight: FontWeight.bold)),
                ),
              ],
            ),
          );
        },
      ),
    );
  }

  Widget _buildTicketSummary(String pending, String closed) {
    return Container(
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: const Color(0xFF1A1A1A),
        borderRadius: BorderRadius.circular(24),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceAround,
        children: [
          _buildSummaryStat(pending, 'PENDIENTES'),
          Container(width: 1, height: 40, color: Colors.white10),
          _buildSummaryStat(closed, 'CERRADOS/RESUELTOS'),
        ],
      ),
    );
  }

  Widget _buildSummaryStat(String val, String label) {
    return Column(
      children: [
        Text(val, style: const TextStyle(color: Colors.white, fontSize: 24, fontWeight: FontWeight.bold)),
        Text(label, style: const TextStyle(color: Colors.white38, fontSize: 10, fontWeight: FontWeight.bold)),
      ],
    );
  }

  Widget _buildTicketItem(Ticket ticket) {
    Color statusColor = Colors.grey;
    if (ticket.status == TicketStatus.newTicket || ticket.status == TicketStatus.pending) statusColor = Colors.amber;
    if (ticket.status == TicketStatus.resolved || ticket.status == TicketStatus.closed) statusColor = InternoColors.success;
    if (ticket.status == TicketStatus.inProgress) statusColor = InternoColors.cyan;

    // Priority color for the left indicator bar
    Color priorityColor;
    String priorityLabel;
    IconData priorityIcon;
    switch (ticket.priority) {
      case TicketPriority.critical:
        priorityColor = const Color(0xFFFF3B30);
        priorityLabel = 'CRÍTICA';
        priorityIcon = Icons.warning_amber_rounded;
        break;
      case TicketPriority.high:
        priorityColor = const Color(0xFFFF9500);
        priorityLabel = 'ALTA';
        priorityIcon = Icons.arrow_upward_rounded;
        break;
      case TicketPriority.low:
        priorityColor = const Color(0xFF8E8E93);
        priorityLabel = 'BAJA';
        priorityIcon = Icons.arrow_downward_rounded;
        break;
      case TicketPriority.medium:
      default:
        priorityColor = const Color(0xFFFFCC00);
        priorityLabel = 'MEDIA';
        priorityIcon = Icons.remove_rounded;
        break;
    }

    final bool isAssigned = ticket.assignedToId != null;

    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      decoration: BoxDecoration(
        color: const Color(0xFF111111),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.white10),
      ),
      child: IntrinsicHeight(
        child: Row(
          children: [
            // Priority indicator bar
            Container(
              width: 4,
              decoration: BoxDecoration(
                color: priorityColor,
                borderRadius: const BorderRadius.only(
                  topLeft: Radius.circular(16),
                  bottomLeft: Radius.circular(16),
                ),
              ),
            ),
            // Content
            Expanded(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Row 1: Reference code + Status badge
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text('#${ticket.referenceCode}', style: const TextStyle(color: InternoColors.cyan, fontWeight: FontWeight.bold, fontSize: 13)),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                          decoration: BoxDecoration(color: statusColor.withOpacity(0.15), borderRadius: BorderRadius.circular(8)),
                          child: Text(ticket.status.name.toUpperCase(), style: TextStyle(color: statusColor, fontSize: 9, fontWeight: FontWeight.bold)),
                        ),
                      ],
                    ),
                    const SizedBox(height: 10),
                    // Row 2: Title
                    Text(ticket.title, style: const TextStyle(color: Colors.white, fontSize: 15, fontWeight: FontWeight.bold), maxLines: 2, overflow: TextOverflow.ellipsis),
                    const SizedBox(height: 10),
                    // Row 3: Priority badge + Area tag + Assignment
                    Wrap(
                      spacing: 8,
                      runSpacing: 6,
                      children: [
                        // Priority badge
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                          decoration: BoxDecoration(
                            color: priorityColor.withOpacity(0.15),
                            borderRadius: BorderRadius.circular(6),
                          ),
                          child: Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Icon(priorityIcon, size: 12, color: priorityColor),
                              const SizedBox(width: 4),
                              Text(priorityLabel, style: TextStyle(color: priorityColor, fontSize: 9, fontWeight: FontWeight.bold)),
                            ],
                          ),
                        ),
                        // Area tag (if present)
                        if (ticket.area != null && ticket.area!.isNotEmpty)
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                            decoration: BoxDecoration(
                              color: Colors.white.withOpacity(0.05),
                              borderRadius: BorderRadius.circular(6),
                            ),
                            child: Text(ticket.area!, style: const TextStyle(color: Colors.white54, fontSize: 9, fontWeight: FontWeight.bold)),
                          ),
                        // Assignment indicator
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                          decoration: BoxDecoration(
                            color: isAssigned ? InternoColors.cyan.withOpacity(0.1) : Colors.white.withOpacity(0.05),
                            borderRadius: BorderRadius.circular(6),
                          ),
                          child: Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Icon(
                                isAssigned ? Icons.person_rounded : Icons.person_outline_rounded,
                                size: 12,
                                color: isAssigned ? InternoColors.cyan : Colors.white38,
                              ),
                              const SizedBox(width: 4),
                              Text(
                                isAssigned ? 'Asignado' : 'Sin asignar',
                                style: TextStyle(color: isAssigned ? InternoColors.cyan : Colors.white38, fontSize: 9, fontWeight: FontWeight.bold),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    // Row 4: Date
                    Text(
                      'Reportado el ${DateFormat('dd MMM yyyy').format(ticket.createdAt)}',
                      style: const TextStyle(color: Colors.white24, fontSize: 11),
                    ),
                  ],
                ),
              ),
            ),
            // Chevron
            const Padding(
              padding: EdgeInsets.only(right: 12),
              child: Icon(Icons.chevron_right_rounded, color: Colors.white24, size: 20),
            ),
          ],
        ),
      ),
    );
  }
}
