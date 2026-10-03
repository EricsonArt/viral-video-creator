#!/bin/bash
cd /home/user/viral-video-creator/edit/work
for r in r1 r4 r2 r5 r7; do
  s=$(date +%s)
  npx hyperframes render hf/$r -f 240 --crf 12 -o hf/out/${r}_240.mp4 > hf/out/${r}_render.log 2>&1
  echo "$r done $(( $(date +%s)-s ))s" >> hf/out/progress.log
done
# CTA overlay: transparent PNG sequence at 60 fps
npx hyperframes render hf/cta -f 60 --format png-sequence -o hf/out/cta_png > hf/out/cta_render.log 2>&1
echo "cta done" >> hf/out/progress.log
echo ALLDONE >> hf/out/progress.log
