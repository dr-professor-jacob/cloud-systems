#!/usr/bin/env python3
"""
Cathedral Workshop Interior  v2 — fixed block IDs, signs, staircase
4 rooms: Power (NW), Mekanism (NE), MI Processing (SW), AE2 Storage (SE)
+ mezzanine loft above north rooms
Center: CX=-80 CZ=149 YF=60
Interior X[-101,-59] Z[132,166]
"""
import subprocess, time

def rcon(*args):
    cmd = ['sudo', 'docker', 'exec', 'minecraft', 'rcon-cli', '--'] + [str(a) for a in args]
    r = subprocess.run(cmd, capture_output=True, text=True)
    out = r.stdout.strip()
    if out: print(out)
    time.sleep(0.06)

def fill(x1, y1, z1, x2, y2, z2, blk, mode=None):
    args = ['fill', x1, y1, z1, x2, y2, z2, blk]
    if mode: args.append(mode)
    rcon(*args)

def setblock(x, y, z, blk):
    rcon('setblock', x, y, z, blk)

def sign(x, y, z, facing, text):
    """Wall sign — places a chiseled quartz backing block first so it never floats."""
    backing = {'east': (x-1,y,z), 'west': (x+1,y,z),
               'south': (x,y,z-1), 'north': (x,y,z+1)}
    bx, by, bz = backing[facing]
    setblock(bx, by, bz, 'chiseled_quartz_block')
    nbt = ('{front_text:{messages:[\'{\"text\":\"' + text +
           '\"}\',\'{\"text\":\"\"}\',\'{\"text\":\"\"}\',\'{\"text\":\"\"}\']}}')
    rcon('setblock', x, y, z, f'oak_wall_sign[facing={facing}]{nbt}')

def chest(x, y, z, facing='south'):
    setblock(x, y, z, f'chest[facing={facing}]')

def stair(x, y, z, blk, facing, half='bottom'):
    setblock(x, y, z, f'{blk}[facing={facing},half={half}]')

# ── Coordinate constants ──────────────────────────────────────────────────────
YF   = 60   # ground floor
YC1  = 75   # mezzanine floor / ground-floor ceiling
YC2  = 99   # cathedral roof
MID_X = -81 # N-S wall (splits Power/Mekanism  west/east)
MID_Z = 149 # E-W wall (splits Power/MI  north/south)

# ── 1. Clear interior ─────────────────────────────────────────────────────────
print("=== Clearing interior ===")
# Split into two fills to stay under 32768-block limit
fill(-101, YF+1, 132,  -80, YC2-1, 166, 'air')
fill( -80, YF+1, 132,  -59, YC2-1, 166, 'air')

# ── 2. Floors ─────────────────────────────────────────────────────────────────
print("=== Floors ===")
fill(-101, YF, 132, -59, YF, 166, 'smooth_basalt')
# Room colour coding
fill(-101, YF, 132, MID_X, YF, MID_Z-1, 'blackstone')       # NW Power
fill(MID_X+1, YF, 132, -59, YF, MID_Z-1, 'end_stone_bricks') # NE Mekanism
fill(-101, YF, MID_Z+1, MID_X, YF, 166, 'purpur_block')      # SW MI
fill(MID_X+1, YF, MID_Z+1, -59, YF, 166, 'quartz_block')     # SE AE2
# Central crossroads diamond
fill(MID_X-1, YF, MID_Z-1, MID_X+1, YF, MID_Z+1, 'amethyst_block')
# Mezzanine floor (north half)
fill(-101, YC1, 132, -59, YC1, MID_Z-5, 'blackstone')
# Cut dramatic void-window in mezzanine ceiling center
fill(-89, YC1, 133, -73, YC1, MID_Z-7, 'air')

# ── 3. Room divider walls ─────────────────────────────────────────────────────
print("=== Room dividers ===")
# E-W wall (Z=149) from floor to mezzanine
fill(-101, YF+1, MID_Z, -59, YC1-1, MID_Z, 'quartz_block')
# Central doorway in E-W wall (4 wide, 5 tall)
fill(-83, YF+1, MID_Z, -79, YF+5, MID_Z, 'air')

# N-S wall (X=-81) from floor to mezzanine
fill(MID_X, YF+1, 132, MID_X, YC1-1, 166, 'quartz_block')
# North doorway in N-S wall
fill(MID_X, YF+1, 139, MID_X, YF+5, 143, 'air')
# South doorway in N-S wall
fill(MID_X, YF+1, 155, MID_X, YF+5, 159, 'air')

# ── 4. Staircase (NE room, climbs east→up along Z=136-138) ───────────────────
print("=== Staircase ===")
# 15 steps climbing NORTH (facing=north) from Z=146 down to Z=132
# Each step: i=0 starts at Z=146 Y=61, i=14 ends at Z=132 Y=75
for i in range(15):
    z_step = 146 - i
    y_step = YF + 1 + i
    # 3-wide staircase at X=-63,-64,-65
    for sx in [-65, -64, -63]:
        setblock(sx, y_step, z_step, 'quartz_stairs[facing=north]')
        setblock(sx, y_step+1, z_step, 'air')  # headroom

# Stair landing at mezzanine level
fill(-66, YC1, 133, -62, YC1, 138, 'blackstone')
# Opening in mezzanine floor above stairs
fill(-66, YC1, 133, -62, YC1, 145, 'air')
# Railing along stair opening
fill(-66, YC1+1, 132, -62, YC1+1, 132, 'quartz_slab')
fill(-67, YC1+1, 132, -67, YC1+1, 145, 'quartz_slab')

# Mezzanine perimeter railing
fill(-101, YC1+1, MID_Z-5, -67, YC1+1, MID_Z-5, 'quartz_slab')  # south rail
fill(-101, YC1+1, 132, -101, YC1+1, MID_Z-5, 'quartz_slab')       # west rail
fill(-59,  YC1+1, 132,  -59, YC1+1, MID_Z-5, 'quartz_slab')       # east rail

# ── 5. POWER ROOM — NW ────────────────────────────────────────────────────────
print("=== Power Room (NW) ===")
sign(-101, YF+5, 140, 'east', 'POWER ROOM')

# MI Bronze Boiler row (steam source) — west wall
setblock(-99, YF+1, 135, 'modern_industrialization:bronze_boiler')
setblock(-99, YF+1, 137, 'modern_industrialization:bronze_boiler')
setblock(-99, YF+1, 139, 'modern_industrialization:coke_oven')
sign(-99, YF+3, 134, 'south', 'Boilers')

# Mekanism energy cubes + universal cable bus
setblock(-96, YF+1, 135, 'mekanism:advanced_energy_cube')
setblock(-96, YF+1, 137, 'mekanism:advanced_energy_cube')
setblock(-94, YF+1, 135, 'mekanism:advanced_energy_cube')
sign(-96, YF+3, 134, 'south', 'Energy Store')

# IE Crusher
setblock(-91, YF+1, 135, 'immersiveengineering:crusher')
sign(-91, YF+3, 134, 'south', 'IE Crusher')

# Power cables (Mekanism universal cable)
fill(-99, YF+1, 140, -83, YF+1, 140, 'mekanism:basic_universal_cable')
fill(-96, YF+1, 136, -96, YF+1, 140, 'mekanism:basic_universal_cable')
fill(-91, YF+1, 136, -91, YF+1, 140, 'mekanism:basic_universal_cable')

# Input chests
chest(-97, YF+1, 143, 'south')
chest(-95, YF+1, 143, 'south')
sign(-96, YF+2, 144, 'north', 'Coal / Fuel')

# Lighting
setblock(-92, YC1-1, 136, 'glowstone')
setblock(-100, YC1-1, 136, 'sea_lantern')
setblock(-92, YC1-1, 145, 'sea_lantern')
setblock(-100, YC1-1, 145, 'glowstone')

# ── 6. MEKANISM ROOM — NE ────────────────────────────────────────────────────
print("=== Mekanism Room (NE) ===")
sign(-59, YF+5, 140, 'west', 'MEKANISM')

# Digital Miner — pride of place on north wall
setblock(-70, YF+1, 134, 'mekanism:digital_miner')
sign(-70, YF+3, 133, 'south', 'Digital Miner')

# Processing machine row along north wall (Z=135 facing south, sign faces north)
setblock(-78, YF+1, 136, 'mekanism:enrichment_chamber')
setblock(-76, YF+1, 136, 'mekanism:crusher')
setblock(-74, YF+1, 136, 'mekanism:purification_chamber')
setblock(-72, YF+1, 136, 'mekanism:energized_smelter')
setblock(-68, YF+1, 136, 'mekanism:osmium_compressor')
sign(-78, YF+3, 135, 'south', 'Enrichment')
sign(-76, YF+3, 135, 'south', 'Crusher')
sign(-74, YF+3, 135, 'south', 'Purify')
sign(-72, YF+3, 135, 'south', 'Smelter')
sign(-68, YF+3, 135, 'south', 'Compressor')

# Universal cable bus along machine row
fill(-78, YF+1, 137, -68, YF+1, 137, 'mekanism:basic_universal_cable')

# Electric pumps (east side)
setblock(-64, YF+1, 136, 'mekanism:electric_pump')
setblock(-62, YF+1, 136, 'mekanism:electric_pump')
sign(-63, YF+3, 135, 'south', 'Pumps')

# Input/output chests along divider wall
chest(-80, YF+1, 138, 'east')
chest(-80, YF+1, 140, 'east')
chest(-80, YF+1, 142, 'east')
sign(-80, YF+2, 138, 'east', 'Ore Input')
sign(-80, YF+2, 142, 'east', 'Output')

# Lighting
setblock(-70, YC1-1, 136, 'glowstone')
setblock(-70, YC1-1, 145, 'sea_lantern')
setblock(-62, YC1-1, 136, 'sea_lantern')
setblock(-62, YC1-1, 145, 'glowstone')

# ── 7. MI PROCESSING ROOM — SW ───────────────────────────────────────────────
print("=== MI Processing Room (SW) ===")
sign(-101, YF+5, 158, 'east', 'MI PROCESSING')

# Bronze (steam) machine row — north side of SW room
setblock(-99, YF+1, 152, 'modern_industrialization:bronze_macerator')
setblock(-97, YF+1, 152, 'modern_industrialization:bronze_compressor')
setblock(-95, YF+1, 152, 'modern_industrialization:bronze_furnace')
setblock(-93, YF+1, 152, 'modern_industrialization:bronze_mixer')
sign(-99, YF+3, 153, 'north', 'Macerator')
sign(-97, YF+3, 153, 'north', 'Compressor')
sign(-95, YF+3, 153, 'north', 'Furnace')
sign(-93, YF+3, 153, 'north', 'Mixer')

# Electric (advanced) machine row — south side
setblock(-99, YF+1, 160, 'modern_industrialization:electric_macerator')
setblock(-97, YF+1, 160, 'modern_industrialization:electric_compressor')
setblock(-95, YF+1, 160, 'modern_industrialization:electric_furnace')
setblock(-93, YF+1, 160, 'modern_industrialization:electrolyzer')
setblock(-91, YF+1, 160, 'modern_industrialization:chemical_reactor')
sign(-99, YF+3, 161, 'north', 'E-Macerator')
sign(-97, YF+3, 161, 'north', 'E-Compressor')
sign(-95, YF+3, 161, 'north', 'E-Furnace')
sign(-93, YF+3, 161, 'north', 'Electrolyzer')
sign(-91, YF+3, 161, 'north', 'Chem React')

# MI pipes connecting machines (item + fluid)
fill(-99, YF+1, 153, -91, YF+1, 153, 'modern_industrialization:pipe')  # output row
fill(-99, YF+1, 159, -91, YF+1, 159, 'modern_industrialization:pipe')  # input row
# Vertical pipe run through E-W wall to connect boilers in Power room
fill(-88, YF+1, 149, -88, YF+1, 155, 'modern_industrialization:pipe')

# Quarry
setblock(-86, YF+1, 164, 'modern_industrialization:quarry')
sign(-86, YF+3, 165, 'north', 'Quarry')

# Output chests
chest(-84, YF+1, 162, 'east')
chest(-84, YF+1, 163, 'east')
chest(-84, YF+1, 164, 'east')
sign(-84, YF+2, 165, 'north', 'Quarry Output')

# Lighting
setblock(-95, YF+8, 153, 'glowstone')
setblock(-95, YF+8, 160, 'sea_lantern')
setblock(-100, YF+8, 160, 'glowstone')
setblock(-84, YF+8, 160, 'sea_lantern')

# ── 8. AE2 STORAGE ROOM — SE ─────────────────────────────────────────────────
print("=== AE2 Storage Room (SE) ===")
sign(-59, YF+5, 158, 'west', 'AE2 STORAGE')

# ME Controller cluster (centre of room)
setblock(-70, YF+1, 158, 'ae2:controller')
setblock(-70, YF+2, 158, 'ae2:controller')
setblock(-70, YF+3, 158, 'ae2:controller')
setblock(-69, YF+1, 158, 'ae2:controller')
setblock(-71, YF+1, 158, 'ae2:controller')
setblock(-69, YF+2, 158, 'ae2:controller')
setblock(-71, YF+2, 158, 'ae2:controller')
sign(-70, YF+4, 159, 'north', 'ME Controller')

# ME Drives wall (east wall)
setblock(-61, YF+1, 151, 'ae2:drive')
setblock(-61, YF+2, 151, 'ae2:drive')
setblock(-61, YF+3, 151, 'ae2:drive')
setblock(-61, YF+1, 153, 'ae2:drive')
setblock(-61, YF+2, 153, 'ae2:drive')
setblock(-61, YF+3, 153, 'ae2:drive')
setblock(-61, YF+1, 155, 'ae2:drive')
setblock(-61, YF+2, 155, 'ae2:drive')
setblock(-61, YF+3, 155, 'ae2:drive')
sign(-61, YF+4, 153, 'west', 'ME Drives')

# Crafting CPU multiblock
setblock(-76, YF+1, 160, 'ae2:crafting_unit')
setblock(-76, YF+2, 160, 'ae2:crafting_unit')
setblock(-75, YF+1, 160, 'ae2:crafting_unit')
setblock(-75, YF+2, 160, 'ae2:crafting_unit')
setblock(-76, YF+1, 161, 'ae2:crafting_unit')
setblock(-75, YF+1, 161, 'ae2:crafting_unit')
setblock(-76, YF+2, 161, 'ae2:molecular_assembler')
setblock(-75, YF+2, 161, 'ae2:molecular_assembler')
setblock(-76, YF+3, 160, 'ae2:1k_crafting_storage')
setblock(-75, YF+3, 160, 'ae2:1k_crafting_storage')
sign(-76, YF+4, 162, 'north', 'Crafting CPU')

# Pattern providers
setblock(-66, YF+1, 163, 'ae2:pattern_provider')
setblock(-66, YF+2, 163, 'ae2:pattern_provider')
sign(-66, YF+3, 164, 'north', 'Pattern Prov')

# ME Terminals on south wall
setblock(-68, YF+1, 166, 'ae2:crafting_terminal')
setblock(-70, YF+1, 166, 'ae2:terminal')
sign(-69, YF+2, 165, 'south', 'Terminals')

# AE2 network cable bus (cable_bus is the placeable AE2 cable block)
fill(-70, YF+1, 151, -70, YF+1, 165, 'ae2:cable_bus')
fill(-61, YF+1, 158, -70, YF+1, 158, 'ae2:cable_bus')
fill(-70, YF+1, 158, -76, YF+1, 158, 'ae2:cable_bus')
fill(-66, YF+1, 158, -66, YF+1, 163, 'ae2:cable_bus')

# Lighting
setblock(-68, YF+12, 158, 'sea_lantern')
setblock(-68, YF+12, 163, 'glowstone')
setblock(-61, YF+12, 158, 'sea_lantern')

# ── 9. MEZZANINE LOFT ────────────────────────────────────────────────────────
print("=== Mezzanine loft ===")
sign(-101, YC1+3, 136, 'east', 'LOFT')

# Workbench row
setblock(-99, YC1+2, 136, 'crafting_table')
setblock(-97, YC1+2, 136, 'crafting_table')
setblock(-95, YC1+2, 136, 'anvil')
setblock(-93, YC1+2, 136, 'smithing_table')
sign(-95, YC1+3, 135, 'south', 'Anvil & Smith')

# Enchanting alcove
setblock(-89, YC1+2, 136, 'enchanting_table')
# Bookshelf ring around enchanting table (full coverage = max levels)
fill(-91, YC1+2, 134, -87, YC1+2, 138, 'bookshelf', 'hollow')
fill(-91, YC1+3, 134, -87, YC1+3, 138, 'bookshelf', 'hollow')
setblock(-89, YC1+2, 134, 'air')  # leave gap to walk in
setblock(-89, YC1+3, 134, 'air')
sign(-89, YC1+3, 137, 'north', 'Enchanting')

# Bulk storage chests along south edge of loft
for cx in range(-101, -68, 2):
    chest(cx, YC1+2, 144, 'north')
sign(-101, YC1+3, 144, 'east', 'Bulk Storage')

# Loft lighting
for lx in range(-100, -67, 9):
    setblock(lx, YC1+5, 137, 'glowstone')

# ── 10. CENTRAL CROSSROADS ───────────────────────────────────────────────────
print("=== Central crossroads ===")
# Amethyst pillar base with beacon at top
fill(MID_X-1, YF+1, MID_Z-1, MID_X+1, YF+3, MID_Z+1, 'amethyst_block')
# Beacon pyramid base (iron blocks + beacon on top)
fill(MID_X-2, YF, MID_Z-2, MID_X+2, YF, MID_Z+2, 'iron_block')
setblock(MID_X, YF, MID_Z, 'amethyst_block')  # centre stays amethyst
setblock(MID_X, YF+4, MID_Z, 'beacon')

print("=== Workshop v2 complete! ===")
print("Layout:")
print("  NW Power Room      X[-101,-82]  Z[132,149]")
print("  NE Mekanism Room   X[-80,-59]   Z[132,149]")
print("  SW MI Processing   X[-101,-82]  Z[149,166]")
print("  SE AE2 Storage     X[-80,-59]   Z[149,166]")
print("  Loft (mezzanine)   Y=75, north half")
print("  Stairs: NE corner X[-65,-63] climb north, Z146->132")
