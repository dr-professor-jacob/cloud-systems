#!/usr/bin/env python3
"""
rescue_operation.py — Locates the buried shop and builds a safe exit.
"""
import subprocess, time

def rcon(*args):
    cmd = ['sudo', 'docker', 'exec', 'minecraft', 'rcon-cli', '--'] + [str(a) for a in args]
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.stdout.strip()

# Scan area around the plateau edges for non-natural blocks
# Cathedral bounds: X[-103, -57] Z[130, 168]
# Fill bounds: X[-118, -42] Z[115, 183]
print("=== Scanning for buried structures ===")

found_x, found_y, found_z = None, None, None

# Focus on the "shore" side (typically where the dirt fill meets air/water)
# We'll check the North and East perimeters first
for x in range(-120, -40, 4):
    for z in range(110, 190, 4):
        # Check Y=62 (standard water level) for building materials
        res = rcon('execute', 'if', 'block', x, 62, z, '#minecraft:planks')
        if 'passed' in res.lower():
            print(f"Found planks at {x}, 62, {z}")
            found_x, found_y, found_z = x, 62, z
            break
    if found_x: break

if not found_x:
    print("Could not find shop via planks. Scanning for torches/glass...")
    for x in range(-120, -40, 5):
        for z in range(110, 190, 5):
            res = rcon('execute', 'if', 'block', x, 62, z, 'glass')
            if 'passed' in res:
                found_x, found_y, found_z = x, 62, z
                break
        if found_x: break

if found_x:
    print(f"=== Structure detected near {found_x}, {found_y}, {found_z} ===")
    # Build a 3-wide staircase from the detected point up to the new plateau (Y=75)
    print("--- Clearing burial zone and building stairs ---")
    # 1. Clear a vertical shaft to the surface to ensure he's not trapped
    cmd = ['fill', found_x-2, found_y+1, found_z-2, found_x+2, 76, found_z+2, 'air']
    rcon(*cmd)
    
    # 2. Build the staircase (Oak stairs to match the dock/shop vibe)
    for i in range(14): # 75 - 62 = 13 steps
        cur_y = found_y + i
        cur_z = found_z - i # Climbing Northwards
        # Clear headroom
        rcon('fill', found_x-1, cur_y+1, cur_z, found_x+1, cur_y+4, cur_z, 'air')
        # Place stair
        rcon('setblock', found_x, cur_y, cur_z, 'oak_stairs[facing=south]')
        rcon('setblock', found_x-1, cur_y, cur_z, 'oak_planks')
        rcon('setblock', found_x+1, cur_y, cur_z, 'oak_planks')

    print("=== Rescue Mission Complete! ===")
else:
    print("Could not pinpoint shop. Please provide approximate coordinates.")
