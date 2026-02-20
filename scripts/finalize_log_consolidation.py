import os
from pathlib import Path

def finalize_log():
    print("📜 FINALIZANDO CONSOLIDACIÓN DE LOGS...")
    root = Path(__file__).resolve().parent.parent
    old_log = root / "docs" / "archive" / "INTERNAL_CLEANUP_LOG.md"
    
    if old_log.exists():
        print(f"🗑️ Eliminando archivo obsoleto: {old_log}")
        os.remove(old_log)
    else:
        print(f"⚠️ No se encontró {old_log}, quizás ya fue eliminado.")

if __name__ == "__main__":
    finalize_log()