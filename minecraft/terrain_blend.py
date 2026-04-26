#!/usr/bin/env python3
"""
terrain_blend.py — The "Void Crater" Protocol
Blends the recessed cathedral into the natural terrain with sci-fi flair.
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

# Center and Bounds
CX, CZ, YF = -80, 149, 60
X1, X2 = -103, -57
Z1, Z2 = 130, 168

print("=== Initiating Void Crater Protocol ===")

# 1. Slope the "Recessed Cube" Walls
# We create a 20-block wide transition zone to smooth out the vertical walls
print("--- Naturalizing cliff edges ---")
for i in range(1, 21):
    # Transition blocks get higher as we move away from the cathedral
    # At i=1 (closest), Y is slightly above floor. At i=20, it reaches top terrain.
    # We use 'replace air' to fill gaps and 'replace water' to stop flooding
    h = YF + (i // 2) 
    
    # North slope
    fill(X1-i, YF-1, Z1-i, X2+i, h, Z1-i, 'deepslate', 'replace air')
    # South slope
    fill(X1-i, YF-1, Z2+i, X2+i, h, Z2+i, 'deepslate', 'replace air')
    # West slope
    fill(X1-i, YF-1, Z1-i, X1-i, h, Z2+i, 'deepslate', 'replace air')
    # East slope
    fill(X2+i, YF-1, Z1-i, X2+i, h, Z2+i, 'deepslate', 'replace air')

# 2. Add Corrupted Surface Blending
print("--- Spreading Void Corruption ---")
for i in range(1, 25):
    # Randomly scatter corruption blocks on the new slopes
    for _ in range(10):
        rx = random.choice([X1-i, X2+i, random.randint(X1-i, X2+i)])
        rz = random.choice([Z1-i, Z2+i, random.randint(Z1-i, Z2+i)])
        block = random.choice(['crying_obsidian', 'tuff', 'cobbled_deepslate', 'magma_block'])
        # Place on the surface
        rcon('execute', 'at', '@a', 'run', 'fill', rx, YF, rz, rx, YF+10, rz, block, 'replace air')

# 3. Floating Void Crystals (The "Cooler" Exterior)
print("--- Spawning Floating Crystals ---")
for _ in range(8):
    vx = random.randint(X1-25, X2+25)
    vz = random.randint(Z1-25, Z2+25)
    # Don't spawn inside the cathedral
    if not (X1 <= vx <= X2 and Z1 <= vz <= Z2):
        vy = random.randint(YF+10, YF+30)
        # 3x3x3 diamond shapes
        fill(vx, vy, vz, vx, vy, vz, 'amethyst_block')
        fill(vx-1, vy, vz, vx+1, vy, vz, 'amethyst_block')
        fill(vx, vy-1, vz, vx, vy+1, vz, 'amethyst_block')
        fill(vx, vy, vz-1, vx, vy, vz+1, 'amethyst_block')
        rcon('setblock', vx, vy, vz, 'sea_lantern')

# 4. The Void Bridge (Floating shards)
print("--- Reconstructing the Void Bridge ---")
fill(X2+1, YF, CZ-4, X2+30, YF+20, CZ+4, 'air') # Clear the path
for i in range(1, 7):
    bx = X2 + (i * 5)
    # Floating platform
    fill(bx-2, YF-1, CZ-2, bx+2, YF-1, CZ+2, 'crying_obsidian')
    # Glowing core
    rcon('setblock', bx, YF-1, CZ, 'beacon')
    fill(bx, YF-2, CZ, bx, YF-2, CZ, 'iron_block')

print("=== Void Crater Complete ===")
