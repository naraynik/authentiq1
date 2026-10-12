#!/bin/sh
# Shrinks the original downloads into web-ready files in public/media/.
# Usage (from frontend/):  sh scripts/prepare-media.sh <folder with the originals>
# Needs ffmpeg. Videos: H.264, no sound, starts playing before fully downloaded.
set -e
SRC="${1:?folder with hero.mp4, packing.mp4, ... }"
OUT=public/media
mkdir -p "$OUT"
for v in hero packing scanning; do
  W=960; [ "$v" = hero ] && W=1280
  ffmpeg -y -loglevel error -i "$SRC/$v.mp4" -t 20 -an -vf "scale=$W:-2,fps=25" \
    -c:v libx264 -preset slow -crf 28 -pix_fmt yuv420p -movflags +faststart "$OUT/$v.mp4"
  # WebM (VP9) copy for browsers without H.264 (e.g. some Linux Chromium builds)
  ffmpeg -y -loglevel error -i "$OUT/$v.mp4" -an -c:v libvpx-vp9 -b:v 0 -crf 40 -row-mt 1 -deadline good -cpu-used 4 "$OUT/$v.webm"
  ffmpeg -y -loglevel error -ss 0.5 -i "$OUT/$v.mp4" -frames:v 1 -q:v 4 "$OUT/$v-poster.jpg"
done
for p in cloned-codes distributor record scan-report check-product protect-products; do
  f=$(ls "$SRC/$p".* 2>/dev/null | head -1)
  ffmpeg -y -loglevel error -i "$f" -vf "scale='min(1200,iw)':-2" -q:v 5 "$OUT/$p.jpg"
done
ls -la "$OUT"
