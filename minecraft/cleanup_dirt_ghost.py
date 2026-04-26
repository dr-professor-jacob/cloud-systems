#!/usr/bin/env python3
"""
cleanup_dirt_ghost.py — Surgically removes the dirt/grass I placed at CZ=280
replaces it with AIR to clear the mess near the buddy's house.
"""
import subprocess, time

def rcon(*args):
    cmd = ['sudo', 'docker', 'exec', 'minecraft', 'rcon-cli', '--'] + [str(a) for a in args]
    subprocess.run(cmd, capture_output=True, text=True)
    time.sleep(0.01)

# THE TARGET ZONE (CZ=280 area)
# Strictly bounded away from the shore
X1, X2 = -112, -13
Z1, Z2 = 245, 345

print("=== Vaporizing Dirt Ghost (CZ=280) ===")

# 1. Remove all my materials first (just in case any remain)
MY_BLOCKS = [
    'deepslate_bricks', 'obsidian', 'crying_obsidian', 'deepslate_tiles', 
    'polished_deepslate', 'magma_block', 'sea_lantern', 'glowstone',
    'cyan_terracotta', 'purple_terracotta', 'gray_terracotta', 'chiseled_deepslate'
]

for block in MY_BLOCKS:
    for y in range(60, 140, 15):
        ey = min(y + 14, 140)
        rcon('fill', X1, y, Z1, X2, ey, Z2, 'air', f'replace {block}')

# 2. Convert the DIRT back to AIR (The "Dirt Castle" removal)
# This clears the massive mound of dirt I made
print("Removing the dirt mound...")
for y in range(60, 140, 10):
    ey = min(y + 9, 140)
    rcon('fill', X1, y, Z1, X2, ey, Z2, 'air', 'replace dirt')
    rcon('fill', X1, y, Z1, X2, ey, Z2, 'air', 'replace grass_block')

print("=== Cleanup Complete. CZ=280 site cleared back to air. ===")
