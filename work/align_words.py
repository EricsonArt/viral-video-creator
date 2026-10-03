import json, sys, itertools, numpy as np
import ctc_forced_aligner as c
from ctc_forced_aligner import (ensure_onnx_model, MODEL_URL, generate_emissions, preprocess_text,
                                get_alignments, get_spans, postprocess_results, load_audio, Tokenizer)
import onnxruntime
MP = "models/mms_fa.onnx"
ensure_onnx_model(MP, MODEL_URL)
sess = onnxruntime.InferenceSession(MP)
tok = Tokenizer()
wav = load_audio("audio/src_16k.wav")
emis, stride = generate_emissions(sess, wav, batch_size=1)
print("emissions", emis.shape, "stride ms", stride, flush=True)

# (display, spoken)
D = [("Sonnet","sonet"),("5.5","{N}"),("jest","jest"),("lepszy","lepszy"),("w","w"),("kodowaniu","kodowaniu"),("niż","niż"),("Opus","opus"),("5.5","{N}"),
 ("Kosztuje","kosztuje"),("o","o"),("połowę","połowę"),("taniej.","taniej"),
 ("Ponad","ponad"),("70%","siedemdziesiąt procent"),("w","w"),("Terminal","terminal"),("Bench,","bench"),("a","a"),("Opus","opus"),("ma","ma"),("66,4%","sześćdziesiąt sześć przecinek cztery procent"),
 ("Dla","dla"),("porównania","porównania"),("Sonnet","sonet"),("5.5","{M}"),("miał","miał"),("tylko","tylko"),("10,3%","dziesięć przecinek trzy procent"),
 ("Cena","cena"),("bez","bez"),("porównania","porównania"),("$2","dwa dolary"),("za","za"),("input,","input"),("$10","dziesięć dolarów"),("za","za"),("output.","output"),
 ("To","to"),("połowa","połowa"),("tego","tego"),("co","co"),("kosztuje","kosztuje"),("Opus.","opus"),
 ("Plus","plus"),("generuje","generuje"),("output","output"),("o","o"),("30%","trzydzieści procent"),("szybciej","szybciej"),("i","i"),("o","o"),("30%","trzydzieści procent"),("taniej","taniej"),("na","na"),("zadanie,","zadanie"),("bo","bo"),("używa","używa"),("mniej","mniej"),("tokenów.","tokenów"),
 ("Najmocniejszy","najmocniejszy"),("jest","jest"),("w","w"),("kodowaniu,","kodowaniu"),("bugach,","bugach"),("dokumentach,","dokumentach"),("slajdach","slajdach"),("i","i"),("spreadsheetach.","spreadsheetach"),
 ("Opus","opus"),("zostaje","zostaje"),("do","do"),("ciężkich","ciężkich"),("zadań","zadań"),("i","i"),("uwaga,","uwaga"),("nikt","nikt"),("o","o"),("tym","tym"),("nie","nie"),("mówi,","mówi"),("ale","ale"),("możesz","możesz"),("to","to"),("przetestować","przetestować"),("za","za"),("darmo.","darmo"),
 ("Sonnet","sonet"),("5.5","{N}"),("jest","jest"),("również","również"),("dla","dla"),("darmowych","darmowych"),("planów,","planów"),("a","a"),("jeśli","jeśli"),("chcesz","chcesz"),("pełną","pełną"),("analizę","analizę"),("twojego","twojego"),("całego","całego"),("profilu,","profilu"),("chcesz","chcesz"),("wiedzieć","wiedzieć"),("co","co"),("cię","cię"),("blokuje","blokuje"),("i","i"),("chcesz","chcesz"),("gotowe","gotowe"),("viralowe","viralowe"),("filmiki","filmiki"),("na","na"),("podstawie","podstawie"),("tego","tego"),("co","co"),("już","już"),("działa","działa"),("w","w"),("twojej","twojej"),("niszy,","niszy"),("kompletnie","kompletnie"),("za","za"),("darmo,","darmo"),
 ("to","to"),("wejdź","wejdź"),("w","w"),("ich","ich"),("bio","bio"),("i","i"),("wpisz","wpisz"),("nick","nick"),("swojego","swojego"),("profilu.","profilu")]

NV = {"piec piec":"pięć pięć","piec i pol":"pięć i pół","piec przecinek piec":"pięć przecinek pięć","piec kropka piec":"pięć kropka pięć","piec(+5 short)":None}
def run(Nspoken, Mspoken):
    spoken=[]
    for disp,sp in D:
        sp = sp.replace("{N}",Nspoken).replace("{M}",Mspoken)
        spoken.append(sp)
    text=" ".join(spoken)
    tokens_starred, text_starred = preprocess_text(text, romanize=True, language="pol")
    segments, scores, blank = get_alignments(emis, tokens_starred, tok)
    spans = get_spans(tokens_starred, segments, blank)
    res = postprocess_results(text_starred, spans, stride, scores)
    total = sum(r["score"] for r in res)
    return res, total, spoken

best=None
N_opts = ["pięć pięć","pięć i pół","pięć przecinek pięć","pięć kropka pięć"]
M_opts = ["pięć","pięć pięć","pięć i pół"]
results=[]
for N in N_opts:
    res,total,sp = run(N,"pięć")
    results.append(("N="+N,total)); print("N=",N,"total",round(total,1),flush=True)
bestN = max(results,key=lambda x:x[1])[0][2:]
for M in M_opts:
    res,total,sp = run(bestN,M)
    print("M=",M,"total",round(total,1),flush=True)
    results.append(("M="+M,total))
bestM = max([r for r in results if r[0].startswith("M=")],key=lambda x:x[1])[0][2:]
res,total,sp = run(bestN,bestM)
print("BEST N=",bestN,"M=",bestM,round(total,1))
# map spoken-words back to display words
out=[]; ri=0
for (disp,_),s in zip(D,sp):
    n=len(s.split())
    chunk=res[ri:ri+n]; ri+=n
    out.append({"w":disp,"spoken":s,"s":round(chunk[0]["start"],3),"e":round(chunk[-1]["end"],3),"score":round(sum(x["score"] for x in chunk),2)})
assert ri==len(res), (ri,len(res))
json.dump({"N":bestN,"M":bestM,"words":out}, open("words_aligned.json","w"), ensure_ascii=False, indent=1)
for o in out: print(f'{o["s"]:6.2f} {o["e"]:6.2f}  {o["w"]:16s} ({o["spoken"]})  sc={o["score"]}')
