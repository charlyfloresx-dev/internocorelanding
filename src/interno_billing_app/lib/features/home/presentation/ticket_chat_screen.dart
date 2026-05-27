import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:interno_billing_app/core/theme/app_theme.dart';
import 'package:interno_billing_app/features/home/data/models/ticket_models.dart';
import 'package:interno_billing_app/features/home/presentation/bloc/tickets_bloc.dart';
import 'package:intl/intl.dart';

class TicketChatScreen extends StatefulWidget {
  final Ticket ticket;
  const TicketChatScreen({super.key, required this.ticket});

  @override
  State<TicketChatScreen> createState() => _TicketChatScreenState();
}

class _TicketChatScreenState extends State<TicketChatScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;

  // Historial tab
  final _commentController = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  String? _currentUserId;
  List<TicketComment> _comments = [];
  bool _commentsLoading = true;

  // CAPA tab
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
    final picked = await showDatePicker(
      context: context,
      initialDate: _actionDate ?? DateTime.now().add(const Duration(days: 1)),
      firstDate: DateTime.now(),
      lastDate: DateTime.now().add(const Duration(days: 365)),
      builder: (ctx, child) => Theme(
        data: Theme.of(ctx).copyWith(
          colorScheme: const ColorScheme.dark(
            primary: InternoColors.cyan,
            onPrimary: Colors.black,
            surface: Color(0xFF1A1A1A),
            onSurface: Colors.white,
          ),
        ),
        child: child!,
      ),
    );
    if (picked != null) setState(() => _actionDate = picked);
  }

  Future<void> _pickTime() async {
    final picked = await showTimePicker(
      context: context,
      initialTime: _actionTime ?? const TimeOfDay(hour: 9, minute: 0),
      builder: (ctx, child) => Theme(
        data: Theme.of(ctx).copyWith(
          colorScheme: const ColorScheme.dark(
            primary: InternoColors.cyan,
            onPrimary: Colors.black,
            surface: Color(0xFF1A1A1A),
            onSurface: Colors.white,
          ),
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

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      appBar: AppBar(
        backgroundColor: Colors.black,
        iconTheme: const IconThemeData(color: Colors.white),
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
          unselectedLabelColor: Colors.white38,
          labelStyle: const TextStyle(
              fontSize: 11, fontWeight: FontWeight.bold, letterSpacing: 1.2),
          tabs: const [
            Tab(text: 'HISTORIAL'),
            Tab(text: 'CAPA'),
          ],
        ),
      ),
      body: BlocConsumer<TicketsBloc, TicketsState>(
        listener: (context, state) {
          if (state is TicketCommentsLoaded &&
              state.ticket.id == widget.ticket.id) {
            setState(() {
              _comments = state.comments;
              _commentsLoading = false;
            });
            Future.delayed(const Duration(milliseconds: 100), _scrollToBottom);
          } else if (state is TicketActionsLoaded &&
              state.ticketId == widget.ticket.id) {
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
            // Reload actions after any CAPA mutation
            setState(() => _actionsLoading = true);
            context
                .read<TicketsBloc>()
                .add(LoadTicketActions(widget.ticket.id));
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
              _buildTicketHeader(),
              Expanded(
                child: TabBarView(
                  controller: _tabController,
                  children: [
                    _buildHistorialTab(),
                    _buildCapaTab(),
                  ],
                ),
              ),
            ],
          );
        },
      ),
    );
  }

  // ─── Ticket header ───────────────────────────────────────────────────────────

  Widget _buildTicketHeader() {
    final priorityColor = _priorityColor(widget.ticket.priority);
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.fromLTRB(16, 14, 16, 12),
      color: const Color(0xFF0D0D0D),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            widget.ticket.title,
            style: const TextStyle(
                color: Colors.white, fontWeight: FontWeight.bold, fontSize: 15),
          ),
          const SizedBox(height: 6),
          Text(
            widget.ticket.description,
            style: const TextStyle(color: Colors.white60, fontSize: 12),
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
                  style: TextStyle(
                      fontSize: 9,
                      fontWeight: FontWeight.bold,
                      color: priorityColor,
                      letterSpacing: 0.5),
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
        style: const TextStyle(
            fontSize: 9,
            fontWeight: FontWeight.bold,
            color: InternoColors.cyan,
            letterSpacing: 0.5),
      ),
    );
  }

  Color _priorityColor(TicketPriority p) {
    switch (p) {
      case TicketPriority.critical:
        return InternoColors.error;
      case TicketPriority.high:
        return InternoColors.warning;
      case TicketPriority.low:
        return Colors.white38;
      default:
        return const Color(0xFF42A5F5);
    }
  }

  String _statusLabel(TicketStatus s) {
    switch (s) {
      case TicketStatus.newTicket:
        return 'NUEVO';
      case TicketStatus.pending:
        return 'PENDIENTE';
      case TicketStatus.reviewing:
        return 'EN REVISIÓN';
      case TicketStatus.assigned:
        return 'ASIGNADO';
      case TicketStatus.inProgress:
        return 'EN PROGRESO';
      case TicketStatus.waiting:
        return 'EN ESPERA';
      case TicketStatus.resolved:
        return 'RESUELTO';
      case TicketStatus.closed:
        return 'CERRADO';
      case TicketStatus.canceled:
        return 'CANCELADO';
    }
  }

  // ─── Historial tab ────────────────────────────────────────────────────────────

  Widget _buildHistorialTab() {
    if (_commentsLoading && _comments.isEmpty) {
      return const Center(
          child: CircularProgressIndicator(color: InternoColors.cyan));
    }

    return Column(
      children: [
        Expanded(
          child: _comments.isEmpty
              ? const Center(
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(Icons.chat_bubble_outline,
                          color: Colors.white12, size: 44),
                      SizedBox(height: 12),
                      Text('Sin comentarios aún',
                          style:
                              TextStyle(color: Colors.white38, fontSize: 13)),
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
                    return _buildMessageBubble(comment, isOperator);
                  },
                ),
        ),
        _buildMessageInput(),
      ],
    );
  }

  Widget _buildMessageBubble(TicketComment comment, bool isOperator) {
    return Align(
      alignment: isOperator ? Alignment.centerLeft : Alignment.centerRight,
      child: Container(
        margin: const EdgeInsets.only(bottom: 16),
        constraints:
            BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.8),
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: isOperator
              ? const Color(0xFF1A1A1A)
              : const Color(0xFF0D1A1A),
          borderRadius: BorderRadius.only(
            topLeft: const Radius.circular(16),
            topRight: const Radius.circular(16),
            bottomLeft: Radius.circular(isOperator ? 0 : 16),
            bottomRight: Radius.circular(isOperator ? 16 : 0),
          ),
          border: Border.all(
            color: isOperator
                ? Colors.white10
                : InternoColors.cyan.withValues(alpha: 0.25),
          ),
        ),
        child: Column(
          crossAxisAlignment:
              isOperator ? CrossAxisAlignment.start : CrossAxisAlignment.end,
          children: [
            Text(comment.content,
                style:
                    const TextStyle(color: Colors.white, fontSize: 12)),
            const SizedBox(height: 4),
            Text(
              DateFormat('HH:mm').format(comment.createdAt),
              style: const TextStyle(
                  color: Colors.white38,
                  fontSize: 9,
                  fontWeight: FontWeight.bold),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildMessageInput() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: const BoxDecoration(
        color: Colors.black,
        border: Border(top: BorderSide(color: Colors.white10)),
      ),
      child: Row(
        children: [
          Expanded(
            child: TextField(
              controller: _commentController,
              style: const TextStyle(color: Colors.white, fontSize: 14),
              decoration: InputDecoration(
                filled: true,
                fillColor: const Color(0xFF111111),
                hintText: 'Escribe un mensaje...',
                hintStyle: const TextStyle(color: Colors.white24),
                contentPadding:
                    const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(24),
                  borderSide: BorderSide.none,
                ),
              ),
              onSubmitted: (_) => _sendComment(),
            ),
          ),
          const SizedBox(width: 8),
          Container(
            decoration: const BoxDecoration(
                color: InternoColors.cyan, shape: BoxShape.circle),
            child: IconButton(
              icon: const Icon(Icons.send, color: Colors.black, size: 20),
              onPressed: _sendComment,
            ),
          ),
        ],
      ),
    );
  }

  // ─── CAPA tab ─────────────────────────────────────────────────────────────────

  Widget _buildCapaTab() {
    return Column(
      children: [
        Expanded(
          child: _actionsLoading
              ? const Center(
                  child:
                      CircularProgressIndicator(color: InternoColors.cyan))
              : _actions.isEmpty
                  ? const Center(
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(Icons.checklist_outlined,
                              color: Colors.white12, size: 44),
                          SizedBox(height: 12),
                          Text('Sin acciones registradas',
                              style: TextStyle(
                                  color: Colors.white38, fontSize: 13)),
                        ],
                      ),
                    )
                  : ListView.builder(
                      padding: const EdgeInsets.fromLTRB(16, 14, 16, 8),
                      itemCount: _actions.length,
                      itemBuilder: (context, index) =>
                          _buildActionCard(_actions[index]),
                    ),
        ),
        _buildActionForm(),
      ],
    );
  }

  Widget _buildActionCard(TicketAction action) {
    final closed = action.isClosed;
    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 14),
      decoration: BoxDecoration(
        color: const Color(0xFF0D0D0D),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(
          color: closed ? Colors.white10 : InternoColors.cyan.withValues(alpha: 0.2),
        ),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Circular checkbox — tap to close (min 44px touch target for gloves)
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
                      color: closed ? InternoColors.success : Colors.white24,
                      width: 2,
                    ),
                  ),
                  child: closed
                      ? const Icon(Icons.check, color: Colors.white, size: 14)
                      : null,
                ),
              ),
            ),
          ),
          const SizedBox(width: 4),
          // Content
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  action.description,
                  style: TextStyle(
                    color: closed ? Colors.white38 : Colors.white,
                    fontSize: 13,
                    decoration: closed ? TextDecoration.lineThrough : null,
                    decorationColor: Colors.white38,
                  ),
                ),
                const SizedBox(height: 6),
                Row(
                  children: [
                    if (action.commitDate != null) ...[
                      const Icon(Icons.calendar_today_outlined, size: 11, color: Colors.white38),
                      const SizedBox(width: 4),
                      Text(
                        DateFormat('d MMM, HH:mm').format(action.commitDate!.toLocal()),
                        style: const TextStyle(color: Colors.white38, fontSize: 10),
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
                          style: TextStyle(
                            fontSize: 9,
                            fontWeight: FontWeight.bold,
                            color: _assigneeColor(action.assigneeType),
                          ),
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

  Widget _buildActionForm() {
    return Container(
      padding: const EdgeInsets.fromLTRB(16, 14, 16, 24),
      decoration: const BoxDecoration(
        color: Color(0xFF080808),
        border: Border(top: BorderSide(color: Colors.white10)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        mainAxisSize: MainAxisSize.min,
        children: [
          const Text(
            'NUEVA ACCIÓN',
            style: TextStyle(
                fontSize: 10,
                fontWeight: FontWeight.bold,
                letterSpacing: 1.5,
                color: Colors.white24),
          ),
          const SizedBox(height: 10),
          TextField(
            controller: _actionDescController,
            style: const TextStyle(color: Colors.white, fontSize: 16),
            maxLines: 3,
            maxLength: 200,
            decoration: InputDecoration(
              filled: true,
              fillColor: const Color(0xFF131313),
              hintText: 'Descripción de la acción...',
              hintStyle:
                  const TextStyle(color: Colors.white24, fontSize: 16),
              counterStyle:
                  const TextStyle(color: Colors.white24, fontSize: 10),
              contentPadding:
                  const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(8),
                borderSide: const BorderSide(color: Colors.white12),
              ),
              enabledBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(8),
                borderSide: const BorderSide(color: Colors.white12),
              ),
              focusedBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(8),
                borderSide:
                    const BorderSide(color: InternoColors.cyan, width: 1.5),
              ),
            ),
          ),
          const SizedBox(height: 10),
          Row(
            children: [
              Expanded(child: _buildDateButton()),
              const SizedBox(width: 10),
              _buildTimeButton(),
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
                disabledBackgroundColor:
                    InternoColors.cyan.withValues(alpha: 0.25),
                shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(8)),
              ),
              child: _submittingAction
                  ? const SizedBox(
                      height: 22,
                      width: 22,
                      child: CircularProgressIndicator(
                          color: Colors.black, strokeWidth: 2.5),
                    )
                  : const Text(
                      'REGISTRAR ACCIÓN',
                      style: TextStyle(
                          fontSize: 14,
                          fontWeight: FontWeight.bold,
                          letterSpacing: 1.2),
                    ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildDateButton() {
    final hasDate = _actionDate != null;
    return GestureDetector(
      onTap: _pickDate,
      child: Container(
        height: 52,
        padding: const EdgeInsets.symmetric(horizontal: 14),
        decoration: BoxDecoration(
          color: const Color(0xFF131313),
          borderRadius: BorderRadius.circular(8),
          border: Border.all(
            color: hasDate
                ? InternoColors.cyan.withValues(alpha: 0.5)
                : Colors.white12,
          ),
        ),
        child: Row(
          children: [
            Icon(Icons.calendar_month_outlined,
                size: 20,
                color: hasDate ? InternoColors.cyan : Colors.white38),
            const SizedBox(width: 10),
            Flexible(
              child: Text(
                hasDate
                    ? DateFormat('d MMM yyyy').format(_actionDate!)
                    : 'Fecha compromiso',
                overflow: TextOverflow.ellipsis,
                style: TextStyle(
                    fontSize: 15,
                    color: hasDate ? Colors.white : Colors.white38),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildTimeButton() {
    final hasTime = _actionTime != null;
    return GestureDetector(
      onTap: _pickTime,
      child: Container(
        height: 52,
        width: 104,
        padding: const EdgeInsets.symmetric(horizontal: 12),
        decoration: BoxDecoration(
          color: const Color(0xFF131313),
          borderRadius: BorderRadius.circular(8),
          border: Border.all(
            color: hasTime
                ? InternoColors.cyan.withValues(alpha: 0.5)
                : Colors.white12,
          ),
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.access_time_outlined,
                size: 20,
                color: hasTime ? InternoColors.cyan : Colors.white38),
            const SizedBox(width: 6),
            Flexible(
              child: Text(
                hasTime ? _actionTime!.format(context) : 'Hora',
                overflow: TextOverflow.ellipsis,
                style: TextStyle(
                    fontSize: 15,
                    color: hasTime ? Colors.white : Colors.white38),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
