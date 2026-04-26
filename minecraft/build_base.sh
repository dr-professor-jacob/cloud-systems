#!/bin/bash
# build_base.sh — v16 Factory Overload
# Identity-Spoofed Construction with full machine lines and piping.
# X: 1271-1309, Z: 1886-1930, Y: 60-69

RCON="sudo docker exec minecraft rcon-cli --"
PLAYER="Dr4g0nS14yer"
EXEC="execute as $PLAYER at $PLAYER run"

echo "=== 1. Wiping and Re-Shelling ==="
# Sliced clear
$RCON "$EXEC fill 1271 60 1886 1285 69 1930 air"
$RCON "$EXEC fill 1286 60 1886 1300 69 1930 air"
$RCON "$EXEC fill 1301 60 1886 1309 69 1930 air"

# Floor, Walls, Ceiling
$RCON "$EXEC fill 1271 60 1886 1309 60 1930 polished_deepslate"
$RCON "$EXEC fill 1271 69 1886 1309 69 1930 deepslate_tiles"
$RCON "$EXEC fill 1271 61 1886 1309 69 1886 deepslate_bricks"
$RCON "$EXEC fill 1271 61 1930 1309 69 1930 deepslate_bricks"
$RCON "$EXEC fill 1271 61 1886 1271 69 1929 deepslate_bricks"
$RCON "$EXEC fill 1309 61 1886 1309 69 1929 deepslate_bricks"

echo "=== 2. Dual Lighting Grid ==="
for x in {1274..1306..6}; do
  for z in {1890..1926..7}; do
    $RCON "$EXEC fill $x 69 $z $x 69 $z sea_lantern"
    $RCON "$EXEC fill $x 59 $z $x 59 $z sea_lantern"
    $RCON "$EXEC fill $x 60 $z $x 60 $z glass"
  done
done

echo "=== 3. Dense Machine Deployment ==="
# Multiblocks
$RCON "$EXEC fill 1273 61 1889 1275 63 1891 modern_industrialization:coke_oven_brick hollow"
$RCON "$EXEC setblock 1274 62 1889 modern_industrialization:coke_oven"
$RCON "$EXEC fill 1304 61 1889 1306 63 1891 modern_industrialization:firebrick hollow"
$RCON "$EXEC setblock 1305 62 1889 modern_industrialization:bronze_blast_furnace"

# Tank Farm (NE Corner)
for i in {0..3}; do
  tx=$((1306 - i*2))
  $RCON "$EXEC setblock $tx 61 1895 modern_industrialization:bronze_tank"
  $RCON "$EXEC setblock $tx 60 1895 modern_industrialization:fluid_pipe"
done
$RCON "$EXEC fill 1300 60 1895 1306 60 1895 modern_industrialization:fluid_pipe"

# 16-Machine Processing Row (SW to Center)
for i in {0..7}; do
  pz=$((1925 - i*3))
  $RCON "$EXEC setblock 1273 61 $pz modern_industrialization:bronze_macerator"
  $RCON "$EXEC setblock 1275 61 $pz modern_industrialization:bronze_furnace"
  # Behind machines: Item Pipes
  $RCON "$EXEC setblock 1272 61 $pz modern_industrialization:item_pipe"
  # Under machines: Fluid Pipes (for Steam)
  $RCON "$EXEC setblock 1273 60 $pz modern_industrialization:fluid_pipe"
done

# The Quarry
$RCON "$EXEC setblock 1305 61 1925 modern_industrialization:quarry"

# Buff Beacon
$RCON "$EXEC fill 1289 59 1907 1291 59 1909 iron_block"
$RCON "$EXEC setblock 1290 60 1908 beacon"

# Mob Purge
$RCON "$EXEC kill @e[type=!player,distance=..60]"

echo "=== v16 Factory Overload Complete! ==="
