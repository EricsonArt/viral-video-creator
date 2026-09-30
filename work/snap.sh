#!/bin/bash
# snap.sh comp times outdir -> renders snapshots and a tiled sheet
comp=$1; times=$2; out=$3
cd /home/user/viral-video-creator/work/hf/viz
rm -rf "$out"; mkdir -p "$out"
npx --yes hyperframes snapshot -c compositions/$comp.html --at "$times" --no-end -o "$out" . > "$out/log.txt" 2>&1 || { tail -20 "$out/log.txt"; exit 1; }
ls "$out"
