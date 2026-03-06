"""
Dwupoziomowe dopasowywanie B-rolli do scen skryptu.

Poziom 1: RapidFuzz token_sort_ratio (szybki, offline)
  - Normalizuje polskie znaki do ASCII przed porownaniem
  - Jesli score >= FUZZY_MATCH_THRESHOLD (70) - uzywa tego wyniku

Poziom 2: Groq/Claude/Ollama semantic fallback (tylko gdy fuzzy < 70)
  - Krotki, tani prompt do LLM
  - Wybiera najlepszy B-roll semantycznie

Variety tracking: unika uzywania tego samego klipu wielokrotnie.
"""

import json
import re
from pathlib import Path
from typing import Optional

from config import (
    BROLLS_DIR,
    FUZZY_MATCH_THRESHOLD,
    ANTHROPIC_API_KEY,
    CLAUDE_MODEL,
    GROQ_API_KEY,
    GROQ_MODEL,
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
)
from modules.utils import normalize_keyword, normalize_polish_to_ascii


class BRollMatcher:
    def __init__(
        self,
        brolls_dir: Path = BROLLS_DIR,
        llm_provider: str = "groq",
        api_key: str = "",
    ):
        self.brolls_dir = brolls_dir
        self.llm_provider = llm_provider
        self.api_key = api_key

        self.broll_index: dict[str, list[Path]] = {}
        self._round_robin: dict[str, int] = {}

        self._build_index()

    def _build_index(self) -> None:
        if not self.brolls_dir.exists():
            return

        for item in self.brolls_dir.iterdir():
            if item.is_dir():
                folder_key = normalize_keyword(item.name)
                video_files = sorted(item.glob("*.mp4"))
                if video_files:
                    self.broll_index.setdefault(folder_key, []).extend(video_files)

                for video_file in video_files:
                    stem_key = normalize_keyword(re.sub(r"_\d+$", "", video_file.stem))
                    if stem_key != folder_key:
                        self.broll_index.setdefault(stem_key, []).append(video_file)

            elif item.suffix.lower() == ".mp4":
                stem_key = normalize_keyword(re.sub(r"_\d+$", "", item.stem))
                self.broll_index.setdefault(stem_key, []).append(item)

        for key in self.broll_index:
            seen = set()
            unique = []
            for p in self.broll_index[key]:
                if p not in seen:
                    seen.add(p)
                    unique.append(p)
            self.broll_index[key] = unique

    def get_all_files(self) -> list[Path]:
        all_files = []
        seen = set()
        for files in self.broll_index.values():
            for f in files:
                if f not in seen:
                    seen.add(f)
                    all_files.append(f)
        return all_files

    def get_index_keys(self) -> list[str]:
        return list(self.broll_index.keys())

    def match_keyword(
        self,
        keyword: str,
        secondary_keywords: Optional[list[str]] = None,
        used_files: Optional[set] = None,
    ) -> tuple[Optional[Path], float]:
        if used_files is None:
            used_files = set()

        candidates = list(self.broll_index.keys())
        if not candidates:
            return None, 0.0

        norm_keyword = normalize_keyword(keyword)
        all_query_keywords = [norm_keyword]

        if secondary_keywords:
            for sk in secondary_keywords:
                all_query_keywords.append(normalize_keyword(sk))

        best_key, best_score = self._fuzzy_match_best(all_query_keywords, candidates)

        if best_score >= FUZZY_MATCH_THRESHOLD:
            return self._select_with_variety(best_key, used_files), best_score

        semantic_key, semantic_score = self._semantic_match(
            keyword, secondary_keywords or [], candidates
        )

        if semantic_key:
            return self._select_with_variety(semantic_key, used_files), semantic_score * 100

        if best_key and best_score > 0:
            return self._select_with_variety(best_key, used_files), best_score

        return None, 0.0

    def match_all_scenes(self, script: dict) -> dict:
        used_files: set[str] = set()

        hook = script.get("hook", {})
        hook_keyword = hook.get("broll_keyword") or "ogolny"
        hook_secondary = hook.get("broll_secondary_keywords", [])
        path, score = self.match_keyword(hook_keyword, hook_secondary, used_files)
        hook["matched_broll_file"] = str(path) if path else None
        hook["matched_broll_score"] = round(score, 1)
        if path:
            used_files.add(str(path))

        for scene in script.get("scenes", []):
            keyword = scene.get("broll_keyword", "")
            secondary = scene.get("broll_secondary_keywords", [])
            path, score = self.match_keyword(keyword, secondary, used_files)
            scene["matched_broll_file"] = str(path) if path else None
            scene["matched_broll_score"] = round(score, 1)
            if path:
                used_files.add(str(path))

        cta = script.get("cta", {})
        cta_keyword = cta.get("broll_keyword") or "zakonczenie"
        cta_secondary = cta.get("broll_secondary_keywords", [])
        path, score = self.match_keyword(cta_keyword, cta_secondary, used_files)
        cta["matched_broll_file"] = str(path) if path else None
        cta["matched_broll_score"] = round(score, 1)

        return script

    def _fuzzy_match_best(
        self,
        queries: list[str],
        candidates: list[str],
    ) -> tuple[Optional[str], float]:
        try:
            from rapidfuzz import process, fuzz
        except ImportError:
            raise RuntimeError("rapidfuzz nie jest zainstalowany. Uruchom: pip install rapidfuzz")

        best_key = None
        best_score = 0.0

        for query in queries:
            if query in candidates:
                return query, 100.0

            result = process.extractOne(
                query,
                candidates,
                scorer=fuzz.token_sort_ratio,
                score_cutoff=0,
            )
            if result and result[1] > best_score:
                best_key = result[0]
                best_score = result[1]

        return best_key, best_score

    def _semantic_match(
        self,
        keyword: str,
        secondary_keywords: list[str],
        candidates: list[str],
    ) -> tuple[Optional[str], float]:
        if not candidates:
            return None, 0.0

        candidates_str = ", ".join(candidates[:20])
        all_keywords = [keyword] + secondary_keywords
        keywords_str = ", ".join(all_keywords)

        prompt = (
            f'Wybierz najlepszy B-roll dla sceny o slowach kluczowych: "{keywords_str}".\n'
            f"Dostepne opcje: {candidates_str}\n"
            f'Odpowiedz TYLKO JSON: {{"key": "wybrany_klucz", "score": 0.8}}\n'
            f"Jesli zadna opcja nie pasuje, zwroc: null"
        )

        try:
            if self.llm_provider == "groq":
                raw = self._call_groq_semantic(prompt)
            elif self.llm_provider == "claude":
                raw = self._call_claude_semantic(prompt)
            else:
                raw = self._call_ollama_semantic(prompt)

            if raw and raw.strip() != "null":
                json_match = re.search(r"\{[^}]+\}", raw)
                if json_match:
                    data = json.loads(json_match.group())
                    key = data.get("key", "")
                    score = float(data.get("score", 0.5))
                    if key in self.broll_index:
                        return key, score
                    norm_key = normalize_keyword(key)
                    if norm_key in self.broll_index:
                        return norm_key, score
        except Exception as e:
            print(f"[BRollMatcher] Blad semantic match: {e}")

        return None, 0.0

    def _call_groq_semantic(self, prompt: str) -> str:
        key = self.api_key or GROQ_API_KEY
        if not key:
            return ""
        try:
            from groq import Groq
            client = Groq(api_key=key)
            completion = client.chat.completions.create(
                model=GROQ_MODEL,
                max_tokens=100,
                messages=[{"role": "user", "content": prompt}],
            )
            return completion.choices[0].message.content
        except Exception:
            return ""

    def _call_claude_semantic(self, prompt: str) -> str:
        key = self.api_key or ANTHROPIC_API_KEY
        if not key:
            return ""
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=key)
            msg = client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=100,
                messages=[{"role": "user", "content": prompt}],
            )
            return msg.content[0].text
        except Exception:
            return ""

    def _call_ollama_semantic(self, prompt: str) -> str:
        try:
            import requests
            resp = requests.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False, "format": "json"},
                timeout=30,
            )
            return resp.json().get("response", "")
        except Exception:
            return ""

    def _select_with_variety(
        self,
        keyword_key: str,
        used_files: set,
    ) -> Optional[Path]:
        files = self.broll_index.get(keyword_key, [])
        if not files:
            return None

        unused = [f for f in files if str(f) not in used_files]
        if unused:
            idx = self._round_robin.get(keyword_key, 0) % len(unused)
            self._round_robin[keyword_key] = idx + 1
            return unused[idx]

        idx = self._round_robin.get(keyword_key, 0) % len(files)
        self._round_robin[keyword_key] = idx + 1
        return files[idx]

    def get_match_report(self, script: dict) -> list[dict]:
        report = []

        hook = script.get("hook", {})
        report.append({
            "segment": "HOOK",
            "keyword": hook.get("broll_keyword", "-"),
            "matched_file": hook.get("matched_broll_file"),
            "score": hook.get("matched_broll_score", 0),
        })

        for scene in script.get("scenes", []):
            report.append({
                "segment": scene.get("scene_id", "?"),
                "keyword": scene.get("broll_keyword", "-"),
                "matched_file": scene.get("matched_broll_file"),
                "score": scene.get("matched_broll_score", 0),
            })

        cta = script.get("cta", {})
        report.append({
            "segment": "CTA",
            "keyword": cta.get("broll_keyword", "-"),
            "matched_file": cta.get("matched_broll_file"),
            "score": cta.get("matched_broll_score", 0),
        })

        return report
