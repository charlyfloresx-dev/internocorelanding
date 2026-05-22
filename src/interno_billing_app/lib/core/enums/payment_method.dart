enum PaymentMethod {
  cash('CASH'),
  card('CARD'),
  transfer('TRANSFER');

  final String value;
  const PaymentMethod(this.value);

  String get displayName {
    switch (this) {
      case PaymentMethod.cash:
        return 'Efectivo';
      case PaymentMethod.card:
        return 'Tarjeta';
      case PaymentMethod.transfer:
        return 'Transferencia';
    }
  }
}
