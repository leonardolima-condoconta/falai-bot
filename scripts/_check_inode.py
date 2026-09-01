#!/usr/bin/env python3
"""Check if app's socket inode exists in /proc/net/tcp"""

target = "344765561"
print(f"=== Buscando inode {target} em /proc/net/tcp ===")

found = False
with open('/proc/net/tcp', 'r') as f:
    for line in f:
        parts = line.strip().split()
        if len(parts) >= 10 and parts[9] == target:
            found = True
            state = parts[3]
            state_name = "ESTABLISHED" if state == "01" else "state=" + state
            remote_hex = parts[2]
            ip_val = int(remote_hex[0:8], 16)
            b1 = ip_val & 0xFF
            b2 = (ip_val >> 8) & 0xFF
            b3 = (ip_val >> 16) & 0xFF
            b4 = (ip_val >> 24) & 0xFF
            ip = f"{b4}.{b3}.{b2}.{b1}"
            port = int(remote_hex[8:12], 16)
            print(f"  ENCONTRADO: {state_name}, Remote={ip}:{port}")
            break
if not found:
    print("  NAO ENCONTRADO em /proc/net/tcp -- app SEM conexao TCP! RED_FLAG")

# List all ESTABLISHED connections to port 443
print("\n=== Todas conexoes ESTABLISHED porta 443 ===")
with open('/proc/net/tcp', 'r') as f:
    next(f)
    count = 0
    for line in f:
        parts = line.strip().split()
        if len(parts) >= 10 and parts[3] == "01":
            remote_hex = parts[2]
            port = int(remote_hex[8:12], 16)
            if port == 443:
                count += 1
                ip_val = int(remote_hex[0:8], 16)
                b1 = ip_val & 0xFF
                b2 = (ip_val >> 8) & 0xFF
                b3 = (ip_val >> 16) & 0xFF
                b4 = (ip_val >> 24) & 0xFF
                ip = f"{b4}.{b3}.{b2}.{b1}"
                inode = parts[9]
                print(f"  inode={inode} -> {ip}:443")
print(f"  Total: {count} conexoes")
