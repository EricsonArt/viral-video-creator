#!/bin/bash
# ffmpeg ebur128: integrated loudness + true peak for each file
for f in "$@"; do
  r=$(/home/user/viral-video-creator/bin/ffmpeg -hide_banner -nostats -i "$f" -af ebur128=peak=true -f null - 2>&1 | grep -A20 Summary)
  I=$(echo "$r" | grep " I:" | awk '{print $2}')
  TP=$(echo "$r" | grep "Peak:" | tail -1 | awk '{print $2}')
  echo "$(basename $f): I=$I LUFS  TP=$TP dBTP"
done
