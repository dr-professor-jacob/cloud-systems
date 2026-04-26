#!/usr/bin/env python3
"""
terrain_blend.py — High Inland Plateau
Elevates the terrain to Y=85 with gradual soil slopes to avoid the "recess" look.
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

# --- SAFE COORDINATES (Far Inland & High) ---
CX, CZ, YF = -80, 450, 85
X1, X2 = CX - 23, CX + 23
Z1, Z2 = CZ - 19, CZ + 19

print(f"=== Leveling Elevated Plateau at {CX}, {YF}, {CZ} ===")

# 1. Solid Infill beneath the building
print("--- Packing soil foundation ---")
# Fill from natural ground level up to Y=85
for y in range(60, YF):
    fill(X1-10, y, Z1-10, X2+10, y, Z2+10, 'dirt', 'keep')

# 2. Gradual Slopes (20 block transition)
print("--- Creating gradual earthen slopes ---")
for i in range(1, 21):
    dist = 10 + i
    # The higher the i, the lower the Y (creating a ramp)
    h = YF - (i // 1.5)
    if h < 64: h = 64
    fill(X1-dist, h, Z1-dist, X2+dist, h, Z2+dist, 'dirt', 'keep')

# 3. Surface Texturing
print("--- Blending soil types ---")
for _ in range(50):
    rx = random.randint(CX-40, CX+40)
    rz = random.randint(CZ-40, CZ+40)
    block = random.choice(['coarse_dirt', 'mud', 'rooted_dirt'])
    fill(rx, YF-1, rz, rx+2, YF-1, rz+2, block, 'replace dirt')

# 4. Greening
print("--- Surface greening ---")
fill(CX-35, YF-1, CZ-35, CX+35, YF-1, CZ+35, 'grass_block', 'replace dirt')

print("=== Plateau Leveling Complete! ===")
