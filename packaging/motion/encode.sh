#!/bin/zsh
# Encodes one recording's frames (rec.mjs's f0000.png on) as an mp4 at real speed and one at half speed, the frame
# rate read from its meta.json (60 when there is none).
# usage: packaging/motion/encode.sh <recording folder> <out-base>   (writes <out-base>.mp4 and <out-base>-half.mp4)
in=$1; out=$2
if [[ -z $in || -z $out || ! -f $in/f0000.png ]]; then print -u2 "usage: encode.sh <recording folder with f0000.png on> <out-base>"; exit 2; fi
fps=60
[[ -f $in/meta.json ]] && fps=$(sed -nE 's/.*"fps":([0-9.]+).*/\1/p' $in/meta.json)
[[ -z $fps ]] && fps=60
vf="pad=ceil(iw/2)*2:ceil(ih/2)*2,format=yuv420p"
ffmpeg -loglevel error -y -framerate $fps -i $in/f%04d.png -vf "$vf" -c:v libx264 -crf 14 -preset slow -movflags +faststart $out.mp4 || exit 1
ffmpeg -loglevel error -y -framerate $((fps / 2.0)) -i $in/f%04d.png -vf "$vf,fps=$fps" -c:v libx264 -crf 14 -preset slow -movflags +faststart $out-half.mp4 || exit 1
for f in $out.mp4 $out-half.mp4; do print "$f $(ffprobe -v error -show_entries format=duration -of csv=p=0 $f) s"; done
