import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


def _get_secret(key: str, default: str = "") -> str:
    """Czyta sekret z Streamlit Secrets lub zmiennej środowiskowej (.env)."""
    try:
        import streamlit as st
        val = st.secrets.get(key, "")
        if val:
            return str(val)
    except Exception:
        pass
    return os.getenv(key, default)


# --- Sciezki ---
BASE_DIR = Path(__file__).parent
BROLLS_DIR = BASE_DIR / "brolls"
OUTPUTS_DIR = BASE_DIR / "outputs"
TEMP_DIR = BASE_DIR / "temp"
FONTS_DIR = BASE_DIR / "fonts"

# --- Groq (darmowy LLM w chmurze, domyslny) ---
GROQ_API_KEY: str = _get_secret("GROQ_API_KEY")
GROQ_MODEL: str = "llama-3.3-70b-versatile"

# --- Claude API ---
ANTHROPIC_API_KEY: str = _get_secret("ANTHROPIC_API_KEY")
CLAUDE_MODEL: str = "claude-haiku-4-5-20251001"

# --- Ollama (lokalny LLM) ---
OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3.2")

# --- TTS ---
DEFAULT_TTS_VOICE: str = "pl-PL-ZofiaNeural"
ALT_TTS_VOICE: str = "pl-PL-MarekNeural"
TTS_RATE: str = "+10%"
TTS_VOLUME: str = "+0%"
TTS_PITCH: str = "+0Hz"

# --- Dopasowanie B-rolli ---
FUZZY_MATCH_THRESHOLD: int = 70

# --- Wideo ---
VIDEO_WIDTH: int = 1080
VIDEO_HEIGHT: int = 1920
VIDEO_FPS: int = 30
VIDEO_CODEC: str = "libx264"
AUDIO_CODEC: str = "aac"
VIDEO_BITRATE: str = "4000k"
MAX_SCENE_DURATION: float = 20.0
MIN_SCENE_DURATION: float = 2.0

# --- Napisy ---
SUBTITLE_FONT: str = str(FONTS_DIR / "NotoSans-Regular.ttf")
SUBTITLE_FONTSIZE: int = 60
SUBTITLE_COLOR: str = "white"
SUBTITLE_STROKE_COLOR: str = "black"
SUBTITLE_STROKE_WIDTH: int = 3
SUBTITLE_Y_POSITION: float = 0.82
SUBTITLE_MAX_CHARS_PER_LINE: int = 28

# --- Skrypt ---
DEFAULT_VIDEO_DURATION: int = 60
DEFAULT_TONE: str = "energetic"
SUPPORTED_TONES: list = ["energetic", "serious", "funny", "inspirational"]
SUPPORTED_DURATIONS: list = [30, 60, 90]
