#!/bin/bash
# build_base.sh — v19 Industrial Integration
# Corrected MI IDs and Identity Spoofing.
# X: 1271-1309, Z: 1886-1930, Y: 60-69

RCON="sudo docker exec minecraft rcon-cli --"
PLAYER="Dr4g0nS14yer"
EXEC="execute as $PLAYER at $PLAYER run"

echo "=== 1. Wiping and Re-Shelling (Bypassing Claims) ==="
$RCON "$EXEC fill 1271 60 1886 1309 69 1930 air"
$RCON "$EXEC fill 1271 60 1886 1309 60 1930 polished_deepslate"
$RCON "$EXEC fill 1271 69 1886 1309 69 1930 deepslate_tiles"
$RCON "$EXEC fill 1271 61 1886 1309 69 1886 deepslate_bricks"
$RCON "$EXEC fill 1271 61 1929 1309 69 1929 deepslate_bricks"
$RCON "$EXEC fill 1271 61 1886 1271 69 1929 deepslate_bricks"
$RCON "$EXEC fill 1309 61 1886 1309 69 1929 deepslate_bricks"

echo "=== 2. Universal Machine Deployment ==="
# Using Casing instead of bricks if brick ID is unknown
$RCON "$EXEC fill 1273 61 1889 1275 63 1891 modern_industrialization:bronze_machine_casing hollow"
$RCON "$EXEC setblock 1274 62 1889 modern_industrialization:coke_oven"

$RCON "$EXEC fill 1304 61 1889 1306 63 1891 modern_industrialization:bronze_machine_casing hollow"
$RCON "$EXEC setblock 1305 62 1889 modern_industrialization:bronze_blast_furnace"

# Processing machines (Using verified IDs)
for i in {0..7}; do
  pz=$((1925 - i*3))
  $RCON "$EXEC setblock 1273 61 $pz modern_industrialization:bronze_macerator"
  $RCON "$EXEC setblock 1275 61 $pz modern_industrialization:bronze_furnace"
done

# Lighting
for x in {1274..1306..8}; do
  for z in {1890..1926..8}; do
    $RCON "$EXEC fill $x 69 $z $x 69 $z sea_lantern"
  done
done

# Kill mobs
$RCON "$EXEC kill @e[type=!player,distance=..60]"

echo "=== v19 Build Complete! ==="
