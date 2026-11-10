# Changelog

Versioning is semver for the **pack**: patch = mod version bumps, minor = mods added,
major = anything that can break an existing world (removing a content mod, block/item changes).

## 1.0.0 (2026-11-09): Phase 1, core engineering

Minecraft **1.21.1**, NeoForge **21.1.265**, Java 21. 25 mods + 3 libraries + the packwiz bootstrap
(24 mod jars on the server, 26 on clients).

| Mod | File | Side | Source | |
|---|---|---|---|---|
| AppleSkin | appleskin-neoforge-mc1.21-3.0.9.jar | both | Modrinth |  |
| Architectury API | architectury-13.0.11-neoforge.jar | both | Modrinth | library (FTB) |
| Chunky | Chunky-NeoForge-1.4.23.jar | server | Modrinth |  |
| Create | create-1.21.1-6.0.10.jar | both | Modrinth |  |
| Create Crafts & Additions | createaddition-1.7.2.jar | both | Modrinth |  |
| Create Deco | createdeco-2.1.3.jar | both | Modrinth |  |
| Create Slice & Dice | sliceanddice-4.3.4-neoforge.jar | both | Modrinth |  |
| Create: Diesel Generators | createdieselgenerators-1.21.1-1.3.15.jar | both | Modrinth |  |
| Entity Culling | entityculling-neoforge-1.11.3-mc1.21.1.jar | client | Modrinth |  |
| Farmer's Delight | FarmersDelight-1.21.1-1.3.4.jar | both | Modrinth |  |
| FerriteCore | ferritecore-7.0.3-neoforge.jar | both | Modrinth |  |
| FTB Chunks (NeoForge) | ftb-chunks-neoforge-2101.1.23.jar | both | CurseForge | not on Modrinth |
| FTB Library (NeoForge) | ftb-library-neoforge-2101.1.39.jar | both | CurseForge | not on Modrinth |
| FTB Teams (NeoForge) | ftb-teams-neoforge-2101.1.12.jar | both | CurseForge | not on Modrinth |
| ImmediatelyFast | ImmediatelyFast-NeoForge-1.6.15+1.21.1.jar | client | Modrinth |  |
| Iris Shaders | iris-neoforge-1.8.12+mc1.21.1.jar | client | Modrinth | **pinned** |
| Jade | Jade-1.21.1-NeoForge-15.10.6.jar | both | Modrinth |  |
| Just Enough Items (JEI) | jei-1.21.1-neoforge-19.64.0.455.jar | both | Modrinth |  |
| Kotlin for Forge | kotlinforforge-5.12.0-all.jar | both | Modrinth | library (Slice & Dice) |
| Lithium | lithium-neoforge-0.15.4+mc1.21.1.jar | both | Modrinth |  |
| MezzConfig | mezz_config-1.21.1-neoforge-0.7.1-standalone.jar | both | Modrinth | library (JEI) |
| ModernFix | modernfix-neoforge-5.27.27+mc1.21.1.jar | both | Modrinth |  |
| packwiz-installer-bootstrap | packwiz-installer-bootstrap.jar | client | GitHub | updater for the Prism hook |
| Simple Backups | SimpleBackups-1.21-4.0.21.jar | server | Modrinth |  |
| Sodium | sodium-neoforge-0.6.13+mc1.21.1.jar | client | Modrinth | **pinned** |
| spark | spark-1.10.124-neoforge.jar | both | Modrinth |  |
| Steam 'n' Rails (NeoForge port) | railways-0.2.1+neoforge-mc1.21.1.jar | both | Modrinth | **pinned**, unofficial port |
| Xaero's Minimap | xaerominimap-neoforge-1.21.1-26.6.0.jar | both | Modrinth |  |
| Xaero's World Map | xaeroworldmap-neoforge-1.21.1-1.47.0.jar | both | Modrinth |  |

### Configs
- `config/ftbchunks-world.snbt`: `force_load_mode = always` (factories run with nobody online; the
  default needs FTB Ranks, which isn't in the pack), `pvp_mode = never`, `def_pvp = false`.
  500 claims / 25 force-loaded chunks per player are already FTB's defaults.
- `config/simplebackups-common.toml`: `backupsToKeep = 24` (every 2 h while players are online,
  compressed: already defaults); `mc2discord = false`.
- Create: untouched (contraption limits checked: 2048 blocks moved, 64 piston poles, 384 rope).
- Xaero's: minimap and radar are **on by default** already (`display_minimap`/`display_radar`).
  **Not shipped: "radar shows animals only."** Xaero 26.x keeps radar categories in both
  `default_radar_categories_client.json` and `..._server.json` and has an enforced server-profile
  system. I couldn't confirm which file a player's live radar reads (vs. one Xaero regenerates),
  so it's left at Xaero's defaults instead of shipping a config that might be silently ignored.
  Per PC: Minimap settings → Entity Radar → turn off Hostile / Items / Other.

### Skipped
- Nothing from the Phase 1 list. Every mod has a NeoForge 1.21.1 build.
- Optional content not taken (per Mike's defaults): Create Big Cannons, Simple Voice Chat.

### Decisions that differ from the handoff
- **Sodium 0.6.13 + Iris 1.8.12 (pinned).** The handoff's reason for avoiding 0.8.x (alpha) is
  outdated: Sodium 0.8.13 is a full release as of 2026-08-28. But the only Iris build for it is
  `1.8.14-beta.1`, so the long-proven 0.6.13/1.8.12 pair stays for Phase 1. Revisit for Phase 3.
- **FTB mods come from CurseForge** (they are not on Modrinth). CurseForge allows third-party
  downloads for them, so packwiz-installer fetches them fine. Their jars are not openly
  licensed, so the full `.mrpack` (which bundles them) is private; see README "Distribution".
- **Server configs live in `config/`, not `defaultconfigs/`.** NeoForge 1.21.1 generates and reads
  server configs from `config/`, and FTB Chunks documents `config/` as the modpack-defaults location.
- **`server.properties` template → `server/amp-settings.json`.** AMP owns difficulty, PvP,
  whitelist, spawn protection, MOTD, distances, etc. and rewrites `server.properties` on every start.
- **Added `allow-flight = true`.** Standing on moving Create contraptions otherwise risks
  "Flying is not enabled" kicks.

### Known issues (upstream, harmless)
- Create Deco 2.1.3 logs one recipe parse error (`createdeco:placard`, malformed dye ingredient).
- Steam 'n' Rails logs ~277 loot-table errors for track variants of mods not in the pack
  (BYG, TerraFirmaCraft, Biomes O' Plenty, Twilight Forest, Quark, ...). It ships compat tracks
  for many mods; the missing ones are skipped.
