import logging

logger = logging.getLogger(__name__)

class EventPublisher:
    """
    Clase base para publicación de eventos de dominio (RabbitMQ/SNS).
    Por ahora implementa un log, listo para ser extendido.
    """
    async def publish(self, event_name: str, payload: dict):
        # TODO: Implementar conexión real a RabbitMQ
        logger.info(f"🚀 EVENT PUBLISHED: {event_name} | Payload: {payload}")