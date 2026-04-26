#!/usr/bin/env python3
"""
Sci-Fi Cathedral "Church of the Void" - FAR INLAND HIGH (Safe Build v2)
Fixes chunk loading issues and TypeError in coordinate passing.
"""
import subprocess, time

def rcon(*args):
    cmd = ['sudo', 'docker', 'exec', 'minecraft', 'rcon-cli', '--'] + [str(a) for a in args]
    r = subprocess.run(cmd, capture_output=True, text=True)
    out = r.stdout.strip()
    if out: print(out)
    time.sleep(0.02)

def safe_fill(x1, y1, z1, x2, y2, z2, blk, mode=None):
    """Chunks large fill commands to stay under Minecraft's 32768 block limit."""
    x1, x2 = min(x1, x2), max(x1, x2)
    y1, y2 = min(y1, y2), max(y1, y2)
    z1, z2 = min(z1, z2), max(z1, z2)
    chunk_size = 6
    for y in range(y1, y2 + 1, chunk_size):
        ey = min(y + chunk_size - 1, y2)
        args = ['fill', x1, y, z1, x2, ey, z2, blk]
        if mode: args.append(mode)
        rcon(*args)

def setblock(x, y, z, blk):
    rcon('setblock', x, y, z, blk)

# --- NEW SAFE COORDINATES ---
CX, CZ, YF = -80, 450, 85
HW, HD, HH = 23, 19, 40
X1, X2 = CX - HW, CX + HW
Z1, Z2 = CZ - HD, CZ + HD
Y1, Y2 = YF, YF + HH
TW, TH = 4, 65

print(f"=== Preparing chunks at {CX}, {CZ} ===")
# Force Minecraft to load the chunks at the new location
rcon('forceload', 'add', X1-20, Z1-20, X2+20, Z2+20)

print(f"=== Starting Safe Build at {CX}, {YF}, {CZ} ===")

print("=== Clearing volume ===")
safe_fill(X1-10, YF, Z1-15, X2+10, YF+TH+30, Z2+15, 'air')

print("=== Foundation ===")
# Build a massive earthen base so it doesn't float (Fixed z2 parameter)
safe_fill(X1-20, YF-25, Z1-20, X2+20, YF-1, Z2+20, 'dirt', 'keep')
safe_fill(X1-TW, YF-1, Z1-TW, X2+TW, YF-1, Z2+TW, 'obsidian')
safe_fill(X1, YF, Z1, X2, YF, Z2, 'polished_deepslate')

print("=== Main Hall ===")
# Walls
safe_fill(X1, YF, Z1, X2, Y2, Z1+1, 'deepslate_bricks')
safe_fill(X1, YF, Z2-1, X2, Y2, Z2, 'deepslate_bricks')
safe_fill(X1, YF, Z1, X1+1, Y2, Z2, 'deepslate_bricks')
safe_fill(X2-1, YF, Z1, X2, Y2, Z2, 'deepslate_bricks')
# Lining
safe_fill(X1+1, YF, Z1+1, X2-1, Y2-1, Z1+2, 'obsidian')
safe_fill(X1+1, YF, Z2-2, X2-1, Y2-1, Z2-1, 'obsidian')

print("=== Roof ===")
safe_fill(X1, Y2, Z1, X2, Y2+2, Z2, 'deepslate_tiles')
safe_fill(X1+8, Y2+4, Z1+8, X2-8, Y2+7, Z2-8, 'crying_obsidian')

print("=== Corner towers ===")
towers = [(X1, Z1), (X1, Z2), (X2, Z1), (X2, Z2)]
for tx, tz in towers:
    safe_fill(tx-TW, YF, tz-TW, tx+TW, YF+TH, tz+TW, 'deepslate_bricks', 'hollow')
    safe_fill(tx-TW+1, YF+1, tz-TW+1, tx+TW-1, YF+TH-1, tz+TW-1, 'air')
    safe_fill(tx-TW, YF+TH, tz-TW, tx+TW, YF+TH+5, tz+TW, 'obsidian')
    setblock(tx, YF+TH-2, tz, 'lava')

print("=== North Entrance ===")
safe_fill(CX-4, YF, Z1-1, CX+4, YF+14, Z1+1, 'air')
safe_fill(CX-5, YF, Z1-1, CX-5, YF+15, Z1+1, 'obsidian')
safe_fill(CX+5, YF, Z1-1, CX+5, YF+15, Z1+1, 'obsidian')
safe_fill(CX-4, YF+15, Z1-1, CX+4, YF+15, Z1+1, 'obsidian')
setblock(CX, YF+15, Z1, 'crying_obsidian')

print("=== Central Spire ===")
safe_fill(CX-5, Y2+7, CZ-5, CX+5, Y2+40, CZ+5, 'obsidian', 'hollow')
setblock(CX, Y2+61, CZ, 'beacon')

print("=== Build Complete. Cleaning up chunk loader. ===")
rcon('forceload', 'remove', X1-20, Z1-20, X2+20, Z2+20)
print("=== Cathedral Build Complete! ===")
