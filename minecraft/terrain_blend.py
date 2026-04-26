#!/usr/bin/env python3
"""
terrain_blend.py — Soil Specialist & Gap Sealer
Fills the area with rich soil (dirt/mud/coarse_dirt) and ensures a flush building fit.
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

# Center and Bounds (Elevated to Y=75)
CX, CZ, YF = -80, 149, 75
X1, X2 = -103, -57
Z1, Z2 = 130, 168

print("=== Applying Soil & Sealing Perimeter ===")

# 1. Fill the "One Block Gap" with Soil
print("--- Packing soil into building gaps ---")
# Fill dirt directly against the walls to ensure no air remains
fill(X1-2, YF-1, Z1-2, X2+2, YF-1, Z2+2, 'dirt', 'replace air')
fill(X1-1, YF, Z1-1, X2+1, YF, Z2+1, 'grass_block', 'replace air')

# 2. Large Scale Soil Infill
print("--- Raising the plateau with mixed soil ---")
for y in range(60, YF):
    # Base layer of dirt
    fill(X1-25, y, Z1-25, X2+25, y, Z2+25, 'dirt', 'keep')
    
    # Randomly inject coarse dirt and mud for texture
    for _ in range(10):
        rx = random.randint(X1-25, X2+25)
        rz = random.randint(Z1-25, Z2+25)
        block = random.choice(['coarse_dirt', 'mud'])
        fill(rx, y, rz, rx+3, y, rz+3, block, 'replace dirt')

# 3. Smooth Soil Transition
print("--- Creating natural soil slopes ---")
for i in range(1, 15):
    dist = 25 + i
    h = YF - (i // 2)
    if h < 62: h = 62
    fill(X1-dist, h, Z1-dist, X2+dist, h, Z2+dist, 'dirt', 'keep')

# 4. Final Surface Greening (Soil topcoat)
fill(X1-25, YF-1, Z1-25, X2+25, YF-1, Z2+25, 'grass_block', 'replace dirt')
fill(X1-25, YF-1, Z1-25, X2+25, YF-1, Z2+25, 'grass_block', 'replace coarse_dirt')
fill(X1-25, YF-1, Z1-25, X2+25, YF-1, Z2+25, 'grass_block', 'replace mud')

print("=== Soil leveling complete! ===")
