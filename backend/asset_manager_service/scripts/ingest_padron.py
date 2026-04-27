import re
import psycopg2
from decimal import Decimal
import os

# Database Connection Info (Hardcoded for script, normally use env)
DB_CONFIG = {
    "dbname": "asset_manager",
    "user": "postgres",
    "password": "password",
    "host": "localhost",
    "port": "5432"
}

def parse_line(line):
    # Regex to extract: ID, Clave Catastral, Description, Value1, Value2
    # Example: 1 PP-018-132 Parque Industrial Pacifico II - Área Verde $ 20,844,457.49 $ -
    pattern = r'^(\d+)\s+([A-Z0-9-]{7,})\s+(.*?)\s+\$\s*([\d,.-]+)\s+\$\s*([\d,.-]+|-)'
    match = re.match(pattern, line.strip())
    if match:
        idx, cve, desc, val_t, val_c = match.groups()
        
        # Clean currency values
        def clean_val(v):
            if v == '-': return Decimal('0')
            return Decimal(v.replace(',', ''))
        
        return {
            "cve": cve,
            "desc": desc,
            "val_t": clean_val(val_t),
            "val_c": clean_val(val_c)
        }
    return None

def ingest_file(file_path, year, conn):
    cur = conn.cursor()
    print(f"Ingesting {file_path} for year {year}...")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            data = parse_line(line)
            if data:
                # Insert or Update
                if year == 2020:
                    cur.execute("""
                        INSERT INTO properties (cve_cat, description, valor_terreno_2020, valor_const_2020)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (cve_cat) DO UPDATE SET
                        valor_terreno_2020 = EXCLUDED.valor_terreno_2020,
                        valor_const_2020 = EXCLUDED.valor_const_2020;
                    """, (data['cve'], data['desc'], data['val_t'], data['val_c']))
                else:
                    cur.execute("""
                        INSERT INTO properties (cve_cat, description, valor_terreno_2026, valor_const_2026)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (cve_cat) DO UPDATE SET
                        valor_terreno_2026 = EXCLUDED.valor_terreno_2026,
                        valor_const_2026 = EXCLUDED.valor_const_2026;
                    """, (data['cve'], data['desc'], data['val_t'], data['val_c']))
                    
    conn.commit()
    cur.close()

if __name__ == "__main__":
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        
        # Ingest 2020 data
        ingest_file('PadronInmoviliarioMunicipal.md', 2020, conn)
        
        # Ingest 2026 data
        ingest_file('PadronInmoviliarioMunicipal2026.md', 2026, conn)
        
        print("Ingestion complete.")
        conn.close()
    except Exception as e:
        print(f"Error: {e}")
