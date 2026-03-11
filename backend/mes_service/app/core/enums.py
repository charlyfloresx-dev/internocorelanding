from enum import Enum

class ProductionEventType(str, Enum):
    START = "START"
    PAUSE = "PAUSE"
    RESUME = "RESUME"
    STOP = "STOP"
    SCRAP = "SCRAP"
    FINISH = "FINISH"