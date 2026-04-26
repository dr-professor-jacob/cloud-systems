#!/usr/bin/env python3
"""
mod_shop.py — Expanded Mod-Ready Workshop v3
X: 1285-1305, Z: 1890-1910, Y: 65
Restores the hill (dirt on top) and adds rows of mod machines.
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
Y_SUB = YF - 2
Y_WALL_TOP = YF + 5

print(f"=== Restoring Hill and Building Workshop at {CX}, {CZ} ===")

# 1. Clear Interior ONLY (Protect the hill above Y=72)
safe_fill(X1, Y_SUB, Z1, X2, Y_WALL_TOP, Z2, 'air')

# 2. RESTORE THE DIRT ON TOP (Fixing the "Bunker Buster" mistake)
# Re-filling the hill from the roof (72) up to Y=85
safe_fill(X1-5, Y_WALL_TOP+2, Z1-5, X2+5, 84, Z2+5, 'dirt', 'replace air')
safe_fill(X1-5, 85, Z1-5, X2+5, 85, Z2+5, 'grass_block', 'replace air')

# 3. Sub-floor & Main Floor
safe_fill(X1, Y_SUB, Z1, X2, YF-1, Z2, 'deepslate_bricks', 'hollow')
safe_fill(X1, YF, Z1, X2, YF, Z2, 'polished_deepslate')

# 4. Access Hatches
for ox, oz in [(-9,-9), (9,-9), (-9,9), (9,9)]:
    setblock(CX+ox, YF, CZ+oz, 'oak_trapdoor')

# 5. Walls
safe_fill(X1, YF+1, Z1, X2, Y_WALL_TOP, Z1, 'deepslate_bricks')
safe_fill(X1, YF+1, Z2, X2, Y_WALL_TOP, Z2, 'deepslate_bricks')
safe_fill(X1, YF+1, Z1, X1, Y_WALL_TOP, Z2, 'deepslate_bricks')
safe_fill(X2, YF+1, Z1, X2, Y_WALL_TOP, Z2, 'deepslate_bricks')

# 6. Wall-Integrated Essentials (South wall)
setblock(CX, YF+1, Z2, 'crafting_table')
for ox in [-1, 1]: setblock(CX+ox, YF+1, Z2, 'furnace')
for ox in [-3, -2, 2, 3]: setblock(CX+ox, YF+1, Z2, 'chest')

# 7. Lighting
for lx in range(X1+3, X2, 6):
    for lz in range(Z1+3, Z2, 6):
        setblock(lx, Y_WALL_TOP, lz, 'glowstone')

# 8. THE MOD STUFF (Heavy Deployment)

# NW: POWER GEN
for i in range(4):
    setblock(X1+1, YF+1, Z1+1+i, 'modern_industrialization:bronze_boiler')
    setblock(X1+3, YF+1, Z1+1+i, 'mekanism:advanced_energy_cube')

# NE: MEKANISM
setblock(X2-1, YF+1, Z1+1, 'mekanism:digital_miner')
machines = ['enrichment_chamber', 'crusher', 'energized_smelter', 'osmium_compressor']
for i, m in enumerate(machines):
    setblock(X2-3, YF+1, Z1+1+i, f'mekanism:{m}')

# SW: MI PROCESSING
mi_machines = ['electric_macerator', 'electric_furnace', 'electrolyzer', 'chemical_reactor']
for i, m in enumerate(mi_machines):
    setblock(X1+1, YF+1, Z2-1-i, f'modern_industrialization:{m}')

# SE: AE2 STORAGE
# 3x3 Controller Cluster
for dx in range(3):
    for dy in range(3):
        setblock(X2-5+dx, YF+1+dy, Z2-5, 'ae2:controller')
setblock(X2-6, YF+1, Z2-5, 'ae2:energy_acceptor')
for i in range(6):
    setblock(X2-1, YF+1+i, Z2-1, 'ae2:drive')

print("=== Mod Workshop Restored & Upgraded! ===")
