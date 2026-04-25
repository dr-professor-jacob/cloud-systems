// kubejs/server_scripts/guide.js
// Drop into: <server>/kubejs/server_scripts/guide.js
// In-game command: /scan  or  /scan <question>
// Scans blocks in SCAN_RADIUS around the player, POSTs to mc_guide.py, replies in chat.

const SCAN_RADIUS = 8      // blocks in each direction (17^3 cube)
const MAX_BLOCKS  = 150    // cap to keep payload reasonable
const GUIDE_URL   = 'http://host.docker.internal:8765/guide'

// Vanilla blocks worth including (everything else non-minecraft is auto-included)
const VANILLA_KEEP = new Set([
  'minecraft:crafting_table', 'minecraft:furnace', 'minecraft:blast_furnace',
  'minecraft:smoker', 'minecraft:chest', 'minecraft:trapped_chest',
  'minecraft:barrel', 'minecraft:hopper', 'minecraft:dropper',
  'minecraft:dispenser', 'minecraft:brewing_stand', 'minecraft:cauldron',
  'minecraft:enchanting_table', 'minecraft:anvil', 'minecraft:grindstone',
])

ServerEvents.commandRegistry(event => {
  const { commands: Commands } = event
  const StringArgumentType = java('com.mojang.brigadier.arguments.StringArgumentType')

  event.register(
    Commands.literal('scan')
      .executes(ctx => {
        runScan(ctx, 'What should I fix or build next?')
        return 1
      })
      .then(
        Commands.argument('question', StringArgumentType.greedyString())
          .executes(ctx => {
            runScan(ctx, StringArgumentType.getString(ctx, 'question'))
            return 1
          })
      )
  )
})

function runScan(ctx, question) {
  const player = ctx.source.player
  if (!player) return

  player.sendSystemMessage(
    Component.literal('[GuideBot] Scanning...').withStyle(s => s.withColor(0xAAAAAA))
  )

  const level      = ctx.source.level
  const origin     = player.blockPosition()
  const playerName = player.name.string
  const server     = ctx.source.server

  // --- collect blocks on the server thread (fast) ---
  const blocks = []

  outer:
  for (let x = -SCAN_RADIUS; x <= SCAN_RADIUS; x++) {
    for (let y = -SCAN_RADIUS; y <= SCAN_RADIUS; y++) {
      for (let z = -SCAN_RADIUS; z <= SCAN_RADIUS; z++) {
        if (blocks.length >= MAX_BLOCKS) break outer

        const pos   = origin.offset(x, y, z)
        const state = level.getBlockState(pos)
        if (state.isAir()) continue

        const blockId = state.block.id.toString()
        const ns      = blockId.split(':')[0]

        if (ns === 'minecraft' && !VANILLA_KEEP.has(blockId)) continue

        // block state properties
        const stateProps = {}
        try {
          state.block.stateDefinition.properties.forEach(prop => {
            stateProps[prop.name] = state.getValue(prop).toString()
          })
        } catch (_) {}

        // tile entity NBT (machine state, energy, inventory, etc.)
        let nbt = null
        try {
          const be = level.getBlockEntity(pos)
          if (be !== null) nbt = be.saveWithoutMetadata().toString()
        } catch (_) {}

        blocks.push({ id: blockId, relPos: { x, y, z }, state: stateProps, nbt })
      }
    }
  }

  // --- HTTP call on a worker thread so the server doesn't stall ---
  const Thread = java('java.lang.Thread')
  new Thread(() => {
    const answer = callGuide(playerName, question, blocks)

    // schedule chat message back on the main server thread
    server.execute(() => {
      const p = server.playerList.getPlayerByName(playerName)
      if (!p) return

      // chunk into 240-char pieces so chat doesn't truncate
      const full = '[GuideBot] ' + answer
      for (let i = 0; i < full.length; i += 240) {
        p.sendSystemMessage(
          Component.literal(full.substring(i, i + 240))
            .withStyle(s => s.withColor(0x55FFFF))
        )
      }
    })
  }).start()
}

function callGuide(playerName, question, blocks) {
  const URL                = java('java.net.URL')
  const StandardCharsets   = java('java.nio.charset.StandardCharsets')
  const BufferedReader     = java('java.io.BufferedReader')
  const InputStreamReader  = java('java.io.InputStreamReader')

  try {
    const body  = JSON.stringify({ player: playerName, question, blocks })
    const url   = new URL(GUIDE_URL)
    const conn  = url.openConnection()

    conn.setRequestMethod('POST')
    conn.setDoOutput(true)
    conn.setRequestProperty('Content-Type', 'application/json')
    conn.setConnectTimeout(5000)
    conn.setReadTimeout(60000)

    const bytes = new (java('java.lang.String'))(body).getBytes(StandardCharsets.UTF_8)
    const os    = conn.getOutputStream()
    os.write(bytes)
    os.close()

    const code   = conn.getResponseCode()
    const stream = code === 200 ? conn.getInputStream() : conn.getErrorStream()
    const reader = new BufferedReader(new InputStreamReader(stream, StandardCharsets.UTF_8))

    let raw = '', line = reader.readLine()
    while (line !== null) { raw += line; line = reader.readLine() }
    reader.close()

    const data = JSON.parse(raw)
    return code === 200 ? data.answer : (data.detail || 'Unknown error')

  } catch (e) {
    return 'Guide unavailable: ' + e.message
  }
}
