# REPORT (skrócony)
END: 40967 ms (40.967 s), 2458 klatek @60 fps, 1080x1920, H.264 + AAC 48 kHz stereo.
Wejście: input/1003_4.mp4 (Google Drive, 1003 (4).mp4), brak osobnego czystego audio -> użyto audio z filmu; offset sync nie dotyczy.
Pacing: brak pauz do skrócenia (ciągła mowa, LRA 1,8 LU); dodano 40 ms room-tone/hold na starcie, 90 ms naturalne wygaszenie końcówki. Kolejność i treść wypowiedzi bez zmian.
## Runy
|start|koniec|dł.|layout|treść|
|--|--|--|--|--|
|0.000|4.467|4.47|SPLIT|hook: Sonnet 5.5 vs Opus 5.5 (+ half price)|
|4.467|10.883|6.42|VISUAL|Terminal-Bench 4.0 table (70.6 / 66.4 / 10.3)|
|10.883|15.783|4.90|SPLIT|API price per 1M tokens: Sonnet 5.5 vs Opus 5.5|
|15.783|21.167|5.38|CAM|direct statement: 30% faster / 30% cheaper|
|21.167|24.800|3.63|VISUAL|strongest at: code, bugs, docs, slides, spreadsheets|
|24.800|28.983|4.18|CAM|Opus stays for heavy work; "nobody talks about it" + free test|
|28.983|31.283|2.30|SPLIT|Sonnet 5.5 on the Free plan (Claude app model picker)|
|31.283|38.150|6.87|VISUAL|ClipCash: account analysis, what blocks you, ready viral videos|
|38.150|40.967|2.82|CAM|outro / CTA: bio + type your nick|

## Fakty (źródła: anthropic.com/claude-sonnet-5-5, Decrypt, The Decoder, Unite.AI)
Terminal-Bench 4.0: Sonnet 5.5 70,6% / Opus 5.5 66,4% / Sonnet 5 10,3% (w filmie: 'Sonet 5' przy 10,3%). Ceny za 1 mln tokenów: Sonnet 5.5 2$/10$, Opus 5.5 4$/20$. Anthropic: 30%+ szybciej i do 30% taniej na zadanie. Zastrzeżenie: wynik 70,6% mierzony na poziomie Max vs Opus Xhigh; w FrontierCode 1.1 Opus 5.5 prowadzi (54,4% vs 46,2%); Anthropic: Opus nadal lepszy w złożonych zadaniach. Darmowy plan: wg źródeł wtórnych Sonnet 5.5 domyślny w Free (nie znalazłem tego na oficjalnej stronie).
## Grafiki
R1,R3,R5,R7: grafiki własne (rekonstrukcje); R2: rekonstrukcja tabeli z anthropic.com (dane prawdziwe); R8: rekonstrukcja strony clipcash.systemskala.pl z jej prawdziwych znaczników/CSS (maskotka Klip = oryginalne SVG). Zrzuty przeglądarką nie były możliwe (Chromium odrzucał certyfikat proxy; obejścia zablokowane).
## SFX
- 2.240s whoosh A
- 3.620s pop 
- 14.123s whoosh B
- 14.833s pop 
- 21.717s ticks 
- 29.783s click 
- 30.483s chime 
- 32.333s whoosh (soft logo reveal) C
- 39.980s key 
- 40.070s key 
- 40.160s key 
- 40.250s key 
- 40.340s key 
- 40.660s click 

## Głośność (ebur128)
master -14.0 LUFS / TP -0.6 dBTP; stemy: voice -14,0 / TP -1,1; sfx -24,6 / -10,9; riser -28,1 / -15,9; music -24,0 / -10,9.
## Uwagi / kompromisy
Bez pełnego QA klatka po klatce (ograniczony budżet). Rozmycie ruchu liczone analitycznie (nie 240 fps). Napis 'bio albo tutaj :) systemskala.pl' jest wypalony w materiale źródłowym i pozostał.
