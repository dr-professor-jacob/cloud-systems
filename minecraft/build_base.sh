#!/bin/bash
# build_base.sh — v14 Ultra-Reliable Base Construction
# Strictly Below Y:70. Full Lighting and Machines.
# X: 1271-1309, Z: 1886-1930, Y: 60-69

RCON="sudo docker exec minecraft rcon-cli --"

echo "=== 1. Clearing Interior (Y:60-69) ==="
# Sliced clear to stay under block limits
$RCON "fill 1271 60 1886 1285 69 1930 air"
$RCON "fill 1286 60 1886 1300 69 1930 air"
$RCON "fill 1301 60 1886 1309 69 1930 air"

echo "=== 2. Building Shell ==="
# Floor and Ceiling
$RCON "fill 1271 60 1886 1309 60 1930 polished_deepslate"
$RCON "fill 1271 69 1886 1309 69 1930 deepslate_tiles"
# Walls (9 blocks high)
$RCON "fill 1271 61 1886 1309 69 1886 deepslate_bricks"
$RCON "fill 1271 61 1930 1309 69 1930 deepslate_bricks"
$RCON "fill 1271 61 1886 1271 69 1930 deepslate_bricks"
$RCON "fill 1309 61 1886 1309 69 1930 deepslate_bricks"

echo "=== 3. Double Lighting Grid (Floor & Ceiling) ==="
for x in {1274..1306..6}; do
  for z in {1890..1926..7}; do
    $RCON "fill $x 69 $z $x 69 $z sea_lantern"
    $RCON "fill $x 59 $z $x 59 $z sea_lantern"
    $RCON "fill $x 60 $z $x 60 $z glass"
  done
done

echo "=== 4. Machine Deployment ==="
# Multiblocks
$RCON "fill 1273 61 1889 1275 63 1891 modern_industrialization:coke_oven_brick hollow"
$RCON "setblock 1274 62 1889 modern_industrialization:coke_oven"
$RCON "fill 1304 61 1889 1306 63 1891 modern_industrialization:firebrick hollow"
$RCON "setblock 1305 62 1889 modern_industrialization:bronze_blast_furnace"

# Processing machines
for i in {0..4}; do
  pz=$((1924 - i*3))
  $RCON "setblock 1273 61 $pz modern_industrialization:bronze_macerator"
  $RCON "setblock 1275 61 $pz modern_industrialization:bronze_furnace"
done

# Mob Purge
$RCON 'kill @e[type=!player,distance=..60]'

echo "=== v14 Build Complete! (All within Y:60-69) ==="
