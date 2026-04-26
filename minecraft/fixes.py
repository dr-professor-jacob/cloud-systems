#!/usr/bin/env python3
"""
fixes.py — terrain clear, entrance rebuild, exterior path
Cathedral center: CX=-80, CZ=149, YF=60
East wall (entrance side): X=-57
"""
import subprocess, time

def rcon(*args):
    cmd = ['sudo', 'docker', 'exec', 'minecraft', 'rcon-cli', '--'] + [str(a) for a in args]
    r = subprocess.run(cmd, capture_output=True, text=True)
    out = r.stdout.strip()
    if out: print(out)
    time.sleep(0.06)

def fill(x1, y1, z1, x2, y2, z2, blk, mode=None):
    args = ['fill', x1, y1, z1, x2, y2, z2, blk]
    if mode: args.append(mode)
    rcon(*args)

def setblock(x, y, z, blk):
    rcon('setblock', x, y, z, blk)

CX, CZ, YF = -80, 149, 60
X2 = -57   # east wall
X1 = -103  # west wall

# ── 1. Clear ALL terrain inside cathedral (brute force, full height) ──────────
print("=== Clearing terrain inside cathedral ===")
fill(-101, YF+1, 132, -80, 99, 166, 'air')
fill(-80,  YF+1, 132, -59, 99, 166, 'air')

# ── 2. Clear terrain OUTSIDE east wall (approach path) ───────────────────────
print("=== Clearing approach area (east side) ===")
fill(X2, YF-5, CZ-15, X2+30, 130, CZ+15, 'air')

# ── 3. Clear terrain OUTSIDE west wall ────────────────────────────────────────
print("=== Clearing west side ===")
fill(X1-20, YF-5, CZ-15, X1, 130, CZ+15, 'air')

# ── 4. Lay ground plate outside entrance so there's solid footing ─────────────
print("=== Ground plate outside ===")
fill(X2, YF-1, CZ-10, X2+25, YF-1, CZ+10, 'blackstone')
fill(X2, YF,   CZ-10, X2+25, YF,   CZ+10, 'smooth_basalt')

# ── 5. Cut proper entrance in east wall ───────────────────────────────────────
print("=== Entrance doorway ===")
# Wide arch: 8 blocks wide, 15 tall, centered on CZ=149
fill(X2-1, YF, CZ-4, X2+1, YF+14, CZ+4, 'air')
# Arch frame in quartz
fill(X2-1, YF, CZ-5, X2+1, YF+15, CZ-5, 'quartz_block')
fill(X2-1, YF, CZ+5, X2+1, YF+15, CZ+5, 'quartz_block')
fill(X2-1, YF+15, CZ-4, X2+1, YF+15, CZ+4, 'quartz_block')
# Keystone
setblock(X2, YF+15, CZ, 'amethyst_block')
# Glowstone lanterns flanking entrance
setblock(X2+1, YF+2, CZ-6, 'glowstone')
setblock(X2+1, YF+2, CZ+6, 'glowstone')

# ── 6. Exterior staircase up to floor level (approach from east) ──────────────
print("=== Exterior approach steps ===")
# If terrain is above YF, build a 5-step ramp from outside in
for i in range(6):
    fill(X2+2+i, YF-i, CZ-4, X2+2+i, YF-i, CZ+4, 'blackstone')   # riser
    fill(X2+2+i, YF-i-1, CZ-5, X2+7+i, YF-i-1, CZ+5, 'smooth_basalt')  # tread

# Flat plaza outside entrance
fill(X2+8, YF-6, CZ-6, X2+20, YF-6, CZ+6, 'smooth_basalt')

# ── 7. Internal floor (re-lay in case terrain overwrote it) ──────────────────
print("=== Re-laying interior floor ===")
fill(-101, YF, 132, -59, YF, 166, 'smooth_basalt')
# Room colour coding
fill(-101, YF, 132, -82, YF, 148, 'blackstone')
fill(-80,  YF, 132, -59, YF, 148, 'end_stone_bricks')
fill(-101, YF, 150, -82, YF, 166, 'purpur_block')
fill(-80,  YF, 150, -59, YF, 166, 'quartz_block')
fill(-82, YF, 148, -80, YF, 150, 'amethyst_block')

print("=== fixes.py complete ===")
print("Entrance: east side X=-57, Z=145-153, Y=60-74")
print("Approach: flat ground from X=-57 to X=-37, ground at Y=54 (6 steps up)")
print("TP to see entrance: /tp -40 63 149")
