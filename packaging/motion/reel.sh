#!/bin/bash
# The titled reel: one shareable video of a review folder's recordings, each after a title card, 1280x720 at 60 a second.
# Each way's recording is <review>/<NN>-<way>-<variant>.mp4 (encode.sh's names, 07-race-1280-light.mp4), scaled down to
# fit 1160x440 under its title, held a moment at its start and its end.
#
# usage: packaging/motion/reel.sh --review <folder> --out <reel.mp4>
#          [--ways "01-spin:Spin 02-pong:Pong ..."]   (default: every <NN>-<way>-<variant>.mp4 there, the way's name capitalised)
#          [--variant 1280-light] [--title "Idiograph, Home mark"] [--crop "race:1400"]
# --crop keeps a way's recording to its left so many pixels first (the race's frame runs to the window's right edge).
# Needs ffmpeg, ffprobe and rsvg-convert.
set -e
REVIEW=""; OUT=""; WAYS=""; VARIANT="1280-light"; TITLE="Idiograph, Home mark"; CROPS="race:1400"
usage() { sed -n '4,8p' "$0" | sed 's/^# \{0,1\}//' >&2; exit 2; }
while [ $# -gt 0 ]; do
  case "$1" in
    --review) REVIEW=$2; shift 2 ;;
    --out) OUT=$2; shift 2 ;;
    --ways) WAYS=$2; shift 2 ;;
    --variant) VARIANT=$2; shift 2 ;;
    --title) TITLE=$2; shift 2 ;;
    --crop) CROPS=$2; shift 2 ;;
    *) usage ;;
  esac
done
[ -n "$REVIEW" ] && [ -n "$OUT" ] && [ -d "$REVIEW" ] || usage
if [ -z "$WAYS" ]; then
  for f in "$REVIEW"/[0-9][0-9]-*-"$VARIANT".mp4; do
    [ -e "$f" ] || continue
    b=$(basename "$f" "-$VARIANT.mp4"); w=${b#*-}
    WAYS="$WAYS $b:$(printf '%s' "${w:0:1}" | tr '[:lower:]' '[:upper:]')${w:1}"
  done
fi
[ -n "$WAYS" ] || { echo "no <NN>-<way>-$VARIANT.mp4 in $REVIEW" >&2; exit 1; }
case "$VARIANT" in
  *dark*) BG="#211d18"; SOFT="#a59d90"; INK="#ece6da" ;;
  *) BG="#faf7ef"; SOFT="#8a8578"; INK="#2b2a26" ;;
esac
TMP=$(mktemp -d "${TMPDIR:-/tmp}/idiograph-reel.XXXXXX")
trap 'rm -rf "$TMP"' EXIT
mkdir -p "$(dirname "$OUT")"
: > "$TMP/list.txt"
i=0; n=$(echo $WAYS | wc -w | tr -d ' ')
for pair in $WAYS; do
  i=$((i+1)); f="${pair%%:*}"; name="${pair#*:}"; name=${name//_/ }; way=${f#*-}
  src="$REVIEW/$f-$VARIANT.mp4"
  [ -f "$src" ] || { echo "no $src" >&2; exit 1; }
  CROP=""
  for c in $CROPS; do [ "${c%%:*}" = "$way" ] && CROP="crop='min(iw,${c#*:})':ih:0:0,"; done
  cat > "$TMP/t$i.svg" <<SVG
<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720"><rect width="1280" height="720" fill="$BG"/>
<text x="640" y="72" font-family="Georgia" font-size="22" fill="$SOFT" text-anchor="middle">$TITLE</text>
<text x="640" y="132" font-family="Georgia" font-size="48" fill="$INK" text-anchor="middle">$i  $name</text></svg>
SVG
  rsvg-convert "$TMP/t$i.svg" -o "$TMP/t$i.png"
  ffmpeg -v error -y -i "$src" -loop 1 -i "$TMP/t$i.png" -filter_complex "\
    [0:v]${CROP}scale=w='min(1160,iw)':h='min(440,ih)':force_original_aspect_ratio=decrease,tpad=start_mode=clone:start_duration=0.4:stop_mode=clone:stop_duration=1.0[a];\
    [1:v]fps=60,format=rgb24[bg];\
    [bg][a]overlay=x=(W-w)/2:y=(H-h)/2+50:shortest=1,format=yuv420p[v]" -map "[v]" -c:v libx264 -crf 22 -preset medium -r 60 "$TMP/seg$i.mp4"
  echo "file '$TMP/seg$i.mp4'" >> "$TMP/list.txt"
  echo "$i of $n: $name ($f)"
done
ffmpeg -v error -y -f concat -safe 0 -i "$TMP/list.txt" -c copy -movflags +faststart "$OUT"
echo "$OUT $(ffprobe -v error -show_entries format=duration,size -of csv=p=0 "$OUT" | awk -F, '{printf "%.1f s, %d KB", $1, $2/1024}')"
