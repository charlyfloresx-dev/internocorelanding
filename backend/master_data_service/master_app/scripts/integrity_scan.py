import asyncio
import sys
import os
import uuid
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

# Ajuste de paths para ejecucion desde la raiz del microservicio
sys.path.append(os.getcwd())
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), "..")))

from common.domain import Base, MultiTenantBase, ProductStatus, VersionStatus
# Importar modelos para cargar metadata
from master_app.models import Product, ProductCategory, UM, ProductVersion
from master_app.db.session import DATABASE_URL

async def run_integrity_scan():
    print("[Antigravity] Iniciando Escaneo de Integridad en Modo Auditor...")
    print(f"Target DB: {DATABASE_URL}")
    
    engine = create_async_engine(DATABASE_URL, pool_pre_ping=True)
    
    # Modo Demo: Inicializar esquema si es SQLite en memoria o test
    if "sqlite" in DATABASE_URL:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("  [DEMO] Esquema inicializado en SQLite.")

    async_session = AsyncSession(bind=engine)
    
    report = {
        "summary": {"total_tables": 0, "violations": 0, "warnings": 0},
        "details": []
    }
    
    async with async_session as session:
        # Descubrir tablas gestionadas por el dominio
        tables = Base.metadata.tables.keys()
        report["summary"]["total_tables"] = len(tables)
        
        for table_name in tables:
            print(f"  Analizando tabla: {table_name}...")
            table = Base.metadata.tables[table_name]
            
            # 1. Verificar herencia de MultiTenantBase (presencia de company_id)
            has_company_id = "company_id" in table.columns
            
            # Contar total de registros
            count_stmt = select(func.count()).select_from(table)
            total_rows = (await session.execute(count_stmt)).scalar() or 0
            
            violations = []
            
            if has_company_id:
                # Buscar registros con company_id nulo
                null_company_stmt = select(func.count()).select_from(table).where(table.c.company_id == None)
                null_company_count = (await session.execute(null_company_stmt)).scalar() or 0
                
                if null_company_count > 0:
                    report["summary"]["violations"] += 1
                    violations.append(f"FAILED: Detectados {null_company_count} registros sin company_id (Fuga de Multi-tenancy)")
            else:
                report["summary"]["warnings"] += 1
                violations.append("WARNING: Tabla no hereda de MultiTenantBase explicitamente.")

            # 2. Verificar colisiones de transaction_id (si existe la columna)
            if "transaction_id" in table.columns:
                collision_stmt = select(table.c.transaction_id, func.count(func.distinct(table.c.company_id)))\
                                .where(table.c.transaction_id != None)\
                                .group_by(table.c.transaction_id)\
                                .having(func.count(func.distinct(table.c.company_id)) > 1)
                
                collisions = (await session.execute(collision_stmt)).all()
                if collisions:
                    report["summary"]["warnings"] += len(collisions)
                    violations.append(f"CONFLICT: Colision de transaction_id en {len(collisions)} IDs compartidos entre multiples tenants.")

            # 3. Validacion de Enums (ej. Status)
            if "status" in table.columns:
                valid_statuses = [s.value for s in ProductStatus]
                invalid_status_stmt = select(func.count()).select_from(table).where(table.c.status.notin_(valid_statuses))
                invalid_count = (await session.execute(invalid_status_stmt)).scalar() or 0
                if invalid_count > 0:
                    report["summary"]["violations"] += 1
                    violations.append(f"FAILED: {invalid_count} registros con Estatus invalido.")

            report["details"].append({
                "table": table_name,
                "total_rows": total_rows,
                "status": "OK" if not violations else "ISSUES",
                "findings": violations
            })

    await engine.dispose()
    return report

def generate_markdown_report(report):
    md = "# Reporte de Integridad Antigravity: Master Data Service\n\n"
    md += f"**Fecha de Escaneo:** {uuid.uuid4().hex[:8]} (Session ID)\n"
    md += f"**Resumen:**\n"
    md += f"- Tablas Escaneadas: {report['summary']['total_tables']}\n"
    md += f"- Violaciones Criticas: {report['summary']['violations']}\n"
    md += f"- Advertencias: {report['summary']['warnings']}\n\n"
    
    md += "## Detalle por Tabla\n\n"
    md += "| Tabla | Registros | Estado | Hallazgos |\n"
    md += "| :--- | :--- | :--- | :--- |\n"
    
    for detail in report["details"]:
        findings = "<br>".join(detail["findings"]) if detail["findings"] else "Sin hallazgos."
        md += f"| {detail['table']} | {detail['total_rows']} | {detail['status']} | {findings} |\n"
        
    md += "\n---\n*Generado por el Agente Antigravity en Modo Auditor.*"
    return md

if __name__ == "__main__":
    result = asyncio.run(run_integrity_scan())
    report_md = generate_markdown_report(result)
    
    report_path = os.path.join("..", "..", "..", ".gemini", "antigravity", "brain", "9dbdbcd5-e7fa-4e78-b30c-2e3676f3f7cf", "integrity_scan_report.md")
    # Intentar guardarlo si existe la ruta de artifacts, si no imprimir localmente
    try:
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_md)
        print(f"\n[OK] Reporte generado en: {report_path}")
    except:
        with open("integrity_scan_report.md", "w", encoding="utf-8") as f:
            f.write(report_md)
        print("\n[OK] Reporte generado localmente en integrity_scan_report.md")
