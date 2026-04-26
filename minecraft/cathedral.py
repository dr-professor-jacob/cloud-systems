#!/usr/bin/env python3
"""
Sci-Fi Cathedral "Church of the Void" - INLAND ELEVATED
Elevated to Y=75 at the inland location.
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

# --- COORDINATES (Inland & Elevated) ---
CX, CZ, YF = -80, 280, 75
HW, HD, HH = 23, 19, 40
X1, X2 = CX - HW, CX + HW
Z1, Z2 = CZ - HD, CZ + HD
Y1, Y2 = YF, YF + HH
TW, TH = 4, 65

print(f"=== Building at Elevated Inland Site: {CX}, {YF}, {CZ} ===")

print("=== Clearing upper airspace ===")
fill(X1-TW-5, YF, Z1-TW-10, X2+TW+5, YF+TH+30, Z2+TW+10, 'air')

print("=== Foundation & Soil Leveling ===")
# Massive soil mound
fill(X1-15, YF-15, Z1-15, X2+15, YF-1, Z2+15, 'dirt', 'keep')
fill(X1-TW, YF-1, Z1-TW, X2+TW, YF-1, Z2+TW, 'obsidian')
fill(X1, YF, Z1, X2, YF, Z2, 'polished_deepslate')

print("=== Main hall walls ===")
fill(X1, YF, Z1, X2, Y2, Z2, 'deepslate_bricks', 'hollow')
fill(X1+1, YF, Z1+1, X2-1, Y2, Z2-1, 'obsidian', 'hollow')
fill(X1+2, YF+1, Z1+2, X2-2, Y2-1, Z2-2, 'air')

print("=== Corner towers ===")
towers = [(X1, Z1), (X1, Z2), (X2, Z1), (X2, Z2)]
for tx, tz in towers:
    fill(tx-TW, YF, tz-TW, tx+TW, YF+TH, tz+TW, 'deepslate_bricks', 'hollow')
    fill(tx-TW+1, YF+1, tz-TW+1, tx+TW-1, YF+TH-1, tz+TW-1, 'air')
    fill(tx-TW, YF+TH, tz-TW, tx+TW, YF+TH+5, tz+TW, 'obsidian')
    setblock(tx, YF+TH-2, tz, 'lava')

print("=== North Entrance (Facing North) ===")
fill(CX-4, YF, Z1-1, CX+4, YF+14, Z1+1, 'air')
fill(CX-5, YF, Z1-1, CX-5, YF+15, Z1+1, 'obsidian')
fill(CX+5, YF, Z1-1, CX+5, YF+15, Z1+1, 'obsidian')
fill(CX-4, YF+15, Z1-1, CX+4, YF+15, Z1+1, 'obsidian')
setblock(CX, YF+15, Z1, 'crying_obsidian')

print("=== Central Spire ===")
fill(CX-5, Y2+7, CZ-5, CX+5, Y2+40, CZ+5, 'obsidian', 'hollow')
setblock(CX, Y2+61, CZ, 'beacon')

print("=== Cathedral Complete! ===")
