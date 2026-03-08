#!/usr/bin/python3 -tt
# Project: naf_naf_solution_wizard
# Filename: utils.py
# claudiadeluna
# PyCharm

__author__ = "Claudia de Luna (claudia@indigowire.net)"
__version__ = ": 1.0 $"
__date__ = "11/25/25"
__copyright__ = "Copyright (c) 2025 Claudia"
__license__ = "Python"


# from __future__ import annotations

from typing import List, Optional
import streamlit as st


def thick_hr(color: str = "red", thickness: int = 3, margin: str = "1rem 0"):
    """
    Render a visually thicker horizontal line in Streamlit using raw HTML.

    Parameters
    - color: CSS color for the rule (named color or hex).
    - thickness: Pixel height of the line.
    - margin: CSS margin to apply (e.g., "1rem 0").

    Behavior
    - Uses st.markdown with unsafe_allow_html to inject an <hr> replacement.
    """
    st.markdown(
        f"""
        <hr style="
            border: none;
            height: {thickness}px;
            background-color: {color};
            margin: {margin};
        ">
        """,
        unsafe_allow_html=True,
    )


import base64
from pathlib import Path


def get_image_base64(image_path: str) -> str:
    """Convert an image file to base64 string for embedding in HTML."""
    try:
        full_path = Path(__file__).parent / image_path
        with open(full_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode()
    except Exception:
        return ""


def hr_colors():
    """
    Returns a dictionary of colors for horizontal lines.

    utils.thick_hr(color="#6785a0", thickness=3)
    """
    hr_color_dict = {
        "naf_yellow": "#fffe03",
        "eia_blue": "#92c0e4",
        "eia_dkblue": "#122e43",
    }
    return hr_color_dict



def render_global_sidebar() -> None:
    """Render global sidebar branding used across all pages.

    Includes the EIA logo, external links, and bottom NAF branding bar.
    """

    hr_color_dict = hr_colors()

    with st.sidebar:
        # Additional logo
        logo_transp_base64 = get_image_base64("images/logo_trim.png")
        if logo_transp_base64:
            st.markdown(
                f'<img src="data:image/jpeg;base64,{logo_transp_base64}" width="100%" style="margin-bottom: 1rem;">',
                unsafe_allow_html=True
            )
        else:
            # Fallback to non-clickable image if base64 fails
            st.image("images/logo_trim.png", width="stretch")

        # Bottom NAF branding bar with NAF icon

        _naf_logo_col, _naf_link_col = st.columns([1, 2])
        with _naf_logo_col:
            # Get base64 encoded image
            naf_logo_base64 = get_image_base64("images/naf_icon.png")
            if naf_logo_base64:
                st.markdown(
                    f'[<img src="data:image/png;base64,{naf_logo_base64}" width="100%">](https://networkautomation.forum/)',
                    unsafe_allow_html=True
                )
            else:
                # Fallback to non-clickable image if base64 fails
                st.image("images/naf_icon.png", width="stretch")
        with _naf_link_col:
            st.markdown("[🏠 NAF Home](https://networkautomation.forum/)")
            # linkedin.com/company/network-automation-forum/
            st.markdown(
                "[[in] NAF on LinkedIn](https://www.linkedin.com/company/network-automation-forum/)"
            )
        thick_hr(
            color=hr_color_dict.get("naf_yellow", "#fffe03"),
            thickness=6,
            margin="0.75rem 0 0.25rem 0",
        )




def join_human(items: List[str]) -> str:
    """
    Join a list of strings into a human-friendly phrase.

    Examples
    - ["A"] -> "A"
    - ["A","B"] -> "A and B"
    - ["A","B","C"] -> "A, B and C"

    Returns "TBD" when the input is empty or only contains falsey values.
    """
    items = [i for i in (items or []) if i]
    if not items:
        return "TBD"
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + f" and {items[-1]}"


def md_line(text: str) -> str:
    """
    Convert plain text to a single markdown bullet line.

    Parameters
    - text (str): Content to prefix with a dash.

    Returns
    - str: "- <text>" when text is truthy, else an empty string.
    """
    return f"- {text}" if text else ""


def is_meaningful(text: str) -> bool:
    """
    Determine if a narrative string is considered meaningful content.

    Rules
    - Empty/whitespace -> False
    - Contains "tbd" (case-insensitive) -> False
    - Matches any known default placeholder sentence -> False
    - Otherwise -> True
    """
    if not text:
        return False
    t = text.strip().lower()
    if not t or "tbd" in t:
        return False
    default_placeholders = {
        "no additional gating logic beyond the defined go/no-go criteria.",
        "this solution will not employ a distinct orchestration layer.",
    }
    return t not in default_placeholders


def main():
    """
    Module self-check entry point (optional).

    Purpose
    - Provides a basic callable for ad-hoc verification or future CLI hooks.

    Current behavior
    - No-op (pass). Keep in place to allow running this module directly without errors.
    """
    pass


# Standard call to the main() function.
if __name__ == "__main__":
    main()
