from app.db.base import Base, engine
from app.models.domain import User, Company, UserCompanyRole # Asegúrate de que estos nombres existan

print("Forzando creación de tablas...")
Base.metadata.create_all(bind=engine)
print("Tablas creadas exitosamente.")