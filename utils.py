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
