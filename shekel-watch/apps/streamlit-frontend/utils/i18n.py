"""
Lightweight i18n helper.

Usage:
    from utils.i18n import t, inject_dir

    t("key")               → translated string (falls back to English)
    t("key").format(...)   → with dynamic values
    inject_dir()           → inject RTL/LTR CSS on every page render
"""

import json
import os
import streamlit as st

_TRANSLATIONS_DIR = os.path.join(os.path.dirname(__file__), "..", "translations")
_cache: dict[str, dict] = {}

RTL_LANGS = {"he", "ar"}


def _load(lang: str) -> dict:
    """Load and cache a translation file. Returns {} if file missing."""
    if lang not in _cache:
        path = os.path.join(_TRANSLATIONS_DIR, f"{lang}.json")
        try:
            with open(path, encoding="utf-8") as f:
                _cache[lang] = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            _cache[lang] = {}
    return _cache[lang]


def t(key: str) -> str:
    """
    Return the translated string for *key* in the current session language.
    Falls back to English; if the key is missing in English too, returns the key itself.
    """
    lang = st.session_state.get("language", "en")
    val = _load(lang).get(key)
    if val is not None:
        return val
    # Fallback to English
    en_val = _load("en").get(key)
    return en_val if en_val is not None else key


def is_rtl() -> bool:
    return st.session_state.get("language", "en") in RTL_LANGS


def inject_dir() -> None:
    """
    Inject a <style> block that sets text direction based on current language.
    Call once near the top of every page, after set_page_config().
    Safe for charts/dataframes — only targets text containers.
    """
    if is_rtl():
        st.markdown(
            """
            <style>
            .block-container { direction: rtl !important; }
            .stMarkdown, .stText, .stCaption,
            p, h1, h2, h3, h4, h5, label,
            .stRadio label, .stSelectbox label,
            .stTextInput label, .stNumberInput label,
            .stToggle label, .stForm label { direction: rtl !important; text-align: right !important; }
            </style>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            "<style>.block-container { direction: ltr !important; }</style>",
            unsafe_allow_html=True,
        )
