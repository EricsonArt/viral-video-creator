#!/bin/bash
# Background removal for every SPLIT run (source frame ranges incl. safety margin). 30 fps source frames, inclusive.
cd /home/user/viral-video-creator
export HYPERFRAMES_NO_TELEMETRY=1
declare -A SEG=( [s01]="0 97" [s04]="255 355" [s07]="513 654" [s13]="1362 1434" [s16]="1614 1770" )
for k in s01 s04 s07 s13 s16; do
  read a b <<< "${SEG[$k]}"
  n=$((b-a+1))
  ffmpeg -v error -y -i "input/1003 (2).mp4" -vf "select='between(n,$a,$b)',setpts=N/30/TB" -vsync 0 -an -c:v libx264 -crf 8 -preset fast -pix_fmt yuv420p work/cut/$k.mp4
  echo "[$k] frames $a-$b ($n) extracted: $(ffprobe -v error -count_frames -select_streams v:0 -show_entries stream=nb_read_frames -of csv=p=0 work/cut/$k.mp4)"
  (cd hf && npx --no-install hyperframes remove-background ../work/cut/$k.mp4 -o ../work/cut/${k}_alpha.webm --quality best --json) 2>&1 | tail -2
done
echo ALLDONE
