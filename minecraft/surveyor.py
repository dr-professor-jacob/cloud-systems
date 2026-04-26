#!/usr/bin/env python3
"""
surveyor.py — High-Accuracy Base Scanner
X: 1271-1310, Z: 1886-1931, Y: 60-70
Generates a 1:1 JSON map of all non-air blocks.
"""
import subprocess, time, json, re, sys

def rcon(*args):
    cmd = ['sudo', 'docker', 'exec', 'minecraft', 'rcon-cli', '--'] + [str(a) for a in args]
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.stdout.strip()

X1, X2 = 1271, 1309
Z1, Z2 = 1886, 1930
Y1, Y2 = 60, 69

layout = []

# Using a more efficient method: 'testforblock' style checks or data get
print(f"=== Scanning Base: ({X1},{Z1}) to ({X2},{Z2}) ===", file=sys.stderr)

for y in range(Y1, Y2 + 1):
    for x in range(X1, X2 + 1):
        for z in range(Z1, Z2 + 1):
            # Check for non-air blocks
            res = rcon('data', 'get', 'block', x, y, z)
            if 'air' not in res.lower() and 'found' not in res.lower():
                match = re.search(r'id: "(.*?)"', res)
                if match:
                    layout.append({"x": x, "y": y, "z": z, "id": match.group(1)})

# Output to file
with open('base_layout.json', 'w') as f:
    json.dump(layout, f)

# Also print to stdout so user can copy/paste easily
print(json.dumps(layout))
