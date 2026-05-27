import 'package:flutter/material.dart';
import 'package:interno_billing_app/core/di/injection.dart';
import 'package:interno_billing_app/core/theme/app_theme.dart';
import 'package:interno_billing_app/features/home/data/document_repository.dart';
import 'package:interno_billing_app/features/home/data/models/document_models.dart';

class ReceiptsScreen extends StatefulWidget {
  const ReceiptsScreen({super.key});

  @override
  State<ReceiptsScreen> createState() => _ReceiptsScreenState();
}

class _ReceiptsScreenState extends State<ReceiptsScreen> {
  static const _filters = [
    _Filter('Todos', null),
    _Filter('Ventas', 'OUT'),
    _Filter('Ingresos', 'IN'),
    _Filter('Ajustes', 'ADJUSTMENT'),
  ];

  int _selectedFilterIndex = 0;
  List<InventoryDocumentRow> _documents = [];
  bool _isLoading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadDocuments();
  }

  Future<void> _loadDocuments() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });
    try {
      final repo = sl<DocumentRepository>();
      final docs = await repo.listDocuments(
        documentType: _filters[_selectedFilterIndex].apiType,
      );
      if (mounted) setState(() => _documents = docs);
    } catch (e) {
      if (mounted) setState(() => _error = 'No se pudo cargar el historial');
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      appBar: AppBar(
        backgroundColor: Colors.black,
        title: const Text(
          'MIS RECIBOS',
          style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold, letterSpacing: 2),
        ),
        centerTitle: true,
        automaticallyImplyLeading: false,
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh_rounded, color: Colors.white54),
            onPressed: _loadDocuments,
            tooltip: 'Actualizar',
          ),
        ],
      ),
      body: Column(
        children: [
          // Filter chips
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
            child: Row(
              children: List.generate(_filters.length, (i) {
                final isSelected = i == _selectedFilterIndex;
                return GestureDetector(
                  onTap: () {
                    if (_selectedFilterIndex != i) {
                      setState(() => _selectedFilterIndex = i);
                      _loadDocuments();
                    }
                  },
                  child: Container(
                    margin: const EdgeInsets.only(right: 8),
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                    decoration: BoxDecoration(
                      color: isSelected
                          ? InternoColors.cyan.withValues(alpha: 0.1)
                          : Colors.white.withValues(alpha: 0.05),
                      borderRadius: BorderRadius.circular(20),
                      border: Border.all(
                        color: isSelected ? InternoColors.cyan : Colors.transparent,
                        width: 1,
                      ),
                    ),
                    child: Text(
                      _filters[i].label,
                      style: TextStyle(
                        color: isSelected ? InternoColors.cyan : Colors.white60,
                        fontSize: 12,
                        fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                      ),
                    ),
                  ),
                );
              }),
            ),
          ),

          // Content
          Expanded(child: _buildBody()),
        ],
      ),
    );
  }

  Widget _buildBody() {
    if (_isLoading) {
      return ListView.builder(
        padding: const EdgeInsets.symmetric(horizontal: 20),
        itemCount: 6,
        itemBuilder: (context, i) => _buildSkeletonCard(),
      );
    }

    if (_error != null) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.cloud_off_rounded, size: 48, color: Colors.white.withValues(alpha: 0.15)),
            const SizedBox(height: 16),
            Text(_error!, style: const TextStyle(color: Colors.white38, fontSize: 14)),
            const SizedBox(height: 16),
            TextButton.icon(
              onPressed: _loadDocuments,
              icon: const Icon(Icons.refresh_rounded, color: InternoColors.cyan),
              label: const Text('Reintentar', style: TextStyle(color: InternoColors.cyan)),
            ),
          ],
        ),
      );
    }

    if (_documents.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.receipt_long_outlined, size: 64, color: Colors.white.withValues(alpha: 0.1)),
            const SizedBox(height: 16),
            const Text('No hay recibos recientes', style: TextStyle(color: Colors.white38, fontSize: 16)),
            const SizedBox(height: 8),
            const Text('Tus documentos aparecerán aquí', style: TextStyle(color: Colors.white24, fontSize: 12)),
          ],
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: _loadDocuments,
      color: InternoColors.cyan,
      backgroundColor: const Color(0xFF1A1A1A),
      child: ListView.builder(
        padding: const EdgeInsets.fromLTRB(20, 4, 20, 20),
        itemCount: _documents.length,
        itemBuilder: (_, index) => _buildDocumentCard(_documents[index]),
      ),
    );
  }

  Widget _buildDocumentCard(InventoryDocumentRow doc) {
    final typeColor = _typeColor(doc.type);
    final statusColor = _statusColor(doc.status);
    final dateLabel = _formatDate(doc.date);

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF0E0E0E),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.white.withValues(alpha: 0.06)),
      ),
      child: Row(
        children: [
          // Type badge
          Container(
            width: 44,
            height: 44,
            decoration: BoxDecoration(
              color: typeColor.withValues(alpha: 0.12),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Center(
              child: Icon(_typeIcon(doc.type), color: typeColor, size: 20),
            ),
          ),
          const SizedBox(width: 14),

          // Main info
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Text(
                      doc.folio,
                      style: const TextStyle(
                        color: Colors.white,
                        fontWeight: FontWeight.bold,
                        fontSize: 14,
                        letterSpacing: 0.3,
                      ),
                    ),
                    const SizedBox(width: 8),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                      decoration: BoxDecoration(
                        color: statusColor.withValues(alpha: 0.12),
                        borderRadius: BorderRadius.circular(6),
                      ),
                      child: Text(
                        _statusLabel(doc.status),
                        style: TextStyle(color: statusColor, fontSize: 9, fontWeight: FontWeight.bold, letterSpacing: 0.5),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 4),
                Text(
                  '${doc.itemsCount} ${doc.itemsCount == 1 ? 'artículo' : 'artículos'} · $dateLabel',
                  style: const TextStyle(color: Colors.white38, fontSize: 11),
                ),
              ],
            ),
          ),

          // Amount
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text(
                '\$${doc.totalAmount.toStringAsFixed(2)}',
                style: TextStyle(
                  color: typeColor,
                  fontWeight: FontWeight.bold,
                  fontSize: 15,
                ),
              ),
              const SizedBox(height: 2),
              Text(
                doc.currency,
                style: const TextStyle(color: Colors.white24, fontSize: 10),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildSkeletonCard() {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      height: 72,
      decoration: BoxDecoration(
        color: const Color(0xFF0E0E0E),
        borderRadius: BorderRadius.circular(16),
      ),
      child: const _Shimmer(),
    );
  }

  Color _typeColor(String type) {
    switch (type) {
      case 'OUT':
        return InternoColors.error;
      case 'IN':
        return InternoColors.success;
      case 'TRANSFER':
        return InternoColors.cyan;
      default:
        return Colors.white54;
    }
  }

  IconData _typeIcon(String type) {
    switch (type) {
      case 'OUT':
        return Icons.arrow_upward_rounded;
      case 'IN':
        return Icons.arrow_downward_rounded;
      case 'TRANSFER':
        return Icons.swap_horiz_rounded;
      default:
        return Icons.receipt_rounded;
    }
  }

  Color _statusColor(String status) {
    switch (status) {
      case 'PROCESSED':
        return InternoColors.success;
      case 'DRAFT':
        return Colors.amber;
      case 'CANCELLED':
        return Colors.red;
      default:
        return Colors.white38;
    }
  }

  String _statusLabel(String status) {
    switch (status) {
      case 'PROCESSED':
        return 'PROCESADO';
      case 'DRAFT':
        return 'BORRADOR';
      case 'CANCELLED':
        return 'CANCELADO';
      default:
        return status;
    }
  }

  String _formatDate(String isoDate) {
    try {
      final dt = DateTime.parse(isoDate).toLocal();
      final now = DateTime.now();
      final diff = now.difference(dt);
      if (diff.inHours < 1) return 'Hace ${diff.inMinutes} min';
      if (diff.inDays < 1) return 'Hace ${diff.inHours} h';
      if (diff.inDays == 1) return 'Ayer';
      return '${dt.day.toString().padLeft(2, '0')}/${dt.month.toString().padLeft(2, '0')}/${dt.year}';
    } catch (_) {
      return isoDate;
    }
  }
}

class _Filter {
  final String label;
  final String? apiType;
  const _Filter(this.label, this.apiType);
}

class _Shimmer extends StatefulWidget {
  const _Shimmer();

  @override
  State<_Shimmer> createState() => _ShimmerState();
}

class _ShimmerState extends State<_Shimmer> with SingleTickerProviderStateMixin {
  late final AnimationController _controller;
  late final Animation<double> _animation;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(vsync: this, duration: const Duration(milliseconds: 1200))
      ..repeat(reverse: true);
    _animation = Tween<double>(begin: 0.03, end: 0.10).animate(_controller);
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _animation,
      builder: (context, child) => Container(
        decoration: BoxDecoration(
          color: Colors.white.withValues(alpha: _animation.value),
          borderRadius: BorderRadius.circular(16),
        ),
      ),
    );
  }
}
