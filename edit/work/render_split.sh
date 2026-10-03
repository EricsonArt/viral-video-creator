#!/bin/bash
cd /home/user/viral-video-creator/edit/work
for r in r1 r5; do
  s=$(date +%s)
  npx hyperframes render hf/$r -f 240 --crf 12 -o hf/out/${r}_240.mp4 > hf/out/${r}_render.log 2>&1
  echo "$r re-rendered $(( $(date +%s)-s ))s" >> hf/out/progress2.log
done
echo ALLDONE >> hf/out/progress2.log
