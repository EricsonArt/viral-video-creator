#!/bin/bash
cd /home/user/viral-video-creator/edit/work/hf
for c in "$@"; do
  echo "== $c $(date +%T)"
  npx --yes hyperframes render . -c $c.html -o renders/${c}_240.mp4 -f 240 -q delivery --quiet 2>&1 | sed 's/\x1b\[[0-9;]*m//g' | grep -vE "^\[(initSession|HyperFrames|BrowserManager)" | tail -3
  ffprobe -v error -show_entries stream=nb_frames,duration -of csv=p=0 renders/${c}_240.mp4
done
echo "ALL DONE $(date +%T)"
