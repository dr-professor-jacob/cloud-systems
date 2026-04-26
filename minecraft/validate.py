#!/usr/bin/env python3
"""
validate.py — reads blocks from the game, fixes anything wrong.
Run on the HOST VM (not inside the container).
Usage: python3 /tmp/validate.py [--fix] [--verbose]
"""
import subprocess, time, sys

FIX     = '--fix'     in sys.argv
VERBOSE = '--verbose' in sys.argv

def rcon(*args):
    cmd = ['sudo', 'docker', 'exec', 'minecraft', 'rcon-cli', '--'] + [str(a) for a in args]
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.stdout.strip()

def check_block(x, y, z, expected_id):
    result = rcon('execute', 'if', 'block', x, y, z, expected_id)
    return 'passed' in result.lower() or result.strip() == '1'

def setblock(x, y, z, blk):
    out = rcon('setblock', x, y, z, blk)
    time.sleep(0.05)
    return out

YF = 60
EXPECTED = {
    (-99, YF+1, 135): 'modern_industrialization:bronze_boiler',
    (-97, YF+1, 135): 'modern_industrialization:bronze_boiler',
    (-95, YF+1, 135): 'modern_industrialization:coke_oven',
    (-99, YF+1, 137): 'mekanism:advanced_energy_cube',
    (-97, YF+1, 137): 'mekanism:advanced_energy_cube',
    (-95, YF+1, 137): 'mekanism:advanced_energy_cube',
    (-70, YF+1, 134): 'mekanism:digital_miner',
    (-76, YF+1, 136): 'mekanism:enrichment_chamber',
    (-74, YF+1, 136): 'mekanism:crusher',
    (-72, YF+1, 136): 'mekanism:energized_smelter',
    (-68, YF+1, 136): 'mekanism:osmium_compressor',
    (-64, YF+1, 136): 'mekanism:electric_pump',
    (-99, YF+1, 152): 'modern_industrialization:electric_macerator',
    (-97, YF+1, 152): 'modern_industrialization:electric_compressor',
    (-95, YF+1, 152): 'modern_industrialization:electric_furnace',
    (-93, YF+1, 152): 'modern_industrialization:electrolyzer',
    (-91, YF+1, 152): 'modern_industrialization:chemical_reactor',
    (-86, YF+1, 164): 'modern_industrialization:quarry',
    (-70, YF+1, 158): 'ae2:controller',
    (-71, YF+1, 158): 'ae2:energy_acceptor',
    (-61, YF+1, 151): 'ae2:drive',
    (-61, YF+1, 153): 'ae2:drive',
    (-76, YF+1, 160): 'ae2:crafting_unit',
    (-75, YF+1, 160): 'ae2:crafting_unit',
    (-81, YF+4, 149): 'beacon',
}

print(f"Checking {len(EXPECTED)} positions  (fix={'ON' if FIX else 'OFF'})\n")
ok = 0
missing = 0
fixed = 0

for (x, y, z), expected in EXPECTED.items():
    match = check_block(x, y, z, expected)
    if match:
        ok += 1
        if VERBOSE: print(f"  OK  {x},{y},{z}  {expected}")
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