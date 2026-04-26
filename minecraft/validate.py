#!/usr/bin/env python3
"""
validate.py — reads blocks from the game, fixes anything wrong.
Run on the HOST VM (not inside the container).
Usage: python3 /tmp/validate.py [--fix] [--verbose]
"""
import subprocess, time, sys, re

FIX     = '--fix'     in sys.argv
VERBOSE = '--verbose' in sys.argv

def rcon(*args):
    cmd = ['sudo', 'docker', 'exec', 'minecraft', 'rcon-cli', '--'] + [str(a) for a in args]
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.stdout.strip()

def get_block(x, y, z):
    """Returns the block ID at x,y,z (e.g. 'minecraft:stone')."""
    out = rcon('data', 'get', 'block', x, y, z)
    # output: "The block at -99,61,152 has the following NBT: {id:\"...\",..."
    # simpler: just use 'execute if block' for a yes/no check
    return out

def check_block(x, y, z, expected_id):
    """Returns True if the block at x,y,z matches expected_id."""
    # 'execute if block X Y Z ID' prints "Test passed" on match
    result = rcon('execute', 'if', 'block', x, y, z, expected_id)
    return 'passed' in result.lower() or result.strip() == '1'

def setblock(x, y, z, blk):
    out = rcon('setblock', x, y, z, blk)
    time.sleep(0.05)
    return out

def fill(x1, y1, z1, x2, y2, z2, blk, mode=None):
    args = ['fill', x1, y1, z1, x2, y2, z2, blk]
    if mode: args.append(mode)
    out = rcon(*args)
    time.sleep(0.07)
    return out

# ── Expected blocks ──────────────────────────────────────────────────────────
# Format: (x, y, z): 'mod:block_id'
YF = 60
EXPECTED = {
    # ── Power Room machines ──
    (-99, YF+1, 135): 'modern_industrialization:bronze_boiler',
    (-99, YF+1, 137): 'modern_industrialization:bronze_boiler',
    (-99, YF+1, 139): 'modern_industrialization:coke_oven',
    (-96, YF+1, 135): 'mekanism:advanced_energy_cube',
    (-96, YF+1, 137): 'mekanism:advanced_energy_cube',
    (-91, YF+1, 135): 'immersiveengineering:crusher',

    # ── Mekanism machines ──
    (-70, YF+1, 134): 'mekanism:digital_miner',
    (-78, YF+1, 136): 'mekanism:enrichment_chamber',
    (-76, YF+1, 136): 'mekanism:crusher',
    (-74, YF+1, 136): 'mekanism:purification_chamber',
    (-72, YF+1, 136): 'mekanism:energized_smelter',
    (-68, YF+1, 136): 'mekanism:osmium_compressor',
    (-64, YF+1, 136): 'mekanism:electric_pump',
    (-62, YF+1, 136): 'mekanism:electric_pump',

    # ── MI Processing machines ──
    (-99, YF+1, 152): 'modern_industrialization:bronze_macerator',
    (-97, YF+1, 152): 'modern_industrialization:bronze_compressor',
    (-95, YF+1, 152): 'modern_industrialization:bronze_furnace',
    (-93, YF+1, 152): 'modern_industrialization:bronze_mixer',
    (-99, YF+1, 160): 'modern_industrialization:electric_macerator',
    (-97, YF+1, 160): 'modern_industrialization:electric_compressor',
    (-95, YF+1, 160): 'modern_industrialization:electric_furnace',
    (-93, YF+1, 160): 'modern_industrialization:electrolyzer',
    (-91, YF+1, 160): 'modern_industrialization:chemical_reactor',

    # ── AE2 machines ──
    (-70, YF+1, 158): 'ae2:controller',
    (-70, YF+2, 158): 'ae2:controller',
    (-70, YF+3, 158): 'ae2:controller',
    (-61, YF+1, 151): 'ae2:drive',
    (-61, YF+2, 151): 'ae2:drive',
    (-61, YF+3, 151): 'ae2:drive',
    (-61, YF+1, 153): 'ae2:drive',
    (-61, YF+2, 153): 'ae2:drive',
    (-61, YF+1, 155): 'ae2:drive',
    (-76, YF+1, 160): 'ae2:crafting_unit',
    (-75, YF+1, 160): 'ae2:crafting_unit',

    # ── Floors (spot-check) ──
    (-99, YF, 135): 'blackstone',
    (-70, YF, 136): 'end_stone_bricks',
    (-99, YF, 152): 'purpur_block',
    (-70, YF, 158): 'quartz_block',

    # ── Beacon ──
    (-81, YF+4, 149): 'beacon',
}

# ── Run checks ───────────────────────────────────────────────────────────────
print(f"Checking {len(EXPECTED)} positions  (fix={'ON' if FIX else 'OFF'})\n")

ok = 0
missing = 0
fixed = 0

for (x, y, z), expected in EXPECTED.items():
    match = check_block(x, y, z, expected)
    if match:
        ok += 1
        if VERBOSE:
            print(f"  OK  {x},{y},{z}  {expected}")
    else:
        missing += 1
        status = "MISSING"
        if FIX:
            result = setblock(x, y, z, expected)
            if 'placed' in result.lower() or 'changed' in result.lower():
                fixed += 1
                status = "FIXED"
            else:
                status = f"FAILED ({result[:60]})"
        print(f"  {status:8}  {x},{y},{z}  {expected}")

print(f"\nResults: {ok} OK  |  {missing} missing  |  {fixed} fixed")
if not FIX and missing > 0:
    print("Run with --fix to place missing blocks automatically.")
