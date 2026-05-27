class InventoryDocumentRow {
  final String id;
  final String folio;
  final String date;
  final String type;
  final String origin;
  final String destination;
  final int itemsCount;
  final String status;
  final double totalAmount;
  final String currency;

  const InventoryDocumentRow({
    required this.id,
    required this.folio,
    required this.date,
    required this.type,
    required this.origin,
    required this.destination,
    required this.itemsCount,
    required this.status,
    required this.totalAmount,
    required this.currency,
  });

  factory InventoryDocumentRow.fromJson(Map<String, dynamic> json) {
    return InventoryDocumentRow(
      id: json['id'] as String? ?? '',
      folio: json['folio'] as String? ?? '',
      date: json['date'] as String? ?? '',
      type: json['type'] as String? ?? '',
      origin: json['origin'] as String? ?? '',
      destination: json['destination'] as String? ?? '',
      itemsCount: (json['items_count'] as num?)?.toInt() ?? 0,
      status: json['status'] as String? ?? '',
      totalAmount: (json['total_amount'] as num?)?.toDouble() ?? 0.0,
      currency: json['currency'] as String? ?? 'MXN',
    );
  }
}
