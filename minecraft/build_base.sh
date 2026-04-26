#!/bin/bash
# build_base.sh — v22 "Fire Clay" Edition
# Using verified fire_clay_bricks ID.
# X: 1271-1309, Z: 1886-1930, Y: 60-69

RCON="sudo docker exec minecraft rcon-cli --"
PLAYER="Dr4g0nS14yer"
EXEC="execute as $PLAYER at $PLAYER run"

echo "=== 1. Wiping and Re-Shelling ==="
$RCON "$EXEC fill 1271 60 1886 1309 69 1930 air"
$RCON "$EXEC fill 1271 60 1886 1309 60 1930 polished_deepslate"
$RCON "$EXEC fill 1271 69 1886 1309 69 1930 deepslate_tiles"
$RCON "$EXEC fill 1271 61 1886 1309 69 1886 deepslate_bricks"
$RCON "$EXEC fill 1271 61 1929 1309 69 1930 deepslate_bricks"
$RCON "$EXEC fill 1271 61 1886 1271 69 1929 deepslate_bricks"
$RCON "$EXEC fill 1309 61 1886 1309 69 1929 deepslate_bricks"

echo "=== 2. MI Multiblocks (Using verified IDs) ==="
# Coke Oven
$RCON "$EXEC fill 1273 61 1889 1275 63 1891 modern_industrialization:coke_oven_bricks hollow"
$RCON "$EXEC setblock 1274 62 1889 modern_industrialization:coke_oven"

# Blast Furnace (Using FIRE CLAY BRICKS)
$RCON "$EXEC fill 1304 61 1889 1306 63 1891 modern_industrialization:fire_clay_bricks hollow"
$RCON "$EXEC setblock 1305 62 1889 modern_industrialization:bronze_blast_furnace"

echo "=== 3. Processing Line & Pipes ==="
for i in {0..7}; do
  pz=$((1925 - i*3))
  $RCON "$EXEC setblock 1273 61 $pz modern_industrialization:bronze_macerator"
  $RCON "$EXEC setblock 1275 61 $pz modern_industrialization:bronze_furnace"
  $RCON "$EXEC setblock 1272 61 $pz modern_industrialization:pipe"
  $RCON "$EXEC setblock 1273 60 $pz modern_industrialization:pipe"
done

# Quarry
$RCON "$EXEC setblock 1305 61 1925 modern_industrialization:quarry"
$RCON "$EXEC setblock 1304 61 1925 modern_industrialization:pipe"

# Lighting
for x in {1274..1306..8}; do
  for z in {1890..1926..8}; do
    $RCON "$EXEC fill $x 69 $z $x 69 $z sea_lantern"
  done
done

# Kill mobs
$RCON "$EXEC kill @e[type=!player,distance=..60]"

echo "=== v22 Build Complete! ==="
