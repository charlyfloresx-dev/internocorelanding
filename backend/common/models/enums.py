from enum import IntEnum

class ProductStatus(IntEnum):
    DRAFT = 1
    ACTIVE = 2
    OBSOLETE = 3
    ARCHIVED = 4

class VersionStatus(IntEnum):
    EXPERIMENTAL = 1
    RELEASED = 2
    UNDER_REVIEW = 3
    DEPRECATED = 4

class ProductType(IntEnum):
    RAW_MATERIAL = 1
    FINISHED_GOOD = 2
    SUB_ASSEMBLY = 3
    SERVICE = 4