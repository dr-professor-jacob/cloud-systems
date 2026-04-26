#!/usr/bin/env python3
"""
terrain_blend.py — Gap Fixer & Plateau Sealer
Ensures no air gaps between the cathedral and the earthen plateau.
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

print("=== Sealing Air Gaps & Leveling Plateau ===")

# 1. Fill the "One Block Gap" around the perimeter
# We'll fill a 2-block wide ring around the building at YF-1 and YF
print("--- Sealing perimeter gaps ---")
# Fill soil up to the building walls (X1, X2, Z1, Z2)
# We use 'replace air' so we don't overwrite the building itself
fill(X1-5, YF-1, Z1-5, X2+5, YF-1, Z2+5, 'dirt', 'replace air')
fill(X1-1, YF, Z1-1, X2+1, YF, Z2+1, 'grass_block', 'replace air')

# 2. Leveling the Earthen Plateau
print("--- Raising terrain for a flush fit ---")
for y in range(60, YF):
    # Fill a wider area to ensure the plateau feels substantial
    fill(X1-20, y, Z1-20, X2+20, y, Z2+20, 'dirt', 'keep')

# 3. Smoothing the transition to natural terrain
print("--- Naturalizing slopes ---")
for i in range(1, 10):
    dist = 20 + i
    h = YF - i
    if h < 62: h = 62 # Don't go below sea level
    # Create steps/slopes of dirt
    fill(X1-dist, h, Z1-dist, X2+dist, h, Z2+dist, 'dirt', 'keep')

# 4. Final Surface Pass
fill(X1-20, YF-1, Z1-20, X2+20, YF-1, Z2+25, 'grass_block', 'replace dirt')

print("=== Gaps sealed and plateau leveled! ===")
