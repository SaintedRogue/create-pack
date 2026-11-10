# Ahrendt Engineering

A small, curated **Create** engineering modpack for a family server.
Minecraft **1.21.1** · NeoForge **21.1.x** · Java 21 · built with [packwiz](https://packwiz.infra.link/).

- Server: CubeCoders AMP instance `CreateMC01` on the Unraid box, `10.0.0.180:25570` (LAN only).
- Clients: Prism Launcher. A pre-launch hook syncs every launch to the published pack.
  Setup steps for each PC: [`client/CLIENT-SETUP.md`](client/CLIENT-SETUP.md).
- Server setup and operations: [`server/AMP-SETUP.md`](server/AMP-SETUP.md).
- What's in it and why: [`CHANGELOG.md`](CHANGELOG.md).

## How the pieces fit

```
 main branch ──(tag vX.Y.Z)──▶ release branch ──▶ raw.githubusercontent.com/.../release/pack/pack.toml
                                                      │                         │
                                     server/sync-server.sh               Prism pre-launch hook
                                     (packwiz-installer -s server)       (packwiz-installer -s client)
                                                      ▼                         ▼
                                              AMP: CreateMC01             each family PC
```

**Clients and the server both follow the `release` branch, never `main`.** Pushing to `main` changes
nothing for players. A version goes live only when `release` moves *and* the server is synced, so
clients can't get ahead of the server.

## Layout

| Path | What |
|---|---|
| `pack/` | packwiz root: `pack.toml`, `index.toml`, `mods/*.pw.toml`, curated `config/` |
| `server/sync-server.sh` | sync the AMP instance to the published pack (idempotent) |
| `server/amp_api.py` | tiny AMP API client used by the sync script (status/stop/start/settings/console) |
| `server/amp-settings.json` | gameplay settings applied as AMP settings (replaces a `server.properties` template) |
| `scripts/smoke-test-server.sh` | headless server boot test |
| `scripts/smoke-test-client.sh` | end-to-end test: real client on a virtual display joins the server |
| `scripts/export-mrpack.sh` | build `dist/*.mrpack` (public + private) |

## Tools

- **packwiz**: has no releases; built from a pinned commit (recorded in `~/.local/bin/.packwiz-commit`):
  ```sh
  docker run --rm --network host -e CGO_ENABLED=0 -e GOBIN=/out -v "$PWD/bin:/out" golang:1.25 \
    go install github.com/packwiz/packwiz@170b22d785959dda5876b54b7f16e1b807a57fb6
  ```
- **Docker** for the smoke tests. On this laptop Docker is *rootless*: the scripts use
  `--network host` (rootlesskit's shared namespace) because the default bridge can't resolve DNS here.
- `python3`, `ssh` key access to Unraid (`~/.ssh/unraid_ed25519`) for the server scripts.

## Common tasks

### Add a mod
1. Confirm a **NeoForge 1.21.1** build exists on Modrinth (CurseForge only if it isn't on Modrinth).
   Pick the exact version, then add it by its version page URL so packwiz can't pick a beta:
   `cd pack && packwiz modrinth add https://modrinth.com/mod/<slug>/version/<id> -y`
2. Check `side` in `mods/<slug>.pw.toml` (`client` for rendering/UI-only mods, `server` for admin tools).
3. `packwiz refresh`, then run **both** smoke tests (below).
4. Bump `version` in `pack/pack.toml` (**minor** for added mods), add a CHANGELOG entry, commit.

### Update mods
- `cd pack && packwiz update <slug>` (one) or `packwiz update --all`. Pinned mods are skipped.
- **Pinned on purpose**: `sodium` + `iris` (must move together; see CHANGELOG), and
  `create-steam-n-rails-1.21.1` (unofficial port, so back up the world before updating it).
  Unpin with `packwiz unpin <slug>` only when you mean it.
- Bump the **patch** version, test, changelog, commit.

### Run the tests
```sh
scripts/smoke-test-server.sh            # ~1 min warm. Boots the server, waits for "Done (".
scripts/smoke-test-client.sh            # ~5-10 min. Real client joins; catches client-only crashes.
```
Both exit non-zero on: missing dependencies, mixin failures, crash reports, timeouts.
Acceptance for any release: both pass, `packwiz refresh` leaves no diff, the `.mrpack` exports.

### Release
```sh
git tag -a v1.2.3 -m "v1.2.3"
git push origin main v1.2.3
git push origin v1.2.3:release            # clients pick this up on their next launch
server/sync-server.sh                     # stop → install → start the AMP server
scripts/export-mrpack.sh                  # writes dist/*-public.mrpack (+ private full pack)
gh release create v1.2.3 --title v1.2.3 --notes-file <(sed -n '/^## 1.2.3/,/^## [0-9]/p' CHANGELOG.md | sed '$d') \
  dist/Ahrendt-Engineering-public.mrpack dist/Ahrendt-Engineering-1.2.3-public.mrpack
# Ahrendt-Engineering-public.mrpack (unversioned) is what CLIENT-SETUP.md links to via releases/latest.
```
Do the `release` push and the server sync back to back. Between them the server is behind,
so anyone launching in that window can't connect until the sync finishes.

### Roll back
1. `git push --force origin v1.2.2:release`, which points `release` at the previous good tag.
2. `server/sync-server.sh`. packwiz-installer removes files the older pack doesn't list.
3. If the bad version **added content mods** and anyone played on it, the world may hold
   blocks the old pack doesn't know. Restore the world from the backup taken before the update
   (AMP backup or `simplebackups/` in the instance) instead of just downgrading.

**Never remove a content mod in a patch or minor release**: it deletes those blocks from the world.

## Distribution and licensing

- This repo holds **metadata only** (`*.pw.toml`); jars are never committed.
- The FTB mods are CurseForge-only and not openly licensed. `scripts/export-mrpack.sh` writes:
  - `dist/*-public.mrpack`: no FTB jars, safe to publish. The client hook fetches FTB on first launch.
  - `dist/*.mrpack`: full and **private**. Use it for offline installs only; `dist/` is git-ignored.
