# 🎬 Viral Video Creator

Automatyczny system tworzenia wiralowych filmów krótkich (TikTok/Reels/Shorts).

## Jak działa?

1. Wgrywasz pliki B-roll (np. `radość.mp4`, `praca_1.mp4`)
2. Wpisujesz temat wideo
3. AI generuje wiralowy skrypt z hookiem i CTA
4. Lektor AI (Edge TTS, darmowy) czyta skrypt
5. System dopasowuje B-rolle do każdej sceny
6. Gotowy plik wideo 9:16 (TikTok format) do pobrania

## Szybki start

### 1. Instalacja zależności

```bash
pip install -r requirements.txt
```

### 2. Konfiguracja API (opcjonalne)

Skopiuj `.env.example` jako `.env` i uzupełnij klucz:

```bash
copy .env.example .env
```

Następnie edytuj `.env`:
```
ANTHROPIC_API_KEY=twoj_klucz_api_tutaj
```

> **Bez klucza API** możesz używać Ollama (lokalny, darmowy LLM).

### 3. Uruchomienie

```bash
streamlit run app.py
```

Otwórz: http://localhost:8501

## Opcje lektora AI

### Edge TTS (domyślny, darmowy, online)
- `pl-PL-ZofiaNeural` — głos kobiecy, naturalny
- `pl-PL-MarekNeural` — głos męski
- Wymaga internetu

### Kokoro TTS (lokalny, offline)
Odkomentuj w `requirements.txt`:
```
kokoro>=0.9.2
```
Następnie:
```bash
pip install kokoro soundfile
```

## Opcje silnika AI (generowanie skryptu)

### Claude API (rekomendowany)
- Najlepsza jakość skryptów
- ~$0.02-0.10 za wideo (claude-haiku)
- Wymaga klucza ANTHROPIC_API_KEY

### Ollama (darmowy, lokalny)
1. Pobierz Ollama: https://ollama.com
2. Uruchom: `ollama serve`
3. Pobierz model: `ollama pull llama3.2`

## Struktura plików B-roll

Umieść pliki w folderze `brolls/`:
```
brolls/
  radosc/
    radosc_1.mp4
    radosc_2.mp4
  praca/
    praca_1.mp4
  natura.mp4
```

Nazwa folderu/pliku = słowo kluczowe dopasowania.

## Napisy

Dla najlepszej jakości napisów pobierz font:
- NotoSans: https://fonts.google.com/noto/specimen/Noto+Sans
- Zapisz jako: `fonts/NotoSans-Regular.ttf`

Bez fontu system używa systemowego Arial.
