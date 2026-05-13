import subprocess
import time
import os

def run_command(cmd):
    print(f"[*] Running: {cmd}")
    return subprocess.run(cmd, shell=True)

def main():
    print("="*60)
    print(" CHAOS TEST: KILL SWITCH & RECOVERY (Muro de Hierro)")
    print("="*60)

    # 1. Start Loader in background
    print("[1/4] Iniciando Bulk Loader (100k registros)...")
    loader_proc = subprocess.Popen(
        ["python", "backend/scripts/big_bang_inventory_loader.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        cwd=os.getcwd()
    )

    # 2. Wait for activity
    print("[2/4] Monitoreando actividad del loader...")
    start_time = time.time()
    db_killed = False
    
    while True:
        line = loader_proc.stdout.readline()
        if not line:
            break
        print(f"  [Loader] {line.strip()}")
        
        # Kill DB after some batches
        if "Batch 20" in line and not db_killed:
            print("\n" + "!"*40)
            print("!!! KILL SWITCH ACTIVATED: Stopping DB !!!")
            print("!"*40 + "\n")
            run_command("docker stop interno-db")
            db_killed = True
            kill_moment = time.time()
        
        # Recovery after 10 seconds
        if db_killed and (time.time() - kill_moment) > 10:
            print("\n" + "!"*40)
            print("!!! RECOVERY INITIATED: Starting DB !!!")
            print("!"*40 + "\n")
            run_command("docker start interno-db")
            db_killed = False # Reset so we don't start it again
            # We don't exit, let the loader finish
            
        if loader_proc.poll() is not None:
            break

    loader_proc.wait()
    print("\n[4/4] Test completado.")
    print("="*60)

if __name__ == "__main__":
    main()
