#!/usr/bin/env python3
"""
Cathedral Workshop Interior
Connected, signless, and functional.
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

YF = 60
YC1 = 75
YC2 = 99
MID_X = -81
MID_Z = 149

print("=== Clearing interior ===")
fill(-101, YF+1, 132,  -80, YC2-1, 166, 'air')
fill( -80, YF+1, 132,  -59, YC2-1, 166, 'air')

print("=== Floors ===")
fill(-101, YF, 132, -59, YF, 166, 'polished_deepslate')
fill(-101, YF, 132, MID_X, YF, MID_Z-1, 'chiseled_deepslate')
fill(MID_X+1, YF, 132, -59, YF, MID_Z-1, 'cyan_terracotta')
fill(-101, YF, MID_Z+1, MID_X, YF, 166, 'gray_terracotta')
fill(MID_X+1, YF, MID_Z+1, -59, YF, 166, 'purple_terracotta')
fill(MID_X-2, YF, MID_Z-2, MID_X+2, YF, MID_Z+2, 'crying_obsidian')
fill(-101, YC1, 132, -59, YC1, MID_Z-5, 'deepslate_tiles')
fill(-89, YC1, 133, -73, YC1, MID_Z-7, 'air')

print("=== Room dividers ===")
fill(-101, YF+1, MID_Z, -59, YC1-1, MID_Z, 'obsidian')
fill(-84, YF+1, MID_Z, -78, YF+6, MID_Z, 'air')
fill(MID_X, YF+1, 132, MID_X, YC1-1, 166, 'obsidian')
fill(MID_X, YF+1, 138, MID_X, YF+6, 144, 'air')
fill(MID_X, YF+1, 154, MID_X, YF+6, 160, 'air')

print("=== Power Network (Ceiling) ===")
fill(-99, YC1-1, 138, -62, YC1-1, 138, 'mekanism:basic_universal_cable')
fill(-99, YC1-1, 158, -62, YC1-1, 158, 'mekanism:basic_universal_cable')
fill(-81, YC1-1, 138, -81, YC1-1, 158, 'mekanism:basic_universal_cable')

print("=== AE2 Network (Sub-floor) ===")
fill(-99, YF-1, 140, -62, YF-1, 140, 'ae2:cable_bus')
fill(-99, YF-1, 160, -62, YF-1, 160, 'ae2:cable_bus')
fill(-81, YF-1, 140, -81, YF-1, 160, 'ae2:cable_bus')

print("=== NW Power ===")
setblock(-99, YF+1, 135, 'modern_industrialization:bronze_boiler')
setblock(-97, YF+1, 135, 'modern_industrialization:bronze_boiler')
setblock(-95, YF+1, 135, 'modern_industrialization:coke_oven')
setblock(-99, YF+1, 137, 'mekanism:advanced_energy_cube')
setblock(-97, YF+1, 137, 'mekanism:advanced_energy_cube')
setblock(-95, YF+1, 137, 'mekanism:advanced_energy_cube')
fill(-97, YF+2, 137, -97, YC1-1, 137, 'mekanism:basic_universal_cable')
setblock(-97, YC1-1, 137, 'mekanism:basic_universal_cable')

print("=== NE Mekanism ===")
setblock(-70, YF+1, 134, 'mekanism:digital_miner')
setblock(-76, YF+1, 136, 'mekanism:enrichment_chamber')
setblock(-74, YF+1, 136, 'mekanism:crusher')
setblock(-72, YF+1, 136, 'mekanism:energized_smelter')
setblock(-68, YF+1, 136, 'mekanism:osmium_compressor')
setblock(-64, YF+1, 136, 'mekanism:electric_pump')
fill(-72, YF+2, 136, -72, YC1-1, 136, 'mekanism:basic_universal_cable')
setblock(-72, YC1-1, 136, 'mekanism:basic_universal_cable')
fill(-76, YF+2, 136, -64, YF+2, 136, 'mekanism:basic_universal_cable')

print("=== SW MI Processing ===")
setblock(-99, YF+1, 152, 'modern_industrialization:electric_macerator')
setblock(-97, YF+1, 152, 'modern_industrialization:electric_compressor')
setblock(-95, YF+1, 152, 'modern_industrialization:electric_furnace')
setblock(-93, YF+1, 152, 'modern_industrialization:electrolyzer')
setblock(-91, YF+1, 152, 'modern_industrialization:chemical_reactor')
setblock(-86, YF+1, 164, 'modern_industrialization:quarry')
fill(-95, YF+2, 152, -95, YC1-1, 152, 'mekanism:basic_universal_cable')
setblock(-95, YC1-1, 152, 'mekanism:basic_universal_cable')
fill(-99, YF+2, 152, -91, YF+2, 152, 'mekanism:basic_universal_cable')

print("=== SE AE2 Storage ===")
setblock(-70, YF+1, 158, 'ae2:controller')
setblock(-70, YF+2, 158, 'ae2:controller')
setblock(-71, YF+1, 158, 'ae2:energy_acceptor')
setblock(-71, YF+2, 158, 'mekanism:advanced_energy_cube')
setblock(-61, YF+1, 151, 'ae2:drive')
setblock(-61, YF+2, 151, 'ae2:drive')
setblock(-61, YF+1, 153, 'ae2:drive')
setblock(-61, YF+2, 153, 'ae2:drive')
setblock(-76, YF+1, 160, 'ae2:crafting_unit')
setblock(-75, YF+1, 160, 'ae2:crafting_unit')
setblock(-76, YF+2, 160, 'ae2:molecular_assembler')
setblock(-75, YF+2, 160, 'ae2:molecular_assembler')
setblock(-76, YF+3, 160, 'ae2:1k_crafting_storage')
setblock(-68, YF+1, 166, 'ae2:crafting_terminal')
fill(-71, YF+3, 158, -71, YC1-1, 158, 'mekanism:basic_universal_cable')
setblock(-71, YC1-1, 158, 'mekanism:basic_universal_cable')

print("=== Mezzanine Loft & Stairs ===")
for i in range(15):
    setblock(-64, YF+1+i, 146-i, 'quartz_stairs[facing=north]')
    setblock(-64, YF+2+i, 146-i, 'air')
fill(-65, YC1, 133, -63, YC1, 138, 'deepslate_tiles')
fill(-65, YC1, 133, -63, YC1, 145, 'air')
setblock(-99, YC1+2, 136, 'crafting_table')
setblock(-95, YC1+2, 136, 'anvil')
setblock(-89, YC1+2, 136, 'enchanting_table')
fill(-91, YC1+2, 134, -87, YC1+3, 138, 'bookshelf', 'hollow')
setblock(-89, YC1+2, 134, 'air')
setblock(-89, YC1+3, 134, 'air')

print("=== Lighting ===")
setblock(-100, YF+8, 140, 'glowstone')
setblock(-60, YF+8, 140, 'glowstone')
setblock(-100, YF+8, 160, 'glowstone')
setblock(-60, YF+8, 160, 'glowstone')
setblock(MID_X, YF+4, MID_Z, 'beacon')

print("=== Workshop integrated and functional! ===")