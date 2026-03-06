"""
Generator wiralowych skryptow wideo.

Obsluguje trzy providery LLM:
  - "groq":   Groq Cloud (Llama 3.3 70B) - darmowy, domyslny
  - "claude": Claude Haiku przez Anthropic API
  - "ollama": lokalny model przez Ollama HTTP API
"""

import json
import re
import requests
from datetime import datetime, timezone

from config import (
    ANTHROPIC_API_KEY, CLAUDE_MODEL,
    GROQ_API_KEY, GROQ_MODEL,
    OLLAMA_BASE_URL, OLLAMA_MODEL,
    DEFAULT_VIDEO_DURATION, DEFAULT_TONE,
)
from modules.utils import generate_session_id


SYSTEM_PROMPT = """Jestes ekspertem od tworzenia wiralowych skryptow wideo w jezyku polskim.
Tworzysz krotkie filmy (30-90 sekund) w stylu TikTok/Reels/YouTube Shorts.
Kluczowe zasady:
- HOOK musi byc szokujacy, zaskakujacy lub bardzo ciekawy - pierwsze 3 sekundy decyduja o ogladaniu
- Kazda scena to 1 krotkie zdanie lub 2 bardzo krotkie zdania
- CTA musi byc konkretne i pilne (np. "Obserwuj teraz", "Zapisz zanim zniknie")
- Jezyk: potoczny, dynamiczny, bezposredni - jak mowisz do przyjaciela
- Kazde broll_keyword MUSI pochodzic z listy dostepnych B-rolli
- Odpowiadasz WYLACZNIE poprawnym JSON-em - zero komentarzy, zero markdown"""


SCRIPT_SCHEMA_EXAMPLE = {
    "meta": {
        "topic": "przykladowy temat",
        "language": "pl",
        "tone": "energetic",
        "target_duration_seconds": 60,
        "session_id": "abc123"
    },
    "hook": {
        "text": "Szokujacy hook przyciagajacy uwage w 3 sekundy.",
        "duration_hint_seconds": 5
    },
    "scenes": [
        {
            "scene_id": "scene_01",
            "order": 1,
            "narration": "Krotka narracja dla tej sceny.",
            "broll_keyword": "slowo_kluczowe_z_listy",
            "broll_secondary_keywords": ["alternatywa1", "alternatywa2"],
            "duration_hint_seconds": 8,
            "emotion": "serious",
            "matched_broll_file": None,
            "matched_broll_score": None,
            "tts_audio_file": None,
            "actual_audio_duration_seconds": None
        }
    ],
    "cta": {
        "text": "Konkretne wezwanie do dzialania.",
        "duration_hint_seconds": 5,
        "broll_keyword": "slowo_kluczowe",
        "broll_secondary_keywords": [],
        "matched_broll_file": None,
        "matched_broll_score": None,
        "tts_audio_file": None,
        "actual_audio_duration_seconds": None
    },
    "assembly": {
        "show_subtitles": True,
        "tts_voice": "pl-PL-ZofiaNeural",
        "status": "pending"
    }
}

TONE_DESCRIPTIONS = {
    "energetic": "energetyczny, szybki, motywujacy, pelny entuzjazmu",
    "serious": "powazny, merytoryczny, autorytatywny, profesjonalny",
    "funny": "zabawny, ludzki, z humorem, luzny",
    "inspirational": "inspirujacy, emocjonalny, podnoszacy na duchu",
}


def generate_script(
    topic: str,
    broll_keywords_available: list[str],
    target_duration: int = DEFAULT_VIDEO_DURATION,
    tone: str = DEFAULT_TONE,
    tts_voice: str = "pl-PL-ZofiaNeural",
    show_subtitles: bool = True,
    provider: str = "groq",
    api_key: str = "",
    session_id: str = None,
) -> dict:
    if session_id is None:
        session_id = generate_session_id()

    prompt = _build_generation_prompt(
        topic=topic,
        available_keywords=broll_keywords_available,
        target_duration=target_duration,
        tone=tone,
        tts_voice=tts_voice,
        show_subtitles=show_subtitles,
        session_id=session_id,
    )

    raw_response = _call_llm(prompt, provider, api_key)
    script = _parse_and_validate(raw_response, provider, api_key, prompt)

    script.setdefault("meta", {})
    script["meta"]["session_id"] = session_id
    script["meta"]["topic"] = topic
    script["meta"]["tone"] = tone
    script["meta"]["target_duration_seconds"] = target_duration
    script["meta"]["language"] = "pl"
    script["meta"]["generated_at"] = datetime.now(timezone.utc).isoformat()

    script.setdefault("assembly", {})
    script["assembly"]["show_subtitles"] = show_subtitles
    script["assembly"]["tts_voice"] = tts_voice
    script["assembly"]["status"] = "pending"

    return script


def _build_generation_prompt(
    topic, available_keywords, target_duration, tone, tts_voice, show_subtitles, session_id
) -> str:
    tone_desc = TONE_DESCRIPTIONS.get(tone, tone)
    keywords_str = ", ".join(available_keywords) if available_keywords else "brak (uzywaj ogolnych slow)"
    approx_scenes = max(2, (target_duration - 10) // 8)
    schema_str = json.dumps(SCRIPT_SCHEMA_EXAMPLE, ensure_ascii=False, indent=2)

    return f"""Stworz wiralowy skrypt wideo na temat: "{topic}"

PARAMETRY:
- Dlugosc: {target_duration} sekund
- Ton: {tone_desc}
- Liczba scen: okolo {approx_scenes} (bez hook i CTA)
- Glos: {tts_voice}
- Napisy: {"tak" if show_subtitles else "nie"}
- Session ID: {session_id}

DOSTEPNE KLUCZE B-ROLLI (uzywaj TYLKO tych slow w broll_keyword i broll_secondary_keywords):
{keywords_str}

WAZNE ZASADY:
1. Hook musi byc natychmiast przyciagajacy - zaskoczenie, szok, pytanie retoryczne lub kontrowersja
2. Kazda scena = 1-2 zdania max (lektor mowi szybko)
3. broll_keyword MUSI byc z powyzszej listy (jesli lista jest pusta, uzyj ogolnych slow po polsku)
4. broll_secondary_keywords to 2-3 alternatywy z listy (lub podobne)
5. duration_hint_seconds = szacowany czas czytania narracji przez lektora
6. emotion: "serious", "hopeful", "exciting", "shocking", "funny", "inspirational"
7. CTA musi byc konkretne i pilne

SCHEMAT JSON (odpowiedz DOKLADNIE w tym formacie):
{schema_str}

Odpowiedz TYLKO JSON-em, bez zadnych komentarzy ani markdown.
Zacznij od {{ i skoncz na }}."""


def _call_llm(prompt: str, provider: str, api_key: str = "") -> str:
    if provider == "groq":
        return _call_groq(prompt, api_key)
    elif provider == "claude":
        return _call_claude(prompt, api_key)
    elif provider == "ollama":
        return _call_ollama(prompt)
    else:
        raise ValueError(f"Nieznany provider: {provider}. Uzyj 'groq', 'claude' lub 'ollama'.")


def _call_groq(prompt: str, api_key: str = "") -> str:
    """Wywolaj Groq Cloud (Llama 3.3 70B) - darmowy."""
    key = api_key or GROQ_API_KEY
    if not key:
        raise RuntimeError(
            "Brak klucza GROQ_API_KEY. Dodaj go do pliku .env lub podaj w aplikacji. "
            "Darmowy klucz: console.groq.com"
        )
    try:
        from groq import Groq
        client = Groq(api_key=key)
        completion = client.chat.completions.create(
            model=GROQ_MODEL,
            max_tokens=4096,
            temperature=0.7,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
        )
        return completion.choices[0].message.content
    except ImportError:
        raise RuntimeError("Pakiet 'groq' nie jest zainstalowany. Uruchom: pip install groq")
    except Exception as e:
        raise RuntimeError(f"Blad Groq API: {e}")


def _call_claude(prompt: str, api_key: str = "") -> str:
    """Wywolaj Claude Haiku przez Anthropic SDK."""
    key = api_key or ANTHROPIC_API_KEY
    if not key:
        raise RuntimeError(
            "Brak klucza ANTHROPIC_API_KEY. Dodaj go do pliku .env lub podaj w aplikacji."
        )
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=key)
        message = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text
    except ImportError:
        raise RuntimeError("Pakiet 'anthropic' nie jest zainstalowany. Uruchom: pip install anthropic")
    except Exception as e:
        raise RuntimeError(f"Blad Claude API: {e}")


def _call_ollama(prompt: str) -> str:
    """Wywolaj lokalny model przez Ollama HTTP API."""
    url = f"{OLLAMA_BASE_URL}/api/generate"
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": f"{SYSTEM_PROMPT}\n\n{prompt}",
        "stream": False,
        "format": "json",
    }
    try:
        resp = requests.post(url, json=payload, timeout=120)
        resp.raise_for_status()
        return resp.json().get("response", "")
    except requests.exceptions.ConnectionError:
        raise RuntimeError(
            f"Nie mozna polaczyc z Ollama pod {OLLAMA_BASE_URL}. "
            "Sprawdz czy Ollama jest uruchomiony: 'ollama serve'"
        )
    except Exception as e:
        raise RuntimeError(f"Blad Ollama API: {e}")


def _parse_and_validate(raw: str, provider: str, api_key: str, original_prompt: str) -> dict:
    raw = raw.strip()
    json_match = re.search(r"\{.*\}", raw, re.DOTALL)
    if json_match:
        raw = json_match.group()

    try:
        script = json.loads(raw)
    except json.JSONDecodeError as e:
        repaired = _repair_json(raw, str(e), provider, api_key, original_prompt)
        script = json.loads(repaired)

    errors = _validate_schema(script)
    if errors:
        raise ValueError(f"Skrypt nie spelnia schematu: {'; '.join(errors)}")

    return script


def _validate_schema(script: dict) -> list[str]:
    errors = []

    if "hook" not in script:
        errors.append("Brak sekcji 'hook'")
    elif "text" not in script.get("hook", {}):
        errors.append("Brak 'hook.text'")

    if "scenes" not in script:
        errors.append("Brak sekcji 'scenes'")
    elif not isinstance(script["scenes"], list) or len(script["scenes"]) == 0:
        errors.append("'scenes' musi byc niepusta lista")
    else:
        for i, scene in enumerate(script["scenes"]):
            for field in ["narration", "broll_keyword"]:
                if field not in scene:
                    errors.append(f"Scena {i+1}: brak pola '{field}'")

    if "cta" not in script:
        errors.append("Brak sekcji 'cta'")
    elif "text" not in script.get("cta", {}):
        errors.append("Brak 'cta.text'")

    return errors


def _repair_json(broken_json: str, error_msg: str, provider: str, api_key: str, original_prompt: str) -> str:
    repair_prompt = (
        f"Popraw ponizszy JSON - jest niepoprawny (blad: {error_msg}).\n"
        f"Odpowiedz TYLKO poprawnym JSON-em:\n\n{broken_json}"
    )
    return _call_llm(repair_prompt, provider, api_key)


def get_available_providers(groq_key: str = "", claude_key: str = "") -> list[str]:
    """Zwroc liste dostepnych providerow LLM."""
    available = []

    if groq_key or GROQ_API_KEY:
        available.append("groq")
    if claude_key or ANTHROPIC_API_KEY:
        available.append("claude")

    try:
        resp = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=3)
        if resp.status_code == 200:
            available.append("ollama")
    except Exception:
        pass

    return available if available else ["groq"]
