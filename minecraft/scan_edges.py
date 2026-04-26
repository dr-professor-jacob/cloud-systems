#!/usr/bin/env python3
"""
scan_edges.py — Scans the 1271-1309 base boundaries to find air gaps.
Generates a fix report.
"""
import subprocess, time, json

def rcon(*args):
    cmd = ['sudo', 'docker', 'exec', 'minecraft', 'rcon-cli', '--'] + [str(a) for a in args]
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.stdout.strip()

X1, X2 = 1271, 1309
Z1, Z2 = 1886, 1930
Y_SURFACE = 76

gaps = []

print(f"=== Scanning Edges for air gaps at Y={Y_SURFACE} ===")

# Scan the perimeter and top layer
for x in [X1-5, X1, X2, X2+5]:
    for z in range(Z1-5, Z2+6, 5):
        res = rcon('execute', 'if', 'block', x, Y_SURFACE, z, 'air')
        if 'passed' in res.lower() or res.strip() == '1':
            gaps.append((x, Y_SURFACE, z))

print(f"Found {len(gaps)} air gaps on the surface level.")

if gaps:
    # Build a surgical fix command
    print("--- Emergency Edge Fix ---")
    # Expanding the fill range to ensure we catch the 'overspill'
    subprocess.run(['sudo', 'docker', 'exec', 'minecraft', 'rcon-cli', '--', 
                    'fill', str(X1-10), str(70), str(Z1-10), str(X2+10), str(75), str(Z2+10), 'dirt', 'replace', 'air'])
    subprocess.run(['sudo', 'docker', 'exec', 'minecraft', 'rcon-cli', '--', 
                    'fill', str(X1-10), str(76), str(Z1-10), str(X2+10), str(76), str(Z2+10), 'grass_block', 'replace', 'air'])
    print("Edge fix commands executed.")
else:
    print("No obvious surface air gaps detected at these specific probe points.")
