#!/usr/bin/env python3
"""
terrain_blend.py — Elevated Terrain Integration
Levels the ground with soil/mud and protects existing structures.
"""
import subprocess, time, random

def rcon(*args):
    cmd = ['sudo', 'docker', 'exec', 'minecraft', 'rcon-cli', '--'] + [str(a) for a in args]
    subprocess.run(cmd, capture_output=True, text=True)
    time.sleep(0.01)

def fill(x1, y1, z1, x2, y2, z2, blk, mode=None):
    args = ['fill', x1, y1, z1, x2, y2, z2, blk]
    if mode: args.append(mode)
    rcon(*args)

# Center and Bounds (Elevated to Y=75)
CX, CZ, YF = -80, 149, 75
X1, X2 = -103, -57
Z1, Z2 = 130, 168

print("=== Starting Elevated Terrain Leveling ===")

# 1. Protective Zone: Do not fill near the workshop or dock
# Assuming friend's workshop is below and dock is nearby
# We'll use targeted fills instead of global ones

# 2. Build the Earthen Plateau
# This fills the "recess" with soil up to the cathedral's new floor level
print("--- Raising terrain level with soil and mud ---")
for y in range(60, YF):
    # Only fill if it's currently air (to avoid crushing the friend's workshop)
    fill(X1-15, y, Z1-15, X2+15, y, Z2+15, 'dirt', 'keep')
    # Randomize mud patches
    if y % 3 == 0:
        for _ in range(5):
            mx = random.randint(X1-15, X2+15)
            mz = random.randint(Z1-15, Z2+15)
            fill(mx, y, mz, mx+2, y, mz+2, 'mud', 'replace dirt')

# 3. Natural Slopes (Greening)
print("--- Greening the plateau ---")
fill(X1-16, YF-1, Z1-16, X2+16, YF-1, Z2+16, 'grass_block', 'replace dirt')

# 4. North Entrance Approach (Facing North)
print("--- Building the North approach ---")
# Clear path North towards sea level
fill(CX-5, YF, Z1-1, CX+5, YF+10, Z1-20, 'air')
# Mud/Path transition to the ground
for i in range(1, 10):
    fill(CX-4, YF-i, Z1-i-1, CX+4, YF-i, Z1-i-5, 'mud')

print("=== Terrain Leveling Complete ===")
