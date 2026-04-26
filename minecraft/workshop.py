#!/usr/bin/env python3
"""
Cathedral Workshop Interior
4 rooms: Power, Mekanism, MI Processing, AE2 Storage
+ mezzanine loft with stairs
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
    nbt = '{front_text:{messages:[\'{"text":"' + text + '"}\',\'{"text":""}\',\'{"text":""}\',\'{"text":""}\']}}'
    rcon('setblock', x, y, z, f'oak_wall_sign[facing={facing}]{nbt}')

def chest(x, y, z, facing='south'):
    setblock(x, y, z, f'chest[facing={facing}]')

def stair(x, y, z, blk, facing, half='bottom'):
    setblock(x, y, z, f'{blk}[facing={facing},half={half}]')

# ── Bounds ────────────────────────────────────────────────────────────────────
# Cathedral interior: X[-101,-59], Z[132,166], Y[60,99]
YF  = 60   # floor
YC1 = 75   # ground ceiling / mezzanine floor
YC2 = 99   # top
MID_X = -81  # N-S divider wall x
MID_Z = 149  # E-W divider wall z

# ── 1. Clear interior completely ──────────────────────────────────────────────
print("=== Clearing interior ===")
fill(-101, YF+1, 132, -59, YC2-1, 166, 'air')

# ── 2. Floors ─────────────────────────────────────────────────────────────────
print("=== Floors ===")
# Ground floor
fill(-101, YF, 132, -59, YF, 166, 'smooth_basalt')
# Room color coding on floor
fill(-101, YF, 132, MID_X+1, YF, MID_Z-1, 'blackstone')        # NW Power
fill(MID_X-1, YF, 132, -59, YF, MID_Z-1, 'end_stone_bricks')   # NE Mekanism
fill(-101, YF, MID_Z+1, MID_X+1, YF, 166, 'purpur_block')      # SW MI
fill(MID_X-1, YF, MID_Z+1, -59, YF, 166, 'quartz_block')       # SE AE2
# Central crossroads
fill(MID_X-1, YF, MID_Z-1, MID_X+1, YF, MID_Z+1, 'amethyst_block')

# Mezzanine floor (north half only, upper level)
fill(-101, YC1, 132, -59, YC1+1, MID_Z-5, 'blackstone')
# Gap above center for double-height feel
fill(-89, YC1, 132, -71, YC1+1, MID_Z-6, 'air')

# ── 3. Room divider walls ─────────────────────────────────────────────────────
print("=== Room walls ===")
# E-W wall (splits north/south rooms)
fill(-101, YF+1, MID_Z, -59, YC1-1, MID_Z, 'quartz_block')
# Doorway in E-W wall (center)
fill(-83, YF+1, MID_Z, -79, YF+4, MID_Z, 'air')

# N-S wall (splits west/east rooms)
fill(MID_X, YF+1, 132, MID_X, YC1-1, 166, 'quartz_block')
# Doorway in N-S wall (north half)
fill(MID_X, YF+1, 138, MID_X, YF+4, 142, 'air')
# Doorway in N-S wall (south half)
fill(MID_X, YF+1, 155, MID_X, YF+4, 159, 'air')

# Ground ceiling (separates ground from mezzanine)
fill(-101, YC1, 132, -59, YC1, 166, 'blackstone')
# Open up south half (no mezzanine over south rooms — double height)
fill(-101, YC1, MID_Z+1, -59, YC1, 166, 'air')
# Open center for grandeur
fill(-88, YC1, 135, -72, YC1, MID_Z-2, 'air')

# ── 4. Stairs to mezzanine ────────────────────────────────────────────────────
print("=== Stairs ===")
# SE corner staircase going up (east side, north half)
for i in range(15):
    setblock(-61, YF+1+i, 133+i, 'quartz_stairs[facing=south]')
    setblock(-62, YF+1+i, 133+i, 'quartz_stairs[facing=south]')
    setblock(-61, YF+2+i, 133+i, 'air')
    setblock(-62, YF+2+i, 133+i, 'air')

# Mezzanine railing
fill(-101, YC1+2, MID_Z-5, -59, YC1+2, MID_Z-5, 'quartz_slab')
fill(-101, YC1+2, 132, -101, YC1+2, MID_Z-5, 'quartz_slab')
fill(-59, YC1+2, 132, -59, YC1+2, MID_Z-5, 'quartz_slab')

# ── 5. POWER ROOM (NW) ───────────────────────────────────────────────────────
print("=== Power Room ===")
# Sign
sign(-101, YF+5, 140, 'east', 'POWER ROOM')
# IE machines row
setblock(-99, YF+1, 135, 'immersiveengineering:windmill')
setblock(-99, YF+1, 138, 'immersiveengineering:crusher')
setblock(-99, YF+1, 141, 'immersiveengineering:metal_press')
# MI boiler setup
setblock(-97, YF+1, 144, 'modern_industrialization:coal_coke_oven')
setblock(-95, YF+1, 144, 'modern_industrialization:steam_boiler')
setblock(-93, YF+1, 144, 'modern_industrialization:steam_boiler')
# Energy cubes
setblock(-99, YF+1, 144, 'mekanism:advanced_energy_cube')
setblock(-99, YF+1, 146, 'mekanism:advanced_energy_cube')
# Cables connecting power
fill(-98, YF+1, 144, -93, YF+1, 144, 'modern_industrialization:tin_cable')
fill(-99, YF+1, 135, -99, YF+1, 144, 'mekanism:basic_universal_cable')
# Chests
chest(-97, YF+1, 135, 'south')
chest(-97, YF+1, 136, 'south')
sign(-97, YF+2, 135, 'south', 'Coal/Fuel')
# Lighting
setblock(-91, YC1-1, 136, 'glowstone')
setblock(-91, YC1-1, 145, 'glowstone')
setblock(-100, YC1-1, 136, 'sea_lantern')
setblock(-100, YC1-1, 145, 'sea_lantern')

# ── 6. MEKANISM ROOM (NE) ────────────────────────────────────────────────────
print("=== Mekanism Room ===")
sign(-59, YF+5, 140, 'west', 'MEKANISM')
# Digital miner (pride of place, center north wall)
setblock(-70, YF+1, 134, 'mekanism:digital_miner')
sign(-70, YF+2, 133, 'south', 'Digital Miner')
# Processing machines row
setblock(-77, YF+1, 135, 'mekanism:enrichment_chamber')
setblock(-75, YF+1, 135, 'mekanism:crusher')
setblock(-73, YF+1, 135, 'mekanism:purification_chamber')
setblock(-71, YF+1, 135, 'mekanism:energized_smelter')
setblock(-69, YF+1, 135, 'mekanism:osmium_compressor')
# Signs for machine row
sign(-77, YF+2, 134, 'south', 'Enrichment')
sign(-75, YF+2, 134, 'south', 'Crusher')
sign(-73, YF+2, 134, 'south', 'Purify')
sign(-71, YF+2, 134, 'south', 'Smelter')
# Electric pump
setblock(-65, YF+1, 135, 'mekanism:electric_pump')
setblock(-63, YF+1, 135, 'mekanism:electric_pump')
sign(-65, YF+2, 134, 'south', 'Pumps')
# Cables
fill(-77, YF+1, 136, -63, YF+1, 136, 'mekanism:basic_universal_cable')
# Chests (ore input/output)
chest(-78, YF+1, 138, 'east')
chest(-78, YF+1, 139, 'east')
chest(-78, YF+1, 140, 'east')
sign(-78, YF+2, 138, 'east', 'Ore Input')
sign(-78, YF+2, 140, 'east', 'Output')
# Lighting
setblock(-70, YC1-1, 136, 'glowstone')
setblock(-70, YC1-1, 145, 'sea_lantern')
setblock(-62, YC1-1, 136, 'sea_lantern')

# ── 7. MI PROCESSING ROOM (SW) ───────────────────────────────────────────────
print("=== MI Processing Room ===")
sign(-101, YF+5, 158, 'east', 'MI PROCESSING')
# MI machine line
setblock(-99, YF+1, 152, 'modern_industrialization:steam_macerator')
setblock(-97, YF+1, 152, 'modern_industrialization:steam_compressor')
setblock(-95, YF+1, 152, 'modern_industrialization:steam_furnace')
setblock(-93, YF+1, 152, 'modern_industrialization:steam_mixer')
setblock(-91, YF+1, 152, 'modern_industrialization:steam_extractor')
# Signs
sign(-99, YF+2, 151, 'south', 'Macerator')
sign(-97, YF+2, 151, 'south', 'Compressor')
sign(-95, YF+2, 151, 'south', 'Furnace')
sign(-93, YF+2, 151, 'south', 'Mixer')
# Electric tier machines (second row)
setblock(-99, YF+1, 155, 'modern_industrialization:electric_macerator')
setblock(-97, YF+1, 155, 'modern_industrialization:electric_compressor')
setblock(-95, YF+1, 155, 'modern_industrialization:electric_furnace')
setblock(-93, YF+1, 155, 'modern_industrialization:electrolyzer')
setblock(-91, YF+1, 155, 'modern_industrialization:chemical_reactor')
sign(-99, YF+2, 156, 'north', 'E-Macerator')
sign(-95, YF+2, 156, 'north', 'E-Furnace')
sign(-93, YF+2, 156, 'north', 'Electrolyzer')
# Fluid pipes connecting steam machines to boiler (via wall gap)
fill(-99, YF+1, 153, -91, YF+1, 153, 'modern_industrialization:fluid_pipe')
fill(-88, YF+1, 144, -88, YF+1, 153, 'modern_industrialization:fluid_pipe')
# Item pipes output to chests
fill(-99, YF+1, 151, -91, YF+1, 151, 'modern_industrialization:item_pipe')
# Quarry
setblock(-86, YF+1, 160, 'modern_industrialization:quarry')
sign(-86, YF+2, 161, 'north', 'Quarry')
# Output chests
chest(-84, YF+1, 160, 'south')
chest(-84, YF+1, 161, 'south')
chest(-84, YF+1, 162, 'south')
sign(-84, YF+2, 160, 'south', 'Quarry Output')
# Lighting
setblock(-91, YF+12, 152, 'glowstone')
setblock(-91, YF+12, 160, 'sea_lantern')
setblock(-100, YF+12, 160, 'glowstone')

# ── 8. AE2 STORAGE ROOM (SE) ─────────────────────────────────────────────────
print("=== AE2 Storage Room ===")
sign(-59, YF+5, 158, 'west', 'AE2 STORAGE')
# ME Controller (center of room)
setblock(-70, YF+1, 158, 'ae2:controller')
setblock(-70, YF+2, 158, 'ae2:controller')
setblock(-70, YF+3, 158, 'ae2:controller')
setblock(-69, YF+1, 158, 'ae2:controller')
setblock(-71, YF+1, 158, 'ae2:controller')
sign(-70, YF+4, 158, 'south', 'ME Controller')
# ME Drives wall
setblock(-62, YF+1, 151, 'ae2:drive')
setblock(-62, YF+2, 151, 'ae2:drive')
setblock(-62, YF+3, 151, 'ae2:drive')
setblock(-62, YF+1, 153, 'ae2:drive')
setblock(-62, YF+2, 153, 'ae2:drive')
setblock(-62, YF+3, 153, 'ae2:drive')
setblock(-62, YF+1, 155, 'ae2:drive')
setblock(-62, YF+2, 155, 'ae2:drive')
sign(-62, YF+4, 152, 'west', 'ME Drives')
# Crafting CPU
setblock(-75, YF+1, 160, 'ae2:crafting_unit')
setblock(-75, YF+2, 160, 'ae2:crafting_unit')
setblock(-74, YF+1, 160, 'ae2:crafting_unit')
setblock(-74, YF+2, 160, 'ae2:crafting_unit')
setblock(-75, YF+1, 161, 'ae2:crafting_unit')
setblock(-74, YF+1, 161, 'ae2:crafting_unit')
setblock(-75, YF+2, 161, 'ae2:molecular_assembler')
setblock(-74, YF+2, 161, 'ae2:molecular_assembler')
setblock(-75, YF+3, 160, 'ae2:crafting_storage_1k')
setblock(-74, YF+3, 160, 'ae2:crafting_storage_1k')
sign(-75, YF+4, 160, 'south', 'Crafting CPU')
# ME Terminal
setblock(-68, YF+1, 165, 'ae2:crafting_terminal')
setblock(-70, YF+1, 165, 'ae2:terminal')
sign(-69, YF+2, 165, 'north', 'Terminals')
# Pattern provider
setblock(-66, YF+1, 162, 'ae2:pattern_provider')
setblock(-66, YF+2, 162, 'ae2:pattern_provider')
# Fluix cables connecting everything
fill(-70, YF+1, 151, -70, YF+1, 165, 'ae2:fluix_glass_cable')
fill(-70, YF+1, 158, -62, YF+1, 158, 'ae2:fluix_glass_cable')
fill(-75, YF+1, 158, -70, YF+1, 158, 'ae2:fluix_glass_cable')
fill(-66, YF+1, 158, -66, YF+1, 162, 'ae2:fluix_glass_cable')
# Lighting
setblock(-68, YF+12, 158, 'sea_lantern')
setblock(-68, YF+12, 163, 'glowstone')
setblock(-62, YF+12, 158, 'sea_lantern')

# ── 9. MEZZANINE LOFT ────────────────────────────────────────────────────────
print("=== Mezzanine loft ===")
sign(-100, YC1+3, 135, 'east', 'LOFT')
# Crafting tables + anvil
setblock(-98, YC1+2, 135, 'crafting_table')
setblock(-96, YC1+2, 135, 'crafting_table')
setblock(-94, YC1+2, 135, 'anvil')
setblock(-92, YC1+2, 135, 'smithing_table')
sign(-94, YC1+3, 135, 'south', 'Anvil')
# Enchanting setup
setblock(-88, YC1+2, 135, 'enchanting_table')
fill(-90, YC1+2, 133, -86, YC1+2, 137, 'bookshelf')
fill(-90, YC1+3, 133, -86, YC1+3, 137, 'bookshelf')
setblock(-90, YC1+2, 133, 'air')
setblock(-86, YC1+2, 133, 'air')
sign(-88, YC1+3, 135, 'south', 'Enchanting')
# Storage chests along loft wall
for cx in range(-101, -84, 2):
    chest(cx, YC1+2, 143, 'south')
sign(-101, YC1+3, 143, 'east', 'Bulk Storage')
# Loft lighting
for lx in range(-100, -63, 8):
    setblock(lx, YC1+5, 137, 'glowstone')

# ── 10. CENTRAL CROSSROADS ───────────────────────────────────────────────────
print("=== Central hall ===")
# Decorative center pillar base
fill(MID_X-1, YF+1, MID_Z-1, MID_X+1, YF+3, MID_Z+1, 'amethyst_block')
setblock(MID_X, YF+4, MID_Z, 'beacon')
# Beacon base
fill(MID_X-2, YF, MID_Z-2, MID_X+2, YF, MID_Z+2, 'iron_block')
setblock(MID_X, YF, MID_Z, 'amethyst_block')

print("=== Workshop complete! ===")
print("Rooms:")
print("  NW: Power Room    (-101 to -82, Z 132-149)")
print("  NE: Mekanism      (-82 to -59,  Z 132-149)")
print("  SW: MI Processing (-101 to -82, Z 149-168)")
print("  SE: AE2 Storage   (-82 to -59,  Z 149-168)")
print("  Loft: Mezzanine above north rooms")
print("  Stairs: NE corner going up")
print("Entrance from cathedral east wall at X=-57, Z=149")
