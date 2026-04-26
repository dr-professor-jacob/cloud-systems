#!/bin/bash
# build_base.sh — v23 Fully Loaded Base
# Bedrooms, Chest Walls, and Plumbed Multiblocks.
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

echo "=== 2. Bedroom & Chest Wall ==="
# Bedroom (SW)
$RCON "$EXEC setblock 1272 61 1927 minecraft:white_bed"
$RCON "$EXEC setblock 1272 61 1925 pneumaticcraft:reinforced_chest"
# Chest Wall (SE)
for i in {0..5}; do
  $RCON "$EXEC setblock 1308 61 $((1928 - i)) pneumaticcraft:reinforced_chest"
  $RCON "$EXEC setblock 1308 62 $((1928 - i)) pneumaticcraft:reinforced_chest"
done

echo "=== 3. Plumbed Multiblocks ==="
# Coke Oven with Hatches
$RCON "$EXEC fill 1273 61 1889 1275 63 1891 modern_industrialization:coke_oven_bricks hollow"
$RCON "$EXEC setblock 1274 62 1889 modern_industrialization:coke_oven"
$RCON "$EXEC setblock 1273 62 1890 modern_industrialization:bronze_item_input_hatch"
$RCON "$EXEC setblock 1275 62 1890 modern_industrialization:bronze_item_output_hatch"
$RCON "$EXEC setblock 1274 61 1890 modern_industrialization:bronze_fluid_output_hatch"

# Blast Furnace with Hatches
$RCON "$EXEC fill 1304 61 1889 1306 63 1891 modern_industrialization:fire_clay_bricks hollow"
$RCON "$EXEC setblock 1305 62 1889 modern_industrialization:bronze_blast_furnace"
$RCON "$EXEC setblock 1304 62 1890 modern_industrialization:bronze_item_input_hatch"
$RCON "$EXEC setblock 1306 62 1890 modern_industrialization:bronze_item_output_hatch"
$RCON "$EXEC setblock 1305 61 1890 modern_industrialization:bronze_energy_input_hatch"

echo "=== 4. Factory Line & Steam Grid ==="
for i in {0..3}; do
  bx=$((1280 + i*2))
  $RCON "$EXEC setblock $bx 61 1895 modern_industrialization:bronze_boiler"
  $RCON "$EXEC setblock $bx 60 1895 modern_industrialization:pipe" # Steam Out
done
$RCON "$EXEC fill 1280 60 1895 1286 60 1895 modern_industrialization:pipe"

# Machines and Item Pipe Grid
for i in {0..7}; do
  pz=$((1920 - i*3))
  $RCON "$EXEC setblock 1273 61 $pz modern_industrialization:bronze_macerator"
  $RCON "$EXEC setblock 1275 61 $pz modern_industrialization:bronze_furnace"
  $RCON "$EXEC setblock 1272 61 $pz modern_industrialization:pipe"
done

# Buffs & Light
$RCON "$EXEC fill 1289 59 1907 1291 59 1909 iron_block"
$RCON "$EXEC setblock 1290 60 1908 beacon"
for x in {1274..1306..8}; do for z in {1890..1926..8}; do $RCON "$EXEC fill $x 69 $z $x 69 $z sea_lantern"; done; done

$RCON "$EXEC kill @e[type=!player,distance=..60]"
echo "=== v23 Build Complete! Base is Fully Loaded. ==="
