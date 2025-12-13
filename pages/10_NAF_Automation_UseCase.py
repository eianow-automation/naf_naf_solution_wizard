#!/usr/bin/python3 -tt
from __future__ import annotations
# Project: naf_naf_solution_wizard
# Filename: naf_naf_solution_wizard.py
# claudiadeluna
# PyCharm

__author__ = "Claudia de Luna (claudia@indigowire.net)"
__version__ = ": 1.0 $"
__date__ = "11/25/25"
__copyright__ = "Copyright (c) 2025 Claudia"
__license__ = "Python"


import os
from pathlib import Path
from typing import Any, Dict, List

import streamlit as st
import yaml
from NAF_NAF_Solution_Wizard import render_global_sidebar

# Page config for consistent favicon across all pages
st.set_page_config(
    page_title="Automation Use Cases",
    page_icon="images/EIA_Favicon.png",
    layout="wide",
)


def _ensure_state() -> None:
    """Ensure the use_cases list and active index exist in session_state."""

    if "use_cases" not in st.session_state or not isinstance(
        st.session_state.get("use_cases"), list
    ):
        st.session_state["use_cases"] = []

    if "use_case_active_index" not in st.session_state:
        st.session_state["use_case_active_index"] = 0 if st.session_state["use_cases"] else -1


def _new_use_case() -> Dict[str, Any]:
    """Return a new blank use case record."""

    return {
        "name": "",
        "description": "",
        "expected_outcome": "",
        "category": "",
        "assumptions": "",
        "trigger": "",
        "building_blocks": "",
        "setup_task": "",
        "tasks": "",
        "standard_deployment_strategy": "",
        "deployment_strategy": "",
        "error_conditions": "",
    }


def _label_for(idx: int, uc: Dict[str, Any]) -> str:
    """Generate a short label for a use case selector."""

    base = (uc.get("name") or uc.get("description") or "Use Case").strip() or "Use Case"
    return f"{idx + 1}. {base[:60]}"  # pragma: no cover - UI detail


def _select_use_case() -> int:
    """Render selector for existing use cases and return active index (or -1)."""

    use_cases: List[Dict[str, Any]] = st.session_state.get("use_cases", [])
    if not use_cases:
        return -1

    labels = [_label_for(i, uc) for i, uc in enumerate(use_cases)]
    default_idx = st.session_state.get("use_case_active_index", 0)
    if default_idx < 0 or default_idx >= len(labels):
        default_idx = 0

    sel = st.selectbox(
        "Select a use case to view/edit",
        options=list(range(len(labels))),
        format_func=lambda i: labels[i],
        index=default_idx,
        key="use_case_selector",
    )
    st.session_state["use_case_active_index"] = int(sel)
    return int(sel)


def _edit_use_case(idx: int) -> None:
    """Render fields to edit a single use case in-place in session_state."""

    use_cases: List[Dict[str, Any]] = st.session_state.get("use_cases", [])
    if idx < 0 or idx >= len(use_cases):
        return

    uc = use_cases[idx]

    st.subheader("Use Case Details")

    # Use case name
    uc["name"] = st.text_input(
        "Use case name",
        value=uc.get("name", ""),
        key=f"uc_name_{idx}",
        help="Name of the use case.",
    )

    # Description / Problem Statement
    uc["description"] = st.text_area(
        "Description / Problem Statement",
        value=uc.get("description", ""),
        key=f"uc_description_{idx}",
        height=80,
        help="A brief description of the use case and the problem statement.",
    )

    # Expected Outcome
    uc["expected_outcome"] = st.text_area(
        "Expected Outcome",
        value=uc.get("expected_outcome", ""),
        key=f"uc_expected_outcome_{idx}",
        height=80,
        help="A brief description of what we expect the automation to do.",
    )

    # Category (load from YAML file)
    yaml_path = Path(__file__).parent.parent / "use_case_categories.yml"
    try:
        with open(yaml_path, "r") as f:
            categories_data = yaml.safe_load(f)
        category_options = list(categories_data.keys()) if categories_data else []
    except Exception:
        category_options = []
    # Add placeholder as first option
    placeholder = "— Select a category —"
    category_options_with_placeholder = [placeholder] + category_options
    current_cat = uc.get("category", "") or placeholder
    if current_cat not in category_options_with_placeholder:
        current_cat = "Other"
    cat = st.selectbox(
        "Category",
        options=category_options_with_placeholder,
        index=category_options_with_placeholder.index(current_cat)
        if current_cat in category_options_with_placeholder
        else 0,
        key=f"uc_category_{idx}",
        help=(
            "Select a category from the list. Choose 'Other' if your use case "
            "doesn't fit the predefined categories."
        ),
    )
    if cat == placeholder:
        st.info("💡 Please select a category from the list above.")
        uc["category"] = ""
    elif cat == "Other":
        cat_other = st.text_input(
            "Custom category",
            value=uc.get("category", "")
            if uc.get("category") not in category_options
            else "",
            key=f"uc_category_other_{idx}",
        )
        uc["category"] = cat_other or cat
    else:
        uc["category"] = cat

    # Assumptions
    uc["assumptions"] = st.text_area(
        "Assumptions",
        value=uc.get("assumptions", ""),
        key=f"uc_assumptions_{idx}",
        height=80,
        help="What are the assumptions made for this use case?",
    )

    # Trigger
    uc["trigger"] = st.text_area(
        "Trigger",
        value=uc.get("trigger", ""),
        key=f"uc_trigger_{idx}",
        height=80,
        help=(
            "What triggers this use case? For example: Alert, planned event "
            "(scaling, feature add, etc.)."
        ),
    )

    # Building Blocks
    uc["building_blocks"] = st.text_area(
        "Building Blocks",
        value=uc.get("building_blocks", ""),
        key=f"uc_building_blocks_{idx}",
        height=100,
        help=(
            "Describe how this use case uses the building blocks and highlight "
            "specific capabilities of these building blocks."
        ),
    )

    # Setup Task
    uc["setup_task"] = st.text_area(
        "Setup Task",
        value=uc.get("setup_task", ""),
        key=f"uc_setup_task_{idx}",
        height=100,
        help=(
            "What is required for this task? Examples include a new config "
            "file/template."
        ),
    )

    # Task(s)
    uc["tasks"] = st.text_area(
        "Task(s)",
        value=uc.get("tasks", ""),
        key=f"uc_tasks_{idx}",
        height=120,
        help=(
            "What tasks can be done for this use case? For example, a config "
            "update use case can have many tasks such as add/delete/change "
            "VLAN, ACL, SNMP community, BGP peer, etc."
        ),
    )

    # Standard Deployment Strategy (load from YAML file)
    deploy_yaml_path = Path(__file__).parent.parent / "deployment_strategies.yml"
    try:
        with open(deploy_yaml_path, "r") as f:
            deploy_data = yaml.safe_load(f)
        deploy_options = list(deploy_data.keys()) if deploy_data else []
    except Exception:
        deploy_options = []
    # Add placeholder as first option
    deploy_placeholder = "— Select a deployment strategy —"
    deploy_options_with_placeholder = [deploy_placeholder] + deploy_options
    current_deploy = uc.get("standard_deployment_strategy", "") or deploy_placeholder
    if current_deploy not in deploy_options_with_placeholder:
        current_deploy = deploy_placeholder
    deploy_sel = st.selectbox(
        "Standard Deployment Strategy",
        options=deploy_options_with_placeholder,
        index=deploy_options_with_placeholder.index(current_deploy)
        if current_deploy in deploy_options_with_placeholder
        else 0,
        key=f"uc_standard_deployment_strategy_{idx}",
        help="Select a standard deployment strategy from the list.",
    )
    if deploy_sel == deploy_placeholder:
        st.info("💡 Please select a deployment strategy from the list above.")
        uc["standard_deployment_strategy"] = ""
    else:
        uc["standard_deployment_strategy"] = deploy_sel

    # Deployment Strategy Description (optional)
    uc["deployment_strategy"] = st.text_area(
        "Deployment Strategy Description (optional)",
        value=uc.get("deployment_strategy", ""),
        key=f"uc_deployment_strategy_{idx}",
        height=80,
        help="Additional details about how the automation is deployed.",
    )

    # Error Conditions
    uc["error_conditions"] = st.text_area(
        "Error Conditions",
        value=uc.get("error_conditions", ""),
        key=f"uc_error_conditions_{idx}",
        height=120,
        help=(
            "What errors could we encounter and how are they handled? "
            "For example, a mismatch between intended state and what is "
            "on the device."
        ),
    )

    # Persist edits back to the list
    st.session_state["use_cases"][idx] = uc


def main() -> None:
    """
    Streamlit page: NAF Automation Use Case

    This page is used to capture one or more automation use cases that will be
    associated with the Solution Wizard report. Data is stored in
    st.session_state['use_cases'] so it can be consumed by the
    Solution Wizard export.

    Render the NAF Automation Use Case page.


    """

    # Shared sidebar branding
    render_global_sidebar()

    st.title("Automation Use Cases")
    st.caption(
        "Capture one or more automation use cases that will be associated with the "
        "Solution Wizard Report."
    )

    _ensure_state()

    # Controls to add/remove use cases
    control_col1, control_col2 = st.columns([1, 1])
    with control_col1:
        if st.button("➕ Add new use case", key="uc_add_new"):
            st.session_state["use_cases"].append(_new_use_case())
            st.session_state["use_case_active_index"] = len(
                st.session_state["use_cases"]
            ) - 1
    with control_col2:
        use_cases = st.session_state.get("use_cases", [])
        if use_cases:
            if st.button("🗑️ Delete current use case", key="uc_delete_current"):
                idx = st.session_state.get("use_case_active_index", 0)
                if 0 <= idx < len(use_cases):
                    use_cases.pop(idx)
                    st.session_state["use_cases"] = use_cases
                    if use_cases:
                        st.session_state["use_case_active_index"] = min(
                            idx, len(use_cases) - 1
                        )
                    else:
                        st.session_state["use_case_active_index"] = -1

    st.markdown("---")

    active_idx = _select_use_case()

    if active_idx == -1:
        st.info("No use cases defined yet. Click **Add new use case** to begin.")
        return

    _edit_use_case(active_idx)

    # Optional preview of all use cases at the bottom
    with st.expander("Preview all use cases (read-only)", expanded=False):
        for i, uc in enumerate(st.session_state.get("use_cases", [])):
            st.markdown(f"#### Use Case {i + 1}: {uc.get('name') or '(Untitled)'}")
            if uc.get("description"):
                st.markdown(uc["description"])
            st.markdown("---")


if __name__ == "__main__":  # pragma: no cover - Streamlit entry
    main()
