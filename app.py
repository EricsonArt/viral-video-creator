"""
Viral Video Creator — Streamlit Web App
Wielouzytkownikowy system z izolowanymi B-rollami i wyborem modelu AI.

Uruchomienie lokalne:
    streamlit run app.py
"""

import json
import traceback
from pathlib import Path

import streamlit as st

from config import (
    BROLLS_DIR, OUTPUTS_DIR, TEMP_DIR,
    DEFAULT_TTS_VOICE, ALT_TTS_VOICE,
    DEFAULT_VIDEO_DURATION, SUPPORTED_DURATIONS,
    GROQ_API_KEY, ANTHROPIC_API_KEY, OLLAMA_BASE_URL,
)
from modules.utils import (
    generate_session_id, ensure_dirs,
    bytes_to_mb, extract_available_keywords, normalize_keyword,
)
from modules.script_generator import generate_script
from modules.broll_matcher import BRollMatcher
from modules.tts_engine import synthesize_all_scenes
from modules.video_assembler import assemble_video

# ============================================================
# KONFIGURACJA STRONY
# ============================================================

st.set_page_config(
    page_title="Viral Video Creator",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="collapsed",
)

ensure_dirs(BROLLS_DIR, OUTPUTS_DIR, TEMP_DIR)

# ============================================================
# SESSION STATE
# ============================================================

def init_state():
    defaults = {
        "phase": 1,
        # user_id - stabilny przez całą sesję przeglądarki (folder B-rolli)
        "user_id": generate_session_id(),
        # session_id - resetowany przy każdym nowym wideo (temp/output)
        "session_id": generate_session_id(),
        "script": None,
        "output_video_path": None,
        "error_msg": None,
        "gen_settings": {},
        # Klucze API użytkownika (opcjonalne nadpisanie domyślnych)
        "user_groq_key": "",
        "user_claude_key": "",
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


# ============================================================
# HELPERS
# ============================================================

def get_session_brolls_dir() -> Path:
    """Folder B-rolli izolowany per sesja przeglądarki."""
    d = BROLLS_DIR / st.session_state.user_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_effective_api_key(provider: str) -> str:
    """Zwróć aktywny klucz API: najpierw użytkownika, potem systemowy."""
    if provider == "groq":
        return st.session_state.get("user_groq_key", "").strip() or GROQ_API_KEY
    elif provider == "claude":
        return st.session_state.get("user_claude_key", "").strip() or ANTHROPIC_API_KEY
    return ""


def save_broll_file(uploaded_file) -> Path:
    import re
    stem = Path(uploaded_file.name).stem
    keyword = re.sub(r"_\d+$", "", stem)
    keyword_dir = get_session_brolls_dir() / normalize_keyword(keyword)
    keyword_dir.mkdir(parents=True, exist_ok=True)
    dest = keyword_dir / uploaded_file.name
    with open(dest, "wb") as f:
        f.write(uploaded_file.read())
    return dest


def get_all_broll_files() -> list[Path]:
    return sorted(get_session_brolls_dir().rglob("*.mp4"))


def run_pipeline(
    script: dict,
    voice: str,
    show_subtitles: bool,
    progress_bar,
    status_text,
    log_container,
) -> Path:
    """
    TTS + składanie wideo dla już wygenerowanego i dopasowanego skryptu.
    Zachowuje wszystkie ręczne korekty B-rolli z Fazy 2.
    """
    session_id = st.session_state.session_id
    temp_dir = TEMP_DIR / session_id
    output_dir = OUTPUTS_DIR / session_id
    ensure_dirs(temp_dir, output_dir)

    logs = []

    def log(msg: str):
        logs.append(msg)
        log_container.code("\n".join(logs), language="")

    # --- Krok 1: TTS ---
    log("[1/2] Generuję narrację lektora AI...")
    status_text.markdown("**Generuję narrację lektora AI...**")
    progress_bar.progress(0.05)

    def tts_progress(current, total, msg):
        if total > 0:
            prog = 0.05 + (current / max(total, 1)) * 0.55
            progress_bar.progress(min(prog, 0.60))
        log(f"    {msg}")

    script = synthesize_all_scenes(
        script=script,
        output_dir=temp_dir / "tts",
        voice=voice,
        prefer_local=False,
        progress_callback=tts_progress,
    )
    log("[OK] Narracja TTS wygenerowana")

    script_json_path = output_dir / "script.json"
    with open(script_json_path, "w", encoding="utf-8") as f:
        json.dump(script, f, ensure_ascii=False, indent=2)

    # --- Krok 2: Składanie wideo ---
    log("[2/2] Składam finalne wideo...")
    status_text.markdown("**Składam wideo (to może chwilę potrwać)...**")
    progress_bar.progress(0.65)

    def assembly_progress(current, total, msg):
        if total > 0:
            prog = 0.65 + (current / max(total, 1)) * 0.33
            progress_bar.progress(min(prog, 0.98))
        log(f"    {msg}")

    output_path = assemble_video(
        script=script,
        output_dir=output_dir,
        temp_dir=temp_dir / "clips",
        progress_callback=assembly_progress,
    )

    progress_bar.progress(1.0)
    log(f"[OK] Wideo gotowe: {output_path.name}")
    status_text.markdown("**Wideo gotowe!**")

    return output_path


# ============================================================
# FAZA 1: UPLOAD I USTAWIENIA
# ============================================================

PROVIDER_LABELS = {
    "groq":   "Groq / Llama 3.3 70B (Darmowy, zalecany)",
    "claude": "Claude Haiku (Najlepsza jakość, płatny)",
    "ollama": "Ollama (Lokalny, bezpłatny)",
}


def render_phase_1():
    st.title("Viral Video Creator")
    st.markdown("Automatyczne tworzenie wiralowych filmów z B-rollami i lektorem AI")

    col_left, col_right = st.columns([1, 1], gap="large")

    # ---- LEWA KOLUMNA: B-rolle ----
    with col_left:
        st.subheader("Twoje B-rolle")
        st.markdown(
            "Wgraj pliki wideo `.mp4`. Nazwa pliku = słowo kluczowe "
            "(np. `radość.mp4`, `praca_1.mp4`)"
        )

        uploaded = st.file_uploader(
            "Wgraj B-rolle",
            type=["mp4"],
            accept_multiple_files=True,
            label_visibility="collapsed",
        )

        if uploaded:
            for uf in uploaded:
                save_broll_file(uf)
            st.success(f"Wgrano {len(uploaded)} plik(ów) B-roll")

        existing = get_all_broll_files()
        brolls_dir = get_session_brolls_dir()

        if existing:
            st.markdown(f"**Dostępne B-rolle ({len(existing)}):**")
            for f in existing[:15]:
                rel = f.relative_to(brolls_dir)
                col_name, col_del = st.columns([4, 1])
                with col_name:
                    st.markdown(f"`{rel}`")
                with col_del:
                    if st.button("X", key=f"del_{f}", help="Usuń"):
                        f.unlink(missing_ok=True)
                        st.rerun()
            if len(existing) > 15:
                st.markdown(f"*...i {len(existing) - 15} więcej*")
        else:
            st.info("Brak wgranych B-rolli. Wgraj pliki powyżej.")

    # ---- PRAWA KOLUMNA: Ustawienia ----
    with col_right:
        st.subheader("Temat i ustawienia")

        topic = st.text_area(
            "Temat wideo",
            placeholder="np. 'Jak schudnąć 5 kg w miesiąc bez diety' lub 'Top 5 trików na lepszy sen'",
            height=100,
        )

        col_dur, col_tone = st.columns(2)
        with col_dur:
            duration = st.select_slider(
                "Długość wideo",
                options=SUPPORTED_DURATIONS,
                value=60,
                format_func=lambda x: f"{x}s",
            )
        with col_tone:
            tone = st.selectbox(
                "Ton skryptu",
                options=["energetic", "serious", "funny", "inspirational"],
                format_func=lambda x: {
                    "energetic": "Energiczny",
                    "serious": "Poważny",
                    "funny": "Zabawny",
                    "inspirational": "Inspirujący",
                }.get(x, x),
            )

        col_voice, col_sub = st.columns(2)
        with col_voice:
            voice = st.selectbox(
                "Głos lektora",
                options=[DEFAULT_TTS_VOICE, ALT_TTS_VOICE],
                format_func=lambda x: {
                    DEFAULT_TTS_VOICE: "Zofia (Kobieta)",
                    ALT_TTS_VOICE: "Marek (Mężczyzna)",
                }.get(x, x),
            )
        with col_sub:
            show_subtitles = st.toggle("Napisy na wideo", value=True)

        st.divider()

        # --- Wybór silnika AI ---
        st.markdown("**Silnik AI**")
        provider = st.radio(
            "Silnik AI",
            options=["groq", "claude", "ollama"],
            format_func=lambda x: PROVIDER_LABELS[x],
            index=0,
            label_visibility="collapsed",
        )

        # --- Klucze API ---
        with st.expander("Klucz API (kliknij aby rozwinąć)"):
            if provider == "groq":
                has_default = bool(GROQ_API_KEY)
                hint = "Zostaw puste — korzystamy z domyślnego klucza" if has_default else "Wymagany — darmowy klucz: console.groq.com"
                user_key = st.text_input(
                    "Groq API Key",
                    type="password",
                    placeholder=hint,
                    value=st.session_state.user_groq_key,
                    key="input_groq_key",
                )
                st.session_state.user_groq_key = user_key
                if not has_default and not user_key:
                    st.warning("Podaj klucz Groq API. Darmowy: console.groq.com")

            elif provider == "claude":
                has_default = bool(ANTHROPIC_API_KEY)
                hint = "Zostaw puste — korzystamy z domyślnego klucza" if has_default else "Wymagany — płatny: console.anthropic.com"
                user_key = st.text_input(
                    "Anthropic (Claude) API Key",
                    type="password",
                    placeholder=hint,
                    value=st.session_state.user_claude_key,
                    key="input_claude_key",
                )
                st.session_state.user_claude_key = user_key
                if not has_default and not user_key:
                    st.warning("Podaj klucz Claude API. Klucz: console.anthropic.com")

            elif provider == "ollama":
                st.info("Ollama nie wymaga klucza. Upewnij się, że serwer Ollama jest uruchomiony lokalnie.")

        # Walidacja przed generowaniem
        effective_key = get_effective_api_key(provider)
        key_ok = (provider == "ollama") or bool(effective_key)

        st.divider()

        can_generate = bool(topic.strip()) and bool(existing or uploaded) and key_ok

        if not topic.strip():
            st.caption("Wpisz temat wideo, żeby kontynuować")
        if not (existing or uploaded):
            st.caption("Wgraj przynajmniej jeden plik B-roll")
        if not key_ok:
            st.caption("Podaj klucz API dla wybranego silnika")

        if st.button("Generuj Skrypt", disabled=not can_generate, type="primary", use_container_width=True):
            with st.spinner("Generuję wiralowy skrypt..."):
                try:
                    brolls_dir = get_session_brolls_dir()
                    available_keywords = extract_available_keywords(brolls_dir)
                    api_key = get_effective_api_key(provider)

                    script = generate_script(
                        topic=topic,
                        broll_keywords_available=available_keywords,
                        target_duration=duration,
                        tone=tone,
                        tts_voice=voice,
                        show_subtitles=show_subtitles,
                        provider=provider,
                        api_key=api_key,
                        session_id=st.session_state.session_id,
                    )

                    matcher = BRollMatcher(
                        brolls_dir=brolls_dir,
                        llm_provider=provider,
                        api_key=api_key,
                    )
                    script = matcher.match_all_scenes(script)

                    st.session_state.script = script
                    st.session_state.gen_settings = {
                        "topic": topic,
                        "duration": duration,
                        "tone": tone,
                        "voice": voice,
                        "show_subtitles": show_subtitles,
                        "provider": provider,
                        "api_key": api_key,
                    }
                    st.session_state.error_msg = None
                    st.session_state.phase = 2
                    st.rerun()

                except Exception as e:
                    st.error(f"Błąd generowania skryptu: {e}")
                    st.code(traceback.format_exc())


# ============================================================
# FAZA 2: PODGLĄD SKRYPTU I KOREKTA DOPASOWAŃ
# ============================================================

def render_phase_2():
    st.title("Viral Video Creator — Podgląd Skryptu")

    script = st.session_state.script
    if not script:
        st.error("Brak skryptu. Wróć do fazy 1.")
        if st.button("Wróć"):
            st.session_state.phase = 1
            st.rerun()
        return

    meta = script.get("meta", {})
    col1, col2, col3, col4 = st.columns(4)
    topic_text = meta.get("topic", "-")
    col1.metric("Temat", topic_text[:30] + "..." if len(topic_text) > 30 else topic_text)
    col2.metric("Długość", f"{meta.get('target_duration_seconds', '-')}s")
    col3.metric("Sceny", len(script.get("scenes", [])))
    col4.metric("Ton", meta.get("tone", "-"))

    st.divider()

    brolls_dir = get_session_brolls_dir()
    all_broll_files = sorted(brolls_dir.rglob("*.mp4"))
    file_options = ["(brak - czarne tło)"] + [str(f.relative_to(brolls_dir)) for f in all_broll_files]
    file_paths = [None] + [str(f) for f in all_broll_files]

    st.subheader("HOOK")
    hook = script.get("hook", {})
    _render_segment_editor(hook, "hook", file_options, file_paths, brolls_dir, "text")

    st.subheader("Sceny")
    for i, scene in enumerate(script.get("scenes", [])):
        with st.expander(
            f"Scena {i+1}: {scene.get('narration', '')[:60]}...",
            expanded=(i < 3),
        ):
            _render_segment_editor(scene, f"scene_{i}", file_options, file_paths, brolls_dir, "narration")

    st.subheader("CTA (Call to Action)")
    cta = script.get("cta", {})
    _render_segment_editor(cta, "cta", file_options, file_paths, brolls_dir, "text")

    st.divider()

    col_back, col_gen = st.columns([1, 2])
    with col_back:
        if st.button("Wróć", use_container_width=True):
            st.session_state.phase = 1
            st.session_state.session_id = generate_session_id()
            st.rerun()
    with col_gen:
        if st.button("Generuj Wideo", type="primary", use_container_width=True):
            st.session_state.phase = 3
            st.rerun()

    with st.expander("Podgląd skryptu JSON (debug)"):
        st.json(script)


def _render_segment_editor(segment, seg_key, file_options, file_paths, brolls_dir, text_field):
    text = segment.get(text_field, "") or segment.get("narration", "") or segment.get("text", "")
    keyword = segment.get("broll_keyword", "-")
    matched_file = segment.get("matched_broll_file")
    score = segment.get("matched_broll_score", 0)

    col_text, col_broll = st.columns([3, 2])

    with col_text:
        st.markdown(f"**Narracja:** {text}")
        if keyword != "-":
            st.caption(f"Słowo kluczowe: `{keyword}`")

    with col_broll:
        if matched_file:
            rel_path = Path(matched_file).name
            score_color = "green" if score >= 70 else "orange" if score >= 40 else "red"
            st.markdown(
                f"`{rel_path}` "
                f"<span style='color:{score_color}'>({score:.0f}% pewności)</span>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown("*Brak dopasowania - czarne tło*")

        current_idx = 0
        if matched_file:
            try:
                current_idx = file_paths.index(matched_file)
            except ValueError:
                current_idx = 0

        selected_idx = st.selectbox(
            "Zmień B-roll",
            options=range(len(file_options)),
            index=current_idx,
            format_func=lambda x: file_options[x],
            key=f"broll_select_{seg_key}",
            label_visibility="collapsed",
        )

        new_file = file_paths[selected_idx]
        if new_file is None:
            segment["matched_broll_file"] = None
            segment["matched_broll_score"] = 0.0
        else:
            abs_path = str(brolls_dir / new_file) if not Path(new_file).is_absolute() else new_file
            segment["matched_broll_file"] = abs_path
            if selected_idx != current_idx:
                segment["matched_broll_score"] = 100.0


# ============================================================
# FAZA 3: GENEROWANIE WIDEO
# ============================================================

def render_phase_3():
    st.title("Viral Video Creator — Generowanie Wideo")

    script = st.session_state.script
    settings = st.session_state.get("gen_settings", {})

    if not script:
        st.error("Brak skryptu. Wróć do fazy 1.")
        if st.button("Wróć do początku"):
            st.session_state.phase = 1
            st.rerun()
        return

    if st.session_state.output_video_path:
        _render_download_section()
        return

    if st.session_state.error_msg:
        st.error(f"Błąd: {st.session_state.error_msg}")
        if st.button("Spróbuj ponownie"):
            st.session_state.error_msg = None
            st.session_state.phase = 2
            st.rerun()
        return

    st.markdown("### Trwa generowanie wideo...")

    progress_bar = st.progress(0.0)
    status_text = st.empty()
    log_container = st.empty()

    try:
        output_path = run_pipeline(
            script=script,
            voice=settings.get("voice", DEFAULT_TTS_VOICE),
            show_subtitles=settings.get("show_subtitles", True),
            progress_bar=progress_bar,
            status_text=status_text,
            log_container=log_container,
        )
        st.session_state.output_video_path = str(output_path)
        st.rerun()

    except Exception as e:
        st.session_state.error_msg = str(e)
        st.error(f"Błąd podczas generowania: {e}")
        st.code(traceback.format_exc())
        if st.button("Wróć do podglądu skryptu"):
            st.session_state.error_msg = None
            st.session_state.phase = 2
            st.rerun()


def _render_download_section():
    output_path = Path(st.session_state.output_video_path)

    st.success("Wideo gotowe!")

    if output_path.exists():
        file_size = bytes_to_mb(output_path.stat().st_size)

        col_info, col_download = st.columns([2, 1])

        with col_info:
            st.markdown(f"**Plik:** `{output_path.name}`")
            st.markdown(f"**Rozmiar:** {file_size} MB")
            try:
                st.video(str(output_path))
            except Exception:
                st.info("Podgląd niedostępny — pobierz plik.")

        with col_download:
            with open(output_path, "rb") as f:
                st.download_button(
                    label="Pobierz wideo",
                    data=f,
                    file_name=output_path.name,
                    mime="video/mp4",
                    use_container_width=True,
                    type="primary",
                )

    st.divider()

    if st.button("Stwórz nowe wideo", use_container_width=True):
        # Nowa sesja wideo, ale user_id (i B-rolle) zostają
        st.session_state.session_id = generate_session_id()
        st.session_state.phase = 1
        st.session_state.script = None
        st.session_state.output_video_path = None
        st.session_state.error_msg = None
        st.rerun()


# ============================================================
# GŁÓWNA PĘTLA
# ============================================================

def main():
    init_state()

    phase = st.session_state.phase

    if phase == 1:
        render_phase_1()
    elif phase == 2:
        render_phase_2()
    elif phase == 3:
        render_phase_3()
    else:
        st.session_state.phase = 1
        st.rerun()


if __name__ == "__main__":
    main()
