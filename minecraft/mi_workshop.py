#!/usr/bin/env python3
"""
mi_workshop.py — Automated Modern Industrialization Workshop Builder.
Builds a steam & steel factory within strict interior bounds:
X: 1272-1308, Y: 61-67, Z: 1887-1928.
Fills foundation Y: 58-60 with polished_deepslate.
"""
import subprocess, time, sys

PLAYER = "Dr4g0nS14yer"
EXEC = f"execute as {PLAYER} at {PLAYER} run"

def rcon(*args):
    cmd = ['sudo', 'docker', 'exec', 'minecraft', 'rcon-cli', '--'] + [str(a) for a in args]
    # Noisy but necessary for debugging
    # print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    time.sleep(0.05) # Prevent RCON packet dropping
    return result.stdout.strip()

def fill(x1, y1, z1, x2, y2, z2, blk, mode=None):
    args = [EXEC, 'fill', str(x1), str(y1), str(z1), str(x2), str(y2), str(z2), blk]
    if mode: args.append(mode)
    return rcon(*args)

def setblock(x, y, z, blk):
    return rcon(EXEC, 'setblock', str(x), str(y), str(z), blk)

# --- COORDINATES ---
# Interior: 1272-1308 (X), 1887-1928 (Z), 61-67 (Y)
# Footprint for foundation: 1271-1309 (X), 1886-1930 (Z), 58-60 (Y)
IX1, IX2 = 1272, 1308
IZ1, IZ2 = 1887, 1928
IY1, IY2 = 61, 67

FX1, FX2 = 1271, 1309
FZ1, FZ2 = 1886, 1930

print("=== Phase 1: Deep Foundation & Interior Clearing ===")
# 3-block foundation to stop mobs
fill(FX1, 58, FZ1, FX2, 60, FZ2, 'polished_deepslate')
# Clear interior strictly within bounds
fill(IX1, IY1, IZ1, IX2, IY2, IZ2, 'air')

print("=== Phase 2: Steam Infrastructure (Boilers & Water) ===")
# NW Corner for Power (X=1273, Z=1889)
# Infinite Water Source (2x2) in floor
fill(IX1+1, 60, IZ1+1, IX1+2, 60, IZ1+2, 'water')
setblock(IX1+1, 61, IZ1+1, 'modern_industrialization:water_pump')
# Boilers (Bank of 3)
for i in range(3):
    setblock(IX1+1, 61, IZ1+3+(i*2), 'modern_industrialization:bronze_boiler')

# Steam Backbone (Fluid Pipes under floor at Y=60)
fill(IX1+1, 60, IZ1+1, IX1+1, 60, IZ2-5, 'modern_industrialization:fluid_pipe')

print("=== Phase 3: Steel Forge (Coke Oven & Blast Furnace) ===")
# SW Corner for Forge (X=1273, Z=1910)
# Coke Oven (3x3x3) - X:1273-1275, Y:61-63, Z:1910-1912
fill(1273, 61, 1910, 1275, 63, 1912, 'modern_industrialization:coke_oven_bricks', 'hollow')
setblock(1274, 62, 1910, 'modern_industrialization:coke_oven')

# Bronze Blast Furnace (3x3x3) - X:1273-1275, Y:61-63, Z:1915-1917
fill(1273, 61, 1915, 1275, 63, 1917, 'modern_industrialization:fire_clay_bricks', 'hollow')
setblock(1274, 62, 1915, 'modern_industrialization:bronze_blast_furnace')

print("=== Phase 4: Quarry & Ore Processing Line ===")
# North Wall: Quarry (X=1285, Z=1888)
setblock(1285, 61, 1888, 'modern_industrialization:steam_quarry')

# East Wall: Ore Processing Line (X=1306, Z: 1890-1910)
# Steam Macerators feeding Steam Furnaces
for i in range(4):
    z = 1890 + (i*4)
    setblock(1306, 61, z, 'modern_industrialization:bronze_macerator')
    setblock(1306, 61, z+2, 'modern_industrialization:bronze_furnace')
    # Connect steam from main line to these machines (Y=60 pipe cross)
    fill(IX1+1, 60, z, 1306, 60, z, 'modern_industrialization:fluid_pipe')

print("=== Phase 5: Storage & Logistics ===")
# SE Corner: Chest Wall
for z in range(1920, 1928, 2):
    setblock(1307, 61, z, 'pneumaticcraft:reinforced_chest')
    setblock(1307, 62, z, 'pneumaticcraft:reinforced_chest')

# Main Logistics Grid (Item Pipes at Y=60)
fill(IX1+1, 60, 1890, 1306, 60, 1928, 'modern_industrialization:item_pipe')

# Trash Can for junk/creosote (Voiding creosote is critical for Coke Oven)
setblock(1273, 61, 1913, 'modern_industrialization:trash_can')

print("=== Build Complete! ===")
print("NOTE: Manual wrenching of MI pipes is required to set extract/insert directions.")
print("Prime the system with coal in the Fuel Buffer chest (X=1273, Z=1890).")
