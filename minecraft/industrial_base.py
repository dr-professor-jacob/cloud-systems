#!/usr/bin/env python3
"""
industrial_base.py — Pro MI Industrial Complex v8
X: 1271-1308, Z: 1886-1929, Y: 58-69
Hollow Multiblocks, Logic Basement, and High-Density Automation.
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

print(f"=== Constructing Pro MI Complex at {CX}, {CZ} ===")

# 1. Total Reset (Deep clearing for basement)
fill(X1, 58, Z1, X2, 69, Z2, 'air')
fill(X1, 57, Z1, X2, 57, Z2, 'polished_deepslate') # Foundation floor
fill(X1, 61, Z1, X2, 68, Z1, 'deepslate_bricks') # Walls
fill(X1, 61, Z2, X2, 68, Z2, 'deepslate_bricks')
fill(X1, 61, Z1, X1, 68, Z2, 'deepslate_bricks')
fill(X2, 61, Z1, X2, 68, Z2, 'deepslate_bricks')
fill(X1, 69, Z1, X2, 69, Z2, 'deepslate_tiles') # Roof

# 2. LOGISTICS BASEMENT (Hollow space for pipes/cables)
fill(X1+1, 58, Z1+1, X2-1, 60, Z2-1, 'air')
fill(X1+1, 61, Z1+1, X2-1, 61, Z2-1, 'polished_deepslate') # Main Working Floor

# 3. HOLLOW COKE OVENS (NW)
for i in range(2):
    oz = Z1 + 2 + (i*4)
    # 3x3x3 Hollow Structure
    fill(X1+2, YF, oz, X1+4, YF+2, oz+2, 'modern_industrialization:coke_oven_brick', 'hollow')
    setblock(X1+3, YF+1, oz, 'modern_industrialization:coke_oven') # Controller
    # Hatches
    setblock(X1+2, YF+1, oz+1, 'modern_industrialization:bronze_item_input_hatch')
    setblock(X1+4, YF+1, oz+1, 'modern_industrialization:bronze_item_output_hatch')
    setblock(X1+3, YF, oz+1, 'modern_industrialization:bronze_fluid_output_hatch')

# 4. HOLLOW BLAST FURNACES (NE)
for i in range(2):
    oz = Z1 + 2 + (i*4)
    # 3x3x3 Hollow Firebrick
    fill(X2-4, YF, oz, X2-2, YF+2, oz+2, 'modern_industrialization:firebrick', 'hollow')
    setblock(X2-3, YF+1, oz, 'modern_industrialization:bronze_blast_furnace')
    # Hatches
    setblock(X2-2, YF+1, oz+1, 'modern_industrialization:bronze_item_input_hatch')
    setblock(X2-4, YF+1, oz+1, 'modern_industrialization:bronze_item_output_hatch')
    setblock(X2-3, YF, oz+1, 'modern_industrialization:bronze_energy_input_hatch')

# 5. DENSE PROCESSING (SW)
for i in range(4):
    setblock(X1+2, YF, Z2-2-i, 'modern_industrialization:bronze_macerator')
    setblock(X1+4, YF, Z2-2-i, 'modern_industrialization:bronze_furnace')
    # Item Pipe Spine
    setblock(X1+3, YF, Z2-2-i, 'modern_industrialization:item_pipe')

# 6. TANK FARM (SE)
for tx in range(2):
    for tz in range(2):
        bx, bz = X2-5+tx*2, Z2-5+tz*2
        fill(bx, YF, bz, bx, YF+2, bz, 'modern_industrialization:bronze_tank')
        setblock(bx, YF-1, bz, 'modern_industrialization:fluid_pipe')

# 7. QUARRY & STEAM GEN (Center-North)
setblock(CX, YF, Z1+2, 'modern_industrialization:quarry')
setblock(CX-2, YF, Z1+2, 'modern_industrialization:bronze_boiler')
setblock(CX+2, YF, Z1+2, 'modern_industrialization:bronze_boiler')
# Steam pipe under floor
fill(CX-2, YF-1, Z1+2, CX+2, YF-1, Z1+2, 'modern_industrialization:fluid_pipe')

# 8. LIGHTING
for x in range(X1+4, X2, 8):
    for z in range(Z1+4, Z2, 8):
        setblock(x, 68, z, 'sea_lantern')

# Kill any stray mobs
rcon('kill', f'@e[type=!player,x={CX},y={YF},z={CZ},distance=..50]')

print("=== Pro MI Factory floor initialized with hollow multiblocks! ===")
