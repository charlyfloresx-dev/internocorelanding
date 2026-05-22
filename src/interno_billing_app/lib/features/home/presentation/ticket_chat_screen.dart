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

class _TicketChatScreenState extends State<TicketChatScreen> {
  final _commentController = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  String? _currentUserId;

  @override
  void initState() {
    super.initState();
    _loadCurrentUserId();
    context.read<TicketsBloc>().add(LoadTicketComments(widget.ticket.id));
  }

  Future<void> _loadCurrentUserId() async {
    final prefs = await SharedPreferences.getInstance();
    if (mounted) {
      setState(() {
        _currentUserId = prefs.getString('user_id');
      });
    }
  }

  @override
  void dispose() {
    _commentController.dispose();
    _scrollController.dispose();
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

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      appBar: AppBar(
        backgroundColor: Colors.black,
        iconTheme: const IconThemeData(color: Colors.white),
        title: Text('#${widget.ticket.referenceCode}', style: const TextStyle(fontSize: 14, fontWeight: FontWeight.bold, letterSpacing: 1, color: InternoColors.cyan)),
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(1),
          child: Container(color: Colors.white10, height: 1),
        ),
      ),
      body: BlocConsumer<TicketsBloc, TicketsState>(
        listener: (context, state) {
          if (state is TicketCommentsLoaded) {
            Future.delayed(const Duration(milliseconds: 100), _scrollToBottom);
          } else if (state is TicketsError) {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(content: Text(state.message), backgroundColor: Colors.red),
            );
          }
        },
        builder: (context, state) {
          if (state is TicketsLoading) {
            return const Center(child: CircularProgressIndicator(color: InternoColors.cyan));
          }
          
          List<TicketComment> comments = [];
          if (state is TicketCommentsLoaded && state.ticket.id == widget.ticket.id) {
            comments = state.comments;
          }

          return Column(
            children: [
              _buildTicketDetailsHeader(),
              Expanded(
                child: ListView.builder(
                  controller: _scrollController,
                  padding: const EdgeInsets.all(16),
                  itemCount: comments.length,
                  itemBuilder: (context, index) {
                    final comment = comments[index];
                    final isOperator = comment.authorId != _currentUserId;
                    return _buildMessageBubble(comment, isOperator);
                  },
                ),
              ),
              _buildMessageInput(),
            ],
          );
        },
      ),
    );
  }

  Widget _buildTicketDetailsHeader() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
      color: const Color(0xFF111111),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(widget.ticket.title, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 16)),
          const SizedBox(height: 8),
          Text(widget.ticket.description, style: const TextStyle(color: Colors.white70, fontSize: 12)),
          const SizedBox(height: 12),
          Row(
            children: [
              Text('Prioridad: ${widget.ticket.priority.name.toUpperCase()}', style: const TextStyle(color: Colors.white38, fontSize: 10, fontWeight: FontWeight.bold)),
              const Spacer(),
              Text('Estado: ${widget.ticket.status.name.toUpperCase()}', style: const TextStyle(color: InternoColors.cyan, fontSize: 10, fontWeight: FontWeight.bold)),
            ],
          )
        ],
      ),
    );
  }

  Widget _buildMessageBubble(TicketComment comment, bool isOperator) {
    return Align(
      alignment: isOperator ? Alignment.centerLeft : Alignment.centerRight,
      child: Container(
        margin: const EdgeInsets.only(bottom: 16),
        constraints: BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.8),
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: isOperator ? const Color(0xFF1A1A1A) : const Color(0xFF111111),
          borderRadius: BorderRadius.only(
            topLeft: const Radius.circular(16),
            topRight: const Radius.circular(16),
            bottomLeft: Radius.circular(isOperator ? 0 : 16),
            bottomRight: Radius.circular(isOperator ? 16 : 0),
          ),
          border: Border.all(color: isOperator ? Colors.white10 : InternoColors.cyan.withOpacity(0.3)),
        ),
        child: Column(
          crossAxisAlignment: isOperator ? CrossAxisAlignment.start : CrossAxisAlignment.end,
          children: [
            Text(comment.content, style: const TextStyle(color: Colors.white, fontSize: 12)),
            const SizedBox(height: 4),
            Text(
              DateFormat('HH:mm').format(comment.createdAt),
              style: const TextStyle(color: Colors.white38, fontSize: 8, fontWeight: FontWeight.bold),
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
}
