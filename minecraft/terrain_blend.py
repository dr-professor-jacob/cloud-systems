#!/usr/bin/env python3
"""
terrain_blend.py — Elevated Inland Plateau
Raised to Y=75 to match the cathedral floor.
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

# --- COORDINATES (Inland & Elevated) ---
CX, CZ, YF = -80, 280, 75
X1, X2 = CX - 23, CX + 23
Z1, Z2 = CZ - 19, CZ + 19

print(f"=== Leveling Elevated Plateau: {CX}, {YF}, {CZ} ===")

# 1. Fill Building Gaps
print("--- Packing soil into building gaps ---")
fill(X1-2, YF-1, Z1-2, X2+2, YF-1, Z2+2, 'dirt', 'replace air')
fill(X1-1, YF, Z1-1, X2+1, YF, Z2+1, 'grass_block', 'replace air')

# 2. Level the Earthen Plateau
print("--- Raising the massive inland plateau ---")
# Build from current ground (approx 64) up to floor (75)
for y in range(60, YF):
    fill(CX-35, y, CZ-35, CX+35, y, CZ+35, 'dirt', 'keep')
    # Texture with mud/coarse dirt
    for _ in range(20):
        rx = random.randint(CX-35, CX+35)
        rz = random.randint(CZ-35, CZ+35)
        block = random.choice(['coarse_dirt', 'mud'])
        fill(rx, y, rz, rx+2, y, rz+2, block, 'replace dirt')

# 3. Create Natural Slopes
print("--- Creating slopes down to natural ground ---")
for i in range(1, 20):
    dist = 35 + i
    h = YF - (i // 2)
    if h < 62: h = 62
    fill(CX-dist, h, CZ-dist, CX+dist, h, CZ+dist, 'dirt', 'keep')

# 4. Surface Greening
fill(CX-35, YF-1, CZ-35, CX+35, YF-1, CZ+35, 'grass_block', 'replace dirt')

print("=== Elevated Plateau Complete! ===")
