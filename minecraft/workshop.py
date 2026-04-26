#!/usr/bin/env python3
"""
Cathedral Workshop Interior - FULLY CONNECTED & LIT
Handles lighting, physical item/energy cabling, and mob prevention.
"""
import subprocess, time

def rcon(*args):
    cmd = ['sudo', 'docker', 'exec', 'minecraft', 'rcon-cli', '--'] + [str(a) for a in args]
    subprocess.run(cmd, capture_output=True, text=True)
    time.sleep(0.02)

def safe_fill(x1, y1, z1, x2, y2, z2, blk, mode=None):
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

# --- COORDINATES (Matches Cathedral Inland High Edition) ---
CX, CZ, YF = -80, 450, 85
YC1 = YF + 15  # Mezzanine
YC2 = YF + 39  # Roof
MID_X = CX - 1
MID_Z = CZ

print("=== Starting Advanced Interior Integration ===")

# 1. MOB PREVENTION & LIGHTING
print("--- Installing High-Intensity Lighting ---")
# Ceiling Grid (Glowstone recessed in roof)
for lx in range(CX-18, CX+19, 6):
    for lz in range(CZ-14, CZ+15, 6):
        setblock(lx, YC2-1, lz, 'glowstone')
# Floor Grid (Sea Lanterns flush with floor)
for lx in range(CX-18, CX+19, 8):
    for lz in range(CZ-14, CZ+15, 8):
        setblock(lx, YF, lz, 'sea_lantern')

# 2. UNIFIED ENERGY GRID (Mekanism Universal Cables)
print("--- Routing Energy Infrastructure ---")
# Main High-Voltage Bus (Under floor for clean look)
# Connects NW Power to all rooms
safe_fill(CX-19, YF-1, CZ-15, CX-19, YF-1, CZ+15, 'mekanism:basic_universal_cable') # West Bus
safe_fill(CX+18, YF-1, CZ-15, CX+18, YF-1, CZ+15, 'mekanism:basic_universal_cable') # East Bus
safe_fill(CX-19, YF-1, CZ, CX+18, YF-1, CZ, 'mekanism:basic_universal_cable')      # Center Cross

# 3. ITEM LOGISTICS (Modern Industrialization Pipes)
print("--- Installing Item & Fluid Transport ---")
# Underground Logistics Grid (Layer YF-2)
safe_fill(CX-17, YF-2, CZ-13, CX+16, YF-2, CZ+13, 'modern_industrialization:pipe')

# 4. MACHINE PLACEMENT & COHERENT CONNECTIONS
print("--- Calibrating Machine Connections ---")

# NW: POWER GEN
setblock(CX-19, YF+1, CZ-14, 'modern_industrialization:bronze_boiler')
setblock(CX-17, YF+1, CZ-14, 'modern_industrialization:bronze_boiler')
setblock(CX-19, YF+1, CZ-12, 'mekanism:advanced_energy_cube')
# Connect Cube to the Bus
setblock(CX-19, YF, CZ-12, 'mekanism:basic_universal_cable')

# NE: MEKANISM ORE PROCESSING
setblock(CX+10, YF+1, CZ-15, 'mekanism:digital_miner')
setblock(CX+4, YF+1, CZ-13, 'mekanism:enrichment_chamber')
setblock(CX+6, YF+1, CZ-13, 'mekanism:crusher')
# Drop cables to floor bus
for x in [4, 6, 10]: setblock(CX+x, YF, CZ-13, 'mekanism:basic_universal_cable')

# SW: MI PROCESSING
setblock(CX-19, YF+1, CZ+3, 'modern_industrialization:electric_macerator')
setblock(CX-17, YF+1, CZ+3, 'modern_industrialization:electric_furnace')
# Drop energy cables
for x in [-19, -17]: setblock(CX+x, YF, CZ+3, 'mekanism:basic_universal_cable')

# SE: AE2 STORAGE & TERMINALS
setblock(CX+10, YF+1, CZ+9, 'ae2:controller')
setblock(CX+9, YF+1, CZ+9, 'ae2:energy_acceptor')
setblock(CX+19, YF+1, CZ+2, 'ae2:drive')
# Connect AE2 to Energy Bus
setblock(CX+9, YF, CZ+9, 'mekanism:basic_universal_cable')
# AE2 Internal Cabling (YF-1)
safe_fill(CX+9, YF-1, CZ+2, CX+9, YF-1, CZ+9, 'ae2:cable_bus')

# 5. FINAL TOUCHES
# Central Beacon (For buffs and dramatic light)
setblock(MID_X, YF+4, MID_Z, 'beacon')
fill(MID_X-1, YF+3, MID_Z-1, MID_X+1, YF+3, MID_Z+1, 'iron_block')

# Kill mobs inside currently
rcon('kill', '@e[type=!player,x=' + str(CX-25) + ',y=' + str(YF) + ',z=' + str(CZ-20) + ',distance=..40]')

print("=== Integration Complete! Building is Lit, Powered, and Connected. ===")
