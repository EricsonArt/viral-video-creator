#!/bin/bash
cd /home/user/viral-video-creator/edit/work
for r in r1 r2 r7; do
  s=$(date +%s)
  npx hyperframes render hf/$r -f 240 --crf 12 -o hf/out/${r}_240.mp4 > hf/out/${r}_render.log 2>&1
  echo "$r fixed $(( $(date +%s)-s ))s" >> hf/out/progress3.log
done
cd /home/user/viral-video-creator/edit/work
/home/user/viral-video-creator/.venv/bin/python compose.py --video final_video_src.mp4 --audio master_mix.wav > compose_run.log 2>&1
echo COMPOSED >> hf/out/progress3.log
ffmpeg -v error -y -i final_video_src.mp4 -i master_mix.wav -map 0:v:0 -map 1:a:0 -c:v copy -c:a aac -b:a 256k -ar 48000 -ac 2 -movflags +faststart -t 41.2 ../final.mp4
echo ALLDONE >> hf/out/progress3.log
