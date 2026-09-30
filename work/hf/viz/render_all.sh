#!/bin/bash
export PATH=/home/user/viral-video-creator/bin:$PATH
cd /home/user/viral-video-creator/work/hf/viz
for c in ${@:-r01 r03 r04 r06 r08 r09 r11 r12}; do
  s=$(date +%s)
  npx --yes hyperframes render -c compositions/$c.html -f 240 -q high --crf 12 -o renders/${c}_240.mp4 . > renders/${c}_240.log 2>&1
  rc=$?
  n=$(ffprobe -v error -count_packets -select_streams v:0 -show_entries stream=nb_read_packets -of csv=p=0 renders/${c}_240.mp4 2>/dev/null)
  echo "$c rc=$rc frames=$n secs=$(( $(date +%s)-s ))"
done
echo RENDERDONE
