#!/bin/bash
set -e
# source frame ranges (30fps) for SPLIT runs: name start_frame count
for spec in "r01 0 130" "r04 395 105" "r08 757 84" "r12 1123 184"; do
  set -- $spec
  ffmpeg -hide_banner -loglevel error -y -i ../../input/0930.mp4 -vf "select='between(n\,$2\,$(($2+$3-1)))',setpts=N/30/TB" -an -r 30 -c:v libx264 -crf 6 -preset veryfast $1_src.mp4
  echo "$1 frames: $(ffprobe -v error -count_frames -select_streams v:0 -show_entries stream=nb_read_frames -of csv=p=0 $1_src.mp4)"
  npx --yes hyperframes remove-background $1_src.mp4 -o $1_matte.webm --quality best > $1.log 2>&1
  echo "$1 done"
done
echo ALLDONE
