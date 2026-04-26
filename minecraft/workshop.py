#!/usr/bin/env python3
"""
Cathedral Workshop Interior - FAR INLAND HIGH
Connected and functional, elevated at Y=85.
"""
import subprocess, time

def rcon(*args):
    cmd = ['sudo', 'docker', 'exec', 'minecraft', 'rcon-cli', '--'] + [str(a) for a in args]
    subprocess.run(cmd, capture_output=True, text=True)
    time.sleep(0.02)

def safe_fill(x1, y1, z1, x2, y2, z2, blk, mode=None):
    """Chunks large fill commands to stay under Minecraft's 32768 block limit."""
    x1, x2 = min(x1, x2), max(x1, x2)
    y1, y2 = min(y1, y2), max(y1, y2)
    z1, z2 = min(z1, z2), max(z1, z2)
    chunk_size = 6
    for y in range(y1, y2 + 1, chunk_size):
        ey = min(y + chunk_size - 1, y2)
        args = ['fill', x1, y, z1, x2, ey, z2, blk]
        if mode: args.append(mode)
        rcon(*args)

def setblock(x, y, z, blk):
    rcon('setblock', x, y, z, blk)

# --- COORDINATES ---
CX, CZ, YF = -80, 450, 85
YC1 = YF + 15
YC2 = YF + 39
MID_X = CX - 1
MID_Z = CZ

print("=== Clearing interior space (Safe Build) ===")
safe_fill(CX-21, YF+1, CZ-17, CX+21, YC2-1, CZ+17, 'air')

print("=== Floors ===")
safe_fill(CX-21, YF, CZ-17, CX+21, YF, CZ+17, 'polished_deepslate')
safe_fill(CX-21, YF, CZ-17, MID_X, YF, MID_Z-1, 'chiseled_deepslate')
safe_fill(MID_X+1, YF, CZ-17, CX+21, YF, MID_Z-1, 'cyan_terracotta')
safe_fill(CX-21, YF, MID_Z+1, MID_X, YF, CZ+17, 'gray_terracotta')
safe_fill(MID_X+1, YF, MID_Z+1, CX+21, YF, CZ+17, 'purple_terracotta')
safe_fill(MID_X-2, YF, MID_Z-2, MID_X+2, YF, MID_Z+2, 'crying_obsidian')
safe_fill(CX-21, YC1, CZ-17, CX+21, YC1, MID_Z-5, 'deepslate_tiles')

print("=== Networks ===")
safe_fill(CX-19, YC1-1, CZ-11, CX+18, YC1-1, CZ-11, 'mekanism:basic_universal_cable')
safe_fill(CX-19, YF-1, CZ-9, CX+18, YF-1, CZ-9, 'ae2:cable_bus')

print("=== Machines ===")
setblock(CX-19, YF+1, CZ-14, 'modern_industrialization:bronze_boiler')
setblock(CX-17, YF+1, CZ-14, 'modern_industrialization:bronze_boiler')
setblock(CX-19, YF+1, CZ-12, 'mekanism:advanced_energy_cube')
setblock(CX+10, YF+1, CZ-15, 'mekanism:digital_miner')
setblock(CX+4, YF+1, CZ-13, 'mekanism:enrichment_chamber')
setblock(CX+6, YF+1, CZ-13, 'mekanism:crusher')
setblock(CX-19, YF+1, CZ+3, 'modern_industrialization:electric_macerator')
setblock(CX-17, YF+1, CZ+3, 'modern_industrialization:electric_furnace')
setblock(CX+10, YF+1, CZ+9, 'ae2:controller')
setblock(CX+9, YF+1, CZ+9, 'ae2:energy_acceptor')
setblock(CX+19, YF+1, CZ+2, 'ae2:drive')

print("=== Loft & Stairs ===")
for i in range(15):
    setblock(CX+16, YF+1+i, CZ-3-i, 'quartz_stairs[facing=north]')
    setblock(CX+16, YF+2+i, CZ-3-i, 'air')

setblock(MID_X, YF+4, MID_Z, 'beacon')
print("=== Workshop Build Complete! ===")
