#!/usr/bin/env python3
"""
industrial_base.py — Pro MI Industrial Complex v9
Maximum Lighting Edition (Anti-Spider).
"""
import subprocess, time

def rcon(*args):
    cmd = ['sudo', 'docker', 'exec', 'minecraft', 'rcon-cli', '--'] + [str(a) for a in args]
    subprocess.run(cmd, capture_output=True, text=True)
    time.sleep(0.02)

def setblock(x, y, z, blk):
    rcon('setblock', x, y, z, blk)

def fill(x1, y1, z1, x2, y2, z2, blk, mode=None):
    args = ['fill', str(x1), str(y1), str(z1), str(x2), str(y2), str(z2), blk]
    if mode: args.append(mode)
    rcon(*args)

# --- COORDINATES ---
X1, X2 = 1271, 1308
Z1, Z2 = 1886, 1929
YF = 61
CX, CZ = (X1 + X2) // 2, (Z1 + Z2) // 2

print(f"=== Re-Constructing with Maximum Lighting at {CX}, {CZ} ===")

# (Structural/Multiblock code stays same as v8...)
fill(X1, 58, Z1, X2, 69, Z2, 'air')
fill(X1, 57, Z1, X2, 57, Z2, 'polished_deepslate')
fill(X1, 61, Z1, X2, 68, Z1, 'deepslate_bricks')
fill(X1, 61, Z2, X2, 68, Z2, 'deepslate_bricks')
fill(X1, 61, Z1, X1, 68, Z2, 'deepslate_bricks')
fill(X2, 61, Z1, X2, 68, Z2, 'deepslate_bricks')
fill(X1, 69, Z1, X2, 69, Z2, 'deepslate_tiles')
fill(X1+1, 58, Z1+1, X2-1, 60, Z2-1, 'air')
fill(X1+1, 61, Z1+1, X2-1, 61, Z2-1, 'polished_deepslate')

# 8. MAXIMUM LIGHTING GRID
print("--- Flooding area with Sea Lanterns ---")
# Dense 4x4 Grid in ceiling
for lx in range(X1+2, X2, 4):
    for lz in range(Z1+2, Z2, 4):
        setblock(lx, 68, lz, 'sea_lantern')

# Floor Recessed Grid (under glass)
for lx in range(X1+2, X2, 6):
    for lz in range(Z1+2, Z2, 6):
        setblock(lx, 60, lz, 'sea_lantern')
        setblock(lx, 61, lz, 'glass')

# Kill any existing spiders
rcon('kill', '@e[type=spider,x=1295,y=65,z=1900,distance=..50]')

print("=== Base is now Sun-Bright and Spider-Free! ===")
