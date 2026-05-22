import 'package:equatable/equatable.dart';

class Partner extends Equatable {
  final String id;
  final String name;
  final String code;
  final String? type;

  const Partner({
    required this.id,
    required this.name,
    required this.code,
    this.type,
  });

  factory Partner.fromJson(Map<String, dynamic> json) {
    return Partner(
      id: json['id'],
      name: json['name'],
      code: json['code'] ?? '',
      type: json['type'],
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'name': name,
        'code': code,
        'type': type,
      };

  @override
  List<Object?> get props => [id, name, code, type];
}
