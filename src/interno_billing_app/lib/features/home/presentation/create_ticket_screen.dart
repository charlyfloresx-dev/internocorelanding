import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
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
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
        content: Text('El asunto debe tener al menos 5 caracteres'),
        backgroundColor: Colors.redAccent,
        behavior: SnackBarBehavior.floating,
      ));
      return;
    }
    if (desc.length < 10) {
      HapticFeedback.heavyImpact();
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
        content: Text('La descripción debe tener al menos 10 caracteres'),
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
    return BlocListener<TicketsBloc, TicketsState>(
      listener: (context, state) {
        if (state is TicketActionSuccess && state.message.contains('creado')) {
          HapticFeedback.heavyImpact();
          setState(() => _showSuccess = true);
        }
      },
      child: Scaffold(
        backgroundColor: Colors.black,
        body: SafeArea(
          child: AnimatedSwitcher(
            duration: const Duration(milliseconds: 280),
            switchInCurve: Curves.easeOut,
            switchOutCurve: Curves.easeIn,
            child: _showSuccess ? _buildSuccess() : _buildForm(),
          ),
        ),
      ),
    );
  }

  // ── Success State ──────────────────────────────────────────────────────────

  Widget _buildSuccess() {
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
            const Text(
              'TICKET ENVIADO',
              style: TextStyle(
                color: Colors.white,
                fontSize: 22,
                fontWeight: FontWeight.w900,
                letterSpacing: 2,
              ),
            ),
            const SizedBox(height: 12),
            Text(
              'El equipo de soporte ha recibido tu reporte y lo atenderá a la brevedad.',
              textAlign: TextAlign.center,
              style: TextStyle(
                color: Colors.white.withValues(alpha: 0.45),
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
                  foregroundColor: Colors.white,
                  side: const BorderSide(color: Colors.white24),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                ),
                child: const Text(
                  'REPORTAR OTRO PROBLEMA',
                  style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13, letterSpacing: 1),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  // ── Form ──────────────────────────────────────────────────────────────────

  Widget _buildForm() {
    return BlocBuilder<TicketsBloc, TicketsState>(
      key: const ValueKey('form'),
      builder: (context, state) {
        final isLoading = state is TicketsLoading;
        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // ── Header ────────────────────────────────────────────────────
            Padding(
              padding: const EdgeInsets.fromLTRB(24, 20, 24, 0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'NUEVO REPORTE',
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 22,
                      fontWeight: FontWeight.w900,
                      letterSpacing: 1.5,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    'Reporta una falla, incidente o solicitud de soporte',
                    style: TextStyle(color: Colors.white.withValues(alpha: 0.38), fontSize: 12),
                  ),
                ],
              ),
            ),
            const Padding(
              padding: EdgeInsets.symmetric(horizontal: 24, vertical: 16),
              child: Divider(color: Colors.white10, height: 1),
            ),

            // ── Fields ────────────────────────────────────────────────────
            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.symmetric(horizontal: 24),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    _label('ASUNTO'),
                    const SizedBox(height: 8),
                    _field(
                      controller: _titleController,
                      hint: 'Ej: Falla en compresor línea 3',
                    ),

                    const SizedBox(height: 20),

                    _label('PRIORIDAD'),
                    const SizedBox(height: 8),
                    _prioritySelector(),

                    const SizedBox(height: 20),

                    _label('ÁREA (OPCIONAL)'),
                    const SizedBox(height: 8),
                    _departmentDropdown(),

                    const SizedBox(height: 20),

                    _label('DESCRIPCIÓN'),
                    const SizedBox(height: 8),
                    _field(
                      controller: _descController,
                      hint: 'Describe el problema con el mayor detalle posible...',
                      minLines: 4,
                      maxLines: 8,
                    ),

                    const SizedBox(height: 32),
                  ],
                ),
              ),
            ),

            // ── CTA ───────────────────────────────────────────────────────
            Padding(
              padding: const EdgeInsets.fromLTRB(24, 0, 24, 24),
              child: SizedBox(
                width: double.infinity,
                height: 56,
                child: ElevatedButton(
                  onPressed: isLoading ? null : _submit,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.white,
                    foregroundColor: Colors.black,
                    disabledBackgroundColor: Colors.white12,
                    elevation: 0,
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                  ),
                  child: isLoading
                      ? const SizedBox(
                          width: 20,
                          height: 20,
                          child: CircularProgressIndicator(strokeWidth: 2, color: Colors.black54),
                        )
                      : const Text(
                          'CREAR TICKET',
                          style: TextStyle(
                            fontWeight: FontWeight.w900,
                            fontSize: 15,
                            letterSpacing: 1.5,
                          ),
                        ),
                ),
              ),
            ),
          ],
        );
      },
    );
  }

  // ── Helpers ───────────────────────────────────────────────────────────────

  Widget _label(String text) => Text(
        text,
        style: const TextStyle(
          color: Colors.white38,
          fontSize: 10,
          fontWeight: FontWeight.bold,
          letterSpacing: 2,
        ),
      );

  Widget _field({
    required TextEditingController controller,
    required String hint,
    int minLines = 1,
    int maxLines = 1,
  }) =>
      TextField(
        controller: controller,
        style: const TextStyle(color: Colors.white, fontSize: 15),
        minLines: minLines,
        maxLines: maxLines,
        textAlignVertical:
            maxLines > 1 ? TextAlignVertical.top : TextAlignVertical.center,
        decoration: InputDecoration(
          filled: true,
          fillColor: const Color(0xFF111111),
          hintText: hint,
          hintStyle: const TextStyle(color: Colors.white24, fontSize: 13),
          contentPadding:
              const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12),
            borderSide: BorderSide.none,
          ),
          enabledBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12),
            borderSide: BorderSide.none,
          ),
          focusedBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12),
            borderSide: const BorderSide(color: Colors.white24),
          ),
        ),
      );

  Widget _prioritySelector() {
    const options = [
      (TicketPriority.low, 'BAJA', Color(0xFF8E8E93)),
      (TicketPriority.medium, 'MEDIA', Color(0xFFFFCC00)),
      (TicketPriority.high, 'ALTA', Color(0xFFFF9500)),
      (TicketPriority.critical, 'CRÍTICA', Color(0xFFFF3B30)),
    ];

    return Row(
      children: [
        for (int i = 0; i < options.length; i++) ...[
          if (i > 0) const SizedBox(width: 8),
          Expanded(
            child: _priorityChip(options[i].$1, options[i].$2, options[i].$3),
          ),
        ],
      ],
    );
  }

  Widget _departmentDropdown() {
    if (_loadingDepts) {
      return Container(
        height: 52,
        decoration: BoxDecoration(
          color: const Color(0xFF111111),
          borderRadius: BorderRadius.circular(12),
        ),
        child: const Center(
          child: SizedBox(
            width: 16,
            height: 16,
            child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white24),
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
          decoration: BoxDecoration(
            color: const Color(0xFF111111),
            borderRadius: BorderRadius.circular(12),
          ),
          child: Row(
            children: [
              Expanded(
                child: Text(
                  'Sin departamentos — Toca para reintentar',
                  style: TextStyle(color: Colors.white24, fontSize: 12),
                ),
              ),
              const Icon(Icons.refresh, color: Colors.white24, size: 16),
            ],
          ),
        ),
      );
    }

    return Container(
      height: 52,
      padding: const EdgeInsets.symmetric(horizontal: 16),
      decoration: BoxDecoration(
        color: const Color(0xFF111111),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: _selectedDept != null ? Colors.white24 : Colors.transparent,
        ),
      ),
      child: DropdownButtonHideUnderline(
        child: DropdownButton<Department>(
          value: _selectedDept,
          isExpanded: true,
          dropdownColor: const Color(0xFF1A1A1A),
          icon: const Icon(Icons.expand_more, color: Colors.white38, size: 20),
          hint: const Text(
            'Seleccionar área',
            style: TextStyle(color: Colors.white24, fontSize: 13),
          ),
          style: const TextStyle(color: Colors.white, fontSize: 14),
          items: [
            const DropdownMenuItem<Department>(
              value: null,
              child: Text('Sin área', style: TextStyle(color: Colors.white38, fontSize: 13)),
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

  Widget _priorityChip(TicketPriority p, String label, Color color) {
    final selected = _priority == p;
    return GestureDetector(
      onTap: () {
        HapticFeedback.selectionClick();
        setState(() => _priority = p);
      },
      child: Container(
        height: 52,
        decoration: BoxDecoration(
          color: selected ? color.withValues(alpha: 0.12) : const Color(0xFF111111),
          borderRadius: BorderRadius.circular(10),
          border: Border.all(
            color: selected ? color : Colors.white10,
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
                color: selected ? color : Colors.white24,
                shape: BoxShape.circle,
              ),
            ),
            const SizedBox(height: 5),
            Text(
              label,
              style: TextStyle(
                color: selected ? color : Colors.white38,
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
