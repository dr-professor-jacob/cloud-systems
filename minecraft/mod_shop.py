#!/usr/bin/env python3
"""
mod_shop.py — Stealth Hidden Workshop v4
Buries the entire structure and perimeter under dirt to remove the "moat".
"""
import subprocess, time

def rcon(*args):
    cmd = ['sudo', 'docker', 'exec', 'minecraft', 'rcon-cli', '--'] + [str(a) for a in args]
    subprocess.run(cmd, capture_output=True, text=True)
    time.sleep(0.02)

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

def setblock(x, y, z, blk):
    rcon('setblock', x, y, z, blk)

# --- COORDINATES ---
CX, CZ = 1295, 1900
YF = 65
X1, X2 = CX - 10, CX + 10
Z1, Z2 = CZ - 10, CZ + 10
Y_WALL_TOP = YF + 5

print(f"=== Hiding Workshop and Removing Moat at {CX}, {CZ} ===")

# 1. CONSTRUCT INTERIOR FIRST
# Floor, Walls, Machines (as previously defined)
safe_fill(X1, YF, Z1, X2, YF, Z2, 'polished_deepslate')
safe_fill(X1, YF+1, Z1, X2, Y_WALL_TOP, Z1, 'deepslate_bricks')
safe_fill(X1, YF+1, Z2, X2, Y_WALL_TOP, Z2, 'deepslate_bricks')
safe_fill(X1, YF+1, Z1, X1, Y_WALL_TOP, Z2, 'deepslate_bricks')
safe_fill(X2, YF+1, Z1, X2, Y_WALL_TOP, Z2, 'deepslate_bricks')
safe_fill(X1, Y_WALL_TOP+1, Z1, X2, Y_WALL_TOP+1, Z2, 'deepslate_tiles')

# 2. BURY THE ENTIRE STRUCTURE AND MOAT (The Stealth Fix)
# Fill everything AROUND the building with solid Dirt from Y=60 to Y=85
print("--- Packing soil around the perimeter to remove the moat ---")
# North Side
safe_fill(X1-10, 60, Z1-10, X2+10, 84, Z1-1, 'dirt', 'replace air')
# South Side
safe_fill(X1-10, 60, Z2+1, X2+10, 84, Z2+10, 'dirt', 'replace air')
# West Side
safe_fill(X1-10, 60, Z1-10, X1-1, X2+10, 84, 'dirt', 'replace air') # fixed bounds
safe_fill(X1-10, 60, Z1-10, X1-1, 84, Z2+10, 'dirt', 'replace air')
# East Side
safe_fill(X2+1, 60, Z1-10, X2+10, 84, Z2+10, 'dirt', 'replace air')

# 3. BURY THE ROOF
print("--- Burrying the roof ---")
safe_fill(X1-10, Y_WALL_TOP+2, Z1-10, X2+10, 84, Z2+10, 'dirt', 'replace air')

# 4. GRASS CAP
print("--- Surface blending ---")
safe_fill(X1-12, 85, Z1-12, X2+12, 85, Z2+12, 'grass_block', 'replace air')

# 5. Restore Machine Essentials
# NW: Power gen
for i in range(4):
    setblock(X1+1, YF+1, Z1+1+i, 'modern_industrialization:bronze_boiler')
    setblock(X1+3, YF+1, Z1+1+i, 'mekanism:advanced_energy_cube')
# NE: Mekanism
setblock(X2-1, YF+1, Z1+1, 'mekanism:digital_miner')
# SE: AE2
for dx in range(3):
    for dy in range(3):
        setblock(X2-5+dx, YF+1+dy, Z2-5, 'ae2:controller')

print("=== Base is now Hidden and Stealthy! ===")
