#!/usr/bin/env bash
# Export the pack as Modrinth .mrpack files for first-time client installs (Prism "Import").
#
#   dist/<name>-<ver>.mrpack         FULL. packwiz bundles CurseForge-only mods (the FTB mods)
#                                     as jars under overrides/, because the .mrpack format can't
#                                     link to CurseForge. FTB's mods aren't openly licensed, so
#                                     this file is PRIVATE: never commit or publish it.
#   dist/<name>-<ver>-public.mrpack  PUBLIC. Same pack with those bundled jars stripped. Safe to
#                                     attach to a GitHub release; the Prism pre-launch hook
#                                     (packwiz-installer) fetches the FTB mods from CurseForge on
#                                     first launch.
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT/pack"
VERSION="$(sed -n 's/^version = "\(.*\)"/\1/p' pack.toml)"
NAME="$(sed -n 's/^name = "\(.*\)"/\1/p' pack.toml | tr ' ' '-')"
packwiz refresh >/dev/null
mkdir -p "$REPO_ROOT/dist"
FULL="$REPO_ROOT/dist/${NAME}-${VERSION}.mrpack"
PUBLIC="$REPO_ROOT/dist/${NAME}-${VERSION}-public.mrpack"
packwiz modrinth export -o "$FULL" | grep -E "added to zip|Modpack exported|Warning|Error" || true

python3 -I - "$FULL" "$PUBLIC" <<'EOF'
import sys, zipfile
src, dst = sys.argv[1], sys.argv[2]
with zipfile.ZipFile(src) as zin, zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zout:
    for item in zin.infolist():
        if item.filename.startswith("overrides/mods/") and item.filename.endswith(".jar"):
            print(f"  public: stripped {item.filename}")
            continue
        zout.writestr(item, zin.read(item.filename))
EOF
# Unversioned copy: CLIENT-SETUP.md links to releases/latest/download/<NAME>-public.mrpack,
# so that link never has to change between versions.
cp "$PUBLIC" "$REPO_ROOT/dist/${NAME}-public.mrpack"
sha256sum "$FULL" "$PUBLIC" | tee "$REPO_ROOT/dist/${NAME}-${VERSION}.sha256"
