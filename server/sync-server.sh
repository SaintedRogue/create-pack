#!/usr/bin/env bash
# Sync the AMP Minecraft instance to the published pack. Idempotent: safe to run any time.
#
#   1. stop the Minecraft app (AMP keeps the instance process itself running)
#   2. make sure AMP has the NeoForge version pack.toml asks for (runs AMP's updater only on change)
#   3. run packwiz-installer (server side) inside the AMP container, in the instance's Minecraft dir
#   4. first run only: apply server/amp-settings.json, the nightly backup schedule, seed whitelist.json
#   5. start the app and wait for Ready
#
# Runs from any Linux box with: python3, ssh key access to the Unraid host, and LAN access to AMP.
# Usage: server/sync-server.sh [--reapply-settings] [--no-start]
# Env overrides: INSTANCE, PACK_URL, UNRAID, SSH_KEY, AMP_CONTAINER, AMP_URL (see amp_api.py)
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTANCE="${INSTANCE:-CreateMC01}"
PACK_URL="${PACK_URL:-https://raw.githubusercontent.com/SaintedRogue/create-pack/release/pack/pack.toml}"
UNRAID="${UNRAID:-root@10.0.0.2}"
SSH_KEY="${SSH_KEY:-$HOME/.ssh/unraid_ed25519}"
AMP_CONTAINER="${AMP_CONTAINER:-AMP}"
export UNRAID SSH_KEY AMP_CONTAINER

# Paths: inside the AMP container vs. on the Unraid host (appdata bind mount).
MC_IN="/home/amp/.ampdata/instances/$INSTANCE/Minecraft"
MC_HOST="/mnt/user/appdata/amp/.ampdata/instances/$INSTANCE/Minecraft"
JAVA21="/usr/lib/jvm/temurin-21-jdk-amd64/bin/java"
AMP_UID="1000:1000"     # amp-dockerized runs AMP as uid/gid 1000; everything in the instance must stay owned by it
BOOTSTRAP_URL="https://github.com/packwiz/packwiz-installer-bootstrap/releases/download/v0.0.3/packwiz-installer-bootstrap.jar"
BOOTSTRAP_SHA256="a8fbb24dc604278e97f4688e82d3d91a318b98efc08d5dbfcbcbcab6443d116c"
MARKER=".create-pack-initialized"

REAPPLY=0; START=1
for a in "$@"; do
  case "$a" in
    --reapply-settings) REAPPLY=1 ;;
    --no-start) START=0 ;;
    *) echo "unknown arg: $a" >&2; exit 2 ;;
  esac
done

amp() { python3 -I "$HERE/amp_api.py" "$@"; }
remote() { ssh -i "$SSH_KEY" -o BatchMode=yes "$UNRAID" "$@"; }

echo "== sync $INSTANCE <- $PACK_URL"
PACK_TOML="$(curl -sfL --max-time 30 "$PACK_URL")" || { echo "cannot fetch $PACK_URL" >&2; exit 1; }
NEOFORGE="$(sed -n 's/^neoforge = "\(.*\)"/\1/p' <<<"$PACK_TOML")"
PACK_VERSION="$(sed -n 's/^version = "\(.*\)"/\1/p' <<<"$PACK_TOML")"
echo "   pack $PACK_VERSION, NeoForge $NEOFORGE"

echo "== 1/5 stopping app"
amp stop "$INSTANCE"

echo "== 2/5 NeoForge"
amp neoforge "$INSTANCE" "$NEOFORGE"

echo "== 3/5 packwiz-installer (server side)"
remote bash -s -- "$MC_HOST" "$BOOTSTRAP_URL" "$BOOTSTRAP_SHA256" <<'EOS'
set -euo pipefail
mc="$1"; url="$2"; sha="$3"; jar="$mc/packwiz-installer-bootstrap.jar"
mkdir -p "$mc"
if ! echo "$sha  $jar" | sha256sum -c --quiet 2>/dev/null; then
  curl -sfL --max-time 60 -o "$jar.tmp" "$url"
  echo "$sha  $jar.tmp" | sha256sum -c --quiet
  mv "$jar.tmp" "$jar"
fi
chown 1000:1000 "$mc" "$jar"
EOS
remote docker exec -u "$AMP_UID" -w "$MC_IN" "$AMP_CONTAINER" \
  "$JAVA21" -jar packwiz-installer-bootstrap.jar -g -s server "$PACK_URL" 2>&1 \
  | grep -v -E "^\s*$" | tail -25

echo "== 4/5 first-run settings"
if [[ $REAPPLY -eq 1 ]] || ! remote test -e "$MC_HOST/$MARKER"; then
  amp settings "$INSTANCE" "$HERE/amp-settings.json"
  amp schedule "$INSTANCE"
  # Seed the whitelist only if the server has none yet; never clobber names added since.
  if ! remote test -e "$MC_HOST/whitelist.json"; then
    remote "cat > '$MC_HOST/whitelist.json' && chown $AMP_UID '$MC_HOST/whitelist.json'" < "$HERE/whitelist.json.template"
  fi
  remote "touch '$MC_HOST/$MARKER' && chown $AMP_UID '$MC_HOST/$MARKER'"
else
  echo "   already initialized (use --reapply-settings to force)"
fi

if [[ $START -eq 1 ]]; then
  echo "== 5/5 starting"
  START_TIMEOUT=900 amp start "$INSTANCE"
fi
echo "== done: $INSTANCE on pack $PACK_VERSION"
