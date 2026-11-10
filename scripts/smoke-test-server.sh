#!/usr/bin/env bash
# Boot the pack as a headless NeoForge server in Docker and verify it reaches "Done (".
#
# Serves ./pack over a throwaway local HTTP server, points itzg/minecraft-server's
# packwiz support at it (the same packwiz-installer path the AMP server and clients use),
# and fails on: timeout, missing mandatory dependencies, mixin crashes, or any crash report.
#
# Usage: scripts/smoke-test-server.sh [--keep] [--timeout SECONDS]
#   --keep     keep the server data dir afterwards (prints its path) — handy for harvesting
#              freshly generated default configs
#   env IMAGE  override the container image (default pinned below)
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PACK_DIR="$REPO_ROOT/pack"
IMAGE="${IMAGE:-docker.io/itzg/minecraft-server:java21}"
WEB_IMAGE="${WEB_IMAGE:-docker.io/library/busybox:stable}"
TIMEOUT=300
KEEP=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --keep) KEEP=1 ;;
    --timeout) TIMEOUT="$2"; shift ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
  shift
done

# Versions come from pack.toml so the test can never drift from the pack.
MC_VERSION="$(sed -n 's/^minecraft = "\(.*\)"/\1/p' "$PACK_DIR/pack.toml")"
NEOFORGE_VERSION="$(sed -n 's/^neoforge = "\(.*\)"/\1/p' "$PACK_DIR/pack.toml")"
[[ -n "$MC_VERSION" && -n "$NEOFORGE_VERSION" ]] || { echo "could not read versions from pack.toml" >&2; exit 2; }

command -v packwiz >/dev/null && (cd "$PACK_DIR" && packwiz refresh >/dev/null)

WORK="$(mktemp -d "${TMPDIR:-/tmp}/create-pack-smoke.XXXXXX")"
DATA="$WORK/data"; mkdir -p "$DATA"
PORT=8765            # bound inside rootlesskit's netns, not the real host, so it can't collide with laptop services
NAME="create-pack-smoke-$$"
WEB="$NAME-web"

cleanup() {
  docker rm -f "$NAME" "$WEB" >/dev/null 2>&1 || true
  if [[ $KEEP -eq 1 ]]; then echo "kept server data: $DATA"; else rm -rf "$WORK"; fi
}
trap cleanup EXIT

echo "smoke test: MC $MC_VERSION / NeoForge $NEOFORGE_VERSION / image $IMAGE / timeout ${TIMEOUT}s"
docker pull -q "$IMAGE" >/dev/null
docker pull -q "$WEB_IMAGE" >/dev/null
# Pack server sidecar. Under rootless Docker, --network host means rootlesskit's network
# namespace (not the laptop's), so a pack server on the laptop's own loopback is unreachable.
# Running BOTH containers with --network host puts them in that same namespace, so they
# share 127.0.0.1. (Joining via --network container:X is refused under rootless, and the
# default bridge can't resolve DNS on this host: UDP out of bridge containers times out.)
docker run -d --name "$WEB" --network host -v "$PACK_DIR:/pack:ro" "$WEB_IMAGE" \
  httpd -f -p "127.0.0.1:$PORT" -h /pack >/dev/null
START=$(date +%s)
# UID/GID=0: under rootless Docker, container root maps to the invoking user, so the
# generated world/config files stay owned by you (uid 1000 in-container would map elsewhere).
docker run -d --name "$NAME" --network host \
  -e EULA=TRUE -e TYPE=NEOFORGE -e VERSION="$MC_VERSION" -e NEOFORGE_VERSION="$NEOFORGE_VERSION" \
  -e PACKWIZ_URL="http://127.0.0.1:$PORT/pack.toml" -e MEMORY=6G -e ONLINE_MODE=FALSE \
  -e UID=0 -e GID=0 -e ENABLE_RCON=FALSE \
  -v "$DATA:/data" "$IMAGE" >/dev/null

FAIL_RE='Missing or unsupported mandatory dependencies|Mixin apply failed|MixinApplyError|MixinTransformerError|Failed to create mod instance|ModLoadingException|Crash report saved|This crash report has been saved'
result="TIMEOUT"
while (( $(date +%s) - START < TIMEOUT )); do
  logs="$(docker logs "$NAME" 2>&1 || true)"
  if grep -qE "$FAIL_RE" <<<"$logs" || compgen -G "$DATA/crash-reports/*" >/dev/null; then result="FAIL"; break; fi
  if grep -qE 'Done \([0-9.]+s\)!' <<<"$logs"; then result="PASS"; break; fi
  if [[ "$(docker inspect -f '{{.State.Running}}' "$NAME" 2>/dev/null)" != "true" ]]; then result="EXITED"; break; fi
  sleep 3
done
ELAPSED=$(( $(date +%s) - START ))

docker logs "$NAME" >"$WORK/server.log" 2>&1 || true
[[ $KEEP -eq 1 ]] && cp "$WORK/server.log" "$DATA/smoke-server.log"
MOD_COUNT=$(find "$DATA/mods" -maxdepth 1 -name '*.jar' 2>/dev/null | wc -l)
LOADED=$(grep -oE 'Loading [0-9]+ mods' "$WORK/server.log" | tail -1 || true)

if [[ "$result" == "PASS" ]]; then
  # Stop cleanly so world save/shutdown hooks run too.
  docker stop -t 60 "$NAME" >/dev/null 2>&1 || true
  docker logs "$NAME" >"$WORK/server.log" 2>&1 || true
  [[ $KEEP -eq 1 ]] && cp "$WORK/server.log" "$DATA/smoke-server.log"
  if compgen -G "$DATA/crash-reports/*" >/dev/null; then result="FAIL (crash during shutdown)"; fi
fi

echo "result:      $result"
echo "mods jars:   $MOD_COUNT  (${LOADED:-loader line not found})"
echo "boot time:   ${ELAPSED}s (includes NeoForge install + mod downloads on a fresh data dir)"
if [[ "$result" != "PASS" ]]; then
  echo "--- matching failure lines ---"; grep -nE "$FAIL_RE|ERROR|Exception" "$WORK/server.log" | head -40 || true
  echo "--- log tail ---"; tail -40 "$WORK/server.log"
  compgen -G "$DATA/crash-reports/*" >/dev/null && { echo "--- crash report ---"; head -60 "$DATA"/crash-reports/*; }
  exit 1
fi
