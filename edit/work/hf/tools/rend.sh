#!/bin/bash
# usage: rend.sh <comp> <fps> [quality]
cd /home/user/viral-video-creator/edit/work/hf
npx --yes hyperframes render . -c $1.html -o renders/$1_$2.mp4 -f $2 -q ${3:-delivery} --quiet 2>&1 | sed 's/\x1b\[[0-9;]*m//g' | grep -vE "^\[(initSession|HyperFrames)" | tail -5
