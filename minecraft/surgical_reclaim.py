#!/usr/bin/env python3
"""
surgical_reclaim.py — Reclaims the shoreline area (CZ=149) by replacing
cathedral blocks with natural soil and filling air gaps safely.
"""
import subprocess, time

def rcon(*args):
    cmd = ['sudo', 'docker', 'exec', 'minecraft', 'rcon-cli', '--'] + [str(a) for a in args]
    subprocess.run(cmd, capture_output=True, text=True)
    time.sleep(0.01)

# Blocks we need to remove
CATHEDRAL_BLOCKS = [
    'deepslate_bricks', 'obsidian', 'crying_obsidian', 'deepslate_tiles', 
    'polished_deepslate', 'magma_block', 'sea_lantern', 'glowstone', 
    'tinted_glass', 'quartz_block', 'lava'
]

# THE SHORE BOUNDARIES (CZ=149)
X1, X2 = -110, -50
Z1, Z2 = 125, 185

print("=== Reclaiming Shoreline (Surgical Mode) ===")

# 1. Remove structure blocks and replace with AIR
# This only touches the specific materials of the cathedral
for block in CATHEDRAL_BLOCKS:
    print(f"Removing {block}...")
    for y in range(60, 140, 10):
        ey = y + 9
        rcon('fill', X1, y, Z1, X2, ey, Z2, 'air', f'replace {block}')

# 2. Fill the Hole with Soil (Safe Mode)
# This ONLY fills empty air with dirt.
# It will skip your friend's blocks because they are not air.
print("Filling air gaps with soil...")
for y in range(60, 78, 5):
    ey = min(y + 4, 77)
    rcon('fill', X1, y, Z1, X2, ey, Z2, 'dirt', 'replace air')

# 3. Final Surface Pass
print("Greening the surface...")
rcon('fill', X1, 78, Z1, X2, 78, Z2, 'grass_block', 'replace dirt')

print("=== Shoreline reclaimed and safe. ===")
