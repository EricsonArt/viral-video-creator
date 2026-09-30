#!/bin/bash
# preview.sh comp fps -> draft render + contact sheet
comp=$1; fps=${2:-10}
cd /home/user/viral-video-creator/work/hf/viz
export PATH=/home/user/viral-video-creator/bin:$PATH
npx --yes hyperframes render -c compositions/$comp.html -f $fps -q draft -o renders/prev_$comp.mp4 . > renders/prev_$comp.log 2>&1 || { tail -30 renders/prev_$comp.log; exit 1; }
grep -iE "warn|error" renders/prev_$comp.log | grep -v "Render:trace" | head -10
cd /home/user/viral-video-creator && source .venv/bin/activate
dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 work/hf/viz/renders/prev_$comp.mp4)
python work/sheet.py work/hf/viz/renders/prev_$comp.mp4 /tmp/claude-0/-home-user-viral-video-creator/68d46a39-f958-5d2b-9eee-d78e3b4e8f43/scratchpad/probe/prev_$comp.jpg 0 $dur ${3:-0.3} - 6 240
