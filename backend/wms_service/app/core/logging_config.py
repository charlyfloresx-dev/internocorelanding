import logging
import sys

# Asumiendo que JsonFormatter está definido en el paquete common
# Si no, se puede usar una implementación estándar de python-json-logger
try:
    from common.logger import JsonFormatter
except ImportError:
    # Fallback a una clase dummy si no se encuentra para evitar errores de importación
    # En un entorno real, esto debería estar garantizado por el paquete common.
    class JsonFormatter(logging.Formatter):
        def format(self, record):
            # Simplistic JSON formatter for demonstration
            log_record = {
                "timestamp": self.formatTime(record, self.datefmt),
                "level": record.levelname,
                "message": record.getMessage(),
                "name": record.name,
            }
            if hasattr(record, 'trace_id'):
                log_record['trace_id'] = record.trace_id
            if hasattr(record, 'company_id'):
                log_record['company_id'] = record.company_id
            return str(log_record)

def setup_logging():
    """
    Configura el logger raíz para usar JsonFormatter y enviar logs a stdout.
    Toma control de los loggers de uvicorn para unificar el formato.
    """
    # Obtenemos los loggers que queremos reconfigurar
    loggers = [logging.getLogger()] + [logging.getLogger(name) for name in logging.root.manager.loggerDict if name.startswith("uvicorn")]
    
    # Creamos el handler con el formateador JSON
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    
    for logger_instance in loggers:
        logger_instance.handlers = [handler]
        logger_instance.setLevel(logging.INFO)