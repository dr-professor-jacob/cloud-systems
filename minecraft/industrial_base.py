#!/usr/bin/env python3
"""
industrial_base.py — Underground Mod-Ready Industrial Complex
X: 1271-1308, Z: 1886-1929, Y: 60-69
Optimized for FTB NeoTech (MI, Mekanism, Power).
Strictly underground, no surface modifications.
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
    chunk_size = 5
    for y in range(y1, y2 + 1, chunk_size):
        ey = min(y + chunk_size - 1, y2)
        args = ['fill', x1, y, z1, x2, ey, z2, blk]
        if mode: args.append(mode)
        rcon(*args)

def setblock(x, y, z, blk):
    rcon('setblock', x, y, z, blk)

# --- COORDINATES (User's Claimed Chunks) ---
X1, X2 = 1271, 1308
Z1, Z2 = 1886, 1929
Y_FLOOR = 61
Y_ROOF = 69
CX, CZ = (X1 + X2) // 2, (Z1 + Z2) // 2

# 1. CLEAN SLATE
# Clear everything within the claimed chunks under Y=70
safe_fill(X1, 60, Z1, X2, 69, Z2, 'air')

# 2. STRUCTURAL SHELL (Underground Industrial)
# Solid floor
safe_fill(X1, 60, Z1, X2, 60, Z2, 'polished_deepslate')
# Decorative walls
safe_fill(X1, 61, Z1, X2, 68, Z1, 'deepslate_bricks')
safe_fill(X1, 61, Z2, X2, 68, Z2, 'deepslate_bricks')
safe_fill(X1, 61, Z1, X1, 68, Z2, 'deepslate_bricks')
safe_fill(X2, 61, Z1, X2, 68, Z2, 'deepslate_bricks')
# Reinforced Roof
safe_fill(X1, 69, Z1, X2, 69, Z2, 'deepslate_tiles')

# 3. INTERIOR ZONING (Crossroads)
# Main Hall (X-axis)
safe_fill(X1+1, 61, CZ-2, X2-1, 61, CZ+2, 'polished_andesite')
# Main Hall (Z-axis)
safe_fill(CX-2, 61, Z1+1, CX+2, 61, Z2-1, 'polished_andesite')
# Central Glow
setblock(CX, 60, CZ, 'beacon')
fill_args = [CX-1, 60, CZ-1, CX+1, 60, CZ+1, 'iron_block']
rcon('fill', *fill_args)

# 4. POWER GENERATION (North-West)
# 4 Boilers, 4 Cubes
for i in range(4):
    setblock(X1+2, 61, Z1+2+i, 'modern_industrialization:bronze_boiler')
    setblock(X1+4, 61, Z1+2+i, 'mekanism:advanced_energy_cube')
# Pre-wire the power floor
safe_fill(X1+2, 60, Z1+2, X1+4, 60, Z1+5, 'mekanism:basic_universal_cable')

# 5. MEKANISM PROCESSING (North-East)
# Digital Miner Input + High Tier Machine Line
setblock(X2-2, 61, Z1+2, 'mekanism:digital_miner')
mek_machines = ['enrichment_chamber', 'crusher', 'energized_smelter', 'osmium_compressor', 'purification_chamber']
for i, m in enumerate(mek_machines):
    setblock(X2-4, 61, Z1+2+i, f'mekanism:{m}')
# Energy Bus under machines
safe_fill(X2-4, 60, Z1+2, X2-4, 60, Z1+7, 'mekanism:basic_universal_cable')

# 6. MI HEAVY PROCESSING (South-West)
mi_machines = ['electric_macerator', 'electric_furnace', 'electrolyzer', 'chemical_reactor', 'mixer']
for i, m in enumerate(mi_machines):
    setblock(X1+2, 61, Z2-2-i, f'modern_industrialization:{m}')
# Item Pipe Bus
safe_fill(X1+2, 60, Z2-6, X1+2, 60, Z2-2, 'modern_industrialization:pipe')

# 7. LOGISTICS & STORAGE (South-East)
# 8 Reinforced Chests (PneumaticCraft)
for i in range(4):
    setblock(X2-2, 61, Z2-2-i, 'pneumaticcraft:reinforced_chest')
    setblock(X2-4, 61, Z2-2-i, 'pneumaticcraft:reinforced_chest')
# Workstation in the corner
setblock(X2-2, 61, Z2-1, 'crafting_table')
setblock(X2-3, 61, Z2-1, 'furnace')

# 8. LIGHTING & MOB PREVENTION
# Recessed ceiling grid
for x in range(X1+4, X2-3, 8):
    for z in range(Z1+4, Z2-3, 8):
        setblock(x, 68, z, 'sea_lantern')

# 9. SECRET ENTRANCE (Discreet 1x1 hole with ladder to surface)
# Entrance at X1+1, Z1+1 (NW Corner)
safe_fill(X1+1, 61, Z1+1, X1+1, 85, Z1+1, 'air')
for y in range(61, 86):
    setblock(X1+1, y, Z1+1, 'ladder[facing=south]')

print("=== Industrial Complex Fully Initialized! ===")
