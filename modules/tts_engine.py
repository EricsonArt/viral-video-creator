"""
Silnik TTS (Text-to-Speech) dla lektora AI.
Glowny: Edge TTS (Microsoft, darmowy, online) - pl-PL-ZofiaNeural / pl-PL-MarekNeural
Fallback: Kokoro TTS (lokalny, Apache 2.0) - odkomentuj w requirements.txt
"""

import asyncio
import os
from pathlib import Path
from typing import Optional, Callable

from config import DEFAULT_TTS_VOICE, ALT_TTS_VOICE, TTS_RATE, TTS_VOLUME, TTS_PITCH


def get_audio_duration(audio_path: Path) -> float:
    """Zmierz dlugosc pliku audio w sekundach uzywajac mutagen."""
    try:
        from mutagen.mp3 import MP3
        audio = MP3(str(audio_path))
        return audio.info.length
    except Exception:
        # Fallback: uzyj moviepy
        try:
            from moviepy.editor import AudioFileClip
            with AudioFileClip(str(audio_path)) as clip:
                return clip.duration
        except Exception:
            return 0.0


class EdgeTTSEngine:
    """
    Silnik TTS oparty na Microsoft Edge TTS.
    Darmowy, wymaga internetu, wysoka jakosc glosu polskiego.
    """

    def __init__(
        self,
        voice: str = DEFAULT_TTS_VOICE,
        rate: str = TTS_RATE,
        volume: str = TTS_VOLUME,
        pitch: str = TTS_PITCH,
    ):
        self.voice = voice
        self.rate = rate
        self.volume = volume
        self.pitch = pitch

    def synthesize(self, text: str, output_path: Path) -> float:
        """
        Syntetyzuj mowe i zapisz do pliku MP3.
        Zwraca dlugosc audio w sekundach.
        """
        try:
            import edge_tts
        except ImportError:
            raise RuntimeError("edge-tts nie jest zainstalowany. Uruchom: pip install edge-tts")

        output_path.parent.mkdir(parents=True, exist_ok=True)

        async def _run():
            communicate = edge_tts.Communicate(
                text=text,
                voice=self.voice,
                rate=self.rate,
                volume=self.volume,
                pitch=self.pitch,
            )
            await communicate.save(str(output_path))

        # Uruchom asyncio event loop
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Jesli jestesmy w kontekscie async (np. Streamlit) - nowy loop
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    future = pool.submit(asyncio.run, _run())
                    future.result(timeout=60)
            else:
                loop.run_until_complete(_run())
        except Exception:
            asyncio.run(_run())

        return get_audio_duration(output_path)

    @staticmethod
    def list_polish_voices() -> list[dict]:
        """Lista polskich glosow Edge TTS."""
        return [
            {"name": "pl-PL-ZofiaNeural", "gender": "Kobieta", "style": "Natural"},
            {"name": "pl-PL-MarekNeural", "gender": "Mezczyzna", "style": "Natural"},
        ]

    @staticmethod
    def is_available() -> bool:
        """Sprawdz czy edge-tts jest zainstalowany."""
        try:
            import edge_tts  # noqa: F401
            return True
        except ImportError:
            return False


class KokoroTTSEngine:
    """
    Lokalny silnik TTS oparty na Kokoro (82M parametrow, Apache 2.0).
    Nie wymaga internetu, bardzo szybki.
    Wymaga: pip install kokoro soundfile
    UWAGA: Obsluga jezyka polskiego jest ograniczona - Kokoro jest optymalizowany pod angielski.
    """

    def __init__(self, voice: str = "af_heart"):
        self.voice = voice
        self._pipeline = None

    def _get_pipeline(self):
        if self._pipeline is None:
            try:
                from kokoro import KPipeline
                self._pipeline = KPipeline(lang_code="pl")
            except ImportError:
                raise RuntimeError(
                    "Kokoro TTS nie jest zainstalowany. "
                    "Uruchom: pip install kokoro soundfile"
                )
        return self._pipeline

    def synthesize(self, text: str, output_path: Path) -> float:
        """Syntetyzuj mowe lokalnie przez Kokoro. Zwraca dlugosc w sekundach."""
        import soundfile as sf
        import numpy as np

        output_path.parent.mkdir(parents=True, exist_ok=True)
        pipeline = self._get_pipeline()

        all_audio = []
        for _, _, audio in pipeline(text, voice=self.voice):
            if audio is not None:
                all_audio.append(audio)

        if all_audio:
            combined = np.concatenate(all_audio)
            sf.write(str(output_path), combined, 24000)

        return get_audio_duration(output_path)

    @staticmethod
    def is_available() -> bool:
        try:
            import kokoro  # noqa: F401
            return True
        except ImportError:
            return False


def get_tts_engine(
    voice: str = DEFAULT_TTS_VOICE,
    prefer_local: bool = False,
) -> EdgeTTSEngine | KokoroTTSEngine:
    """
    Factory: zwroc odpowiedni silnik TTS.
    prefer_local=True -> najpierw Kokoro, potem Edge TTS
    prefer_local=False -> najpierw Edge TTS, potem Kokoro
    """
    if prefer_local and KokoroTTSEngine.is_available():
        return KokoroTTSEngine()
    if EdgeTTSEngine.is_available():
        return EdgeTTSEngine(voice=voice)
    if KokoroTTSEngine.is_available():
        return KokoroTTSEngine()
    raise RuntimeError(
        "Brak silnika TTS. Zainstaluj edge-tts: pip install edge-tts\n"
        "Lub Kokoro: pip install kokoro soundfile"
    )


def synthesize_all_scenes(
    script: dict,
    output_dir: Path,
    voice: str = DEFAULT_TTS_VOICE,
    prefer_local: bool = False,
    progress_callback: Optional[Callable[[int, int, str], None]] = None,
) -> dict:
    """
    Syntetyzuj audio dla wszystkich scen skryptu.
    Uzupelnia w miejscu: scene["tts_audio_file"] i scene["actual_audio_duration_seconds"].

    Args:
        script: Slownik skryptu (modyfikowany w miejscu)
        output_dir: Katalog do zapisu plikow MP3
        voice: Glos Edge TTS
        prefer_local: Czy preferowac Kokoro zamiast Edge TTS
        progress_callback: Opcjonalny callback (current, total, status_msg)

    Returns:
        Zmodyfikowany slownik skryptu
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    engine = get_tts_engine(voice=voice, prefer_local=prefer_local)

    # Zbierz wszystkie segmenty do przetworzenia: hook + scenes + cta
    segments = []

    hook = script.get("hook", {})
    if hook.get("text"):
        segments.append(("hook", hook))

    for scene in script.get("scenes", []):
        if scene.get("narration"):
            segments.append((scene["scene_id"], scene))

    cta = script.get("cta", {})
    if cta.get("text"):
        segments.append(("cta", cta))

    total = len(segments)

    for i, (seg_id, segment) in enumerate(segments):
        text = segment.get("text") or segment.get("narration", "")
        if not text:
            continue

        audio_file = output_dir / f"{seg_id}.mp3"
        status = f"Lektor TTS: {seg_id} ({i+1}/{total})"

        if progress_callback:
            progress_callback(i, total, status)

        try:
            duration = engine.synthesize(text, audio_file)
            segment["tts_audio_file"] = str(audio_file)
            segment["actual_audio_duration_seconds"] = duration
        except Exception as e:
            # Jesli TTS sie nie uda - ustaw zerowy czas (fallback w assemblerze)
            segment["tts_audio_file"] = None
            segment["actual_audio_duration_seconds"] = segment.get("duration_hint_seconds", 5.0)
            print(f"[TTS] Blad dla {seg_id}: {e}")

    if progress_callback:
        progress_callback(total, total, "Lektor TTS: zakonczone")

    return script
