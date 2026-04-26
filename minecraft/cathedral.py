#!/usr/bin/env python3
"""
Sci-Fi Cathedral "Church of the Void" - UPGRADED
"""
import subprocess, time

def rcon(*args):
    cmd = ['sudo', 'docker', 'exec', 'minecraft', 'rcon-cli', '--'] + [str(a) for a in args]
    r = subprocess.run(cmd, capture_output=True, text=True)
    out = r.stdout.strip()
    if out: print(out)
    time.sleep(0.05)

def fill(x1, y1, z1, x2, y2, z2, blk, mode=None):
    args = ['fill', x1, y1, z1, x2, y2, z2, blk]
    if mode: args.append(mode)
    rcon(*args)

def setblock(x, y, z, blk):
    rcon('setblock', x, y, z, blk)

# Coordinates
CX, CZ, YF = -80, 149, 60
HW, HD, HH = 23, 19, 40
X1, X2 = CX - HW, CX + HW
Z1, Z2 = CZ - HD, CZ + HD
Y1, Y2 = YF, YF + HH
TW, TH = 4, 65

print("=== Clearing area ===")
fill(X1-TW-5, YF-3, Z1-TW-10, X2+TW+5, YF+TH+30, Z2+TW+10, 'air')

print("=== Foundation ===")
fill(X1-TW-2, YF-4, Z1-TW-2, X2+TW+2, YF-1, Z2+TW+2, 'obsidian')
fill(X1-TW, YF-3, Z1-TW, X2+TW, YF-1, Z2+TW, 'deepslate_tiles')
fill(X1, YF, Z1, X2, YF, Z2, 'polished_deepslate')
fill(CX-1, YF, Z1+2, CX+1, YF, Z2-2, 'magma_block')
fill(X1+2, YF, CZ-1, X2-2, YF, CZ+1, 'magma_block')
fill(CX-2, YF, CZ-2, CX+2, YF, CZ+2, 'crying_obsidian')

print("=== Main hall walls ===")
fill(X1, YF, Z1, X2, Y2, Z2, 'deepslate_bricks', 'hollow')
fill(X1+1, YF, Z1+1, X2-1, Y2, Z2-1, 'obsidian', 'hollow')
fill(X1+2, YF+1, Z1+2, X2-2, Y2-1, Z2-2, 'air')

fill(X1, YF+10, Z1, X2, YF+10, Z2, 'crying_obsidian', 'hollow')
fill(X1, YF+20, Z1, X2, YF+20, Z2, 'crying_obsidian', 'hollow')
fill(X1, YF+30, Z1, X2, YF+30, Z2, 'crying_obsidian', 'hollow')

print("=== Roof ===")
fill(X1, Y2, Z1, X2, Y2+2, Z2, 'deepslate_tiles')
fill(X1+4, Y2+2, Z1+4, X2-4, Y2+4, Z2-4, 'obsidian')
fill(X1+8, Y2+4, Z1+8, X2-8, Y2+7, Z2-8, 'crying_obsidian')

print("=== Corner towers ===")
towers = [(X1, Z1), (X1, Z2), (X2, Z1), (X2, Z2)]
for tx, tz in towers:
    fill(tx-TW, YF, tz-TW, tx+TW, YF+TH, tz+TW, 'deepslate_bricks', 'hollow')
    fill(tx-TW+1, YF+1, tz-TW+1, tx+TW-1, YF+TH-1, tz+TW-1, 'air')
    fill(tx-TW, YF+TH, tz-TW, tx+TW, YF+TH+5, tz+TW, 'obsidian')
    
    fill(tx-TW, YF+15, tz-TW, tx+TW, YF+15, tz+TW, 'crying_obsidian', 'hollow')
    fill(tx-TW, YF+30, tz-TW, tx+TW, YF+30, tz+TW, 'crying_obsidian', 'hollow')
    fill(tx-TW, YF+45, tz-TW, tx+TW, YF+45, tz+TW, 'magma_block', 'hollow')
    
    setblock(tx, YF+TH-2, tz, 'lava')
    
    for i in range(15):
        s = max(0, TW - i // 3)
        fill(tx-s, YF+TH+5+i, tz-s, tx+s, YF+TH+5+i, tz+s, 'crying_obsidian')

print("=== Windows ===")
window_h_start, window_h_end = YF + 8, YF + 30
for wx in [CX-14, CX-5, CX+5, CX+14]:
    fill(wx-1, window_h_start, Z1, wx+1, window_h_end, Z1, 'tinted_glass')
    fill(wx-1, window_h_start, Z2, wx+1, window_h_end, Z2, 'tinted_glass')
for wz in [CZ-12, CZ, CZ+12]:
    fill(X1, window_h_start, wz-1, X1, window_h_end, wz+1, 'tinted_glass')
for wz in [CZ-12, CZ+12]:
    fill(X2, window_h_start, wz-1, X2, window_h_end, wz+1, 'tinted_glass')

print("=== Central spire ===")
fill(CX-5, Y2+7, CZ-5, CX+5, Y2+40, CZ+5, 'obsidian', 'hollow')
fill(CX-4, Y2+8, CZ-4, CX+4, Y2+39, CZ+4, 'air')
fill(CX-5, Y2+15, CZ-5, CX+5, Y2+15, CZ+5, 'crying_obsidian', 'hollow')
fill(CX-5, Y2+25, CZ-5, CX+5, Y2+25, CZ+5, 'magma_block', 'hollow')
for i in range(20):
    s = max(0, 4 - i // 4)
    fill(CX-s, Y2+40+i, CZ-s, CX+s, Y2+40+i, CZ+s, 'crying_obsidian')
setblock(CX, Y2+61, CZ, 'beacon')

print("=== Exterior Details ===")
for bx in [CX-14, CX, CX+14]:
    fill(bx-2, YF, Z1-10, bx+2, YF+20, Z1, 'deepslate_tiles')
    fill(bx-2, YF, Z2, bx+2, YF+20, Z2+10, 'deepslate_tiles')

print("=== Cathedral complete! ===")