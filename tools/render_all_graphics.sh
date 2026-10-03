#!/bin/bash
# Re-render every graphic run with the final kit (dithered ground), high quality, exact frame counts verified against plan.json
cd /home/user/viral-video-creator/hf && source env.sh
for r in "$@"; do
  frames=$(python3 -c "import json;print([x['frames'] for x in json.load(open('../work/plan.json'))['runs'] if x['id']=='$r'][0])")
  npx --no-install hyperframes render . -c runs/$r.html -o renders/$r.mp4 -f 60 -q high --crf 10 -w 4 --quiet 2>&1 | tail -2
  n=$(ffprobe -v error -count_frames -select_streams v:0 -show_entries stream=nb_read_frames -of csv=p=0 renders/$r.mp4)
  echo "$r frames=$n expected=$frames $([ "$n" = "$frames" ] && echo OK || echo MISMATCH)"
done
