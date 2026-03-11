import uuid
from typing import Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Request
from common.models.audit_log import AuditLog
from common.context import request_context

class AuditLogger:
    @staticmethod
    async def log_action(
        db: AsyncSession,
        action: str,
        table_name: Optional[str] = None,
        record_id: Optional[str] = None,
        old_value: Optional[dict[str, Any]] = None,
        new_value: Optional[dict[str, Any]] = None,
        request: Optional[Request] = None,
        user_id: Optional[str] = None,
        company_id: Optional[str] = None,
        group_id: Optional[str] = None,
        trace_id: Optional[str] = None
    ) -> AuditLog:
        """
        Logs an action into the unified audit_logs table.
        It attempts to extract context from UserContext if no explicit identifiers are passed.
        """
        # Attempt to get from context if not provided
        ctx = request_context.get()
        final_user_id = user_id or (str(ctx.user_id) if ctx and ctx.user_id else None)
        final_company_id = company_id or (str(ctx.company_id) if ctx and ctx.company_id else None)
        final_group_id = group_id or (str(ctx.group_id) if ctx and ctx.group_id else None)
        final_trace_id = trace_id or (ctx.trace_id if ctx and ctx.trace_id else None)
        
        # Get metadata from request
        ip_address = None
        user_agent = None
        
        if request:
            ip_address = request.client.host if request.client else None
            # Behind proxy support
            x_forwarded_for = request.headers.get("x-forwarded-for")
            if x_forwarded_for:
                ip_address = x_forwarded_for.split(",")[0]
            user_agent = request.headers.get("user-agent")
            
            # Fallback to request.state if not in context
            if not final_trace_id:
                final_trace_id = getattr(request.state, 'transaction_id', None)
            
            if not final_trace_id:
                final_trace_id = request.headers.get("X-Trace-Id") or \
                                 request.headers.get("X-Correlation-ID") or \
                                 request.headers.get("X-Transaction-ID")

        audit_log = AuditLog(
            id=str(uuid.uuid4()),
            table_name=table_name,
            record_id=record_id,
            action=action,
            old_value=old_value,
            new_value=new_value,
            user_id=final_user_id,
            company_id=final_company_id,
            group_id=final_group_id,
            ip_address=ip_address,
            user_agent=user_agent,
            trace_id=final_trace_id
        )
        
        db.add(audit_log)
        await db.flush() # Execute but wait for outermost commit
        
        return audit_log
