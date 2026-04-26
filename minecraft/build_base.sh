#!/bin/bash
# build_base.sh — v15 Identity-Spoofed Construction
# Executes all commands AS Dr4g0nS14yer to bypass FTB Chunks claims.
# X: 1271-1309, Z: 1886-1930, Y: 60-69

RCON="sudo docker exec minecraft rcon-cli --"
PLAYER="Dr4g0nS14yer"
EXEC="execute as $PLAYER at $PLAYER run"

echo "=== 1. Clearing Interior (Bypassing Claims) ==="
$RCON "$EXEC fill 1271 60 1886 1285 69 1930 air"
$RCON "$EXEC fill 1286 60 1886 1300 69 1930 air"
$RCON "$EXEC fill 1301 60 1886 1309 69 1930 air"

echo "=== 2. Building Shell ==="
# Floor and Ceiling
$RCON "$EXEC fill 1271 60 1886 1309 60 1930 polished_deepslate"
$RCON "$EXEC fill 1271 69 1886 1309 69 1930 deepslate_tiles"
# Walls
$RCON "$EXEC fill 1271 61 1886 1309 69 1886 deepslate_bricks"
$RCON "$EXEC fill 1271 61 1929 1309 69 1929 deepslate_bricks"
$RCON "$EXEC fill 1271 61 1886 1271 69 1929 deepslate_bricks"
$RCON "$EXEC fill 1308 61 1886 1308 69 1929 deepslate_bricks"

echo "=== 3. Double Lighting Grid ==="
for x in {1274..1306..6}; do
  for z in {1890..1926..7}; do
    $RCON "$EXEC fill $x 69 $z $x 69 $z sea_lantern"
    $RCON "$EXEC fill $x 59 $z $x 59 $z sea_lantern"
    $RCON "$EXEC fill $x 60 $z $x 60 $z glass"
  done
done

echo "=== 4. Machine Deployment ==="
$RCON "$EXEC fill 1273 61 1889 1275 63 1891 modern_industrialization:coke_oven_brick hollow"
$RCON "$EXEC setblock 1274 62 1889 modern_industrialization:coke_oven"
$RCON "$EXEC fill 1304 61 1889 1306 63 1891 modern_industrialization:firebrick hollow"
$RCON "$EXEC setblock 1305 62 1889 modern_industrialization:bronze_blast_furnace"

for i in {0..4}; do
  pz=$((1924 - i*3))
  $RCON "$EXEC setblock 1273 61 $pz modern_industrialization:bronze_macerator"
  $RCON "$EXEC setblock 1275 61 $pz modern_industrialization:bronze_furnace"
done

# Mob Purge
$RCON "$EXEC kill @e[type=!player,distance=..60]"

echo "=== v15 Build Complete! ==="
