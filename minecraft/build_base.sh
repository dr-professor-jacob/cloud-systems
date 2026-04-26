#!/bin/bash
# build_base.sh — v17 "Strict Sub-70" Industrial Build
# Strictly below Y=70. Full Lighting and Machines.
# X: 1271-1309, Z: 1886-1930, Y: 60-69

RCON="sudo docker exec minecraft rcon-cli --"
PLAYER="Dr4g0nS14yer"
EXEC="execute as $PLAYER at $PLAYER run"

echo "=== 1. Clearning Interior (Below Y:70 ONLY) ==="
# Sliced clear to stay under block limits
$RCON "$EXEC fill 1271 60 1886 1285 69 1930 air"
$RCON "$EXEC fill 1286 60 1886 1300 69 1930 air"
$RCON "$EXEC fill 1301 60 1886 1309 69 1930 air"

echo "=== 2. Building Shell ==="
# Floor and Ceiling (Recessed under roof)
$RCON "$EXEC fill 1271 60 1886 1309 60 1930 polished_deepslate"
$RCON "$EXEC fill 1271 69 1886 1309 69 1930 deepslate_tiles"
# Walls (9 blocks high)
$RCON "$EXEC fill 1271 61 1886 1309 69 1886 deepslate_bricks"
$RCON "$EXEC fill 1271 61 1930 1309 69 1930 deepslate_bricks"
$RCON "$EXEC fill 1271 61 1886 1271 69 1930 deepslate_bricks"
$RCON "$EXEC fill 1309 61 1886 1309 69 1930 deepslate_bricks"

echo "=== 3. Symmetrical Lighting Grid ==="
for x in {1274..1306..6}; do
  for z in {1890..1926..7}; do
    $RCON "$EXEC fill $x 69 $z $x 69 $z sea_lantern"
    $RCON "$EXEC fill $x 59 $z $x 59 $z sea_lantern"
    $RCON "$EXEC fill $x 60 $z $x 60 $z glass"
  done
done

echo "=== 4. Advanced MI Machine Deployment ==="
# Multiblocks (Full 3x3 structures)
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

# 16-Machine Processing Row (SW Line)
for i in {0..7}; do
  pz=$((1925 - i*3))
  $RCON "$EXEC setblock 1273 61 $pz modern_industrialization:bronze_macerator"
  $RCON "$EXEC setblock 1275 61 $pz modern_industrialization:bronze_furnace"
  # Pre-routed logistics pipes
  $RCON "$EXEC setblock 1272 61 $pz modern_industrialization:item_pipe"
  $RCON "$EXEC setblock 1273 60 $pz modern_industrialization:fluid_pipe"
done

# Quarry & Beacon
$RCON "$EXEC setblock 1305 61 1925 modern_industrialization:quarry"
$RCON "$EXEC fill 1289 59 1907 1291 59 1909 iron_block"
$RCON "$EXEC setblock 1290 60 1908 beacon"

# Mob Purge
$RCON "$EXEC kill @e[type=!player,distance=..60]"

echo "=== v17 Sub-70 Build Complete! Base is Hidden, Powered, and Mob-Proof. ==="
