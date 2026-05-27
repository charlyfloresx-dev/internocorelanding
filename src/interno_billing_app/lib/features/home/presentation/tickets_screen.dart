import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:easy_localization/easy_localization.dart';
import 'package:interno_billing_app/core/theme/app_theme.dart';
import 'package:interno_billing_app/features/home/data/models/ticket_models.dart';
import 'package:interno_billing_app/features/home/presentation/bloc/tickets_bloc.dart';
import 'package:interno_billing_app/features/home/presentation/create_ticket_screen.dart';
import 'package:interno_billing_app/features/home/presentation/ticket_chat_screen.dart';

class TicketsScreen extends StatelessWidget {
  const TicketsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    final scaffoldBg = Theme.of(context).scaffoldBackgroundColor;
    final cardBg = Theme.of(context).cardColor;

    return Scaffold(
      backgroundColor: scaffoldBg,
      appBar: AppBar(
        backgroundColor: scaffoldBg,
        title: Text('tickets.title'.tr(), style: const TextStyle(fontSize: 14, fontWeight: FontWeight.bold, letterSpacing: 1)),
        actions: [
          IconButton(
            icon: Icon(Icons.refresh, color: cs.onSurface),
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
                _buildTicketSummary(pending.toString(), closed.toString(), cs, cardBg),
                const SizedBox(height: 32),
                Expanded(
                  child: state is TicketsLoading && tickets.isEmpty
                      ? const Center(child: CircularProgressIndicator(color: InternoColors.cyan))
                      : tickets.isEmpty
                          ? Center(child: Text('tickets.no_tickets'.tr(), style: TextStyle(color: cs.onSurface.withValues(alpha: 0.38))))
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
                                      context.read<TicketsBloc>().add(LoadTickets());
                                    });
                                  },
                                  child: _buildTicketItem(t, cs, cardBg),
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
                  child: Text('tickets.create'.tr(), style: const TextStyle(fontWeight: FontWeight.bold)),
                ),
              ],
            ),
          );
        },
      ),
    );
  }

  Widget _buildTicketSummary(String pending, String closed, ColorScheme cs, Color cardBg) {
    return Container(
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: cardBg,
        borderRadius: BorderRadius.circular(24),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceAround,
        children: [
          _buildSummaryStat(pending, 'tickets.pending'.tr(), cs),
          Container(width: 1, height: 40, color: cs.onSurface.withValues(alpha: 0.1)),
          _buildSummaryStat(closed, 'tickets.closed_resolved'.tr(), cs),
        ],
      ),
    );
  }

  Widget _buildSummaryStat(String val, String label, ColorScheme cs) {
    return Column(
      children: [
        Text(val, style: TextStyle(color: cs.onSurface, fontSize: 24, fontWeight: FontWeight.bold)),
        Text(label, style: TextStyle(color: cs.onSurface.withValues(alpha: 0.38), fontSize: 10, fontWeight: FontWeight.bold)),
      ],
    );
  }

  Widget _buildTicketItem(Ticket ticket, ColorScheme cs, Color cardBg) {
    Color statusColor = Colors.grey;
    if (ticket.status == TicketStatus.newTicket || ticket.status == TicketStatus.pending) statusColor = Colors.amber;
    if (ticket.status == TicketStatus.resolved || ticket.status == TicketStatus.closed) statusColor = InternoColors.success;
    if (ticket.status == TicketStatus.inProgress) statusColor = InternoColors.cyan;

    Color priorityColor;
    String priorityLabel;
    IconData priorityIcon;
    switch (ticket.priority) {
      case TicketPriority.critical:
        priorityColor = const Color(0xFFFF3B30);
        priorityLabel = 'tickets.priority_critical'.tr();
        priorityIcon = Icons.warning_amber_rounded;
        break;
      case TicketPriority.high:
        priorityColor = const Color(0xFFFF9500);
        priorityLabel = 'tickets.priority_high'.tr();
        priorityIcon = Icons.arrow_upward_rounded;
        break;
      case TicketPriority.low:
        priorityColor = const Color(0xFF8E8E93);
        priorityLabel = 'tickets.priority_low'.tr();
        priorityIcon = Icons.arrow_downward_rounded;
        break;
      case TicketPriority.medium:
        priorityColor = const Color(0xFFFFCC00);
        priorityLabel = 'tickets.priority_medium'.tr();
        priorityIcon = Icons.remove_rounded;
        break;
    }

    final bool isAssigned = ticket.assignedToId != null;

    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      decoration: BoxDecoration(
        color: cardBg,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: cs.onSurface.withValues(alpha: 0.08)),
      ),
      child: IntrinsicHeight(
        child: Row(
          children: [
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
            Expanded(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text('#${ticket.referenceCode}', style: const TextStyle(color: InternoColors.cyan, fontWeight: FontWeight.bold, fontSize: 13)),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                          decoration: BoxDecoration(color: statusColor.withValues(alpha:0.15), borderRadius: BorderRadius.circular(8)),
                          child: Text(ticket.status.name.toUpperCase(), style: TextStyle(color: statusColor, fontSize: 9, fontWeight: FontWeight.bold)),
                        ),
                      ],
                    ),
                    const SizedBox(height: 10),
                    Text(ticket.title, style: TextStyle(color: cs.onSurface, fontSize: 15, fontWeight: FontWeight.bold), maxLines: 2, overflow: TextOverflow.ellipsis),
                    const SizedBox(height: 10),
                    Wrap(
                      spacing: 8,
                      runSpacing: 6,
                      children: [
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                          decoration: BoxDecoration(
                            color: priorityColor.withValues(alpha:0.15),
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
                        if (ticket.area != null && ticket.area!.isNotEmpty)
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                            decoration: BoxDecoration(
                              color: cs.onSurface.withValues(alpha: 0.05),
                              borderRadius: BorderRadius.circular(6),
                            ),
                            child: Text(ticket.area!, style: TextStyle(color: cs.onSurface.withValues(alpha: 0.54), fontSize: 9, fontWeight: FontWeight.bold)),
                          ),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                          decoration: BoxDecoration(
                            color: isAssigned ? InternoColors.cyan.withValues(alpha:0.1) : cs.onSurface.withValues(alpha: 0.05),
                            borderRadius: BorderRadius.circular(6),
                          ),
                          child: Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Icon(
                                isAssigned ? Icons.person_rounded : Icons.person_outline_rounded,
                                size: 12,
                                color: isAssigned ? InternoColors.cyan : cs.onSurface.withValues(alpha: 0.38),
                              ),
                              const SizedBox(width: 4),
                              Text(
                                isAssigned ? 'tickets.assigned'.tr() : 'tickets.not_assigned'.tr(),
                                style: TextStyle(color: isAssigned ? InternoColors.cyan : cs.onSurface.withValues(alpha: 0.38), fontSize: 9, fontWeight: FontWeight.bold),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    Text(
                      '${'tickets.reported_on'.tr()} ${DateFormat('dd MMM yyyy').format(ticket.createdAt)}',
                      style: TextStyle(color: cs.onSurface.withValues(alpha: 0.24), fontSize: 11),
                    ),
                  ],
                ),
              ),
            ),
            Padding(
              padding: const EdgeInsets.only(right: 12),
              child: Icon(Icons.chevron_right_rounded, color: cs.onSurface.withValues(alpha: 0.24), size: 20),
            ),
          ],
        ),
      ),
    );
  }
}
