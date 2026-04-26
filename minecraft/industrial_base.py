#!/usr/bin/env python3
"""
industrial_base.py — Cathedral Factory v11 (Trimmed)
X: 1271-1308, Z: 1886-1929, Y: 60-69
Optimized height (Below 70), massive interior, mob-proof.
"""
import subprocess, time

def rcon(*args):
    cmd = ['sudo', 'docker', 'exec', 'minecraft', 'rcon-cli', '--'] + [str(a) for a in args]
    subprocess.run(cmd, capture_output=True, text=True)
    time.sleep(0.02)

def setblock(x, y, z, blk):
    rcon('setblock', x, y, z, blk)

def safe_fill(x1, y1, z1, x2, y2, z2, blk, mode=None):
    x1, x2 = min(int(x1), int(x2)), max(int(x1), int(x2))
    y1, y2 = min(int(y1), int(y2)), max(int(y1), int(y2))
    z1, z2 = min(int(z1), int(z2)), max(int(z1), int(z2))
    chunk_size = 5
    for y in range(y1, y2 + 1, chunk_size):
        ey = min(y + chunk_size - 1, y2)
        args = ['fill', x1, y, z1, x2, ey, z2, blk]
        if mode: args.append(mode)
        rcon(*args)

# --- COORDINATES ---
X1, X2 = 1271, 1308
Z1, Z2 = 1886, 1929
YF = 60 # Floor
YH = 69 # Ceiling (Strictly below 70)
CX, CZ = (X1 + X2) // 2, (Z1 + Z2) // 2

print(f"=== Constructing Trimmed Cathedral Factory at {CX}, {CZ} ===")

# 1. EXCAVATION
safe_fill(X1, YF, Z1, X2, YH, Z2, 'air')

# 2. SHELL
safe_fill(X1, YF, Z1, X2, YF, Z2, 'polished_deepslate') # Floor
safe_fill(X1, YF+1, Z1, X2, YH-1, Z1, 'deepslate_bricks') # Walls
safe_fill(X1, YF+1, Z2, X2, YH-1, Z2, 'deepslate_bricks')
safe_fill(X1, YF+1, Z1, X1, YH-1, Z2, 'deepslate_bricks')
safe_fill(X2, YF+1, Z1, X2, YH-1, Z2, 'deepslate_bricks')
safe_fill(X1, YH, Z1, X2, YH, Z2, 'deepslate_tiles') # Roof

# Pillars
for px, pz in [(X1, Z1), (X1, Z2), (X2, Z1), (X2, Z2)]:
    safe_fill(px, YF+1, pz, px, YH-1, pz, 'obsidian')

# 3. LIGHTING
for lx in range(X1+4, X2, 6):
    for lz in range(Z1+4, Z2, 6):
        setblock(lx, YH, lz, 'sea_lantern')

# 4. MULTIBLOCKS
# NW: Coke Ovens
for i in range(2):
    oz = Z1 + 3 + (i*5)
    safe_fill(X1+2, YF+1, oz, X1+4, YF+3, oz+2, 'modern_industrialization:coke_oven_brick', 'hollow')
    setblock(X1+3, YF+2, oz, 'modern_industrialization:coke_oven')

# NE: Blast Furnaces
for i in range(2):
    oz = Z1 + 3 + (i*5)
    safe_fill(X2-4, YF+1, oz, X2-2, YF+3, oz+2, 'modern_industrialization:firebrick', 'hollow')
    setblock(X2-3, YF+2, oz, 'modern_industrialization:bronze_blast_furnace')

# 5. LOGISTICS
safe_fill(X1+1, YF, CZ, X2-1, YF, CZ, 'polished_andesite')
safe_fill(CX, YF, Z1+1, CX, YF, Z2-1, 'polished_andesite')
setblock(CX, YF, CZ, 'beacon')
safe_fill(CX-1, YF-1, CZ-1, CX+1, YF-1, CZ+1, 'iron_block')

# 6. MACHINES
for i in range(4):
    setblock(X1+2, YF+1, Z2-2-i*2, 'modern_industrialization:bronze_macerator')
    setblock(X1+4, YF+1, Z2-2-i*2, 'modern_industrialization:bronze_furnace')

rcon('kill', f'@e[type=!player,x={CX},y={YF},z={CZ},distance=..50]')
print("=== Trimmed Cathedral Factory Complete! ===")
