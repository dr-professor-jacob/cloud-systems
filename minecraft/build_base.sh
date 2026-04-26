#!/bin/bash
# build_base.sh — Ultra-reliable shell-based base construction
# Coordinates: X: 1271-1308, Z: 1886-1929, Y: 60-69

RCON="sudo docker exec minecraft rcon-cli --"

echo "=== 1. Wiping old blocks ==="
# Break wipe into 3 strips to stay under 32768 limit
$RCON "fill 1271 60 1886 1285 69 1929 air"
$RCON "fill 1286 60 1886 1300 69 1929 air"
$RCON "fill 1301 60 1886 1308 69 1929 air"

echo "=== 2. Building Shell ==="
# Floor
$RCON "fill 1271 60 1886 1308 60 1929 polished_deepslate"
# Ceiling
$RCON "fill 1271 69 1886 1308 69 1929 deepslate_tiles"
# Walls (9 blocks high)
$RCON "fill 1271 61 1886 1308 69 1886 deepslate_bricks"
$RCON "fill 1271 61 1929 1308 69 1929 deepslate_bricks"
$RCON "fill 1271 61 1886 1271 69 1929 deepslate_bricks"
$RCON "fill 1308 61 1886 1308 69 1929 deepslate_bricks"

echo "=== 3. Lighting ==="
# Grid of lanterns
for x in {1275..1305..8}; do
  for z in {1890..1925..8}; do
    $RCON "setblock $x 69 $z sea_lantern"
  done
done

echo "=== 4. Base Machines ==="
# NW: Coke Ovens
$RCON "fill 1273 61 1889 1275 63 1891 modern_industrialization:coke_oven_brick hollow"
$RCON "setblock 1274 62 1889 modern_industrialization:coke_oven"
# NE: Blast Furnaces
$RCON "fill 1304 61 1889 1306 63 1891 modern_industrialization:firebrick hollow"
$RCON "setblock 1305 62 1889 modern_industrialization:bronze_blast_furnace"

# Processing row
for i in {0..4}; do
  pz=$((1924 - i*3))
  $RCON "setblock 1273 61 $pz modern_industrialization:bronze_macerator"
  $RCON "setblock 1275 61 $pz modern_industrialization:bronze_furnace"
done

echo "=== Base Build Complete! ==="
