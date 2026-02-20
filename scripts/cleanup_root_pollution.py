import os

ROOT_DIR = r"c:\API\interno"
FILES_TO_REMOVE = [
    "enums.py",
    "product.py",
    "product_service.py",
    "products.py",
    "uom.py",
    "20260212_create_master_data_tables.py",
    "requirements.txt" # Solo si está en la raíz y es redundante
]

def clean_root():
    print(f"🧹 Iniciando limpieza de archivos huérfanos en {ROOT_DIR}...")
    for file_name in FILES_TO_REMOVE:
        file_path = os.path.join(ROOT_DIR, file_name)
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"✅ Eliminado: {file_name}")

if __name__ == "__main__":
    clean_root()