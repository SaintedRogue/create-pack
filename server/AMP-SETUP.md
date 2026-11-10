# AMP server setup: Ahrendt Engineering

**Current state:** built through the AMP API on 2026-11-09 with the repo's scripts.
You don't need to click through any of this unless you're rebuilding by hand.

| | |
|---|---|
| AMP panel | <http://10.0.0.180:8080>, login `rogue` |
| Instance | `CreateMC01` (shown as "Ahrendt Engineering"), AMP management port 8082 |
| Join address | **`10.0.0.180:25570`**, LAN only, no port forward |
| Loader | NeoForge **21.1.265** (Minecraft 1.21.1), Server JAR `[Autoselect]` |
| Java | Temurin **21**, 8 GB heap (min = max = 8192 MB) |
| Files (Unraid) | `/mnt/user/appdata/amp/.ampdata/instances/CreateMC01/Minecraft` |
| Files (in AMP container) | `/home/amp/.ampdata/instances/CreateMC01/Minecraft` |
| Neighbours | `KidsMC01` (Paper 26.3, Bedrock via Geyser) runs alongside on 25565/19132 |

The AMP container sits on Unraid's `br0` network with its own LAN IP (10.0.0.180), so every
instance port is reachable on the LAN without port mapping, and nothing is exposed to the internet.

## Keeping the server in sync with the pack

```sh
server/sync-server.sh                  # stop → NeoForge check → packwiz-installer → start
server/sync-server.sh --reapply-settings   # also re-push server/amp-settings.json
```
Run it from the repo on any machine with SSH access to Unraid (`~/.ssh/unraid_ed25519`). It's
idempotent. It installs whatever the `release` branch's `pack.toml` lists and removes files the
pack no longer lists. AMP's own updater runs only when the pack's NeoForge version changes.

## Settings (applied by `server/amp_api.py settings`)

AMP rewrites `server.properties` from its own settings on every start, so these are AMP
settings, not a properties template. Source of truth: [`amp-settings.json`](amp-settings.json).

| AMP setting (Configuration → …) | Value | Why |
|---|---|---|
| Minecraft → Server Type | NeoForge | |
| Minecraft → NeoForge Version | 21.1.265 | must match `pack/pack.toml` |
| Minecraft → Server JAR | [Autoselect] | NeoForge has no single startup jar |
| Java → Java Version | Temurin 21 | NeoForge 21.1 needs 21. The container default is 25 |
| Java → Memory Limit / pre-allocation | 8192 / 8192 MB | |
| Game → Difficulty | Normal | |
| Game → PvP | off | FTB Chunks also blocks PvP in claims |
| Game → Use / Enforce Whitelist | on / on | |
| Game → Spawn Protection Radius | 0 | FTB Chunks handles protection |
| Game → Allow Flight | **on** | moving Create contraptions otherwise trigger "flying" kicks |
| Minecraft → View / Simulation Distance | 10 / 8 | |
| Limits → Max Players | 10 | |
| Limits → **Sleep Mode** | **off** | AMP sleep stops the whole server when empty, so force-loaded factories would halt |

## Schedule (Configuration → Schedule)

One trigger, **"create-pack: nightly backup + restart (03:30)"**, runs AMP's *Take Backup* with
*Back up while running* **off**. AMP stops the server, backs up the world while it's stopped
(so the backup is consistent), and starts it again, which doubles as the daily restart.
AMP keeps 28 backups (20 GB cap) in the instance's `Backups/` folder. Recreate it with
`server/amp_api.py schedule CreateMC01`.

**Why 03:30, not 04:30:** Unraid's *Appdata Backup* plugin stops **every** container at
04:30 Eastern (01:30 on the Unraid clock, which is on Pacific time), AMP included. The original
04:30 job collided with it and was killed 14 seconds into the backup. So both servers also
restart once more around 04:30-04:40, and they come back on their own because
**start-on-boot is on** for both `CreateMC01` and `KidsMC01` (`server/amp_api.py autostart <instance> on`).
Without it, every instance stays offline after that nightly container restart.

On top of that, the **Simple Backups** mod saves the world every 2 hours while anyone is online,
keeping 24, in `Minecraft/simplebackups/`.

## First start: accept the Minecraft EULA

AMP only asks for the EULA **when the server is starting**, so there's nothing to find while it's
stopped ("Application Idle"). To get the prompt:

1. **Instances** → on the **CreateMC01** card, click the green **Manage** button (cube icon, far right).
2. On the instance's **Status** page, click **Start**.
3. AMP pops up a question asking you to accept the Minecraft EULA. Accept it.

The server then installs its first-run files and boots (NeoForge with this pack takes about 1-2 minutes).
This is a one-time legal acceptance by the server owner, so the scripts deliberately don't do it:
`sync-server.sh` stops with a message telling you to do it.

## One-time steps after the first boot

From the AMP console (or `server/amp_api.py console CreateMC01 "<command>"`):

```
gamerule keepInventory true
gamerule playersSleepingPercentage 1
chunky world minecraft:overworld
chunky spawn
chunky radius 2000
chunky start
```
Chunky pre-generates a 4000×4000-block area centred on world spawn (`chunky spawn`, otherwise it
centres on 0,0). On this host it ran at about 150 chunks/s, so roughly 7 minutes; players can be on
while it runs. `chunky progress` shows how far it is.

Done on the live server on 2026-11-10, right after the EULA was accepted. The first boot took 6.4 s, and
the log has only the two known upstream errors from the CHANGELOG (277 Steam 'n' Rails loot tables + 1 Create Deco recipe).

## If the server shows "Failed" after a restart

Create 6.0.10 has a rare startup race. In testing it happened only under heavy CPU load, and never in
17 plain server boots. When it hits, the log ends with `IndexOutOfBoundsException ... PackageStyles.getDefaultBox`.
Nothing is damaged, because it fails before the world loads. Press **Start** in AMP, or run
`server/amp_api.py start CreateMC01`. See CHANGELOG 1.1.0 "Known issue".

## Whitelist

Players are turned away until whitelisted. When a kid first tries to join, the console shows
their exact Java username in the rejection message. Then:
```
whitelist add <JavaUsername>
```
Op isn't needed for anyone: the AMP console already has full control.

## Rebuilding by hand (reference)

1. **Instances → Create Instance**: Application *Minecraft Java Edition*, name `CreateMC01`.
2. **Configuration → Minecraft → Server and Startup**: Server Type *NeoForge*, NeoForge Version
   `21.1.265`, Server JAR *[Autoselect]*. Click **Update** and wait for "NeoForge installed".
3. **Configuration → Java**: Java *Temurin 21*, memory 8192/8192.
4. Game, Limits and Network settings from the table above (game port is under the instance's
   *Network* settings and can only be changed while the instance is stopped).
5. **Schedule**: add the 03:30 trigger with *Take Backup* (Local ✓, Back up while running ✗).
6. Run `server/sync-server.sh` to install the mods, then do the one-time console steps.
