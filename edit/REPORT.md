# REPORT - edycja shorta (Źle używasz czata GPT)

## 1. Długość finalna
- END = **39 733 ms** (39,733 s) = 2384 klatki @ 60 fps.

## 2. Obsługa wejścia
- Źródło: `1003 (3).mp4` z Dysku Google (1080x1920, 30 fps, 39,8 s, AAC 44,1 kHz).
- Osobnego czystego audio **nie było** -> użyto audio z filmu (offset synchronizacji: nie dotyczy).
- Transkrypcja słów: faster-whisper large-v3 (HyperFrames transcribe wymaga whisper-cpp, którego brak w środowisku).
- Struktura wypowiedzi (19 zdań) i kolejność **nie zostały zmienione**; nie wybierano ujęć.
- Eye contact: Face Landmarker (irysy + poza głowy) na wszystkich 1194 klatkach - wzrok stale w obiektyw; tylko 3 krótkie zwroty głowy (<=0,27 s: ~5,07 s, ~28,6 s, 37,0-37,2 s), więc bez cut-awayów.

## 3. Edycje tempa
- Obcięto 66,7 ms (2 klatki) przed pierwszym słowem (początek głosu ~100 ms -> ~33 ms zapasu).
- Wewnętrzne pauzy: najdłuższy cichy odcinek ~190 ms (wewnątrz frazy), żadna nie przekracza 250 ms -> **nic nie skracano**; nie wstawiano ciszy.
- Koniec głosu: ostatnie 60 ms łagodnie wygaszone; END = ostatnia klatka materiału.
- Cięcia obrazu między runami wypadają ~50 ms po początku zdania (audio wyprzedza obraz = J-cut).

## 4. Runy układów
| start (s) | koniec (s) | czas (s) | układ | pokazane | powód |
|---|---|---|---|---|---|
| 0.000 | 4.933 | 4.933 | SPLIT | ChatGPT: logo -> okno czatu, prompt „Daj mi 10 pomysłów…”, generyczna odpowiedź + czerwony ✕ | Hook = SPLIT wg specyfikacji; pokazuje „kiepskie podejście” |
| 4.933 | 7.900 | 2.967 | CAM | Kamera (bez grafiki) | Bezpośrednia obietnica do kamery; pod spodem riser |
| 7.900 | 12.483 | 4.583 | VISUAL | Logo YouTube (wektor z youtube.com) -> nagłówek YouTube (real) + własna karta „wiralowego filmu” -> Udostępnij/Kopiuj -> whip -> prawdziwe youtubetranscript.com z wklejonym linkiem i „Go” | Kroki 1-2 wymagają czytelnego UI -> FULL VISUAL |
| 12.483 | 15.683 | 3.200 | SPLIT | Karta transkrypcji (strumień linii) + przycisk Kopiuj -> „Skopiowano” | Kompaktowa karta -> SPLIT |
| 15.683 | 19.783 | 4.100 | VISUAL | Okno ChatGPT: wklejony tekst + wpisywany prompt, kamera wewnątrz okna 1.15x | Demonstracja UI -> FULL VISUAL |
| 19.783 | 24.033 | 4.250 | CAM | Kamera (bez grafiki) | Osobista porada („open loop”) -> FULL CAM |
| 24.033 | 29.783 | 5.750 | SPLIT | Lista 5 pomysłów (wybór #3) -> polecenie o scenariusz -> karta gotowego scenariusza | Kompaktowe karty -> SPLIT |
| 29.783 | 36.767 | 6.983 | VISUAL | Twój prawdziwy zrzut strony produktu (upscale 3x) w stałej ramce 24/200/1032x1040, rozmyty duplikat w tle, ruch kamery 1.25-1.32x + podświetlenia | Realny UI produktu -> FULL VISUAL |
| 36.767 | 39.733 | 2.967 | CAM | Kamera + karta CTA (pole z nickiem + przycisk) u góry; wypalony napis „albo tu :)” z Twojego materiału | Outro/CTA -> FULL CAM |

## 5. Grafiki
- ChatGPT: **rekonstrukcja** UI (chatgpt.com zwraca 403 z tego środowiska); logo OpenAI z pakietu Simple Icons.
- YouTube: logo i nagłówek to **prawdziwe przechwycenie** youtube.com; karta „4,2 mln” to własna grafika ilustracyjna (bez cudzych treści/twarzy).
- youtubetranscript.com: **prawdziwe przechwycenie** (stany: puste pole, wklejony link, wciśnięte „Go”).
- Karta transkrypcji, lista pomysłów, karta scenariusza, karta CTA: własna grafika (custom).
- Strona Twojego produktu: **Twój prawdziwy zrzut** (733x877) przeskalowany 3x; ruch kamery wewnątrz ramki.
- Silnik: HyperFrames (1 kompozycja na run), render 240 fps -> uśrednianie 3 z 4 podklatek do 60 fps (motion blur tylko w ruchu).

## 6. Fact-checking
- Brak liczb/premier/cytatów wymagających weryfikacji. Jedyny realny serwis: youtubetranscript.com - zweryfikowany żywym przechwyceniem strony (formularz URL + „Go” generujący transkrypcje YouTube); drugie niezależne źródło nie było potrzebne dla tego twierdzenia.
- „4,2 mln wyświetleń”, nick `eryk_hajduczek`, link `youtu.be/hV3Qm2Zr8Kc` są przykładami ilustracyjnymi.

## 7. SFX
Zdarzenia (poza ticki): 

| czas (s) | dźwięk | poziom vs szczyt głosu |
|---|---|---|
| 1.250 | pop | -10 dB |
| 3.700 | click | -10 dB |
| 4.120 | pop | -10 dB |
| 8.800 | pop | -10 dB |
| 9.850 | click | -10 dB |
| 9.930 | chime | -10 dB |
| 10.300 | click | -10 dB |
| 10.850 | whoosh | -9 dB |
| 12.200 | click | -10 dB |
| 15.343 | click | -10 dB |
| 16.133 | pop | -10 dB |
| 19.543 | click | -10 dB |
| 25.033 | click | -10 dB |
| 28.333 | click | -10 dB |
| 28.553 | pop | -10 dB |
| 28.633 | chime | -10 dB |
| 37.917 | pop | -10 dB |
| 38.422 | key | -16 dB |
| 38.458 | key | -16 dB |
| 38.494 | key | -16 dB |
| 38.529 | key | -16 dB |
| 38.565 | key | -16 dB |
| 38.601 | key | -16 dB |
| 38.637 | key | -16 dB |
| 38.672 | key | -16 dB |
| 38.708 | key | -16 dB |
| 38.744 | key | -16 dB |
| 38.779 | key | -16 dB |
| 38.815 | key | -16 dB |
| 38.851 | key | -16 dB |
| 38.887 | key | -16 dB |
| 39.387 | click | -10 dB |

Dodatkowo 74 cichych ticków (-16 dB) zsynchronizowanych z pisaniem/strumieniem tekstu (R1, R4, R5, R7). Jedyny whoosh = jedyny whip (R3); jego szczyt wypada dokładnie w środku whipa (10,850 s). Generator ma 4 warianty whooshy, wyrenderowano jeden, bo w montażu jest jeden whip. Riser: 4,900-7,900 s, kończy się równo na cięciu do R3.

## 8. Pomiary audio (ebur128)
| ścieżka | LUFS zintegrowane | true peak |
|---|---|---|
| voice | -14,0 | ~0,0 dBTP (stem) |
| sfx | -25,1 | -8,7 dBTP |
| riser | -23,5 | -14,3 dBTP |
| music | -24,0 | -11,1 dBTP |
| master (WAV) | -14,0 | -1,2 dBTP |
| final.mp4 (po AAC) | -14,0 | -1,2 dBTP |

Master: suma stemów, trim -0,1 dB i transparentny limiter (sufit 0,80) - limiter ścina tylko pojedyncze szczyty głosu.

## 9. Fallbacki / odstępstwa
- **SPLIT dla pionowego źródła**: głowa jest bardzo duża (włosy->broda ~940 px), więc zamiast karty 1210 px użyto karty 888 px (skala 0,822) z górną krawędzią y=1200, wycięcie głowy z tej samej klatki i feather 40 px; napisy w pasie y~910.
- **Wycięcie**: ten sam model u2net_human_seg co w HyperFrames remove-background (CLI przetestowane), ale własny pipeline: wycinek wokół głowy + bramka MediaPipe + guided filter + wygładzenie czasowe (usunięto fałszywe plamy od pasków sufitu).
- **Napisy**: FULL CAM u góry (y~400; outro y~545) zamiast 1267-1536, bo tam jest Twoja twarz.
- **CTA**: Twoje mówione CTA to „wpisz nick w bio”, nie komentarz ze słowem-kluczem, więc karta CTA = pole z nickiem + pomarańczowy przycisk „Chcę moje 3 filmy” (jak w produkcie) i leży u góry, bo dolna trzecia zasłoniłaby usta/brodę.
- **Wypalony napis „albo tu :) systemskala.pl”** (od 38,53 s) był już w Twoim materiale - zachowany.
- Okładka (klatka 0) wymyślona z hooka: „Źle używasz czata GPT”.
- Trzeba było użyć lokalnych obejść: shim libEGL z Chromium, pin klucza CA proxy dla Chromium, venv Pythona.
- Nie dostarczono osobnej warstwy overlay (napisy/CTA są wypalone w final.mp4).

## 10. QA końcowe
Zweryfikowane automatycznie na gotowym pliku: 1080x1920, 60 fps, H.264 High, 2384 klatki, AAC 48 kHz stereo; czas wideo 39,733 s = audio 39,733 s; brak czarnych i białych klatek; największe skoki obrazu wyłącznie na 8 zaplanowanych cięciach (brak klatek-błysków); napisy w poprawnym pasie na każdej z 2384 klatek; głowa i karta wyrównane także przy najszybszych ruchach głowy; loudness -14,0 LUFS, -1,2 dBTP. Struktura wypowiedzi zachowana. Ostatnia klatka to prawdziwy materiał (bez zamrożenia).
Nie wykonano (na Twoją prośbę o szybkie oddanie plików): ponownego, ręcznego przeglądu klatek po obu stronach każdego cięcia w finalnym pliku i odsłuchu na słuchawkach.
