import re
from typing import Tuple, Optional
from decimal import Decimal

class ParserService:
    """
    Servicio encargado de transformar inputs crudos del scanner en SKU y Cantidad.
    Soporta patrones seriales (ENO...), multi-conteo (5*ITEM) y etiquetas de pallet/box.
    """
    
    # 1. Patrón para Seriales Únicos (Enovis/Safran)
    # Ejemplo: ENO123456789 -> Qty = 1
    SERIAL_PATTERN = r"^ENO[A-Z0-9]+$"
    
    # 2. Patrón para Etiquetas Enovix (A-Series)
    # Ejemplo: A0012345 -> Qty = 1
    ENOVIX_LABEL_PATTERN = r"^A\d+$"
    
    # 3. Patrón para Multi-conteo
    # Ejemplo: 5*ITEM123 -> Qty = 5, SKU = ITEM123
    MULTI_COUNT_PATTERN = r"^(\d+)\*(.+)$"
    
    # 4. Comandos de Sistema (Inputs que disparan lógica en lugar de producción)
    SYSTEM_COMMANDS = ["CLEAR", "STOP", "REJECT", "PAUSE"]

    @classmethod
    def parse_scan(cls, scan_input: str) -> Tuple[str, Decimal]:
        """
        Analiza el input y retorna (sku, qty).
        """
        if not scan_input:
            return "", Decimal("0")
            
        # Limpieza básica
        scan_input = scan_input.strip().upper()
        
        # A. Comandos de Sistema
        if scan_input in cls.SYSTEM_COMMANDS:
            return f"CMD_{scan_input}", Decimal("0")
        
        # B. Verificar Multi-conteo (5*ITEM)
        multi_match = re.match(cls.MULTI_COUNT_PATTERN, scan_input)
        if multi_match:
            qty = Decimal(multi_match.group(1))
            sku = multi_match.group(2)
            return sku, qty
            
        # C. Verificar Serial Único (ENO...) o Enovix Label (A...)
        if re.match(cls.SERIAL_PATTERN, scan_input) or re.match(cls.ENOVIX_LABEL_PATTERN, scan_input):
            return scan_input, Decimal("1.0")
            
        # D. Default: El input es el SKU y la cantidad es 1
        return scan_input, Decimal("1.0")

    @classmethod
    def is_container(cls, sku: str) -> bool:
        """
        Detecta si el SKU representa un contenedor físico (Box, Pallet, Bin).
        Esto permite al ScannerService aplicar la cantidad estándar del master.
        """
        sku_clean = sku.upper()
        return any(x in sku_clean for x in ["BOX", "PALLET", "BIN", "CONTAINER"])
