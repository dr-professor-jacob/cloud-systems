#!/usr/bin/env python3
"""
tiny_shop.py — Discrete Shop Build
X: 1291-1299, Z: 1894-1907, Y: 65
No chat broadcasts.
"""
import subprocess, time

def rcon(*args):
    cmd = ['sudo', 'docker', 'exec', 'minecraft', 'rcon-cli', '--'] + [str(a) for a in args]
    # Suppress output to keep things quiet
    subprocess.run(cmd, capture_output=True, text=True)
    time.sleep(0.02)

def fill(x1, y1, z1, x2, y2, z2, blk, mode=None):
    args = ['fill', x1, y1, z1, x2, y2, z2, blk]
    if mode: args.append(mode)
    rcon(*args)

def setblock(x, y, z, blk):
    rcon('setblock', x, y, z, blk)

X1, X2 = 1291, 1299
Z1, Z2 = 1894, 1907
YF = 65
Y2 = YF + 4

# Discrete Build sequence
fill(X1, YF, Z1, X2, Y2+2, Z2, 'air') # Clear
fill(X1, YF, Z1, X2, YF, Z2, 'polished_andesite') # Floor
fill(X1, YF+1, Z1, X2, Y2, Z2, 'stone_bricks', 'hollow') # Walls
for x in (X1, X2):
    for z in (Z1, Z2):
        fill(x, YF+1, z, x, Y2, z, 'oak_log') # Corners
fill(X1, Y2+1, Z1, X2, Y2+1, Z2, 'deepslate_tiles') # Roof
fill(X1, YF+2, Z1+3, X1, YF+3, Z2-3, 'glass_pane') # Windows
fill(X2, YF+2, Z1+3, X2, YF+3, Z2-3, 'glass_pane')
door_x = X1 + 4
fill(door_x, YF+1, Z1, door_x, YF+2, Z1, 'air') # Doorway
setblock(X1+2, YF+1, Z2-1, 'crafting_table') # Furniture
setblock(X1+3, YF+1, Z2-1, 'furnace')
setblock(X1+4, YF+1, Z2-1, 'chest')
setblock(X1+5, YF+1, Z2-1, 'chest')
setblock(X1+4, Y2, Z1+7, 'lantern[hanging=true]') # Light
