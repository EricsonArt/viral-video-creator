"""
Modul skladania wideo (VideoAssembler).
Laczy klipy B-roll z lektorem TTS i napisami w jeden finalny film.

Pipeline dla kazdej sceny:
  1. Wczytaj klip B-roll
  2. Dopasuj dlugosc klipu do dlugosci audio (trim/loop/slow)
  3. Przeskaluj i wytnij do formatu 1080x1920 (9:16)
  4. Dolacz audio TTS
  5. Dodaj napisy (opcjonalnie)
  6. Zloz CompositeVideoClip

Nastepnie: concatenate_videoclips → export MP4
"""

import os
from pathlib import Path
from typing import Optional, Callable

from config import (
    VIDEO_WIDTH, VIDEO_HEIGHT, VIDEO_FPS,
    VIDEO_CODEC, AUDIO_CODEC, VIDEO_BITRATE,
    MAX_SCENE_DURATION, MIN_SCENE_DURATION,
    SUBTITLE_FONT, SUBTITLE_FONTSIZE, SUBTITLE_COLOR,
    SUBTITLE_STROKE_COLOR, SUBTITLE_STROKE_WIDTH,
    SUBTITLE_Y_POSITION, SUBTITLE_MAX_CHARS_PER_LINE,
)
from modules.utils import (
    split_into_subtitle_chunks,
    distribute_subtitle_timing,
    bytes_to_mb,
)


def assemble_video(
    script: dict,
    output_dir: Path,
    temp_dir: Path,
    progress_callback: Optional[Callable[[int, int, str], None]] = None,
) -> Path:
    """
    Glowna funkcja skladajaca finalny plik wideo.

    Args:
        script: Skrypt z uzupelnionymi polami matched_broll_file i tts_audio_file
        output_dir: Katalog wyjsciowy dla finalnego wideo
        temp_dir: Katalog tymczasowy
        progress_callback: Opcjonalny callback (current, total, status_msg)

    Returns:
        Path do finalnego pliku wideo
    """
    try:
        import moviepy.editor as mpy
    except ImportError:
        raise RuntimeError("moviepy nie jest zainstalowany. Uruchom: pip install moviepy")

    output_dir.mkdir(parents=True, exist_ok=True)
    temp_dir.mkdir(parents=True, exist_ok=True)

    show_subtitles = script.get("assembly", {}).get("show_subtitles", True)

    # Zbierz wszystkie segmenty do zlozenia: hook + scenes + cta
    segments = _collect_segments(script)
    total = len(segments)

    if total == 0:
        raise ValueError("Skrypt nie zawiera zadnych segmentow do zlozenia")

    clips = []
    for i, segment in enumerate(segments):
        seg_id = segment.get("scene_id") or segment.get("_seg_type", f"seg_{i}")
        narration = segment.get("narration") or segment.get("text", "")

        if progress_callback:
            progress_callback(i, total, f"Skladam scene {i+1}/{total}: {seg_id}")

        clip = _build_scene_clip(
            segment=segment,
            narration=narration,
            seg_index=i,
            show_subtitles=show_subtitles,
            temp_dir=temp_dir,
        )
        clips.append(clip)

    if progress_callback:
        progress_callback(total - 1, total, "Lacze wszystkie sceny...")

    # Polacz wszystkie klipy
    final_clip = mpy.concatenate_videoclips(clips, method="compose")

    # Eksportuj
    output_path = output_dir / "final_video.mp4"

    if progress_callback:
        progress_callback(total, total, "Renderuję wideo (to moze chwilę potrwać)...")

    final_clip.write_videofile(
        str(output_path),
        fps=VIDEO_FPS,
        codec=VIDEO_CODEC,
        audio_codec=AUDIO_CODEC,
        bitrate=VIDEO_BITRATE,
        threads=4,
        logger=None,  # Wycisz domyslny logger moviepy
    )

    # Zwolnij zasoby
    final_clip.close()
    for clip in clips:
        try:
            clip.close()
        except Exception:
            pass

    return output_path


def _collect_segments(script: dict) -> list[dict]:
    """Zbierz hook + scenes + cta z oznakami typow."""
    segments = []

    hook = script.get("hook", {})
    if hook.get("text") or hook.get("narration"):
        hook = dict(hook)
        hook["_seg_type"] = "hook"
        if "scene_id" not in hook:
            hook["scene_id"] = "hook"
        if "narration" not in hook and "text" in hook:
            hook["narration"] = hook["text"]
        segments.append(hook)

    for scene in script.get("scenes", []):
        s = dict(scene)
        s["_seg_type"] = "scene"
        segments.append(s)

    cta = script.get("cta", {})
    if cta.get("text") or cta.get("narration"):
        cta = dict(cta)
        cta["_seg_type"] = "cta"
        if "scene_id" not in cta:
            cta["scene_id"] = "cta"
        if "narration" not in cta and "text" in cta:
            cta["narration"] = cta["text"]
        segments.append(cta)

    return segments


def _build_scene_clip(
    segment: dict,
    narration: str,
    seg_index: int,
    show_subtitles: bool,
    temp_dir: Path,
):
    """Zbuduj pojedynczy CompositeVideoClip dla sceny."""
    import moviepy.editor as mpy

    # Ustal dlugosc klipu na podstawie audio
    audio_duration = segment.get("actual_audio_duration_seconds") or segment.get("duration_hint_seconds", 6.0)
    audio_duration = max(MIN_SCENE_DURATION, min(MAX_SCENE_DURATION, float(audio_duration)))

    broll_file = segment.get("matched_broll_file")
    tts_file = segment.get("tts_audio_file")

    # --- Klip wideo (B-roll lub fallback) ---
    if broll_file and Path(broll_file).exists():
        video_clip = _load_and_fit_broll(broll_file, audio_duration)
    else:
        video_clip = _create_fallback_clip(narration, audio_duration)

    # Przeskaluj i wytnij do formatu docelowego
    video_clip = _resize_and_crop(video_clip, VIDEO_WIDTH, VIDEO_HEIGHT)

    # --- Audio TTS ---
    if tts_file and Path(tts_file).exists():
        audio_clip = mpy.AudioFileClip(tts_file)
        # Przytnij audio jesli dluzsze niz klip wideo
        if audio_clip.duration > video_clip.duration:
            audio_clip = audio_clip.subclip(0, video_clip.duration)
        video_clip = video_clip.set_audio(audio_clip)

    # --- Napisy ---
    if show_subtitles and narration:
        subtitle_clips = _create_subtitle_clips(narration, audio_duration)
        if subtitle_clips:
            video_clip = mpy.CompositeVideoClip([video_clip] + subtitle_clips)

    return video_clip


def _load_and_fit_broll(broll_file: str, target_duration: float):
    """
    Wczytaj B-roll i dopasuj do docelowej dlugosci.
    - Dluzszy niz target → trim ze srodka
    - Krotszy ≤ 50% target → loop
    - Krotszy > 50% → loop + lekkie spowolnienie (max 0.85x)
    """
    import moviepy.editor as mpy

    clip = mpy.VideoFileClip(broll_file, audio=False)
    clip_duration = clip.duration

    if clip_duration >= target_duration:
        # Trim ze srodka: zachowaj akcje ze srodka klipu
        if clip_duration > target_duration + 1.0:
            start = (clip_duration - target_duration) / 2
            clip = clip.subclip(start, start + target_duration)
        else:
            clip = clip.subclip(0, target_duration)
    else:
        # Klip jest krotszy - loop
        ratio = target_duration / clip_duration

        if ratio > 3.0:
            # Bardzo krotki klip - spowolnij do 0.85x zeby zmniejszyc potrzebna liczbe loopow
            clip = clip.fx(mpy.vfx.speedx, 0.85)
            clip_duration = clip.duration
            ratio = target_duration / clip_duration

        # Petla klipu
        loop_count = int(ratio) + 1
        looped = mpy.concatenate_videoclips([clip] * loop_count)
        clip = looped.subclip(0, target_duration)

    return clip.set_duration(target_duration)


def _resize_and_crop(clip, target_width: int, target_height: int):
    """
    Przeskaluj klip do docelowej rozdzielczosci z center-crop.
    Nie rozciaga - zachowuje proporcje przez crop.
    """
    import moviepy.editor as mpy

    orig_w = clip.w
    orig_h = clip.h
    target_ratio = target_width / target_height
    orig_ratio = orig_w / orig_h

    if orig_ratio > target_ratio:
        # Szerszy niz cel - przeskaluj do wysokosci, przytnij szerokosc
        new_h = target_height
        new_w = int(orig_ratio * new_h)
        clip = clip.resize(height=new_h)
        x_center = clip.w / 2
        clip = clip.crop(
            x1=x_center - target_width / 2,
            x2=x_center + target_width / 2,
            y1=0,
            y2=target_height,
        )
    else:
        # Wyzszy niz cel - przeskaluj do szerokosci, przytnij wysokosc
        new_w = target_width
        clip = clip.resize(width=new_w)
        y_center = clip.h / 2
        clip = clip.crop(
            x1=0,
            x2=target_width,
            y1=y_center - target_height / 2,
            y2=y_center + target_height / 2,
        )

    return clip.resize((target_width, target_height))


def _create_fallback_clip(text: str, duration: float):
    """
    Stworz czarny klip z tekstem gdy B-roll jest niedostepny.
    """
    import moviepy.editor as mpy

    # Czarne tlo
    bg = mpy.ColorClip(size=(VIDEO_WIDTH, VIDEO_HEIGHT), color=(0, 0, 0), duration=duration)

    # Tekst na srodku (skrocony jesli za dlugi)
    display_text = text[:80] + "..." if len(text) > 80 else text

    try:
        txt = mpy.TextClip(
            display_text,
            fontsize=50,
            color="white",
            font="Arial",
            stroke_color="black",
            stroke_width=2,
            method="caption",
            size=(VIDEO_WIDTH - 100, None),
            align="center",
        ).set_duration(duration).set_position("center")
        return mpy.CompositeVideoClip([bg, txt])
    except Exception:
        # Jesli TextClip sie nie uda - samo czarne tlo
        return bg


def _create_subtitle_clips(narration: str, total_duration: float) -> list:
    """
    Stworz klipy napisow w stylu TikTok dla danej narracji.
    Dzieli tekst na fragmenty i rozklada je w czasie.
    """
    import moviepy.editor as mpy

    chunks = split_into_subtitle_chunks(narration, max_chars=SUBTITLE_MAX_CHARS_PER_LINE)
    timed_chunks = distribute_subtitle_timing(chunks, total_duration)

    subtitle_clips = []
    y_pos = int(VIDEO_HEIGHT * SUBTITLE_Y_POSITION)

    for text, start, end in timed_chunks:
        duration = end - start
        if duration < 0.1:
            continue

        # Dwuliniowe napisy - polacz linie nowa linia
        display_text = text

        try:
            font_to_use = SUBTITLE_FONT if Path(SUBTITLE_FONT).exists() else "Arial"

            txt_clip = mpy.TextClip(
                display_text,
                fontsize=SUBTITLE_FONTSIZE,
                color=SUBTITLE_COLOR,
                font=font_to_use,
                stroke_color=SUBTITLE_STROKE_COLOR,
                stroke_width=SUBTITLE_STROKE_WIDTH,
                method="caption",
                size=(VIDEO_WIDTH - 60, None),
                align="center",
            )

            txt_clip = (
                txt_clip
                .set_start(start)
                .set_duration(duration)
                .set_position(("center", y_pos))
            )
            subtitle_clips.append(txt_clip)

        except Exception as e:
            # Jesli font nie dziala - pominij napisy dla tego fragmentu
            print(f"[Subtitles] Blad tworzenia napisu '{display_text[:20]}': {e}")
            continue

    return subtitle_clips
