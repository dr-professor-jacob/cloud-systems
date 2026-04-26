#!/usr/bin/env python3
"""
Sci-Fi Cathedral "Church of the Void"
Builds at center (-80, 60, 149)
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

# ── Coordinates ───────────────────────────────────────────────────────────────
CX, CZ, YF = -80, 149, 60   # center x, center z, floor y

# Main hall: 46 wide x 38 deep x 40 tall
HW, HD, HH = 23, 19, 40     # half-width, half-depth, height
X1, X2 = CX - HW, CX + HW  # -103 to -57
Z1, Z2 = CZ - HD, CZ + HD  # 130 to 168
Y1, Y2 = YF, YF + HH        # 60 to 100

# Tower: 7x7 at each corner, 60 tall
TW, TH = 3, 60              # tower half-width, height
towers = [(X1, Z1), (X1, Z2), (X2, Z1), (X2, Z2)]

print("=== Clearing area ===")
fill(X1-TW-5, YF-3, Z1-TW-10, X2+TW+5, YF+TH+30, Z2+TW+10, 'air')

# ── Foundation ────────────────────────────────────────────────────────────────
print("=== Foundation ===")
fill(X1-TW, YF-3, Z1-TW, X2+TW, YF-1, Z2+TW, 'blackstone')
fill(X1, YF, Z1, X2, YF, Z2, 'smooth_basalt')
# Central glowing floor cross
fill(CX-1, YF, Z1+2, CX+1, YF, Z2-2, 'sea_lantern')
fill(X1+2, YF, CZ-1, X2-2, YF, CZ+1, 'sea_lantern')
# Amethyst corner accents on floor
for ox, oz in [(-15,-12),(-15,12),(15,-12),(15,12)]:
    fill(CX+ox-1, YF, CZ+oz-1, CX+ox+1, YF, CZ+oz+1, 'amethyst_block')

# ── Main hall shell ───────────────────────────────────────────────────────────
print("=== Main hall walls ===")
fill(X1, YF, Z1, X2, Y2, Z2, 'blackstone', 'hollow')
fill(X1+1, YF, Z1+1, X2-1, Y2, Z2-1, 'quartz_block', 'hollow')
fill(X1+2, YF+1, Z1+2, X2-2, Y2-1, Z2-2, 'air')

# Crying obsidian trim bands
fill(X1, YF+10, Z1, X2, YF+10, Z2, 'crying_obsidian', 'hollow')
fill(X1, YF+20, Z1, X2, YF+20, Z2, 'crying_obsidian', 'hollow')
fill(X1, YF+30, Z1, X2, YF+30, Z2, 'crying_obsidian', 'hollow')
fill(X1, Y2-1, Z1, X2, Y2-1, Z2, 'crying_obsidian', 'hollow')

# ── Roof ──────────────────────────────────────────────────────────────────────
print("=== Roof ===")
fill(X1, Y2, Z1, X2, Y2+2, Z2, 'blackstone')
fill(X1+4, Y2+2, Z1+4, X2-4, Y2+4, Z2-4, 'quartz_block')
fill(X1+8, Y2+4, Z1+8, X2-8, Y2+6, Z2-8, 'blackstone')

# ── Corner towers ─────────────────────────────────────────────────────────────
print("=== Corner towers ===")
for tx, tz in towers:
    fill(tx-TW, YF, tz-TW, tx+TW, YF+TH, tz+TW, 'end_stone_bricks', 'hollow')
    fill(tx-TW+1, YF+1, tz-TW+1, tx+TW-1, YF+TH-1, tz+TW-1, 'air')
    # Tower cap
    fill(tx-TW, YF+TH, tz-TW, tx+TW, YF+TH+4, tz+TW, 'purpur_block')
    # Crying obsidian bands on towers
    fill(tx-TW, YF+15, tz-TW, tx+TW, YF+15, tz+TW, 'crying_obsidian', 'hollow')
    fill(tx-TW, YF+30, tz-TW, tx+TW, YF+30, tz+TW, 'crying_obsidian', 'hollow')
    fill(tx-TW, YF+45, tz-TW, tx+TW, YF+45, tz+TW, 'crying_obsidian', 'hollow')
    # Tower spire
    for i in range(12):
        s = max(0, TW - i // 3)
        fill(tx-s, YF+TH+4+i, tz-s, tx+s, YF+TH+4+i, tz+s, 'purpur_pillar')
    # Tower lights
    setblock(tx, YF+8, tz, 'sea_lantern')
    setblock(tx, YF+22, tz, 'sea_lantern')
    setblock(tx, YF+38, tz, 'sea_lantern')
    setblock(tx, YF+52, tz, 'glowstone')

# ── Windows ───────────────────────────────────────────────────────────────────
print("=== Windows ===")
window_h_start, window_h_end = YF + 8, YF + 28
# North wall (z=Z1) windows
for wx in [CX-14, CX-5, CX+5, CX+14]:
    fill(wx-1, window_h_start, Z1-1, wx+1, window_h_end, Z1+1, 'tinted_glass')
    setblock(wx, window_h_start-1, Z1, 'chiseled_quartz_block')
    setblock(wx, window_h_end+1, Z1, 'chiseled_quartz_block')
# South wall (z=Z2) windows
for wx in [CX-14, CX-5, CX+5, CX+14]:
    fill(wx-1, window_h_start, Z2-1, wx+1, window_h_end, Z2+1, 'tinted_glass')
    setblock(wx, window_h_start-1, Z2, 'chiseled_quartz_block')
    setblock(wx, window_h_end+1, Z2, 'chiseled_quartz_block')
# West wall (x=X1) windows
for wz in [CZ-12, CZ, CZ+12]:
    fill(X1-1, window_h_start, wz-1, X1+1, window_h_end, wz+1, 'tinted_glass')
# East wall (x=X2) windows — leave gap for entrance
for wz in [CZ-12, CZ+12]:
    fill(X2-1, window_h_start, wz-1, X2+1, window_h_end, wz+1, 'tinted_glass')

# ── Central spire ─────────────────────────────────────────────────────────────
print("=== Central spire ===")
fill(CX-4, Y2+6, CZ-4, CX+4, Y2+35, CZ+4, 'purpur_block', 'hollow')
fill(CX-3, Y2+7, CZ-3, CX+3, Y2+34, CZ+3, 'air')
# Spire bands
fill(CX-4, Y2+12, CZ-4, CX+4, Y2+12, CZ+4, 'crying_obsidian', 'hollow')
fill(CX-4, Y2+22, CZ-4, CX+4, Y2+22, CZ+4, 'crying_obsidian', 'hollow')
# Spire tip
for i in range(16):
    s = max(0, 3 - i // 4)
    fill(CX-s, Y2+35+i, CZ-s, CX+s, Y2+35+i, CZ+s, 'crying_obsidian')
# Spire interior light
for y in range(Y2+8, Y2+35, 6):
    setblock(CX, y, CZ, 'glowstone')

# ── Interior pillars ──────────────────────────────────────────────────────────
print("=== Interior pillars ===")
pillar_positions = [
    (CX-15, CZ-12), (CX-15, CZ+12),
    (CX,    CZ-12), (CX,    CZ+12),
    (CX+15, CZ-12), (CX+15, CZ+12),
]
for px, pz in pillar_positions:
    fill(px-1, YF+1, pz-1, px+1, Y2-2, pz+1, 'quartz_pillar')
    fill(px-2, YF+20, pz-2, px+2, YF+20, pz+2, 'chiseled_quartz_block', 'hollow')
    setblock(px, Y2-1, pz, 'sea_lantern')

# ── Ceiling lights ────────────────────────────────────────────────────────────
print("=== Ceiling lighting ===")
for lx in range(X1+6, X2-5, 8):
    for lz in range(Z1+6, Z2-5, 8):
        setblock(lx, Y2-1, lz, 'glowstone')

# ── Main entrance (east wall) ─────────────────────────────────────────────────
print("=== Entrance ===")
fill(CX-4, YF, X2-1, CX+4, YF+14, X2+1, 'air')
fill(CX-5, YF, X2-1, CX+5, YF+15, X2+1, 'quartz_block', 'hollow')
# Entrance pillars
fill(CX-7, YF, X2-3, CX-5, YF+18, X2+3, 'purpur_block')
fill(CX+5, YF, X2-3, CX+7, YF+18, X2+3, 'purpur_block')
setblock(CX-6, YF+19, X2, 'glowstone')
setblock(CX+6, YF+19, X2, 'glowstone')
# Welcome mat
fill(CX-3, YF, X2+1, CX+3, YF, X2+5, 'amethyst_block')

# ── Flying buttresses (north + south) ────────────────────────────────────────
print("=== Buttresses ===")
for bx in [CX-14, CX, CX+14]:
    # North
    fill(bx-1, YF, Z1-8, bx+1, YF+18, Z1, 'blackstone')
    fill(bx-1, YF+18, Z1-6, bx+1, YF+22, Z1, 'quartz_block')
    # South
    fill(bx-1, YF, Z2, bx+1, YF+18, Z2+8, 'blackstone')
    fill(bx-1, YF+18, Z2, bx+1, YF+22, Z2+6, 'quartz_block')

# ── Outer decorative walls ────────────────────────────────────────────────────
print("=== Outer detail ===")
# Gilded blackstone crenellations on top of main walls
for x in range(X1, X2+1, 4):
    setblock(x, Y2+2, Z1, 'gilded_blackstone')
    setblock(x, Y2+2, Z2, 'gilded_blackstone')
for z in range(Z1, Z2+1, 4):
    setblock(X1, Y2+2, z, 'gilded_blackstone')
    setblock(X2, Y2+2, z, 'gilded_blackstone')

print("=== Church of the Void complete! ===")
print(f"Entrance is on the east side at X={X2}, Z={CZ}")
print(f"Center: {CX}, {YF}, {CZ}")
