#!/usr/bin/env python3
"""GuideBot: block-scan-aware Claude endpoint for FTB NeoTech."""
import os
import time
import json
from collections import defaultdict

import anthropic
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()
client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

rate_limits: dict[str, float] = {}
COOLDOWN = 60  # seconds per player

SYSTEM_PROMPT = """\
You are GuideBot, embedded in FTB NeoTech (Minecraft 1.20.4, NeoForge).
You receive a JSON scan of blocks near the player and answer their question.

== FTB NeoTech progression ==
Steam tier (first) → LV electric → MV → HV → endgame (AE2 + Mekanism)

== Key mods & block prefixes ==
modernindust:   Modern Industrialization — primary tech mod, steam→LV→MV→HV tiers
ae2:            Applied Energistics 2 — ME storage, autocrafting
mekanism:       Mekanism — ore tripling, advanced processing
immersiveengineering:  Immersive Engineering — multiblocks, power gen
actuallyadditions:     Actually Additions — useful gadgets, item pipes
laserio:        LaserIO — item/fluid/energy routing
pneumaticcraft: PneumaticCraft — air-pressure automation
justdirethings: JustDireThings — Direwolf20 extras

== Modern Industrialization quick reference ==
Power tiers (EU/t): LV=32, MV=128, HV=512
Cables:  lv_cable, mv_cable, hv_cable  (must match machine tier)
Hatches: input_hatch, output_hatch, energy_hatch (go on casing faces)

Electric Blast Furnace (EBF):
  Shell = electric_blast_furnace_casing, hollow cuboid, minimum 3 tall
  Needs: ≥1 input_hatch, ≥1 output_hatch, ≥1 energy_hatch on outer faces
  Shell must be sealed — no gaps except where hatches sit
  Coils (kanthal_coil etc.) go inside the shell

Steam Blast Furnace:
  Same layout but steam_blast_furnace_casing + steam_input_hatch

Distillery / Electrolyzer / Centrifuge:
  Single-block machines — just place + connect energy + pipe fluids/items

== Reading the scan ==
Each block entry has:
  id       — registry name (e.g. modernindust:electric_blast_furnace_casing)
  relPos   — position relative to player {x, y, z}
  state    — blockstate properties (facing, active, waterlogged, etc.)
  nbt      — tile entity data (energy stored, inventory, recipe, etc.) if present

== Response rules ==
- Under 200 words — must fit Minecraft chat
- Lead with the single most important issue or next step
- Name specific blocks and relative positions when relevant (e.g. "the block at +2, 0, -1")
- If the setup looks correct, confirm it and suggest the natural next upgrade
- Plain text only, no markdown
"""


class BlockEntry(BaseModel):
    id: str
    relPos: dict
    state: dict = {}
    nbt: str | None = None


class ScanPayload(BaseModel):
    player: str
    question: str
    blocks: list[BlockEntry]


def summarise_blocks(blocks: list[BlockEntry]) -> str:
    by_ns: dict[str, list] = defaultdict(list)
    for b in blocks:
        ns = b.id.split(":")[0]
        entry: dict = {"id": b.id, "pos": b.relPos}
        if b.state:
            entry["state"] = b.state
        if b.nbt:
            entry["nbt"] = b.nbt[:600] if len(b.nbt) > 600 else b.nbt
        by_ns[ns].append(entry)

    lines = []
    for ns in sorted(by_ns):
        group = by_ns[ns]
        lines.append(f"[{ns}] {len(group)} block(s):")
        for entry in group[:40]:
            line = f"  {entry['id']}  pos={entry['pos']}"
            if entry.get("state"):
                line += f"  state={entry['state']}"
            lines.append(line)
            if entry.get("nbt"):
                lines.append(f"    nbt: {entry['nbt']}")
    return "\n".join(lines)


@app.post("/guide")
async def guide(payload: ScanPayload):
    now = time.time()
    last = rate_limits.get(payload.player, 0.0)
    if now - last < COOLDOWN:
        remaining = int(COOLDOWN - (now - last))
        raise HTTPException(429, f"[GuideBot] Cooldown: {remaining}s remaining")
    rate_limits[payload.player] = now

    block_summary = summarise_blocks(payload.blocks)
    user_msg = (
        f"Question: {payload.question}\n\n"
        f"Block scan ({len(payload.blocks)} blocks found):\n{block_summary}"
    )

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=450,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_msg}],
    )
    return {"answer": response.content[0].text}
