#!/bin/bash
# build_base.sh — v24 Hole-Fixer Edition
# Forcefully fills gaps in shell and interior.
# X: 1271-1309, Z: 1886-1930, Y: 60-69

RCON="sudo docker exec minecraft rcon-cli --"
PLAYER="Dr4g0nS14yer"
EXEC="execute as $PLAYER at $PLAYER run"

echo "=== 1. Deep Clearing and Structural Force-Fill ==="
# Total Clear (Y:60-69)
$RCON "$EXEC fill 1271 60 1886 1309 69 1930 air"

# Force Floor (Overwrites everything)
$RCON "$EXEC fill 1271 60 1886 1309 60 1930 polished_deepslate"

# Force Ceiling
$RCON "$EXEC fill 1271 69 1886 1309 69 1930 deepslate_tiles"

# Force Walls (Overwrites natural stone/dirt holes)
$RCON "$EXEC fill 1271 61 1886 1309 69 1886 deepslate_bricks"
$RCON "$EXEC fill 1271 61 1930 1309 69 1930 deepslate_bricks"
$RCON "$EXEC fill 1271 61 1886 1271 69 1929 deepslate_bricks"
$RCON "$EXEC fill 1309 61 1886 1309 69 1929 deepslate_bricks"

echo "=== 2. Furnishing and Machines ==="
# Bedroom (SW)
$RCON "$EXEC setblock 1272 61 1927 minecraft:white_bed"
$RCON "$EXEC setblock 1272 61 1925 pneumaticcraft:reinforced_chest"

# Chest Wall (SE)
for i in {0..5}; do
  $RCON "$EXEC setblock 1308 61 $((1928 - i)) pneumaticcraft:reinforced_chest"
  $RCON "$EXEC setblock 1308 62 $((1928 - i)) pneumaticcraft:reinforced_chest"
done

# Multiblocks
$RCON "$EXEC fill 1273 61 1889 1275 63 1891 modern_industrialization:coke_oven_bricks hollow"
$RCON "$EXEC setblock 1274 62 1889 modern_industrialization:coke_oven"
$RCON "$EXEC fill 1304 61 1889 1306 63 1891 modern_industrialization:fire_clay_bricks hollow"
$RCON "$EXEC setblock 1305 62 1889 modern_industrialization:bronze_blast_furnace"

# Factory Line
for i in {0..7}; do
  pz=$((1920 - i*3))
  $RCON "$EXEC setblock 1273 61 $pz modern_industrialization:bronze_macerator"
  $RCON "$EXEC setblock 1275 61 $pz modern_industrialization:bronze_furnace"
  $RCON "$EXEC setblock 1272 61 $pz modern_industrialization:pipe"
done

# Lighting
for x in {1274..1306..8}; do for z in {1890..1926..8}; do $RCON "$EXEC fill $x 69 $z $x 69 $z sea_lantern"; done; done

$RCON "$EXEC kill @e[type=!player,distance=..60]"
echo "=== v24 Build Complete! Shell is Solid. ==="
