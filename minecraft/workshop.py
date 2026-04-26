#!/usr/bin/env python3
"""
Cathedral Workshop Interior - INLAND ELEVATED
Connected and functional, elevated at Y=75.
"""
import subprocess, time

def rcon(*args):
    cmd = ['sudo', 'docker', 'exec', 'minecraft', 'rcon-cli', '--'] + [str(a) for a in args]
    subprocess.run(cmd, capture_output=True, text=True)
    time.sleep(0.05)

def fill(x1, y1, z1, x2, y2, z2, blk, mode=None):
    args = ['fill', x1, y1, z1, x2, y2, z2, blk]
    if mode: args.append(mode)
    rcon(*args)

def setblock(x, y, z, blk):
    rcon('setblock', x, y, z, blk)

# --- COORDINATES (Inland & Elevated) ---
CX, CZ, YF = -80, 280, 75
YC1 = YF + 15
YC2 = YF + 39
MID_X = CX - 1
MID_Z = CZ

print("=== Clearing interior space ===")
fill(CX-21, YF+1, CZ-17, CX+21, YC2-1, CZ+17, 'air')

print("=== Floors ===")
fill(CX-21, YF, CZ-17, CX+21, YF, CZ+17, 'polished_deepslate')
fill(CX-21, YF, CZ-17, MID_X, YF, MID_Z-1, 'chiseled_deepslate')
fill(MID_X+1, YF, CZ-17, CX+21, YF, MID_Z-1, 'cyan_terracotta')
fill(CX-21, YF, MID_Z+1, MID_X, YF, CZ+17, 'gray_terracotta')
fill(MID_X+1, YF, MID_Z+1, CX+21, YF, CZ+17, 'purple_terracotta')
fill(MID_X-2, YF, MID_Z-2, MID_X+2, YF, MID_Z+2, 'crying_obsidian')
fill(CX-21, YC1, CZ-17, CX+21, YC1, MID_Z-5, 'deepslate_tiles')
fill(CX-9, YC1, CZ-16, CX+7, YC1, MID_Z-7, 'air') # Mezzanine void

print("=== Room Dividers ===")
fill(CX-21, YF+1, MID_Z, CX+21, YC1-1, MID_Z, 'obsidian')
fill(CX-4, YF+1, MID_Z, CX+4, YF+6, MID_Z, 'air')
fill(MID_X, YF+1, CZ-17, MID_X, YC1-1, CZ+17, 'obsidian')
fill(MID_X, YF+1, CZ-11, MID_X, YF+6, CZ-5, 'air')
fill(MID_X, YF+1, CZ+5, MID_X, YF+6, CZ+11, 'air')

print("=== Networks (Ceiling Power / Sub-floor AE2) ===")
fill(CX-19, YC1-1, CZ-11, CX+18, YC1-1, CZ-11, 'mekanism:basic_universal_cable')
fill(CX-19, YF-1, CZ-9, CX+18, YF-1, CZ-9, 'ae2:cable_bus')

print("=== Machine Deployment ===")
# NW Power
setblock(CX-19, YF+1, CZ-14, 'modern_industrialization:bronze_boiler')
setblock(CX-17, YF+1, CZ-14, 'modern_industrialization:bronze_boiler')
setblock(CX-19, YF+1, CZ-12, 'mekanism:advanced_energy_cube')
# NE Mekanism
setblock(CX+10, YF+1, CZ-15, 'mekanism:digital_miner')
setblock(CX+4, YF+1, CZ-13, 'mekanism:enrichment_chamber')
setblock(CX+6, YF+1, CZ-13, 'mekanism:crusher')
# SW MI
setblock(CX-19, YF+1, CZ+3, 'modern_industrialization:electric_macerator')
setblock(CX-17, YF+1, CZ+3, 'modern_industrialization:electric_furnace')
# SE AE2
setblock(CX+10, YF+1, CZ+9, 'ae2:controller')
setblock(CX+9, YF+1, CZ+9, 'ae2:energy_acceptor')
setblock(CX+19, YF+1, CZ+2, 'ae2:drive')

print("=== Loft & Stairs ===")
for i in range(15):
    setblock(CX+16, YF+1+i, CZ-3-i, 'quartz_stairs[facing=north]')
    setblock(CX+16, YF+2+i, CZ-3-i, 'air')

setblock(MID_X, YF+4, MID_Z, 'beacon')
print("=== Workshop Integrated at Elevated Inland Location! ===")
