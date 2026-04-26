#!/usr/bin/env python3
"""
industrial_base.py — High-Ceiling Cathedral Factory v10
X: 1271-1308, Z: 1886-1929, Y: 55-80
Massive interior volume, high-tech aesthetic, and mob-proof.
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

def safe_fill(x1, y1, z1, x2, y2, z2, blk, mode=None):
    x1, x2 = min(int(x1), int(x2)), max(int(x1), int(x2))
    y1, y2 = min(int(y1), int(y2)), max(int(y1), int(y2))
    z1, z2 = min(int(z1), int(z2)), max(int(z1), int(z2))
    chunk_size = 6
    for y in range(y1, y2 + 1, chunk_size):
        ey = min(y + chunk_size - 1, y2)
        args = ['fill', x1, y, z1, x2, ey, z2, blk]
        if mode: args.append(mode)
        rcon(*args)

# --- COORDINATES ---
X1, X2 = 1271, 1308
Z1, Z2 = 1886, 1929
YF = 60 # Floor
YH = 75 # High Ceiling (15 blocks tall!)
CX, CZ = (X1 + X2) // 2, (Z1 + Z2) // 2

print(f"=== Constructing High-Ceiling Industrial Base at {CX}, {CZ} ===")

# 1. MASSIVE EXCAVATION (Safe Build)
# Clear the interior volume from 60 up to 76
safe_fill(X1+1, YF+1, Z1+1, X2-1, YH+1, Z2-1, 'air')

# 2. ARCHITECTURAL SHELL
# Polished Deepslate Floor
safe_fill(X1, YF, Z1, X2, YF, Z2, 'polished_deepslate')
# Reinforced Walls (Deepslate Bricks with Obsidian Support Pillars)
safe_fill(X1, YF, Z1, X2, YH, Z1, 'deepslate_bricks')
safe_fill(X1, YF, Z2, X2, YH, Z2, 'deepslate_bricks')
safe_fill(X1, YF, Z1, X1, YH, Z2, 'deepslate_bricks')
safe_fill(X2, YF, Z1, X2, YH, Z2, 'deepslate_bricks')
# Pillars in corners
for px, pz in [(X1, Z1), (X1, Z2), (X2, Z1), (X2, Z2)]:
    safe_fill(px, YF, pz, px, YH, pz, 'obsidian')

# 3. HIGH-TECH ROOF (Deepslate Tiles with Industrial Girders)
safe_fill(X1, YH+1, Z1, X2, YH+1, Z2, 'deepslate_tiles')
# Girders across the ceiling
for z in range(Z1+5, Z2, 10):
    safe_fill(X1+1, YH, z, X2-1, YH, z, 'obsidian')

# 4. ADVANCED LIGHTING (Industrial Lanterns & Beams)
print("--- Installing High-Altitude Lighting ---")
# Ceiling Spotlights (Recessed in roof)
for lx in range(X1+4, X2, 8):
    for lz in range(Z1+4, Z2, 8):
        setblock(lx, YH+1, lz, 'glowstone')
# Floating Light Beams (Using Tinted Glass and Sea Lanterns)
for lx in [CX-10, CX+10]:
    for lz in [CZ-15, CZ+15]:
        safe_fill(lx, YF+1, lz, lx, YH-1, lz, 'sea_lantern')

# 5. MULTI-BLOCK STAGING (Pre-built platforms)
# NW: Coke Oven Row
for i in range(3):
    oz = Z1 + 2 + (i*4)
    fill(X1+2, YF+1, oz, X1+4, YF+3, oz+2, 'modern_industrialization:coke_oven_brick', 'hollow')
    setblock(X1+3, YF+2, oz, 'modern_industrialization:coke_oven')

# NE: Blast Furnace Row
for i in range(3):
    oz = Z1 + 2 + (i*4)
    fill(X2-4, YF+1, oz, X2-2, YF+3, oz+2, 'modern_industrialization:firebrick', 'hollow')
    setblock(X2-3, YF+2, oz, 'modern_industrialization:bronze_blast_furnace')

# 6. LOGISTICS HUB (Center Cross)
# 4-block wide main corridor
safe_fill(X1+1, YF, CZ-2, X2-1, YF, CZ+2, 'polished_andesite')
safe_fill(CX-2, YF, Z1+1, CX+2, YF, Z2-1, 'polished_andesite')
# Central Beacon Buff
fill(CX-1, YF-1, CZ-1, CX+1, YF-1, CZ+1, 'iron_block')
setblock(CX, YF, CZ, 'beacon')

# 7. MACHINE AUTOMATION (Early MI)
# SW processing line
for i in range(5):
    setblock(X1+2, YF+1, Z2-2-i*2, 'modern_industrialization:bronze_macerator')
    setblock(X1+4, YF+1, Z2-2-i*2, 'modern_industrialization:bronze_furnace')
    setblock(X1+3, YF+1, Z2-2-i*2, 'modern_industrialization:item_pipe')

print("=== High-Ceiling Cathedral Factory Initialized! ===")
