import socket

# --- CONFIGURACION ---
# Cambia esta IP por tu IP actual si cambia (192.168.1.146)
TARGET_IP = '192.168.1.146'
DOMAIN = 'momentos.com'

def build_response(data):
    # Transaction ID
    TID = data[:2]
    # Flags: standard query response, no error
    Flags = b'\x81\x80'
    # Questions and Answer Counts
    Counts = b'\x00\x01\x00\x01\x00\x00\x00\x00'
    # Original Question
    Question = data[12:]
    
    # Answer part
    # Pointer to domain name in question (0xc00c)
    Answer = b'\xc0\x0c'
    # Type A (0x0001), Class IN (0x0001)
    Answer += b'\x00\x01\x00\x01'
    # TTL: 60 seconds
    Answer += b'\x00\x00\x00\x3c'
    # Data length: 4 bytes (IPv4)
    Answer += b'\x00\x04'
    # The IP address bytes
    Answer += bytes(map(int, TARGET_IP.split('.')))
    
    return TID + Flags + Counts + Question + Answer

def start_dns():
    # UDP socket for DNS
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.bind(('0.0.0.0', 53))
        print(f"🚀 Servidor DNS Interno CORRIENDO...")
        print(f"📍 Redirigiendo {DOMAIN} -> {TARGET_IP}")
        print(f"-------------------------------------------")
        print(f"Instruccion: Configura el DNS de tu celular a {TARGET_IP}")
    except PermissionError:
        print("❌ ERROR: Debes ejecutar este script como ADMINISTRADOR.")
        return

    while True:
        data, addr = sock.recvfrom(512)
        # Check if query contains our domain
        if DOMAIN.encode() in data:
            print(f"🔍 Solicitud para {DOMAIN} recibida de {addr[0]}")
            response = build_response(data)
            sock.sendto(response, addr)

if __name__ == '__main__':
    start_dns()
