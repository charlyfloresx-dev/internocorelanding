import 'package:equatable/equatable.dart';

class ScanPattern extends Equatable {
  final String id;
  final String itemCode;
  final String patternName;
  final String regex;
  final String errorMessage;
  final int priority;
  final bool isActive;

  const ScanPattern({
    required this.id,
    required this.itemCode,
    required this.patternName,
    required this.regex,
    required this.errorMessage,
    required this.priority,
    required this.isActive,
  });

  factory ScanPattern.fromJson(Map<String, dynamic> json) {
    return ScanPattern(
      id: json['id'] as String,
      itemCode: json['item_code'] as String,
      patternName: json['pattern_name'] as String,
      regex: json['regex'] as String,
      errorMessage: json['error_message'] as String,
      priority: (json['priority'] as num?)?.toInt() ?? 0,
      isActive: json['is_active'] as bool? ?? true,
    );
  }

  @override
  List<Object?> get props => [id, itemCode, patternName, regex, errorMessage, priority, isActive];
}
