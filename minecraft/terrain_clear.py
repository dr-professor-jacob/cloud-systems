#!/usr/bin/env python3
"""
terrain_clear.py
Clears all natural terrain around and above the cathedral.
Cathedral footprint: X[-103,-57] Z[130,168] floor Y=60
Clears: X[-125,-35] Z[108,190] Y[55,160] in chunks under 32768-block limit
"""
import subprocess, time

def rcon(*args):
    cmd = ['sudo', 'docker', 'exec', 'minecraft', 'rcon-cli', '--'] + [str(a) for a in args]
    r = subprocess.run(cmd, capture_output=True, text=True)
    out = r.stdout.strip()
    if out: print(out)
    time.sleep(0.08)

def fill(x1, y1, z1, x2, y2, z2, blk, mode=None):
    args = ['fill', x1, y1, z1, x2, y2, z2, blk]
    if mode: args.append(mode)
    rcon(*args)

# Clear in vertical slabs — each slab: 20 wide * 82 deep * 19 tall = 31,160 blocks (under 32768)
# X ranges (20 wide each): [-125,-106], [-105,-86], [-85,-66], [-65,-46], [-45,-35]
# Y ranges (19 tall each): [55,73],[74,92],[93,111],[112,130],[131,149],[150,160]

X_STRIPS = [(-125,-106), (-105,-86), (-85,-66), (-65,-46), (-45,-35)]
Y_STRIPS = [(55,73),(74,92),(93,111),(112,130),(131,149),(150,160)]
Z1, Z2 = 108, 190

total = len(X_STRIPS) * len(Y_STRIPS)
count = 0
for x1, x2 in X_STRIPS:
    for y1, y2 in Y_STRIPS:
        count += 1
        print(f"  Clearing strip {count}/{total}  X[{x1},{x2}] Y[{y1},{y2}] Z[{Z1},{Z2}]")
        fill(x1, y1, Z1, x2, y2, Z2, 'air')

# Flatten ground plate below the cleared area so there's no void
print("=== Ground plate ===")
fill(-125, 54, 108, -35, 54, 190, 'stone')
fill(-125, 55, 108, -35, 55, 190, 'grass_block')

print("=== Done! TP to see cathedral ===")
print("Run: sudo docker exec minecraft rcon-cli -- tp Dr4g0nS14yer -80 120 149")
