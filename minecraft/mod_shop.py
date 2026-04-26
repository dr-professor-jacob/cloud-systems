#!/usr/bin/env python3
"""
mod_shop.py — Expanded Mod-Ready Workshop v2
X: 1285-1305, Z: 1890-1910, Y: 65
Wall-mounted essentials with wiring sub-floor.
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

print(f"=== Constructing Wall-Integrated Workshop at {CX}, {CZ} ===")

# 1. Clear Volume
safe_fill(X1-5, Y_SUB, Z1-5, X2+5, Y_WALL_TOP+5, Z2+5, 'air')

# 2. Sub-floor (Hollow basement for wiring)
safe_fill(X1, Y_SUB, Z1, X2, YF-1, Z2, 'deepslate_bricks', 'hollow')

# 3. Main Floor (Solid)
safe_fill(X1, YF, Z1, X2, YF, Z2, 'polished_deepslate')

# 4. Access Hatches to Sub-floor
for ox, oz in [(-9,-9), (9,-9), (-9,9), (9,9)]:
    setblock(CX+ox, YF, CZ+oz, 'oak_trapdoor')

# 5. Walls
safe_fill(X1, YF+1, Z1, X2, Y_WALL_TOP, Z1, 'deepslate_bricks')
safe_fill(X1, YF+1, Z2, X2, Y_WALL_TOP, Z2, 'deepslate_bricks')
safe_fill(X1, YF+1, Z1, X1, Y_WALL_TOP, Z2, 'deepslate_bricks')
safe_fill(X2, YF+1, Z1, X2, Y_WALL_TOP, Z2, 'deepslate_bricks')

# 6. Wall-Integrated Essentials (Inside the north/south walls)
# Replacing parts of the Deepslate Brick wall with useful blocks at Y=66
# South wall essentials (at Z2)
setblock(CX, YF+1, Z2, 'crafting_table')
for ox in [-1, 1]: setblock(CX+ox, YF+1, Z2, 'furnace')
for ox in [-3, -2, 2, 3]: setblock(CX+ox, YF+1, Z2, 'chest')

# 7. Windows
safe_fill(X1, YF+2, CZ-4, X1, YF+4, CZ+4, 'glass_pane')
safe_fill(X2, YF+2, CZ-4, X2, YF+4, CZ+4, 'glass_pane')

# 8. North Entrance
fill(CX-2, YF+1, Z1, CX+2, YF+3, Z1, 'air')

# 9. Roof & Lighting
safe_fill(X1, Y_WALL_TOP+1, Z1, X2, Y_WALL_TOP+1, Z2, 'deepslate_tiles')
for lx in range(X1+3, X2, 6):
    for lz in range(Z1+3, Z2, 6):
        setblock(lx, Y_WALL_TOP, lz, 'glowstone')

# 10. Mod Machine Placement (Un-wired)
# NW: Power
setblock(X1+2, YF+1, Z1+2, 'modern_industrialization:bronze_boiler')
setblock(X1+2, YF+1, Z1+4, 'mekanism:advanced_energy_cube')
# NE: Mekanism
setblock(X2-2, YF+1, Z1+2, 'mekanism:digital_miner')
setblock(X2-2, YF+1, Z1+5, 'mekanism:enrichment_chamber')
# SW: MI
setblock(X1+2, YF+1, Z2-2, 'modern_industrialization:electric_macerator')
# SE: AE2
setblock(X2-4, YF+1, Z2-4, 'ae2:controller')
setblock(X2-5, YF+1, Z2-4, 'ae2:energy_acceptor')
setblock(X2-2, YF+1, Z2-2, 'ae2:drive')

print("=== Mod Workshop Ready (Wall-Integrated)! ===")
