#!/usr/bin/env python3
"""
industrial_base.py — MI Starter Complex
X: 1271-1308, Z: 1886-1929, Y: 60-69
Focused on Early-Mid MI (Multi-blocks, Tanks, Pipes).
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

print(f"=== Constructing MI Industrial Complex at {CX}, {CZ} ===")

# 1. Clear & Structural
fill(X1, 60, Z1, X2, 69, Z2, 'air')
fill(X1, 60, Z1, X2, 60, Z2, 'polished_deepslate')
fill(X1, 61, Z1, X2, 68, Z1, 'deepslate_bricks') # Walls
fill(X1, 61, Z2, X2, 68, Z2, 'deepslate_bricks')
fill(X1, 61, Z1, X1, 68, Z2, 'deepslate_bricks')
fill(X2, 61, Z1, X2, 68, Z2, 'deepslate_bricks')

# 2. NW: MULTI-BLOCK ZONE
# Bronze Blast Furnace (3x3x3 footprint)
fill(X1+1, YF, Z1+1, X1+3, YF+2, Z1+3, 'modern_industrialization:firebrick')
setblock(X1+2, YF+1, Z1+1, 'modern_industrialization:bronze_blast_furnace') # The controller
# Coke Oven (3x3x3 footprint)
fill(X1+5, YF, Z1+1, X1+7, YF+2, Z1+3, 'modern_industrialization:coke_oven_brick')
setblock(X1+6, YF+1, Z1+1, 'modern_industrialization:coke_oven')

# 3. NE: FLUID STORAGE (Tanks & Pipes)
for i in range(4):
    tx = X2-2-i*2
    setblock(tx, YF, Z1+1, 'modern_industrialization:bronze_tank')
    # Connect with fluid pipes
    setblock(tx, YF-1, Z1+1, 'modern_industrialization:fluid_pipe')
fill(X2-8, YF-1, Z1+1, X2-2, YF-1, Z1+1, 'modern_industrialization:fluid_pipe')

# 4. SW: PROCESSING START
setblock(X1+1, YF, Z2-2, 'modern_industrialization:bronze_boiler')
setblock(X1+3, YF, Z2-2, 'modern_industrialization:bronze_macerator')
setblock(X1+5, YF, Z2-2, 'modern_industrialization:bronze_furnace')
# Pre-wire with Bronze Pipes
fill(X1+1, YF-1, Z2-2, X1+5, YF-1, Z2-2, 'modern_industrialization:pipe')

# 5. SE: QUARRY ZONE
setblock(X2-2, YF, Z2-2, 'modern_industrialization:quarry')
setblock(X2-2, YF, Z2-4, 'modern_industrialization:bronze_tank') # Steam buffer for quarry

# 6. STORAGE & LOGISTICS
for i in range(4):
    setblock(X2-1, YF, Z2-1-i, 'pneumaticcraft:reinforced_chest')

# 7. LIGHTING
for x in [X1+4, CX, X2-4]:
    for z in [Z1+4, CZ, Z2-4]:
        setblock(x, 68, z, 'sea_lantern')

print("=== MI Complex Built and Ready for Steel! ===")
