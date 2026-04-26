#!/usr/bin/env python3
"""
surveyor.py — Scans the base area and generates a JSON map for analysis.
X: 1271-1308, Z: 1886-1929, Y: 60-70
"""
import subprocess, time, json, re

def rcon(*args):
    cmd = ['sudo', 'docker', 'exec', 'minecraft', 'rcon-cli', '--'] + [str(a) for a in args]
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.stdout.strip()

X1, X2 = 1271, 1308
Z1, Z2 = 1886, 1929
Y1, Y2 = 60, 70

layout = []

print(f"=== Starting Survey of {X1},{Z1} to {X2},{Z2} ===")

# Scan non-air blocks to keep JSON small and analysis quick
for y in range(Y1, Y2 + 1):
    print(f"Scanning layer Y={y}...")
    for x in range(X1, X2 + 1, 2): # Stepped scan for "cheap/quick" speed
        for z in range(Z1, Z2 + 1, 2):
            # Get block data
            res = rcon('data', 'get', 'block', x, y, z)
            if 'air' not in res.lower() and 'found' not in res.lower():
                # Extract the ID using regex
                match = re.search(r'id: "(.*?)"', res)
                if match:
                    block_id = match.group(1)
                    layout.append({
                        "x": x, "y": y, "z": z,
                        "id": block_id
                    })

with open('base_layout.json', 'w') as f:
    json.dump(layout, f, indent=2)

print(f"=== Survey Complete! Found {len(layout)} relevant blocks. Saved to base_layout.json ===")
