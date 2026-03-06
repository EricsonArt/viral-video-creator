import re
import uuid
from pathlib import Path


# Mapowanie polskich znakow na ASCII
_POLISH_MAP = str.maketrans(
    "ąćęłńóśźżĄĆĘŁŃÓŚŹŻ",
    "acelnoszzACELNOSZZ"
)


def normalize_polish_to_ascii(text: str) -> str:
    """Zamien polskie znaki diakrytyczne na ASCII. ą→a, ę→e, ó→o, itd."""
    return text.translate(_POLISH_MAP)


def normalize_keyword(text: str) -> str:
    """Normalizuj slowo kluczowe: polskie znaki → ASCII, male litery, tylko alfanumeryczne."""
    text = normalize_polish_to_ascii(text.lower())
    text = re.sub(r"[^a-z0-9]+", "_", text).strip("_")
    return text


def generate_session_id() -> str:
    """Generuj krotki unikalny identyfikator sesji (12 znakow hex)."""
    return uuid.uuid4().hex[:12]


def sanitize_filename(name: str) -> str:
    """Zrob z dowolnego stringa bezpieczna nazwe pliku."""
    name = normalize_polish_to_ascii(name)
    name = re.sub(r"[^\w\-_.]", "_", name)
    return name.strip("._")[:64]


def ensure_dirs(*paths: Path) -> None:
    """Stworz katalogi jesli nie istnieja."""
    for path in paths:
        path.mkdir(parents=True, exist_ok=True)


def extract_available_keywords(brolls_dir: Path) -> list[str]:
    """
    Skanuj katalog /brolls/ i zwroc liste unikalnych slow kluczowych.
    Kazdy podkatalog + kazdy plik .mp4 bez rozszerzenia jest slow kluczem.
    Zwraca oryginalne nazwy (z polskimi znakami jesli sa w nazwach).
    """
    keywords = set()
    if not brolls_dir.exists():
        return []

    for item in brolls_dir.iterdir():
        if item.is_dir():
            # Nazwa katalogu to slowo kluczowe
            keywords.add(item.name)
            # Pliki wideo w katalogu tez sa slow kluczami
            for video_file in item.glob("*.mp4"):
                # Usun numer na koncu: radosc_1 → radosc
                stem = re.sub(r"_\d+$", "", video_file.stem)
                keywords.add(stem)
        elif item.suffix.lower() == ".mp4":
            # Pliki .mp4 bezposrednio w /brolls/
            stem = re.sub(r"_\d+$", "", item.stem)
            keywords.add(stem)

    return sorted(keywords)


def get_all_broll_files(brolls_dir: Path) -> list[Path]:
    """Zwroc liste wszystkich plikow .mp4 w katalogu brolls/."""
    if not brolls_dir.exists():
        return []
    files = list(brolls_dir.rglob("*.mp4"))
    return sorted(files)


def get_video_metadata(video_path: Path) -> dict:
    """
    Zwroc metadane wideo: duration, width, height, fps.
    Uzywamy moviepy - nie wymaga dodatkowych zaleznosci.
    """
    try:
        from moviepy.editor import VideoFileClip
        with VideoFileClip(str(video_path)) as clip:
            return {
                "duration": clip.duration,
                "width": clip.w,
                "height": clip.h,
                "fps": clip.fps,
            }
    except Exception as e:
        return {"duration": 0, "width": 0, "height": 0, "fps": 0, "error": str(e)}


def format_duration(seconds: float) -> str:
    """Formatuj sekundy jako MM:SS."""
    seconds = int(seconds)
    m, s = divmod(seconds, 60)
    return f"{m:02d}:{s:02d}"


def bytes_to_mb(size_bytes: int) -> float:
    """Przelicz bajty na megabajty."""
    return round(size_bytes / (1024 * 1024), 1)


def split_into_subtitle_chunks(text: str, max_chars: int = 28) -> list[str]:
    """
    Podziel tekst na linie do napisow.
    Respektuje granice slow, max max_chars znakow na linie.
    """
    words = text.split()
    lines = []
    current = []
    current_len = 0

    for word in words:
        # +1 dla spacji
        if current_len + len(word) + (1 if current else 0) <= max_chars:
            current.append(word)
            current_len += len(word) + (1 if len(current) > 1 else 0)
        else:
            if current:
                lines.append(" ".join(current))
            current = [word]
            current_len = len(word)

    if current:
        lines.append(" ".join(current))

    return lines


def distribute_subtitle_timing(
    chunks: list[str],
    total_duration: float
) -> list[tuple[str, float, float]]:
    """
    Przypisz czas poczatku i konca do kazdego fragmentu napisu.
    Rozklada proporcjonalnie do liczby znakow.
    Zwraca liste (text, start_time, end_time).
    """
    if not chunks:
        return []

    total_chars = sum(len(c) for c in chunks)
    if total_chars == 0:
        return [(c, 0.0, total_duration) for c in chunks]

    result = []
    t = 0.0
    for chunk in chunks:
        proportion = len(chunk) / total_chars
        duration = total_duration * proportion
        result.append((chunk, t, t + duration))
        t += duration

    return result
