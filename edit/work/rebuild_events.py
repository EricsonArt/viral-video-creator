import json
import gen_hf, gen_hf2
for fn in (gen_hf.gen_r1, gen_hf2.gen_r2, gen_hf2.gen_r4, gen_hf2.gen_r5, gen_hf2.gen_r7, gen_hf2.gen_cta):
    fn()
json.dump(gen_hf.EVENTS, open('hf_events.json','w'), indent=1)
print({k:(len(v) if isinstance(v,list) else v) for k,v in gen_hf.EVENTS.items()})
