import logging
import uuid
from typing import List, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from notification_app.models.notification import Notification, NotificationRecipient, NotificationPriority, NotificationCategory
from notification_app.core.websocket import manager

logger = logging.getLogger(__name__)

class NotificationService:
    def __init__(self, db: AsyncSession):
        self.db = db

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
        from sqlalchemy import select
        from auth_app.models.user import User
        from auth_app.models.role import Role
        from auth_app.models.user_company_role import UserCompanyRole

        # 1. Buscar a los usuarios que tienen ese rol en esa empresa
        query = (
            select(User.id)
            .join(UserCompanyRole, User.id == UserCompanyRole.user_id)
            .join(Role, UserCompanyRole.role_id == Role.id)
            .where(
                UserCompanyRole.company_id == company_id,
                Role.name == role_name
            )
        )
        result = await self.db.execute(query)
        user_ids = result.scalars().all()

        if not user_ids:
            logger.warning(f"⚠️ No users found for role {role_name} in company {company_id}. Notifying company instead.")
            return await self.notify_company(company_id, title, message, category, priority, action_url, metadata)

        # 2. Crear la notificación base (para el historial)
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
