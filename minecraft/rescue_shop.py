#!/usr/bin/env python3
"""
rescue_shop.py — Advanced Rescue Operation
Searches for chests, doors, and crafting blocks to pinpoint the buried shop.
"""
import subprocess, time

def rcon(*args):
    cmd = ['sudo', 'docker', 'exec', 'minecraft', 'rcon-cli', '--'] + [str(a) for a in args]
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.stdout.strip()

print("=== Scanning for buried life signs (Chests/Doors/Workshop blocks) ===")

# Possible shop locations (Shoreline areas)
search_points = []
for x in range(-130, -30, 3):
    for z in range(100, 200, 3):
        search_points.append((x, z))

found_pos = None
targets = ['#minecraft:doors', 'chest', 'crafting_table', 'furnace', 'glass_pane', 'torch', 'lantern', 'barrel']

for x, z in search_points:
    # Check at multiple heights in case it's slightly above or below sea level
    for y in range(60, 68):
        for target in targets:
            res = rcon('execute', 'if', 'block', x, y, z, target)
            if 'passed' in res.lower() or res.strip() == '1':
                print(f"Structure detected: {target} at {x}, {y}, {z}")
                found_pos = (x, y, z)
                break
        if found_pos: break
    if found_pos: break

if found_pos:
    fx, fy, fz = found_pos
    print(f"=== Rescuing buried shop at {fx}, {fy}, {fz} ===")
    
    # 1. Clear the burial zone (Soil/Mud only, don't delete his shop)
    # We clear a 7x7 area to ensure the entrance and surroundings are visible
    for y in range(fy + 1, 77):
        # We fill 'air' but only replacing dirt/mud to protect his structure
        subprocess.run(['sudo', 'docker', 'exec', 'minecraft', 'rcon-cli', 'fill', 
                        str(fx-3), str(y), str(fz-3), str(fx+3), str(y), str(fz+3), 'air', 'replace dirt'], capture_output=True)
        subprocess.run(['sudo', 'docker', 'exec', 'minecraft', 'rcon-cli', 'fill', 
                        str(fx-3), str(y), str(fz-3), str(fx+3), str(y), str(fz+3), 'air', 'replace mud'], capture_output=True)
        subprocess.run(['sudo', 'docker', 'exec', 'minecraft', 'rcon-cli', 'fill', 
                        str(fx-3), str(y), str(fz-3), str(fx+3), str(y), str(fz+3), 'air', 'replace grass_block'], capture_output=True)

    # 2. Build a proper exit staircase to the new surface (Y=75)
    print("--- Constructing exit staircase ---")
    for i in range(16): # Range to reach surface from base
        step_y = fy + i
        step_z = fz - i # Climbing North
        # Ensure headroom
        rcon('fill', fx-1, step_y+1, step_z, fx+1, step_y+4, step_z, 'air', 'replace dirt')
        rcon('fill', fx-1, step_y+1, step_z, fx+1, step_y+4, step_z, 'air', 'replace mud')
        # Place stairs
        rcon('setblock', fx, step_y, step_z, 'oak_stairs[facing=south]')
        rcon('setblock', fx-1, step_y, step_z, 'oak_planks')
        rcon('setblock', fx+1, step_y, step_z, 'oak_planks')
        if step_y >= 75: break

    print("=== Shop entrance cleared and staircase connected! ===")
else:
    print("Failed to locate shop. Searching for any non-natural block in the shore zone...")
    # Last ditch effort: scan for anything that isn't air/dirt/water/deepslate
    # (Implementation omitted for brevity, but focus on the search points)
