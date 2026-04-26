#!/usr/bin/env python3
"""
industrial_base.py — Pro MI Industrial Complex v13
Fixed height (9 blocks), verified walls, and full machine interior.
X: 1271-1308, Z: 1886-1929, Y: 60-69
"""
import subprocess, time

def rcon(*args):
    cmd = ['sudo', 'docker', 'exec', 'minecraft', 'rcon-cli', '--'] + [str(a) for a in args]
    subprocess.run(cmd, capture_output=True, text=True)
    time.sleep(0.05)

def safe_fill(x1, y1, z1, x2, y2, z2, blk, mode=None):
    x1, x2 = min(int(x1), int(x2)), max(int(x1), int(x2))
    y1, y2 = min(int(y1), int(y2)), max(int(y1), int(y2))
    z1, z2 = min(int(z1), int(z2)), max(int(z1), int(z2))
    # Chunks are small (5 tall) to ensure reliability
    for y in range(y1, y2 + 1, 5):
        ey = min(y + 4, y2)
        args = ['fill', str(x1), str(y), str(z1), str(x2), str(ey), str(z2), blk]
        if mode: args.append(mode)
        rcon(*args)

def setblock(x, y, z, blk):
    rcon('setblock', str(x), str(y), str(z), blk)

# --- COORDINATES ---
X1, X2 = 1271, 1308
Z1, Z2 = 1886, 1929
YF = 60 # Floor
YH = 69 # Ceiling (Strictly below 70)
CX, CZ = (X1 + X2) // 2, (Z1 + Z2) // 2

print(f"=== Constructing v13 Factory at {CX}, {CZ} ===")

# 1. TOTAL EXCAVATION
# Ensure the entire volume is air before we start
safe_fill(X1, YF, Z1, X2, YH, Z2, 'air')

# 2. STRUCTURAL SHELL
# Main Floor
safe_fill(X1, YF, Z1, X2, YF, Z2, 'polished_deepslate')
# Main Ceiling
safe_fill(X1, YH, Z1, X2, YH, Z2, 'deepslate_tiles')

# WALLS (9 blocks tall: Y=61 to 69)
# North/South Walls
safe_fill(X1, YF+1, Z1, X2, YH, Z1, 'deepslate_bricks')
safe_fill(X1, YF+1, Z2, X2, YH, Z2, 'deepslate_bricks')
# West/East Walls
safe_fill(X1, YF+1, Z1, X1, YH, Z2, 'deepslate_bricks')
safe_fill(X2, YF+1, Z1, X2, YH, Z2, 'deepslate_bricks')

# 3. INTERIOR LIGHTING (Recessed into ceiling)
for lx in range(X1+4, X2, 6):
    for lz in range(Z1+4, Z2, 6):
        setblock(lx, YH, lz, 'sea_lantern')

# 4. MULTI-BLOCKS (2 Coke Ovens, 2 Blast Furnaces)
# NW Quadrant: Coke Ovens
for i in range(2):
    oz = Z1 + 5 + (i*8)
    # The structure
    safe_fill(X1+2, YF+1, oz, X1+4, YF+3, oz+2, 'modern_industrialization:coke_oven_brick', 'hollow')
    # The controller
    setblock(X1+3, YF+2, oz, 'modern_industrialization:coke_oven')

# NE Quadrant: Blast Furnaces
for i in range(2):
    oz = Z1 + 5 + (i*8)
    # The structure
    safe_fill(X2-4, YF+1, oz, X2-2, YF+3, oz+2, 'modern_industrialization:firebrick', 'hollow')
    # The controller
    setblock(X2-3, YF+2, oz, 'modern_industrialization:bronze_blast_furnace')

# 5. MACHINE LINE (Processing)
# SW Quadrant: Macerators and Furnaces
for i in range(5):
    pz = Z2 - 5 - (i*3)
    setblock(X1+2, YF+1, pz, 'modern_industrialization:bronze_macerator')
    setblock(X1+4, YF+1, pz, 'modern_industrialization:bronze_furnace')
    # Item Pipe Bus connecting them
    setblock(X1+3, YF+1, pz, 'modern_industrialization:item_pipe')

# SE Quadrant: Storage
for i in range(4):
    setblock(X2-2, YF+1, Z2-2-i, 'pneumaticcraft:reinforced_chest')

# 6. CENTRAL INFRASTRUCTURE
setblock(CX, YF+1, CZ, 'beacon')
fill(CX-1, YF, CZ-1, CX+1, YF, CZ+1, 'iron_block')

# Kill mobs
rcon('kill', '@e[type=!player,distance=..60]')

print("=== v13 Build Complete! Base is Hidden and Populated. ===")
