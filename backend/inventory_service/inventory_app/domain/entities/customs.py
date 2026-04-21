import enum

class CustomsOperationType(str, enum.Enum):
    IMPORT = "IMPORT"
    EXPORT = "EXPORT"
