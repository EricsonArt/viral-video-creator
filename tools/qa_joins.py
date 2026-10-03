"""QA: frames on BOTH sides of every cut (f-2, f-1 | f, f+1) -> work/qa_joins.png ; and whole-video contact sheet -> work/qa_sheet_*.png"""
import json, subprocess, sys
video = sys.argv[1] if len(sys.argv) > 1 else "edit/final.mp4"
plan = json.load(open("work/plan.json")); runs = plan["runs"]
cuts = [r["out_f0"] for r in runs[1:]]
idx = []
for c in cuts: idx += [c - 2, c - 1, c, c + 1]
sel = "+".join(f"eq(n\\,{i})" for i in idx)
cols = 8; rows = (len(idx) + cols - 1) // cols
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", video, "-vf", f"select='{sel}',scale=216:384,tile={cols}x{rows}", "-frames:v", "1", "work/qa_joins.png"], check=True)
print("cuts at output frames:", cuts)
# whole-video sheet: 1 frame / 0.5 s => 120 frames, 3 sheets of 40
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", video, "-vf", "fps=2,scale=216:384,tile=10x4", "-frames:v", "3", "work/qa_sheet_%d.png"], check=True)
print("done")
