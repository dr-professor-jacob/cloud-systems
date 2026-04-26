#!/usr/bin/env python3
"""
terrain_blend.py — Inland Plateau Edition
Levels the ground with soil and mud, ensuring a flush building fit in the new location.
"""
import subprocess, time, random

def rcon(*args):
    cmd = ['sudo', 'docker', 'exec', 'minecraft', 'rcon-cli', '--'] + [str(a) for a in args]
    subprocess.run(cmd, capture_output=True, text=True)
    time.sleep(0.01)

def fill(x1, y1, z1, x2, y2, z2, blk, mode=None):
    args = ['fill', x1, y1, z1, x2, y2, z2, blk]
    if mode: args.append(mode)
    rcon(*args)

# --- COORDINATES (Matches Cathedral Inland Edition) ---
CX, CZ, YF = -80, 280, 64
X1, X2 = CX - 23, CX + 23
Z1, Z2 = CZ - 19, CZ + 19

print(f"=== Leveling Plateau at New Location: {CX}, {YF}, {CZ} ===")

# 1. Fill Building Gaps
print("--- Packing soil into building gaps ---")
fill(X1-2, YF-1, Z1-2, X2+2, YF-1, Z2+2, 'dirt', 'replace air')
fill(X1-1, YF, Z1-1, X2+1, YF, Z2+1, 'grass_block', 'replace air')

# 2. Level the Earthen Plateau
print("--- Raising the inland plateau ---")
# Fill from sea level (62) to floor level (64) in a 60x60 area
for y in range(60, YF):
    fill(CX-30, y, CZ-30, CX+30, y, CZ+30, 'dirt', 'keep')
    # Texture with mud/coarse dirt
    for _ in range(15):
        rx = random.randint(CX-30, CX+30)
        rz = random.randint(CZ-30, CZ+30)
        block = random.choice(['coarse_dirt', 'mud'])
        fill(rx, y, rz, rx+2, y, rz+2, block, 'replace dirt')

# 3. Naturalize Surface
print("--- Surface greening ---")
fill(CX-32, YF-1, CZ-32, CX+32, YF-1, CZ+32, 'grass_block', 'replace dirt')

print("=== Plateau Leveling Complete! ===")
