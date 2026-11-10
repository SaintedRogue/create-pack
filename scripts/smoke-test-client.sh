#!/usr/bin/env bash
# End-to-end test: boot the pack's SERVER, install the CLIENT side exactly like the Prism
# pre-launch hook does (packwiz-installer-bootstrap -s client), launch a real NeoForge client
# on a virtual display (Xvfb + Mesa software GL), and have it join the server.
#
# PASS = the server logs "<user> joined the game" and neither side crashes for SOAK seconds after.
# This is the only test that exercises client-only mods (Sodium, Iris, ImmediatelyFast,
# Entity Culling) against Create's renderer, and client<->server mod/registry agreement.
#
# Usage: scripts/smoke-test-client.sh [--keep] [--timeout SECONDS] [--soak SECONDS]
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PACK_DIR="$REPO_ROOT/pack"
SERVER_IMAGE="${SERVER_IMAGE:-docker.io/itzg/minecraft-server:java21}"
WEB_IMAGE="${WEB_IMAGE:-docker.io/library/busybox:stable}"
CLIENT_IMAGE="create-pack-clienttest:local"
BOOTSTRAP_URL="https://github.com/packwiz/packwiz-installer-bootstrap/releases/download/v0.0.3/packwiz-installer-bootstrap.jar"
BOOTSTRAP_SHA256="a8fbb24dc604278e97f4688e82d3d91a318b98efc08d5dbfcbcbcab6443d116c"
TIMEOUT=1200; SOAK=45; KEEP=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --keep) KEEP=1 ;;
    --timeout) TIMEOUT="$2"; shift ;;
    --soak) SOAK="$2"; shift ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
  shift
done

MC_VERSION="$(sed -n 's/^minecraft = "\(.*\)"/\1/p' "$PACK_DIR/pack.toml")"
NEOFORGE_VERSION="$(sed -n 's/^neoforge = "\(.*\)"/\1/p' "$PACK_DIR/pack.toml")"
command -v packwiz >/dev/null && (cd "$PACK_DIR" && packwiz refresh >/dev/null)

# All three containers use --network host = rootlesskit's shared netns (see smoke-test-server.sh).
WEB_PORT=8766; GAME_PORT=25599; USERNAME="SmokeKid"
WORK="$(mktemp -d "${TMPDIR:-/tmp}/create-pack-client.XXXXXX")"
mkdir -p "$WORK/server" "$WORK/client/mc" "$WORK/client/pmc"
TAG="create-pack-c$$"
cleanup() {
  docker rm -f "$TAG-client" "$TAG-server" "$TAG-web" >/dev/null 2>&1 || true
  if [[ $KEEP -eq 1 ]]; then echo "kept: $WORK"; else rm -rf "$WORK"; fi
}
trap cleanup EXIT

if ! docker image inspect "$CLIENT_IMAGE" >/dev/null 2>&1; then
  echo "building $CLIENT_IMAGE (one-time, several minutes)..."
  docker build --network host -q -t "$CLIENT_IMAGE" "$REPO_ROOT/scripts/clienttest" >/dev/null
fi
curl -sfL --max-time 60 -o "$WORK/client/mc/packwiz-installer-bootstrap.jar" "$BOOTSTRAP_URL"
echo "$BOOTSTRAP_SHA256  $WORK/client/mc/packwiz-installer-bootstrap.jar" | sha256sum -c --quiet

echo "client e2e: MC $MC_VERSION / NeoForge $NEOFORGE_VERSION / timeout ${TIMEOUT}s / soak ${SOAK}s"
START=$(date +%s)
docker run -d --name "$TAG-web" --network host -v "$PACK_DIR:/pack:ro" "$WEB_IMAGE" \
  httpd -f -p "127.0.0.1:$WEB_PORT" -h /pack >/dev/null
docker run -d --name "$TAG-server" --network host \
  -e EULA=TRUE -e TYPE=NEOFORGE -e VERSION="$MC_VERSION" -e NEOFORGE_VERSION="$NEOFORGE_VERSION" \
  -e PACKWIZ_URL="http://127.0.0.1:$WEB_PORT/pack.toml" -e MEMORY=6G -e ONLINE_MODE=FALSE \
  -e SERVER_PORT="$GAME_PORT" -e UID=0 -e GID=0 -e ENABLE_RCON=FALSE \
  -v "$WORK/server:/data" "$SERVER_IMAGE" >/dev/null

# Client: same install path as the Prism pre-launch hook, then launch and auto-join.
# Xvfb is started directly (not via xvfb-run): xvfb-run waits for Xvfb's SIGUSR1 "ready" signal,
# which gets lost when it runs as the container's PID 1, so it hangs forever. --init adds tini as PID 1.
# The display number is unique per run: all containers share rootlesskit's netns, and X's abstract
# sockets live in the network namespace.
DISPLAY_NUM=$(( 100 + $$ % 800 ))
docker run -d --init --name "$TAG-client" --network host -e LIBGL_ALWAYS_SOFTWARE=1 \
  -v "$WORK/client:/work" "$CLIENT_IMAGE" bash -c "
    set -e
    cd /work/mc
    java -jar packwiz-installer-bootstrap.jar -g -s client http://127.0.0.1:$WEB_PORT/pack.toml
    echo '== waiting for server port'
    for i in \$(seq 1 300); do (exec 3<>/dev/tcp/127.0.0.1/$GAME_PORT) 2>/dev/null && break; sleep 2; done
    echo '== starting Xvfb :$DISPLAY_NUM'
    Xvfb :$DISPLAY_NUM -screen 0 1280x720x24 -nolisten tcp >/work/xvfb.log 2>&1 &
    export DISPLAY=:$DISPLAY_NUM
    for i in \$(seq 1 30); do [ -e /tmp/.X11-unix/X$DISPLAY_NUM ] && break; sleep 1; done
    echo '== launching client'
    exec portablemc --main-dir /work/pmc \
      start --mc-dir /work/mc neoforge::$NEOFORGE_VERSION -u $USERNAME --jvm-arg=-Xmx4G \
      --join-server 127.0.0.1 --join-server-port $GAME_PORT
  " >/dev/null

FAIL_RE='Missing or unsupported mandatory dependencies|Mixin apply failed|MixinApplyError|MixinTransformerError|Failed to create mod instance|ModLoadingException|Crash report saved|This crash report has been saved|Game crashed|Mismatched mod channel|Incompatible client|Disconnected from server|lost connection'
result="TIMEOUT"; joined_at=0
while (( $(date +%s) - START < TIMEOUT )); do
  slog="$(docker logs "$TAG-server" 2>&1 || true)"; clog="$(docker logs "$TAG-client" 2>&1 || true)"
  if grep -qE "$FAIL_RE" <<<"$slog$clog" \
     || compgen -G "$WORK/server/crash-reports/*" >/dev/null || compgen -G "$WORK/client/mc/crash-reports/*" >/dev/null; then
    result="FAIL"; break
  fi
  if [[ $joined_at -eq 0 ]] && grep -qE "$USERNAME joined the game" <<<"$slog"; then
    joined_at=$(date +%s); echo "joined after $((joined_at - START))s; soaking ${SOAK}s..."
  fi
  if [[ $joined_at -gt 0 ]] && (( $(date +%s) - joined_at >= SOAK )); then result="PASS"; break; fi
  for c in server client; do
    if [[ "$(docker inspect -f '{{.State.Running}}' "$TAG-$c" 2>/dev/null)" != "true" ]]; then result="EXITED ($c)"; break 2; fi
  done
  sleep 3
done

docker logs "$TAG-server" >"$WORK/server.log" 2>&1 || true
docker logs "$TAG-client" >"$WORK/client.log" 2>&1 || true
CLIENT_MODS=$(find "$WORK/client/mc/mods" -maxdepth 1 -name '*.jar' 2>/dev/null | wc -l)
SERVER_MODS=$(find "$WORK/server/mods" -maxdepth 1 -name '*.jar' 2>/dev/null | wc -l)
echo "result:       $result"
echo "mod jars:     client $CLIENT_MODS / server $SERVER_MODS"
echo "elapsed:      $(( $(date +%s) - START ))s"
grep -m1 -oE "OpenGL: .{0,90}|GL_RENDERER.{0,60}|Renderer: .{0,60}" "$WORK/client/mc/logs/latest.log" 2>/dev/null || true
if [[ "$result" != "PASS" ]]; then
  echo "--- failure lines ---"; grep -nhE "$FAIL_RE" "$WORK/server.log" "$WORK/client.log" "$WORK/client/mc/logs/latest.log" 2>/dev/null | head -30 || true
  echo "--- client log tail ---"; tail -40 "$WORK/client.log"
  for f in "$WORK"/server/crash-reports/* "$WORK"/client/mc/crash-reports/*; do [[ -e "$f" ]] && { echo "--- $f"; head -50 "$f"; }; done
  exit 1
fi
