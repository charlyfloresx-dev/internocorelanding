from enum import Enum


class OpportunityStatus(str, Enum):
    SCOUTING = "Scouting"
    DUE_DILIGENCE = "Due Diligence"
    NEGOCIACION = "Negociación"
    ADJUDICACION = "Adjudicación/Cierre"
    VENTA = "Venta"
    DESCARTADO = "Descartado"


class LegalStatus(str, Enum):
    LIBRE = "Libre"
    INTESTADO = "Intestado"
    LITIGIO = "Litigio"
    EMBARGADO = "Embargado"
    DESCONOCIDO = "Desconocido"
