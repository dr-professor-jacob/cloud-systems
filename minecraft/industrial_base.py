#!/usr/bin/env python3
"""
industrial_base.py — Dense MI Automation Base v7
X: 1271-1308, Z: 1886-1929, Y: 60-69
Full Multiblocks, Item/Fluid Pipe Networks, and Steam Power Grid.
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

print(f"=== Constructing Dense MI Industrial Base at {CX}, {CZ} ===")

# 1. Structural Reset
fill(X1, 60, Z1, X2, 69, Z2, 'air')
fill(X1, 60, Z1, X2, 60, Z2, 'polished_deepslate')
fill(X1, 61, Z1, X2, 68, Z1, 'deepslate_bricks')
fill(X1, 61, Z2, X2, 68, Z2, 'deepslate_bricks')
fill(X1, 61, Z1, X1, 68, Z2, 'deepslate_bricks')
fill(X2, 61, Z1, X2, 68, Z2, 'deepslate_bricks')
fill(X1, 69, Z1, X2, 69, Z2, 'deepslate_tiles')

# 2. SW: FULL MULTIBLOCKS (Blast Furnaces & Coke Ovens)
# Coke Oven 1
fill(X1+2, YF, Z2-5, X1+4, YF+2, Z2-3, 'modern_industrialization:coke_oven_brick')
setblock(X1+3, YF+1, Z2-5, 'modern_industrialization:coke_oven')
# Coke Oven 2
fill(X1+6, YF, Z2-5, X1+8, YF+2, Z2-3, 'modern_industrialization:coke_oven_brick')
setblock(X1+7, YF+1, Z2-5, 'modern_industrialization:coke_oven')

# Bronze Blast Furnace 1
fill(X1+10, YF, Z2-5, X1+12, YF+2, Z2-3, 'modern_industrialization:firebrick')
setblock(X1+11, YF+1, Z2-5, 'modern_industrialization:bronze_blast_furnace')
# Bronze Blast Furnace 2
fill(X1+14, YF, Z2-5, X1+16, YF+2, Z2-3, 'modern_industrialization:firebrick')
setblock(X1+15, YF+1, Z2-5, 'modern_industrialization:bronze_blast_furnace')

# 3. NW: STEAM POWER GRID
# 4 Boilers in a row
for i in range(4):
    bx = X1+2 + (i*2)
    setblock(bx, YF, Z1+2, 'modern_industrialization:bronze_boiler')
    # Fluid pipe bus for Steam (above boilers)
    setblock(bx, YF+1, Z1+2, 'modern_industrialization:fluid_pipe')
fill(X1+2, YF+1, Z1+2, X1+8, YF+1, Z1+2, 'modern_industrialization:fluid_pipe')

# 4. NE: AUTOMATED ORE LINE
# Processing Machines
machines = ['bronze_macerator', 'bronze_furnace', 'bronze_macerator', 'bronze_furnace']
for i, m in enumerate(machines):
    mx = X2-10 + (i*2)
    setblock(mx, YF, Z1+2, f'modern_industrialization:{m}')
    # Item Pipe Bus (behind machines)
    setblock(mx, YF, Z1+1, 'modern_industrialization:item_pipe')
    # Fluid Pipe Bus (under floor for Steam)
    setblock(mx, YF-1, Z1+2, 'modern_industrialization:fluid_pipe')
fill(X2-10, YF, Z1+1, X2-4, YF, Z1+1, 'modern_industrialization:item_pipe')
fill(X2-10, YF-1, Z1+2, X2-4, YF-1, Z1+2, 'modern_industrialization:fluid_pipe')

# 5. SE: STORAGE & FLUID TANKS
for i in range(4):
    tx = X2-2-i*2
    setblock(tx, YF, Z2-2, 'modern_industrialization:bronze_tank')
    setblock(tx, YF-1, Z2-2, 'modern_industrialization:fluid_pipe')
fill(X2-8, YF-1, Z2-2, X2-2, YF-1, Z2-2, 'modern_industrialization:fluid_pipe')

# 8 Reinforced Chests
for i in range(8):
    setblock(X2-1, YF, Z2-2-i, 'pneumaticcraft:reinforced_chest')

# 6. INFRASTRUCTURE: The Quarry
setblock(X2-2, YF, CZ, 'modern_industrialization:quarry')
setblock(X2-3, YF, CZ, 'modern_industrialization:fluid_pipe')

# 7. MOB-PROOF LIGHTING
for x in range(X1+4, X2, 8):
    for z in range(Z1+4, Z2, 8):
        setblock(x, 68, z, 'sea_lantern')
        setblock(x, 63, Z1, 'sea_lantern')
        setblock(x, 63, Z2, 'sea_lantern')

# Kill mobs currently inside
rcon('kill', f'@e[type=!player,x={CX},y={YF},z={CZ},distance=..50]')

print("=== MI Factory Floor Initialized with Multiblocks and Piping! ===")
