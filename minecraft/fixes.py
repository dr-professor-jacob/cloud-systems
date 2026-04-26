#!/usr/bin/env python3
"""
fixes.py — terrain clear, entrance rebuild, exterior path
"""
import subprocess, time

def rcon(*args):
    cmd = ['sudo', 'docker', 'exec', 'minecraft', 'rcon-cli', '--'] + [str(a) for a in args]
    subprocess.run(cmd, capture_output=True, text=True)
    time.sleep(0.06)

def fill(x1, y1, z1, x2, y2, z2, blk, mode=None):
    args = ['fill', x1, y1, z1, x2, y2, z2, blk]
    if mode: args.append(mode)
    rcon(*args)

def setblock(x, y, z, blk):
    rcon('setblock', x, y, z, blk)

CX, CZ, YF = -80, 149, 60
X2 = -57
X1 = -103

print("=== Clearing terrain inside cathedral ===")
fill(-101, YF+1, 132, -80, 99, 166, 'air')
fill(-80,  YF+1, 132, -59, 99, 166, 'air')

print("=== Clearing approach area (east side) ===")
fill(X2, YF-5, CZ-15, X2+30, 130, CZ+15, 'air')

print("=== Clearing west side ===")
fill(X1-20, YF-5, CZ-15, X1, 130, CZ+15, 'air')

print("=== Ground plate outside ===")
fill(X2, YF-1, CZ-10, X2+25, YF-1, CZ+10, 'obsidian')
fill(X2, YF,   CZ-10, X2+25, YF,   CZ+10, 'deepslate_tiles')

print("=== Entrance doorway ===")
fill(X2-1, YF, CZ-4, X2+1, YF+14, CZ+4, 'air')
fill(X2-1, YF, CZ-5, X2+1, YF+15, CZ-5, 'obsidian')
fill(X2-1, YF, CZ+5, X2+1, YF+15, CZ+5, 'obsidian')
fill(X2-1, YF+15, CZ-4, X2+1, YF+15, CZ+4, 'obsidian')
setblock(X2, YF+15, CZ, 'crying_obsidian')
setblock(X2+1, YF+2, CZ-6, 'glowstone')
setblock(X2+1, YF+2, CZ+6, 'glowstone')

print("=== Exterior approach steps ===")
for i in range(6):
    fill(X2+2+i, YF-i, CZ-4, X2+2+i, YF-i, CZ+4, 'obsidian')
    fill(X2+2+i, YF-i-1, CZ-5, X2+7+i, YF-i-1, CZ+5, 'deepslate_tiles')

fill(X2+8, YF-6, CZ-6, X2+20, YF-6, CZ+6, 'deepslate_tiles')

print("=== Re-laying interior floor ===")
fill(-101, YF, 132, -59, YF, 166, 'polished_deepslate')
fill(-101, YF, 132, -82, YF, 148, 'chiseled_deepslate')
fill(-80,  YF, 132, -59, YF, 148, 'cyan_terracotta')
fill(-101, YF, 150, -82, YF, 166, 'gray_terracotta')
fill(-80,  YF, 150, -59, YF, 166, 'purple_terracotta')
fill(-82, YF, 148, -80, YF, 150, 'crying_obsidian')

print("=== fixes.py complete ===")