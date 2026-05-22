import logging
import uuid
from typing import List, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
import sqlalchemy as sa
from app.models.notification import (
    Notification, NotificationRecipient, NotificationPriority,
    NotificationCategory, NotificationChannel, NotificationStatus,
)
from app.models.whatsapp_mapping import WhatsAppGroupMapping
from app.infrastructure.whatsapp_client import WhatsAppClient, WhatsAppClientError
from app.infrastructure.base_whatsapp import BaseWhatsAppClient
from app.infrastructure.whatsapp_factory import WhatsAppClientFactory
from app.core.websocket import manager

logger = logging.getLogger(__name__)

class NotificationService:
    def __init__(self, db: AsyncSession, whatsapp_client: Optional[BaseWhatsAppClient] = None):
        self.db = db
        self._whatsapp_client = whatsapp_client

    async def notify_company(
        self, 
        company_id: uuid.UUID,
        title: str,
        message: str,
        category: NotificationCategory = NotificationCategory.INFO,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        action_url: Optional[str] = None,
        metadata: Optional[dict] = None
    ):
        """
        Envía una notificación global a todos los miembros de una empresa.
        1. Persiste en DB.
        2. Hace broadcast vía WebSocket.
        """
        notification = Notification(
            company_id=company_id,
            tenant_id=company_id,
            title=title,
            message=message,
            category=category,
            priority=priority,
            action_url=action_url,
            payload=metadata
        )
        self.db.add(notification)
        await self.db.flush() # Para obtener el ID

        # Enviar vía WebSocket en tiempo real
        await manager.broadcast_to_company(
            message={
                "type": "NOTIFICATION_RECEIVED",
                "data": notification.to_dict()
            },
            company_id=str(company_id)
        )
        
        logger.info(f"🔔 Global Notification sent to company {company_id}: {title}")
        return notification

    async def notify_user(
        self,
        company_id: uuid.UUID,
        user_id: uuid.UUID,
        title: str,
        message: str,
        category: NotificationCategory = NotificationCategory.INFO,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        action_url: Optional[str] = None,
        metadata: Optional[dict] = None
    ):
        """
        Envía una notificación dirigida a un usuario específico.
        """
        final_payload = metadata or {}
        if action_url and "action_url" not in final_payload:
            final_payload["action_url"] = action_url

        notification = Notification(
            company_id=company_id,
            tenant_id=company_id,
            title=title,
            message=message,
            category=category,
            priority=priority,
            payload=final_payload
        )
        self.db.add(notification)
        await self.db.flush()

        recipient = NotificationRecipient(
            company_id=company_id,
            tenant_id=company_id,
            notification_id=notification.id,
            user_id=user_id
        )
        self.db.add(recipient)

        # Enviar vía WebSocket solo al usuario
        await manager.send_personal_message(
            message={
                "type": "NOTIFICATION_RECEIVED",
                "data": notification.to_dict()
            },
            user_id=str(user_id),
            company_id=str(company_id)
        )

        logger.info(f"👤 Private Notification sent to user {user_id}: {title}")
        return notification

    async def notify_role(
        self,
        company_id: uuid.UUID,
        role_name: str,
        title: str,
        message: str,
        category: NotificationCategory = NotificationCategory.INFO,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        action_url: Optional[str] = None,
        metadata: Optional[dict] = None
    ):
        """
        Envía una notificación a todos los usuarios que tengan un rol específico.
        """
        # Consulta directa a las tablas compartidas (sin importar auth_app)
        # Ambos servicios comparten la misma BD, las tablas siempre existen.
        from sqlalchemy import text

        query = text("""
            SELECT u.id FROM users u
            JOIN user_company_roles ucr ON u.id = ucr.user_id
            JOIN roles r ON ucr.role_id = r.id
            WHERE ucr.company_id = :company_id
              AND lower(r.name) = lower(:role_name)
        """)
        result = await self.db.execute(query, {"company_id": company_id, "role_name": role_name})
        user_ids = result.scalars().all()

        if not user_ids:
            logger.warning(f"⚠️ No users found for role {role_name} in company {company_id}. Notifying company instead.")
            return await self.notify_company(company_id, title, message, category, priority, action_url, metadata)

        # 2. Crear la notificación base (para el historial)
        final_payload = metadata or {}
        if action_url and "action_url" not in final_payload:
            final_payload["action_url"] = action_url

        notification = Notification(
            company_id=company_id,
            tenant_id=company_id,
            title=title,
            message=message,
            category=category,
            priority=priority,
            payload=final_payload
        )
        self.db.add(notification)
        await self.db.flush()

        # 3. Vincular a cada destinatario
        for u_id in user_ids:
            recipient = NotificationRecipient(
                company_id=company_id,
                tenant_id=company_id,
                notification_id=notification.id,
                user_id=u_id
            )
            self.db.add(recipient)
            
            # 4. Enviar WebSocket en tiempo real si están conectados
            await manager.send_personal_message(
                message={
                    "type": "NOTIFICATION_RECEIVED",
                    "data": notification.to_dict()
                },
                user_id=str(u_id),
                company_id=str(company_id)
            )

        logger.info(f"👥 Role-based Notification sent to {len(user_ids)} users with role {role_name}")
        return notification

    # ─── WHATSAPP GROUP NOTIFICATIONS ───────────────────────────────────────

    async def notify_whatsapp_group(
        self,
        company_id: uuid.UUID,
        group_name: str,
        title: str,
        message: str,
        category: NotificationCategory = NotificationCategory.INFO,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        template_name: Optional[str] = None,
        template_params: Optional[dict] = None,
        metadata: Optional[dict] = None,
    ) -> Notification:
        """
        Envía una notificación a un grupo de WhatsApp mapeado para una empresa.

        Flujo:
          1. Resuelve el whatsapp_group_id desde la tabla de mapeo (company_id + group_name).
          2. Envía el mensaje vía WhatsAppClient (texto plano o template).
          3. Persiste el registro en la tabla de notificaciones con status SENT/FAILED.

        Args:
            company_id: UUID de la empresa (multitenant isolation).
            group_name: Nombre lógico del grupo (e.g., "TECNICOS_PLANTA", "SUPERVISORES").
            title: Título de la notificación (para auditoría interna).
            message: Cuerpo del mensaje de texto plano.
            template_name: (Opcional) Nombre de template pre-aprobado de WhatsApp.
            template_params: (Opcional) Parámetros para rellenar el template.
            metadata: (Opcional) Datos extra para el payload de auditoría.
        """
        from sqlalchemy import select

        # 1. Resolver los mappings multitenant (soporta múltiples destinatarios para un mismo nombre de grupo)
        query = select(WhatsAppGroupMapping).where(
            WhatsAppGroupMapping.company_id == company_id,
            WhatsAppGroupMapping.group_name == group_name,
            WhatsAppGroupMapping.is_active == True,
        )
        result = await self.db.execute(query)
        mappings = result.scalars().all()

        if not mappings:
            logger.error(
                f"❌ WhatsApp: No active mappings found for company={company_id}, group={group_name}"
            )
            raise ValueError(
                f"No WhatsApp mappings for company={company_id}, group_name='{group_name}'. "
                f"Register at least one via the admin endpoint first."
            )

        # 2. Crear el registro de notificación base (auditoría global)
        final_payload = metadata or {}
        final_payload["whatsapp_group_name"] = group_name
        final_payload["recipient_count"] = len(mappings)

        notification = Notification(
            company_id=company_id,
            tenant_id=company_id,
            title=title,
            message=message,
            category=category,
            priority=priority,
            channel=NotificationChannel.WHATSAPP,
            status=NotificationStatus.PENDING,
            payload=final_payload,
        )
        self.db.add(notification)
        await self.db.flush()

        # 3. Resolver el cliente de WhatsApp — Factory multitenant dinámico
        wa_client = self._whatsapp_client
        if not wa_client:
            try:
                wa_client = await WhatsAppClientFactory.get_client_for_tenant(self.db, str(company_id))
            except Exception as e:
                logger.error(f"❌ WhatsApp: Factory resolution failed for company {company_id}: {e}")
                notification.status = NotificationStatus.FAILED
                await self.db.flush()
                return notification

        success_count = 0
        delivery_details = []

        for mapping in mappings:
            try:
                if template_name:
                    response = await wa_client.send_template_message(
                        group_id=mapping.whatsapp_group_id,
                        template_name=template_name,
                        template_params=template_params,
                    )
                else:
                    formatted_message = f"*{title}*\n\n{message}"
                    response = await wa_client.send_group_message(
                        group_id=mapping.whatsapp_group_id,
                        message=formatted_message,
                        metadata={"notification_id": str(notification.id), "company_id": str(company_id)},
                    )

                success_count += 1
                delivery_details.append({
                    "target": mapping.whatsapp_group_id,
                    "status": "SENT",
                    "sid": response.get("sid") if response else None
                })

            except (WhatsAppClientError, Exception) as e:
                error_msg = getattr(e, 'message', str(e))
                logger.error(f"❌ WhatsApp: Failed to send to {mapping.whatsapp_group_id}: {error_msg}")
                delivery_details.append({
                    "target": mapping.whatsapp_group_id,
                    "status": "FAILED",
                    "error": error_msg
                })

        # Actualizar estado final
        final_payload["delivery_details"] = delivery_details
        notification.payload = final_payload
        
        if success_count == len(mappings):
            notification.status = NotificationStatus.SENT
        elif success_count > 0:
            notification.status = NotificationStatus.PARTIAL
        else:
            notification.status = NotificationStatus.FAILED

        logger.info(
            f"✅ WhatsApp Broadcast: Notification '{title}' sent to {success_count}/{len(mappings)} "
            f"recipients in group '{group_name}' for company {company_id}"
        )

        await self.db.flush()
        return notification

