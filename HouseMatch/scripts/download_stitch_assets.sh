#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   ./scripts/download_stitch_assets.sh <url1> [url2 ...]
# Example:
#   ./scripts/download_stitch_assets.sh \
#     "https://.../screen-code.zip" \
#     "https://.../preview.png"

PROJECT_ID="17586284210553657525"
SCREEN_ID="d069d8f822cd4822b7479018d72c7c14"
OUT_DIR="stitch_assets/${PROJECT_ID}/${SCREEN_ID}"

if [ "$#" -lt 1 ]; then
  echo "Provide at least one hosted Stitch URL." >&2
  exit 1
fi

mkdir -p "$OUT_DIR"

for url in "$@"; do
  file_name="$(basename "${url%%\?*}")"
  [ -z "$file_name" ] && file_name="asset_$(date +%s).bin"
  echo "Downloading: $url"
  curl -L "$url" -o "$OUT_DIR/$file_name"
  echo "Saved: $OUT_DIR/$file_name"
done
