#!/usr/bin/env python3
"""
mod_shop.py — Simplified Stealth Workshop v6
Buries the entire structure for stealth.
Automates Ore -> Ingot with minimal footprint.
Height trimmed to Y=77.
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
X1, X2 = CX - 8, CX + 8
Z1, Z2 = CZ - 8, CZ + 8
Y_WALL_TOP = YF + 4 # 69
Y_HILL_TOP = 77

print(f"=== Building Simplified Stealth Workshop (Trimmed to Y:{Y_HILL_TOP}) at {CX}, {CZ} ===")

# 1. CLEAR EXCESS TERRAIN (Trim the high hill down to 77)
# Wipe anything above 77 back to air
print("--- Trimming excess hill height ---")
safe_fill(X1-15, Y_HILL_TOP + 1, Z1-15, X2+15, 100, Z2+15, 'air')

# 2. CONSTRUCT INTERIOR
safe_fill(X1, YF, Z1, X2, YF, Z2, 'polished_deepslate')
safe_fill(X1, YF+1, Z1, X2, Y_WALL_TOP, Z1, 'deepslate_bricks')
safe_fill(X1, YF+1, Z2, X2, Y_WALL_TOP, Z2, 'deepslate_bricks')
safe_fill(X1, YF+1, Z1, X1, Y_WALL_TOP, Z2, 'deepslate_bricks')
safe_fill(X2, YF+1, Z1, X2, Y_WALL_TOP, Z2, 'deepslate_bricks')
safe_fill(X1, Y_WALL_TOP+1, Z1, X2, Y_WALL_TOP+1, Z2, 'deepslate_tiles')

# 3. BURY FOR STEALTH (Flush with Y=77)
print("--- Burying structure to Y=77 ---")
# Surround with dirt
safe_fill(X1-5, 60, Z1-5, X2+5, Y_HILL_TOP-1, Z1-1, 'dirt', 'replace air')
safe_fill(X1-5, 60, Z2+1, X2+5, Y_HILL_TOP-1, Z2+10, 'dirt', 'replace air')
safe_fill(X1-5, 60, Z1-5, X1-1, Y_HILL_TOP-1, Z2+5, 'dirt', 'replace air')
safe_fill(X2+1, 60, Z1-5, X2+5, Y_HILL_TOP-1, Z2+5, 'dirt', 'replace air')
# Cover roof up to 76
safe_fill(X1-5, Y_WALL_TOP+2, Z1-5, X2+5, Y_HILL_TOP-1, Z2+5, 'dirt', 'replace air')
# Grass cap exactly at 77
safe_fill(X1-10, Y_HILL_TOP, Z1-10, X2+10, Y_HILL_TOP, Z2+10, 'grass_block', 'replace air')
safe_fill(X1-10, Y_HILL_TOP, Z1-10, X2+10, Y_HILL_TOP, Z2+10, 'grass_block', 'replace dirt')

# 4. ORE AUTOMATION LINE
print("--- Deploying Ore-to-Ingot Line ---")
setblock(X1+1, YF+1, Z1+1, 'modern_industrialization:bronze_boiler')
setblock(X1+1, YF+1, Z1+2, 'modern_industrialization:bronze_boiler')
setblock(X1+3, YF+1, Z1+1, 'mekanism:advanced_energy_cube')
setblock(X1+3, YF+1, Z1+2, 'mekanism:advanced_energy_cube')
setblock(X2-2, YF+1, Z1+1, 'mekanism:digital_miner')
setblock(CX-2, YF+1, Z1+2, 'mekanism:crusher')
setblock(CX,   YF+1, Z1+2, 'mekanism:enrichment_chamber')
setblock(CX+2, YF+1, Z1+2, 'mekanism:energized_smelter')
setblock(CX, YF+1, CZ, 'chest')
setblock(CX, YF+1, Z2, 'crafting_table')
setblock(CX-1, YF+1, Z2, 'furnace')
setblock(CX+1, YF+1, Z2, 'furnace')
setblock(CX, Y_WALL_TOP, CZ, 'glowstone')

print("=== Trimmed Stealth Base Complete! ===")
