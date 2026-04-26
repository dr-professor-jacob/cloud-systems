#!/usr/bin/env python3
"""
terrain_blend.py — Organic Stealth Blending
Smooths the hard edges of the artificial plateau into natural terrain.
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

CX, CZ = 1295, 1900
Y_PLATEAU = 71
RADIUS = 25

print("=== Smoothing Terrain Naturally ===")

# 1. Sculpt Slopes
for i in range(1, 15):
    dist = RADIUS + i
    drop = i // 2 + random.randint(0, 1)
    h = Y_PLATEAU - drop
    if h < 63: h = 63
    
    # Ring fill at calculated height
    fill(CX-dist, h, CZ-dist, CX+dist, h, CZ-dist+1, 'dirt', 'keep')
    fill(CX-dist, h, CZ+dist-1, CX+dist, h, CZ+dist, 'dirt', 'keep')
    fill(CX-dist, h, CZ-dist, CX-dist+1, h, CZ+dist, 'dirt', 'keep')
    fill(CX+dist-1, h, CZ-dist, CX+dist, h, CZ+dist, 'dirt', 'keep')

# 2. Rounded Corners
for ox, oz in [(-RADIUS, -RADIUS), (RADIUS, -RADIUS), (-RADIUS, RADIUS), (RADIUS, RADIUS)]:
    fill(CX+ox-3, Y_PLATEAU, CZ+oz-3, CX+ox+3, Y_PLATEAU+5, CZ+oz+3, 'air')
    fill(CX+ox-3, Y_PLATEAU-1, CZ+oz-3, CX+ox+3, Y_PLATEAU-1, CZ+oz+3, 'grass_block', 'replace air')

# 3. Final Grass Pass
fill(CX-45, Y_PLATEAU-10, CZ-45, CX+45, Y_PLATEAU, CZ+45, 'grass_block', 'replace dirt')

print("=== Blending Complete! ===")
