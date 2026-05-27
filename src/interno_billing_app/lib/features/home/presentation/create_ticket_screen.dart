import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:easy_localization/easy_localization.dart';
import 'package:interno_billing_app/core/di/injection.dart';
import 'package:interno_billing_app/core/theme/app_theme.dart';
import 'package:interno_billing_app/features/home/data/models/ticket_models.dart';
import 'package:interno_billing_app/features/home/data/ticket_repository.dart';
import 'package:interno_billing_app/features/home/presentation/bloc/tickets_bloc.dart';

class CreateTicketScreen extends StatefulWidget {
  const CreateTicketScreen({super.key});

  @override
  State<CreateTicketScreen> createState() => _CreateTicketScreenState();
}

class _CreateTicketScreenState extends State<CreateTicketScreen> {
  final _titleController = TextEditingController();
  final _descController = TextEditingController();
  TicketPriority _priority = TicketPriority.medium;
  bool _showSuccess = false;

  List<Department> _departments = [];
  bool _loadingDepts = true;
  Department? _selectedDept;

  @override
  void initState() {
    super.initState();
    _loadDepartments();
  }

  Future<void> _loadDepartments() async {
    if (mounted) setState(() => _loadingDepts = true);
    final depts = await sl<TicketRepository>().getDepartments();
    if (mounted) {
      setState(() {
        _departments = depts;
        _loadingDepts = false;
      });
    }
  }

  @override
  void dispose() {
    _titleController.dispose();
    _descController.dispose();
    super.dispose();
  }

  void _reset() {
    setState(() {
      _titleController.clear();
      _descController.clear();
      _priority = TicketPriority.medium;
      _selectedDept = null;
      _showSuccess = false;
    });
  }

  void _submit() {
    final title = _titleController.text.trim();
    final desc = _descController.text.trim();

    if (title.length < 5) {
      HapticFeedback.heavyImpact();
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(
        content: Text('create_ticket.subject_error'.tr()),
        backgroundColor: Colors.redAccent,
        behavior: SnackBarBehavior.floating,
      ));
      return;
    }
    if (desc.length < 10) {
      HapticFeedback.heavyImpact();
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(
        content: Text('create_ticket.desc_error'.tr()),
        backgroundColor: Colors.redAccent,
        behavior: SnackBarBehavior.floating,
      ));
      return;
    }

    HapticFeedback.mediumImpact();
    context.read<TicketsBloc>().add(CreateTicket(TicketCreateRequest(
      title: title,
      description: desc,
      priority: _priority,
      area: _selectedDept?.name,
    )));
  }

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    final scaffoldBg = Theme.of(context).scaffoldBackgroundColor;
    final cardBg = Theme.of(context).cardColor;

    return BlocListener<TicketsBloc, TicketsState>(
      listener: (context, state) {
        if (state is TicketActionSuccess && state.message.contains('creado')) {
          HapticFeedback.heavyImpact();
          setState(() => _showSuccess = true);
        }
      },
      child: Scaffold(
        backgroundColor: scaffoldBg,
        body: SafeArea(
          child: AnimatedSwitcher(
            duration: const Duration(milliseconds: 280),
            switchInCurve: Curves.easeOut,
            switchOutCurve: Curves.easeIn,
            child: _showSuccess ? _buildSuccess(cs) : _buildForm(cs, cardBg),
          ),
        ),
      ),
    );
  }

  Widget _buildSuccess(ColorScheme cs) {
    return Center(
      key: const ValueKey('success'),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 40),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              width: 72,
              height: 72,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                border: Border.all(color: InternoColors.success, width: 2),
              ),
              child: const Icon(Icons.check, color: InternoColors.success, size: 36),
            ),
            const SizedBox(height: 28),
            Text(
              'create_ticket.sent'.tr(),
              style: TextStyle(
                color: cs.onSurface,
                fontSize: 22,
                fontWeight: FontWeight.w900,
                letterSpacing: 2,
              ),
            ),
            const SizedBox(height: 12),
            Text(
              'create_ticket.sent_desc'.tr(),
              textAlign: TextAlign.center,
              style: TextStyle(
                color: cs.onSurface.withValues(alpha: 0.45),
                fontSize: 13,
                height: 1.6,
              ),
            ),
            const SizedBox(height: 48),
            SizedBox(
              width: double.infinity,
              height: 56,
              child: OutlinedButton(
                onPressed: _reset,
                style: OutlinedButton.styleFrom(
                  foregroundColor: cs.onSurface,
                  side: BorderSide(color: cs.onSurface.withValues(alpha: 0.24)),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                ),
                child: Text(
                  'create_ticket.report_another'.tr(),
                  style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13, letterSpacing: 1),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildForm(ColorScheme cs, Color cardBg) {
    return BlocBuilder<TicketsBloc, TicketsState>(
      key: const ValueKey('form'),
      builder: (context, state) {
        final isLoading = state is TicketsLoading;
        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(24, 20, 24, 0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'create_ticket.title'.tr(),
                    style: TextStyle(
                      color: cs.onSurface,
                      fontSize: 22,
                      fontWeight: FontWeight.w900,
                      letterSpacing: 1.5,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    'create_ticket.subtitle'.tr(),
                    style: TextStyle(color: cs.onSurface.withValues(alpha: 0.38), fontSize: 12),
                  ),
                ],
              ),
            ),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
              child: Divider(color: cs.onSurface.withValues(alpha: 0.1), height: 1),
            ),
            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.symmetric(horizontal: 24),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    _label('create_ticket.subject'.tr(), cs),
                    const SizedBox(height: 8),
                    _field(controller: _titleController, hint: 'create_ticket.subject_hint'.tr(), cs: cs, cardBg: cardBg),
                    const SizedBox(height: 20),
                    _label('create_ticket.priority'.tr(), cs),
                    const SizedBox(height: 8),
                    _prioritySelector(cs),
                    const SizedBox(height: 20),
                    _label('create_ticket.area'.tr(), cs),
                    const SizedBox(height: 8),
                    _departmentDropdown(cs, cardBg),
                    const SizedBox(height: 20),
                    _label('create_ticket.description'.tr(), cs),
                    const SizedBox(height: 8),
                    _field(
                      controller: _descController,
                      hint: 'create_ticket.desc_hint'.tr(),
                      minLines: 4,
                      maxLines: 8,
                      cs: cs,
                      cardBg: cardBg,
                    ),
                    const SizedBox(height: 32),
                  ],
                ),
              ),
            ),
            Padding(
              padding: const EdgeInsets.fromLTRB(24, 0, 24, 24),
              child: SizedBox(
                width: double.infinity,
                height: 56,
                child: ElevatedButton(
                  onPressed: isLoading ? null : _submit,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: cs.onSurface,
                    foregroundColor: cs.surface,
                    disabledBackgroundColor: cs.onSurface.withValues(alpha: 0.12),
                    elevation: 0,
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                  ),
                  child: isLoading
                      ? SizedBox(
                          width: 20,
                          height: 20,
                          child: CircularProgressIndicator(strokeWidth: 2, color: cs.surface.withValues(alpha: 0.54)),
                        )
                      : Text(
                          'create_ticket.create'.tr(),
                          style: const TextStyle(fontWeight: FontWeight.w900, fontSize: 15, letterSpacing: 1.5),
                        ),
                ),
              ),
            ),
          ],
        );
      },
    );
  }

  Widget _label(String text, ColorScheme cs) => Text(
        text,
        style: TextStyle(
          color: cs.onSurface.withValues(alpha: 0.38),
          fontSize: 10,
          fontWeight: FontWeight.bold,
          letterSpacing: 2,
        ),
      );

  Widget _field({
    required TextEditingController controller,
    required String hint,
    required ColorScheme cs,
    required Color cardBg,
    int minLines = 1,
    int maxLines = 1,
  }) =>
      TextField(
        controller: controller,
        style: TextStyle(color: cs.onSurface, fontSize: 15),
        minLines: minLines,
        maxLines: maxLines,
        textAlignVertical: maxLines > 1 ? TextAlignVertical.top : TextAlignVertical.center,
        decoration: InputDecoration(
          filled: true,
          fillColor: cardBg,
          hintText: hint,
          hintStyle: TextStyle(color: cs.onSurface.withValues(alpha: 0.24), fontSize: 13),
          contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
          border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide.none),
          enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide.none),
          focusedBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12),
            borderSide: BorderSide(color: cs.onSurface.withValues(alpha: 0.24)),
          ),
        ),
      );

  Widget _prioritySelector(ColorScheme cs) {
    const options = [
      (TicketPriority.low, 'tickets.priority_low', Color(0xFF8E8E93)),
      (TicketPriority.medium, 'tickets.priority_medium', Color(0xFFFFCC00)),
      (TicketPriority.high, 'tickets.priority_high', Color(0xFFFF9500)),
      (TicketPriority.critical, 'tickets.priority_critical', Color(0xFFFF3B30)),
    ];

    return Row(
      children: [
        for (int i = 0; i < options.length; i++) ...[
          if (i > 0) const SizedBox(width: 8),
          Expanded(child: _priorityChip(options[i].$1, options[i].$2.tr(), options[i].$3, cs)),
        ],
      ],
    );
  }

  Widget _departmentDropdown(ColorScheme cs, Color cardBg) {
    if (_loadingDepts) {
      return Container(
        height: 52,
        decoration: BoxDecoration(color: cardBg, borderRadius: BorderRadius.circular(12)),
        child: Center(
          child: SizedBox(
            width: 16,
            height: 16,
            child: CircularProgressIndicator(strokeWidth: 2, color: cs.onSurface.withValues(alpha: 0.24)),
          ),
        ),
      );
    }

    if (_departments.isEmpty) {
      return GestureDetector(
        onTap: _loadDepartments,
        child: Container(
          height: 52,
          padding: const EdgeInsets.symmetric(horizontal: 16),
          decoration: BoxDecoration(color: cardBg, borderRadius: BorderRadius.circular(12)),
          child: Row(
            children: [
              Expanded(
                child: Text(
                  'create_ticket.no_depts'.tr(),
                  style: TextStyle(color: cs.onSurface.withValues(alpha: 0.24), fontSize: 12),
                ),
              ),
              Icon(Icons.refresh, color: cs.onSurface.withValues(alpha: 0.24), size: 16),
            ],
          ),
        ),
      );
    }

    return Container(
      height: 52,
      padding: const EdgeInsets.symmetric(horizontal: 16),
      decoration: BoxDecoration(
        color: cardBg,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: _selectedDept != null ? cs.onSurface.withValues(alpha: 0.24) : Colors.transparent,
        ),
      ),
      child: DropdownButtonHideUnderline(
        child: DropdownButton<Department>(
          value: _selectedDept,
          isExpanded: true,
          dropdownColor: cardBg,
          icon: Icon(Icons.expand_more, color: cs.onSurface.withValues(alpha: 0.38), size: 20),
          hint: Text('create_ticket.select_area'.tr(), style: TextStyle(color: cs.onSurface.withValues(alpha: 0.24), fontSize: 13)),
          style: TextStyle(color: cs.onSurface, fontSize: 14),
          items: [
            DropdownMenuItem<Department>(
              value: null,
              child: Text('create_ticket.no_area'.tr(), style: TextStyle(color: cs.onSurface.withValues(alpha: 0.38), fontSize: 13)),
            ),
            ..._departments.map((dept) => DropdownMenuItem<Department>(
                  value: dept,
                  child: Text(dept.name),
                )),
          ],
          onChanged: (dept) {
            HapticFeedback.selectionClick();
            setState(() => _selectedDept = dept);
          },
        ),
      ),
    );
  }

  Widget _priorityChip(TicketPriority p, String label, Color color, ColorScheme cs) {
    final selected = _priority == p;
    return GestureDetector(
      onTap: () {
        HapticFeedback.selectionClick();
        setState(() => _priority = p);
      },
      child: Container(
        height: 52,
        decoration: BoxDecoration(
          color: selected ? color.withValues(alpha: 0.12) : Theme.of(context).cardColor,
          borderRadius: BorderRadius.circular(10),
          border: Border.all(
            color: selected ? color : cs.onSurface.withValues(alpha: 0.1),
            width: selected ? 1.5 : 1,
          ),
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              width: 8,
              height: 8,
              decoration: BoxDecoration(
                color: selected ? color : cs.onSurface.withValues(alpha: 0.24),
                shape: BoxShape.circle,
              ),
            ),
            const SizedBox(height: 5),
            Text(
              label,
              style: TextStyle(
                color: selected ? color : cs.onSurface.withValues(alpha: 0.38),
                fontSize: 9,
                fontWeight: FontWeight.bold,
                letterSpacing: 1,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
