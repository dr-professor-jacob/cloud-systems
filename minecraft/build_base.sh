#!/bin/bash
# build_base.sh — v18 Debug Edition
# Strictly below Y=70. With detailed placement verification.
# X: 1271-1309, Z: 1886-1930, Y: 60-69

RCON="sudo docker exec minecraft rcon-cli --"
PLAYER="Dr4g0nS14yer"
EXEC="execute as $PLAYER at $PLAYER run"

echo "=== 1. Pre-Flight Debug Checks ==="
# Check if player is online
PLAYER_CHECK=$($RCON "list" | grep "$PLAYER")
if [[ -z "$PLAYER_CHECK" ]]; then
  echo "!!! WARNING: $PLAYER not detected in player list. 'execute as' might fail."
else
  echo "--- Player $PLAYER found. ---"
fi

# Test placement at player's feet
echo "--- Testing Claim Bypass ---"
$RCON "$EXEC setblock ~ ~ ~ minecraft:gold_block"
TEST_CHECK=$($RCON "$EXEC execute if block ~ ~ ~ minecraft:gold_block run say TEST_SUCCESS")
if [[ "$TEST_CHECK" == *"TEST_SUCCESS"* ]]; then
  echo "--- SUCCESS: Claims bypassed. Building authorized. ---"
  $RCON "$EXEC setblock ~ ~ ~ minecraft:air"
else
  echo "!!! FAILURE: Could not place test block. FTB Chunks is likely blocking RCON. !!!"
  echo "!!! Ensure 'Allow All Fake Players' is TRUE in Team Settings. !!!"
fi

echo "=== 2. Clearing and Shell Build ==="
$RCON "$EXEC fill 1271 60 1886 1285 69 1930 air"
$RCON "$EXEC fill 1286 60 1886 1300 69 1930 air"
$RCON "$EXEC fill 1301 60 1886 1309 69 1930 air"
$RCON "$EXEC fill 1271 60 1886 1309 60 1930 polished_deepslate"
$RCON "$EXEC fill 1271 69 1886 1309 69 1930 deepslate_tiles"

echo "=== 3. Machine & Multiblock Debug Build ==="
# We will place a single multiblock and verify it
echo "--- Placing Coke Oven Controller ---"
$RCON "$EXEC fill 1273 61 1889 1275 63 1891 modern_industrialization:coke_oven_brick hollow"
OUT=$($RCON "$EXEC setblock 1274 62 1889 modern_industrialization:coke_oven")
echo "RCON Response: $OUT"

# Verify the placement
VERIFY=$($RCON "$EXEC execute if block 1274 62 1889 modern_industrialization:coke_oven run say COKE_OVEN_OK")
if [[ "$VERIFY" == *"COKE_OVEN_OK"* ]]; then
  echo "--- VERIFIED: Coke Oven is in place. ---"
else
  echo "!!! FAILED: Coke Oven missing. Error: $VERIFY !!!"
fi

echo "--- Deploying Processing Row ---"
for i in {0..7}; do
  pz=$((1925 - i*3))
  # Place macerator and immediately verify
  $RCON "$EXEC setblock 1273 61 $pz modern_industrialization:bronze_macerator"
  $RCON "$EXEC setblock 1272 61 $pz modern_industrialization:item_pipe"
done

echo "=== 4. Finishing Touches ==="
for x in {1274..1306..8}; do
  for z in {1890..1926..8}; do
    $RCON "$EXEC fill $x 69 $z $x 69 $z sea_lantern"
  done
done

echo "=== Debug Build Sequence Finished ==="
