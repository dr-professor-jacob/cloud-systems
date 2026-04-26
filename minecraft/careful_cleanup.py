#!/usr/bin/env python3
"""
careful_cleanup.py
Transforms the cathedral structures into solid dirt mounds and removes all machines.
Strictly confined to the exact bounding boxes of the two cathedrals to ensure no other builds are touched.
"""
import subprocess, time

def rcon(*args):
    cmd = ['sudo', 'docker', 'exec', 'minecraft', 'rcon-cli', '--'] + [str(a) for a in args]
    subprocess.run(cmd, capture_output=True, text=True)
    time.sleep(0.02)

def safe_replace(x1, y1, z1, x2, y2, z2, new_blk, old_blk):
    x1, x2 = min(x1, x2), max(x1, x2)
    y1, y2 = min(y1, y2), max(y1, y2)
    z1, z2 = min(z1, z2), max(z1, z2)
    for y in range(y1, y2 + 1, 5):
        ey = min(y + 4, y2)
        rcon('fill', x1, y, z1, x2, ey, z2, new_blk, 'replace', old_blk)

def safe_fill_air(x1, y1, z1, x2, y2, z2, blk):
    # Only fills air blocks, strictly within the provided bounds
    x1, x2 = min(x1, x2), max(x1, x2)
    y1, y2 = min(y1, y2), max(y1, y2)
    z1, z2 = min(z1, z2), max(z1, z2)
    for y in range(y1, y2 + 1, 5):
        ey = min(y + 4, y2)
        rcon('fill', x1, y, z1, x2, ey, z2, blk, 'replace', 'air')

CATHEDRAL_BLOCKS = [
    'deepslate_bricks', 'obsidian', 'crying_obsidian', 'polished_deepslate',
    'deepslate_tiles', 'magma_block', 'sea_lantern', 'glowstone', 'tinted_glass',
    'quartz_block', 'lava', 'beacon', 'cyan_terracotta', 'purple_terracotta',
    'gray_terracotta', 'chiseled_deepslate', 'mekanism:basic_universal_cable',
    'ae2:cable_bus', 'modern_industrialization:pipe', 'modern_industrialization:bronze_boiler',
    'mekanism:advanced_energy_cube', 'mekanism:digital_miner', 'mekanism:enrichment_chamber',
    'mekanism:crusher', 'modern_industrialization:electric_macerator',
    'modern_industrialization:electric_furnace', 'ae2:controller', 'ae2:energy_acceptor',
    'ae2:drive', 'quartz_stairs', 'iron_block'
]

# Site 1: The Shore Cathedral (CZ=149)
# Bounding box: X=-105 to -55, Z=125 to 170
print("=== Neutralizing Shore Cathedral (CZ=149) ===")
for block in CATHEDRAL_BLOCKS:
    safe_replace(-105, 60, 125, -55, 100, 170, 'dirt', block)
# Fill the hollow inside with dirt up to Y=70, top with grass
safe_fill_air(-105, 60, 125, -55, 69, 170, 'dirt')
safe_fill_air(-105, 70, 125, -55, 70, 170, 'grass_block')

# Site 2: The "Too Close" Cathedral (CZ=280)
# Bounding box: X=-105 to -55, Z=255 to 305
print("=== Neutralizing CZ=280 Cathedral ===")
for block in CATHEDRAL_BLOCKS:
    safe_replace(-105, 60, 255, -55, 110, 305, 'dirt', block)
# Fill the hollow inside with dirt up to Y=70, top with grass
safe_fill_air(-105, 60, 255, -55, 69, 305, 'dirt')
safe_fill_air(-105, 70, 255, -55, 70, 305, 'grass_block')

print("=== Cleanup Complete. Cathedrals are now solid dirt mounds. ===")
