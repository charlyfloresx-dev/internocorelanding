import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:easy_localization/easy_localization.dart';
import 'package:interno_billing_app/core/theme/app_theme.dart';
import 'package:interno_billing_app/features/home/data/models/ticket_models.dart';
import 'package:interno_billing_app/features/home/presentation/bloc/tickets_bloc.dart';

class TicketChatScreen extends StatefulWidget {
  final Ticket ticket;
  const TicketChatScreen({super.key, required this.ticket});

  @override
  State<TicketChatScreen> createState() => _TicketChatScreenState();
}

class _TicketChatScreenState extends State<TicketChatScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;

  final _commentController = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  String? _currentUserId;
  List<TicketComment> _comments = [];
  bool _commentsLoading = true;

  List<TicketAction> _actions = [];
  bool _actionsLoading = false;
  bool _actionsLoaded = false;
  final _actionDescController = TextEditingController();
  DateTime? _actionDate;
  TimeOfDay? _actionTime;
  bool _submittingAction = false;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
    _tabController.addListener(_onTabChanged);
    _loadCurrentUserId();
    context.read<TicketsBloc>().add(LoadTicketComments(widget.ticket.id));
  }

  void _onTabChanged() {
    if (_tabController.index == 1 && !_actionsLoaded && !_actionsLoading) {
      _loadActions();
    }
  }

  Future<void> _loadCurrentUserId() async {
    final prefs = await SharedPreferences.getInstance();
    if (mounted) setState(() => _currentUserId = prefs.getString('user_id'));
  }

  void _loadActions() {
    setState(() => _actionsLoading = true);
    context.read<TicketsBloc>().add(LoadTicketActions(widget.ticket.id));
  }

  @override
  void dispose() {
    _tabController.removeListener(_onTabChanged);
    _tabController.dispose();
    _commentController.dispose();
    _scrollController.dispose();
    _actionDescController.dispose();
    super.dispose();
  }

  void _sendComment() {
    if (_commentController.text.trim().isEmpty) return;
    context.read<TicketsBloc>().add(AddTicketComment(
      ticketId: widget.ticket.id,
      content: _commentController.text.trim(),
    ));
    _commentController.clear();
  }

  void _scrollToBottom() {
    if (_scrollController.hasClients) {
      _scrollController.animateTo(
        _scrollController.position.maxScrollExtent,
        duration: const Duration(milliseconds: 300),
        curve: Curves.easeOut,
      );
    }
  }

  Future<void> _pickDate() async {
    final cs = Theme.of(context).colorScheme;
    final picked = await showDatePicker(
      context: context,
      initialDate: _actionDate ?? DateTime.now().add(const Duration(days: 1)),
      firstDate: DateTime.now(),
      lastDate: DateTime.now().add(const Duration(days: 365)),
      builder: (ctx, child) => Theme(
        data: Theme.of(ctx).copyWith(
          colorScheme: cs.copyWith(primary: InternoColors.cyan, onPrimary: Colors.black),
        ),
        child: child!,
      ),
    );
    if (picked != null) setState(() => _actionDate = picked);
  }

  Future<void> _pickTime() async {
    final cs = Theme.of(context).colorScheme;
    final picked = await showTimePicker(
      context: context,
      initialTime: _actionTime ?? const TimeOfDay(hour: 9, minute: 0),
      builder: (ctx, child) => Theme(
        data: Theme.of(ctx).copyWith(
          colorScheme: cs.copyWith(primary: InternoColors.cyan, onPrimary: Colors.black),
        ),
        child: child!,
      ),
    );
    if (picked != null) setState(() => _actionTime = picked);
  }

  void _submitAction() {
    if (_actionDescController.text.trim().isEmpty || _submittingAction) return;
    DateTime? commitDate;
    if (_actionDate != null) {
      final t = _actionTime ?? const TimeOfDay(hour: 23, minute: 59);
      commitDate = DateTime(
        _actionDate!.year, _actionDate!.month, _actionDate!.day, t.hour, t.minute,
      );
    }
    setState(() => _submittingAction = true);
    context.read<TicketsBloc>().add(AddTicketActionEvent(
      ticketId: widget.ticket.id,
      description: _actionDescController.text.trim(),
      commitDate: commitDate,
    ));
  }

  void _closeAction(TicketAction action) {
    context.read<TicketsBloc>().add(CloseTicketActionEvent(
      ticketId: widget.ticket.id,
      actionId: action.id,
    ));
  }

  Color _assigneeColor(String? type) {
    switch (type) {
      case 'PLANTA':
        return const Color(0xFF26C6DA);
      case 'EXTERNO':
        return const Color(0xFFAB47BC);
      default:
        return const Color(0xFFFFB300);
    }
  }

  Color _priorityColor(TicketPriority p, ColorScheme cs) {
    switch (p) {
      case TicketPriority.critical:
        return InternoColors.error;
      case TicketPriority.high:
        return InternoColors.warning;
      case TicketPriority.low:
        return cs.onSurface.withValues(alpha: 0.38);
      default:
        return const Color(0xFF42A5F5);
    }
  }

  String _statusLabel(TicketStatus s) {
    switch (s) {
      case TicketStatus.newTicket:
        return 'ticket_chat.status_new'.tr();
      case TicketStatus.pending:
        return 'ticket_chat.status_pending'.tr();
      case TicketStatus.reviewing:
        return 'ticket_chat.status_reviewing'.tr();
      case TicketStatus.assigned:
        return 'ticket_chat.status_assigned'.tr();
      case TicketStatus.inProgress:
        return 'ticket_chat.status_in_progress'.tr();
      case TicketStatus.waiting:
        return 'ticket_chat.status_waiting'.tr();
      case TicketStatus.resolved:
        return 'ticket_chat.status_resolved'.tr();
      case TicketStatus.closed:
        return 'ticket_chat.status_closed'.tr();
      case TicketStatus.canceled:
        return 'ticket_chat.status_canceled'.tr();
    }
  }

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    final scaffoldBg = Theme.of(context).scaffoldBackgroundColor;
    final cardBg = Theme.of(context).cardColor;

    return Scaffold(
      backgroundColor: scaffoldBg,
      appBar: AppBar(
        backgroundColor: scaffoldBg,
        iconTheme: IconThemeData(color: cs.onSurface),
        title: Text(
          '#${widget.ticket.referenceCode}',
          style: const TextStyle(
            fontSize: 14,
            fontWeight: FontWeight.bold,
            letterSpacing: 1,
            color: InternoColors.cyan,
          ),
        ),
        bottom: TabBar(
          controller: _tabController,
          indicatorColor: InternoColors.cyan,
          indicatorWeight: 2,
          labelColor: InternoColors.cyan,
          unselectedLabelColor: cs.onSurface.withValues(alpha: 0.38),
          labelStyle: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold, letterSpacing: 1.2),
          tabs: [
            Tab(text: 'ticket_chat.history'.tr()),
            Tab(text: 'ticket_chat.capa'.tr()),
          ],
        ),
      ),
      body: BlocConsumer<TicketsBloc, TicketsState>(
        listener: (context, state) {
          if (state is TicketCommentsLoaded && state.ticket.id == widget.ticket.id) {
            setState(() {
              _comments = state.comments;
              _commentsLoading = false;
            });
            Future.delayed(const Duration(milliseconds: 100), _scrollToBottom);
          } else if (state is TicketActionsLoaded && state.ticketId == widget.ticket.id) {
            setState(() {
              _actions = state.actions;
              _actionsLoading = false;
              _actionsLoaded = true;
            });
          } else if (state is TicketActionSuccess) {
            setState(() {
              _submittingAction = false;
              _actionDescController.clear();
              _actionDate = null;
              _actionTime = null;
            });
            ScaffoldMessenger.of(context).showSnackBar(SnackBar(
              content: Text(state.message),
              backgroundColor: InternoColors.success,
            ));
            setState(() => _actionsLoading = true);
            context.read<TicketsBloc>().add(LoadTicketActions(widget.ticket.id));
          } else if (state is TicketsError) {
            setState(() {
              _commentsLoading = false;
              _actionsLoading = false;
              _submittingAction = false;
            });
            ScaffoldMessenger.of(context).showSnackBar(SnackBar(
              content: Text(state.message),
              backgroundColor: Colors.red[700],
            ));
          }
        },
        builder: (context, state) {
          return Column(
            children: [
              _buildTicketHeader(cs, cardBg),
              Expanded(
                child: TabBarView(
                  controller: _tabController,
                  children: [
                    _buildHistorialTab(cs, cardBg),
                    _buildCapaTab(cs, cardBg, scaffoldBg),
                  ],
                ),
              ),
            ],
          );
        },
      ),
    );
  }

  Widget _buildTicketHeader(ColorScheme cs, Color cardBg) {
    final priorityColor = _priorityColor(widget.ticket.priority, cs);
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.fromLTRB(16, 14, 16, 12),
      color: cardBg,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            widget.ticket.title,
            style: TextStyle(color: cs.onSurface, fontWeight: FontWeight.bold, fontSize: 15),
          ),
          const SizedBox(height: 6),
          Text(
            widget.ticket.description,
            style: TextStyle(color: cs.onSurface.withValues(alpha: 0.5), fontSize: 12),
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
          ),
          const SizedBox(height: 10),
          Row(
            children: [
              _statusChip(widget.ticket.status),
              const SizedBox(width: 8),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 3),
                decoration: BoxDecoration(
                  color: priorityColor.withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(4),
                  border: Border.all(color: priorityColor.withValues(alpha: 0.4)),
                ),
                child: Text(
                  widget.ticket.priority.name.toUpperCase(),
                  style: TextStyle(fontSize: 9, fontWeight: FontWeight.bold, color: priorityColor, letterSpacing: 0.5),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _statusChip(TicketStatus status) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 3),
      decoration: BoxDecoration(
        color: InternoColors.cyan.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(4),
        border: Border.all(color: InternoColors.cyan.withValues(alpha: 0.4)),
      ),
      child: Text(
        _statusLabel(status),
        style: const TextStyle(fontSize: 9, fontWeight: FontWeight.bold, color: InternoColors.cyan, letterSpacing: 0.5),
      ),
    );
  }

  Widget _buildHistorialTab(ColorScheme cs, Color cardBg) {
    if (_commentsLoading && _comments.isEmpty) {
      return const Center(child: CircularProgressIndicator(color: InternoColors.cyan));
    }

    return Column(
      children: [
        Expanded(
          child: _comments.isEmpty
              ? Center(
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(Icons.chat_bubble_outline, color: cs.onSurface.withValues(alpha: 0.12), size: 44),
                      const SizedBox(height: 12),
                      Text('ticket_chat.no_comments'.tr(), style: TextStyle(color: cs.onSurface.withValues(alpha: 0.38), fontSize: 13)),
                    ],
                  ),
                )
              : ListView.builder(
                  controller: _scrollController,
                  padding: const EdgeInsets.all(16),
                  itemCount: _comments.length,
                  itemBuilder: (context, index) {
                    final comment = _comments[index];
                    final isOperator = comment.authorId != _currentUserId;
                    return _buildMessageBubble(comment, isOperator, cs, cardBg);
                  },
                ),
        ),
        _buildMessageInput(cs, cardBg),
      ],
    );
  }

  Widget _buildMessageBubble(TicketComment comment, bool isOperator, ColorScheme cs, Color cardBg) {
    return Align(
      alignment: isOperator ? Alignment.centerLeft : Alignment.centerRight,
      child: Container(
        margin: const EdgeInsets.only(bottom: 16),
        constraints: BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.8),
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: isOperator ? cardBg : InternoColors.cyan.withValues(alpha: 0.08),
          borderRadius: BorderRadius.only(
            topLeft: const Radius.circular(16),
            topRight: const Radius.circular(16),
            bottomLeft: Radius.circular(isOperator ? 0 : 16),
            bottomRight: Radius.circular(isOperator ? 16 : 0),
          ),
          border: Border.all(
            color: isOperator ? cs.onSurface.withValues(alpha: 0.08) : InternoColors.cyan.withValues(alpha: 0.25),
          ),
        ),
        child: Column(
          crossAxisAlignment: isOperator ? CrossAxisAlignment.start : CrossAxisAlignment.end,
          children: [
            Text(comment.content, style: TextStyle(color: cs.onSurface, fontSize: 12)),
            const SizedBox(height: 4),
            Text(
              DateFormat('HH:mm').format(comment.createdAt),
              style: TextStyle(color: cs.onSurface.withValues(alpha: 0.38), fontSize: 9, fontWeight: FontWeight.bold),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildMessageInput(ColorScheme cs, Color cardBg) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Theme.of(context).scaffoldBackgroundColor,
        border: Border(top: BorderSide(color: cs.onSurface.withValues(alpha: 0.08))),
      ),
      child: Row(
        children: [
          Expanded(
            child: TextField(
              controller: _commentController,
              style: TextStyle(color: cs.onSurface, fontSize: 14),
              decoration: InputDecoration(
                filled: true,
                fillColor: cardBg,
                hintText: 'ticket_chat.type_message'.tr(),
                hintStyle: TextStyle(color: cs.onSurface.withValues(alpha: 0.24)),
                contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                border: OutlineInputBorder(borderRadius: BorderRadius.circular(24), borderSide: BorderSide.none),
              ),
              onSubmitted: (_) => _sendComment(),
            ),
          ),
          const SizedBox(width: 8),
          Container(
            decoration: const BoxDecoration(color: InternoColors.cyan, shape: BoxShape.circle),
            child: IconButton(
              icon: const Icon(Icons.send, color: Colors.black, size: 20),
              onPressed: _sendComment,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildCapaTab(ColorScheme cs, Color cardBg, Color scaffoldBg) {
    return Column(
      children: [
        Expanded(
          child: _actionsLoading
              ? const Center(child: CircularProgressIndicator(color: InternoColors.cyan))
              : _actions.isEmpty
                  ? Center(
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(Icons.checklist_outlined, color: cs.onSurface.withValues(alpha: 0.12), size: 44),
                          const SizedBox(height: 12),
                          Text('ticket_chat.no_actions'.tr(), style: TextStyle(color: cs.onSurface.withValues(alpha: 0.38), fontSize: 13)),
                        ],
                      ),
                    )
                  : ListView.builder(
                      padding: const EdgeInsets.fromLTRB(16, 14, 16, 8),
                      itemCount: _actions.length,
                      itemBuilder: (context, index) => _buildActionCard(_actions[index], cs, cardBg),
                    ),
        ),
        _buildActionForm(cs, cardBg, scaffoldBg),
      ],
    );
  }

  Widget _buildActionCard(TicketAction action, ColorScheme cs, Color cardBg) {
    final closed = action.isClosed;
    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 14),
      decoration: BoxDecoration(
        color: cardBg,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(
          color: closed ? cs.onSurface.withValues(alpha: 0.08) : InternoColors.cyan.withValues(alpha: 0.2),
        ),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          GestureDetector(
            onTap: closed ? null : () => _closeAction(action),
            child: SizedBox(
              width: 44,
              height: 44,
              child: Center(
                child: AnimatedContainer(
                  duration: const Duration(milliseconds: 200),
                  width: 26,
                  height: 26,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: closed ? InternoColors.success : Colors.transparent,
                    border: Border.all(
                      color: closed ? InternoColors.success : cs.onSurface.withValues(alpha: 0.24),
                      width: 2,
                    ),
                  ),
                  child: closed ? const Icon(Icons.check, color: Colors.white, size: 14) : null,
                ),
              ),
            ),
          ),
          const SizedBox(width: 4),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  action.description,
                  style: TextStyle(
                    color: closed ? cs.onSurface.withValues(alpha: 0.38) : cs.onSurface,
                    fontSize: 13,
                    decoration: closed ? TextDecoration.lineThrough : null,
                    decorationColor: cs.onSurface.withValues(alpha: 0.38),
                  ),
                ),
                const SizedBox(height: 6),
                Row(
                  children: [
                    if (action.commitDate != null) ...[
                      Icon(Icons.calendar_today_outlined, size: 11, color: cs.onSurface.withValues(alpha: 0.38)),
                      const SizedBox(width: 4),
                      Text(
                        DateFormat('d MMM, HH:mm').format(action.commitDate!.toLocal()),
                        style: TextStyle(color: cs.onSurface.withValues(alpha: 0.38), fontSize: 10),
                      ),
                      const SizedBox(width: 10),
                    ],
                    if (action.assigneeName != null)
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 2),
                        decoration: BoxDecoration(
                          color: _assigneeColor(action.assigneeType).withValues(alpha: 0.12),
                          borderRadius: BorderRadius.circular(3),
                          border: Border.all(color: _assigneeColor(action.assigneeType).withValues(alpha: 0.4)),
                        ),
                        child: Text(
                          action.assigneeName!,
                          style: TextStyle(fontSize: 9, fontWeight: FontWeight.bold, color: _assigneeColor(action.assigneeType)),
                        ),
                      ),
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildActionForm(ColorScheme cs, Color cardBg, Color scaffoldBg) {
    return Container(
      padding: const EdgeInsets.fromLTRB(16, 14, 16, 24),
      decoration: BoxDecoration(
        color: scaffoldBg,
        border: Border(top: BorderSide(color: cs.onSurface.withValues(alpha: 0.08))),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(
            'ticket_chat.new_action'.tr(),
            style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, letterSpacing: 1.5, color: cs.onSurface.withValues(alpha: 0.24)),
          ),
          const SizedBox(height: 10),
          TextField(
            controller: _actionDescController,
            style: TextStyle(color: cs.onSurface, fontSize: 16),
            maxLines: 3,
            maxLength: 200,
            decoration: InputDecoration(
              filled: true,
              fillColor: cardBg,
              hintText: 'ticket_chat.action_hint'.tr(),
              hintStyle: TextStyle(color: cs.onSurface.withValues(alpha: 0.24), fontSize: 16),
              counterStyle: TextStyle(color: cs.onSurface.withValues(alpha: 0.24), fontSize: 10),
              contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(8),
                borderSide: BorderSide(color: cs.onSurface.withValues(alpha: 0.12)),
              ),
              enabledBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(8),
                borderSide: BorderSide(color: cs.onSurface.withValues(alpha: 0.12)),
              ),
              focusedBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(8),
                borderSide: const BorderSide(color: InternoColors.cyan, width: 1.5),
              ),
            ),
          ),
          const SizedBox(height: 10),
          Row(
            children: [
              Expanded(child: _buildDateButton(cs, cardBg)),
              const SizedBox(width: 10),
              _buildTimeButton(cs, cardBg),
            ],
          ),
          const SizedBox(height: 12),
          SizedBox(
            height: 56,
            child: ElevatedButton(
              onPressed: _submittingAction ? null : _submitAction,
              style: ElevatedButton.styleFrom(
                backgroundColor: InternoColors.cyan,
                foregroundColor: Colors.black,
                disabledBackgroundColor: InternoColors.cyan.withValues(alpha: 0.25),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
              ),
              child: _submittingAction
                  ? const SizedBox(height: 22, width: 22, child: CircularProgressIndicator(color: Colors.black, strokeWidth: 2.5))
                  : Text(
                      'ticket_chat.register_action'.tr(),
                      style: const TextStyle(fontSize: 14, fontWeight: FontWeight.bold, letterSpacing: 1.2),
                    ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildDateButton(ColorScheme cs, Color cardBg) {
    final hasDate = _actionDate != null;
    return GestureDetector(
      onTap: _pickDate,
      child: Container(
        height: 52,
        padding: const EdgeInsets.symmetric(horizontal: 14),
        decoration: BoxDecoration(
          color: cardBg,
          borderRadius: BorderRadius.circular(8),
          border: Border.all(
            color: hasDate ? InternoColors.cyan.withValues(alpha: 0.5) : cs.onSurface.withValues(alpha: 0.12),
          ),
        ),
        child: Row(
          children: [
            Icon(Icons.calendar_month_outlined, size: 20, color: hasDate ? InternoColors.cyan : cs.onSurface.withValues(alpha: 0.38)),
            const SizedBox(width: 10),
            Flexible(
              child: Text(
                hasDate ? DateFormat('d MMM yyyy').format(_actionDate!) : 'ticket_chat.commit_date'.tr(),
                overflow: TextOverflow.ellipsis,
                style: TextStyle(fontSize: 15, color: hasDate ? cs.onSurface : cs.onSurface.withValues(alpha: 0.38)),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildTimeButton(ColorScheme cs, Color cardBg) {
    final hasTime = _actionTime != null;
    return GestureDetector(
      onTap: _pickTime,
      child: Container(
        height: 52,
        width: 104,
        padding: const EdgeInsets.symmetric(horizontal: 12),
        decoration: BoxDecoration(
          color: cardBg,
          borderRadius: BorderRadius.circular(8),
          border: Border.all(
            color: hasTime ? InternoColors.cyan.withValues(alpha: 0.5) : cs.onSurface.withValues(alpha: 0.12),
          ),
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.access_time_outlined, size: 20, color: hasTime ? InternoColors.cyan : cs.onSurface.withValues(alpha: 0.38)),
            const SizedBox(width: 6),
            Flexible(
              child: Text(
                hasTime ? _actionTime!.format(context) : 'ticket_chat.hour'.tr(),
                overflow: TextOverflow.ellipsis,
                style: TextStyle(fontSize: 15, color: hasTime ? cs.onSurface : cs.onSurface.withValues(alpha: 0.38)),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
