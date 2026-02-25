import sys
import os
import asyncio
import uuid
from sqlalchemy import Column, String, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base

# Forzar la raíz del proyecto para asegurar que 'common' sea importable
root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if root_path not in sys.path:
    sys.path.insert(0, root_path)

from common.middleware import request_context
from common.models.user_context import UserContext
from common.repository import BaseRepository

# Mock de Modelo y DB para la prueba (sin conectar a DB real para simplicidad del script)
Base = declarative_base()

class MockProduct(Base):
    __tablename__ = 'mock_products'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String)
    company_id = Column(UUID(as_uuid=True))
    is_active = Column(Boolean, default=True)

class MockDbSession:
    """Simula una sesión de SQLAlchemy para capturar la query generada."""
    async def execute(self, query):
        print(f"\n[SQL GENERADO]: {query}")
        return MockResult()
    
    def add(self, obj): pass
    async def flush(self): pass
    async def refresh(self, obj): pass

class MockResult:
    def scalars(self): return self
    def all(self): return []
    def first(self): return None

async def run_test():
    print("🔥 INICIANDO PRUEBA DE FUEGO CQRS FILTER 🔥")
    
    # 1. Definir un contexto de prueba (Empresa A)
    test_company_id = uuid.uuid4()
    user_ctx = UserContext(user_id="user-123", company_id=test_company_id)
    
    # 2. Inyectar contexto en el ContextVar (Simulando Middleware)
    token = request_context.set(user_ctx)
    print(f"✅ Contexto inyectado: Company ID = {test_company_id}")

    # 3. Instanciar Repositorio
    repo = BaseRepository(MockProduct, MockDbSession())

    # 4. Ejecutar consulta (Debería incluir el filtro WHERE company_id = ...)
    print("Ejecutando repo.list()...")
    await repo.list()

    # Limpieza
    request_context.reset(token)

    print("\n🔥 PRUEBA 2: CONTEXTO VACÍO (SYSTEM/ADMIN) 🔥")
    # Sin setear contexto (simulando tarea de fondo o super-admin sin tenant)
    
    # 5. Ejecutar consulta (NO debería incluir el filtro WHERE company_id)
    print("Ejecutando repo.list() sin contexto...")
    await repo.list()

if __name__ == "__main__":
    asyncio.run(run_test())