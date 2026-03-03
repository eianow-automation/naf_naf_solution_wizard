#!/usr/bin/python3 -tt
# Project: naf_naf_solution_wizard
# Filename: naf_naf_solution_wizard.py
# claudiadeluna
# PyCharm

__author__ = "Claudia de Luna (claudia@indigowire.net)"
__version__ = ": 1.0 $"
__date__ = "11/25/25"
__copyright__ = "Copyright (c) 2025 Claudia"
__license__ = "Python"

# Streamlit page: NAF Solution Wizard
#
# This page hosts the main Solution Wizard experience for the
# Network Automation Forum's Network Automation Framework (NAF).
#
# The implementation lives in NAF_NAF_Solution_Wizard.solution_wizard_main.


# from NAF_NAF_Solution_Wizard import solution_wizard_main


# When this file is run as a Streamlit page, simply delegate to the
# existing Solution Wizard implementation.
# solution_wizard_main()


from typing import List
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

import io
import re
import json
import yaml
import zipfile
import datetime
import pandas as pd
import streamlit as st
import plotly.express as px
import getpass
import os

import utils

# Optional lightweight holiday support
try:
    import holidays as _hol
except Exception:  # pragma: no cover
    _hol = None


# --- Module-level constants ---
# Default values to avoid repetition
DEFAULT_TITLE = "My new network automation project"
DEFAULT_DESCRIPTION = "Here is a short description of my new network automation project"
DEFAULT_DEPLOYMENT_STRATEGY_PLACEHOLDER = "— Select a deployment strategy —"
DEFAULT_CATEGORY_PLACEHOLDER = "— Select a category —"


# Utility functions moved to utils.py - local aliases for brevity
join_human = utils.join_human
md_line = utils.md_line
is_meaningful = utils.is_meaningful
_join = utils.join_human


# --- Module-level helper functions ---


def _sorted_deps(items):
    """Sort dependency items by name and details for comparison."""
    return sorted(items, key=lambda x: (x.get("name") or "", x.get("details") or ""))


def _render_template_preview(payload: dict, summary_md: str) -> str:
    """Render the Jinja template for preview, removing images."""
    try:
        templates_dir = (Path(__file__).parent.parent / "templates").resolve()
        env = Environment(
            loader=FileSystemLoader(str(templates_dir)),
            autoescape=False,
        )
        tmpl = env.get_template("Solution_Design_Report.j2")
        sdd_ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        context = {
            "generated_timestamp": sdd_ts,
            "highlights": summary_md,
            "initiative": payload.get("initiative", {}),
            "my_role": payload.get("my_role", {}),
            "stakeholders": payload.get("stakeholders", {}),
            "presentation": payload.get("presentation", {}),
            "intent": payload.get("intent", {}),
            "observability": payload.get("observability", {}),
            "orchestration": payload.get("orchestration", {}),
            "collector": payload.get("collector", {}),
            "executor": payload.get("executor", {}),
            "dependencies": payload.get("dependencies", {}),
            "timeline": payload.get("timeline", {}),
        }
        
        rendered = tmpl.render(**context)
        
        # Remove image references from the rendered markdown
        import re
        # Remove markdown image syntax: ![alt text](url)
        rendered = re.sub(r'!\[([^\]]*)\]\([^)]+\)', r'[\1]', rendered)
        # Remove HTML img tags
        rendered = re.sub(r'<img[^>]+src="[^"]+"[^>]*>', '', rendered)
        
        return rendered
    except Exception as e:
        # Fallback to simple summary if template rendering fails
        return f"Error rendering template: {e}\n\n---\n\n{summary_md}"


def _has_list_selections(d: dict) -> bool:
    """Check if a dict contains any non-empty list values."""
    return any(isinstance(v, list) and v for v in d.values())


def _norm_role_choice(choice, other, sentinel="— Select one —"):
    """Normalize a role radio choice, handling 'Other' and sentinel values."""
    if choice == "Other (fill in)":
        return (other or "").strip()
    if choice == sentinel:
        return ""
    return choice or ""


def _add_business_days(d, n, holiday_set=None):
    """Add n business days (Mon-Fri) to date d, optionally skipping holidays."""
    days = int(n or 0)
    cur = d
    while days > 0:
        cur = cur + datetime.timedelta(days=1)
        if cur.weekday() < 5 and (holiday_set is None or cur not in holiday_set):
            days -= 1
    return cur


def _section_md(title, lines):
    """Build a markdown section with title and bullet lines."""
    lines = [l for l in (lines or []) if (l or "").strip()]
    if not lines:
        return ""
    return f"## {title}\n" + "\n".join(lines) + "\n\n"


def _sanitize_title(t: str) -> str:
    """Sanitize a title string for use in filenames."""
    t = (t or "").strip()
    out = []
    for ch in t:
        if ch.isalnum() or ch in {"-", "_"}:
            out.append(ch)
        else:
            out.append("_")
    t = "".join(out)
    while "__" in t:
        t = t.replace("__", "_")
    t = t.strip("_")
    return (t or "solution")[0:30]


def _load_stakeholders_catalog() -> dict:
    p = Path(__file__).resolve().parents[1] / "stakeholders.json"
    try:
        raw = p.read_text(encoding="utf-8")
    except Exception:
        return {}

    for _ in range(2):
        try:
            data = json.loads(raw)
            return data if isinstance(data, dict) else {}
        except Exception:
            raw = (raw or "").strip()
            if raw.endswith("."):
                raw = raw[:-1]
                continue
            return {}


def _has_any_content(p: dict) -> bool:
    """Determine if payload has meaningful content beyond defaults."""
    try:
        pres_narr = p.get("presentation", {}) or {}
        intent_narr = p.get("intent", {}) or {}
        obs_narr = p.get("observability", {}) or {}
        orch_narr = p.get("orchestration", {}) or {}
        coll_narr = p.get("collector", {}) or {}
        exec_narr = p.get("executor", {}) or {}
        deps = p.get("dependencies", []) or []
        tl = p.get("timeline", {}) or {}
        ini = p.get("initiative", {}) or {}
        my_role = p.get("my_role", {}) or {}

        pres_flag = any(
            is_meaningful(pres_narr.get(k))
            for k in ("users", "interaction", "tools", "auth")
        )
        intent_flag = any(
            is_meaningful(intent_narr.get(k)) for k in ("development", "provided")
        )
        obs_flag = any(
            is_meaningful(obs_narr.get(k))
            for k in ("methods", "go_no_go", "additional_logic", "tools")
        )
        _orch_sel = (
            (orch_narr.get("selections") or {}) if isinstance(orch_narr, dict) else {}
        )
        _orch_choice = (_orch_sel.get("choice") or "").strip()
        orch_flag = bool(
            _orch_choice and _orch_choice != "— Select one —"
        ) or is_meaningful(orch_narr.get("summary"))
        coll_flag = any(
            is_meaningful(coll_narr.get(k))
            for k in ("methods", "auth", "handling", "normalization", "scale", "tools")
        )
        exec_flag = is_meaningful(exec_narr.get("methods"))

        deps_flag = False
        if deps:
            deps_slim = [
                {
                    "name": (d or {}).get("name"),
                    "details": (d or {}).get("details", "").strip(),
                }
                for d in deps
                if (d or {}).get("name")
            ]
            default_deps = [
                {"name": "Network Infrastructure", "details": ""},
                {"name": "Revision Control system", "details": "GitHub"},
            ]
            deps_flag = _sorted_deps(deps_slim) != _sorted_deps(default_deps)

        tl_flag = bool((tl.get("staffing_plan_md") or "").strip())

        default_title = DEFAULT_TITLE
        default_desc = DEFAULT_DESCRIPTION
        title = (ini.get("title") or "").strip()
        desc = (ini.get("description") or "").strip()
        ini_flag = bool(
            (title and title != default_title) or (desc and desc != default_desc)
        )
        role_flag = any(
            ((my_role.get(k) or "").strip()) for k in ("who", "skills", "developer")
        )

        return any(
            [
                pres_flag,
                intent_flag,
                obs_flag,
                orch_flag,
                coll_flag,
                exec_flag,
                deps_flag,
                tl_flag,
                ini_flag,
                role_flag,
            ]
        )
    except Exception:
        pass
    return False


# --- End module-level helper functions ---


def solution_wizard_main():
    """
    Solution Wizard (NAF Framework) interactive page

    A comprehensive tool for designing network automation solutions using the
    Network Automation Forum's Network Automation Framework (NAF).

    Includes guided inputs for:
    - Initiative: Title, description, category, problem statement, expected use,
      error conditions, assumptions, deployment strategy
    - Stakeholders: Who is supporting the project
    - My Role: Who is filling out the wizard and their skills
    - Presentation: User types, interaction modes, presentation tools, authentication
    - Intent: Development approaches, provided formats
    - Observability: Methods, go/no-go criteria, additional logic, tools
    - Orchestration: Choice and details for workflow automation
    - Collector: Methods, authentication, handling, normalization, scale, tools
    - Executor: Methods for executing automation

    Planning section:
    - "Staffing, Timeline, & Milestones" with:
      - Staffing fields (direct staff count and markdown-supported staffing plan)
      - Start date calendar
      - Editable milestone rows (name, duration in business days, notes)
      - Business-day scheduling that skips weekends and optionally public holidays (via python-holidays)
      - Optional Plotly Gantt chart visualization
      - Summary callouts for expected delivery date (st.success) and approximate duration in months/years (st.info)

    Dependencies section:
    - Add/remove network infrastructure dependencies
    - Default dependencies: Network Infrastructure, Revision Control system

    Export functionality:
    - Download complete solution design as ZIP with JSON and Markdown files
    - Upload previously saved JSON to restore wizard state
    - Solution Design Document template with all sections

    ==================================================================================
    STATE PERSISTENCE (LEGACY)
    ==================================================================================
    Previously used backing storage pattern for inter-page navigation.
    With single-page operation, widget state persists naturally.
    Legacy code marked for potential removal:
    - "_wizard_data": dict storing scalar field values
    - "_wizard_checkboxes": dict storing checkbox/toggle states

    ==================================================================================
    GUI FIELD TO VARIABLE MAPPING
    ==================================================================================
    Below is a mapping of GUI field labels to their session_state keys and types.

    MY ROLE SECTION:
    ---------------------------------------------------------------------------------
    GUI Label                                    | st.session_state Key     | Type
    ---------------------------------------------------------------------------------
    Who's filling out this wizard?               | my_role_who              | str (radio, single)
    What best describes your technical skills?   | my_role_skills           | str (radio, single)
    Who will actually develop the automation?    | my_role_dev              | str (radio, single)

    INITIATIVE/PROJECT SECTION:
    ---------------------------------------------------------------------------------
    GUI Label                                    | st.session_state Key             | Type
    ---------------------------------------------------------------------------------
    Automation initiative title                  | _wizard_automation_title         | str (text_input)
    Short description / scope                    | _wizard_automation_description   | str (text_area)
    Problem statement                            | _wizard_problem_statement        | str (text_area)
    Expected use (Markdown supported)            | _wizard_expected_use             | str (text_area)
    Out of scope (optional)                      | _wizard_out_of_scope             | str (text_area)
    Standard reasons                             | no_move_forward_reasons          | list[str] (multiselect, multi)
    Additional risks in not moving forward       | no_move_forward                  | str (text_area)

    PRESENTATION SECTION:
    ---------------------------------------------------------------------------------
    GUI Label                                    | st.session_state Key Pattern     | Type
    ---------------------------------------------------------------------------------
    Intended users checkboxes                    | pres_user_{option}               | bool (checkbox, multi)
    Custom users enable                          | pres_user_custom_enable          | bool (checkbox)
    Custom users text                            | pres_user_custom                 | str (text_input)
    Interaction method checkboxes                | pres_interact_{option}           | bool (checkbox, multi)
    Custom interaction enable                    | pres_interact_custom_enable      | bool (checkbox)
    Tools checkboxes                             | pres_tool_{option}               | bool (checkbox, multi)
    Custom tool enable                           | pres_tool_custom_enable          | bool (checkbox)
    Authentication checkboxes                    | pres_auth_{option}               | bool (checkbox, multi)
    Other auth enable                            | pres_auth_other_enable           | bool (checkbox)
    Other auth details                           | pres_auth_other_text             | str (text_input)

    INTENT SECTION:
    ---------------------------------------------------------------------------------
    GUI Label                                    | st.session_state Key Pattern     | Type
    ---------------------------------------------------------------------------------
    Intent development checkboxes                | intent_dev_{option}              | bool (checkbox, multi)
    Custom intent enable                         | intent_dev_custom_enable         | bool (checkbox)
    Intent provision checkboxes                  | intent_prov_{option}             | bool (checkbox, multi)
    Custom provision enable                      | intent_prov_custom_enable        | bool (checkbox)

    OBSERVABILITY SECTION:
    ---------------------------------------------------------------------------------
    GUI Label                                    | st.session_state Key Pattern     | Type
    ---------------------------------------------------------------------------------
    State representation checkboxes              | obs_state_{option}               | bool (checkbox, multi)
    Observability tools checkboxes               | obs_tool_{option}                | bool (checkbox, multi)
    Other tool enable                            | obs_tool_other_enable            | bool (checkbox)
    Other tool text                              | obs_tool_other_text              | str (text_input)
    Go/No-Go criteria                            | obs_go_no_go                     | str (text_area)
    Additional gating logic choice               | obs_add_logic_choice             | str (radio, single)
    Additional gating logic text                 | obs_add_logic_text               | str (text_area)

    ORCHESTRATION SECTION:
    ---------------------------------------------------------------------------------
    GUI Label                                    | st.session_state Key             | Type
    ---------------------------------------------------------------------------------
    Orchestration choice                         | orch_choice                      | str (radio, single)
    Orchestration details                        | orch_details_text                | str (text_area)

    COLLECTOR SECTION:
    ---------------------------------------------------------------------------------
    GUI Label                                    | st.session_state Key Pattern     | Type
    ---------------------------------------------------------------------------------
    Collection method checkboxes                 | collector_method_{option}        | bool (checkbox, multi)
    Custom method enable                         | collector_methods_other_enable   | bool (checkbox)
    Authentication checkboxes                    | collector_auth_{option}          | bool (checkbox, multi)
    Custom auth enable                           | collector_auth_other_enable      | bool (checkbox)
    Data handling checkboxes                     | collector_handle_{option}        | bool (checkbox, multi)
    Custom handling enable                       | collector_handling_other_enable  | bool (checkbox)
    Normalization checkboxes                     | collector_norm_{option}          | bool (checkbox, multi)
    Custom normalization enable                  | collector_norm_other_enable      | bool (checkbox)
    Collection tools checkboxes                  | collection_tools_{option}        | bool (checkbox, multi)
    Custom tools enable                          | collection_tools_other_enable    | bool (checkbox)
    Devices/scope                                | collector_devices                | str (text_area)
    Metrics/data                                 | collector_metrics                | str (text_area)
    Cadence                                      | collector_cadence                | str (text_input)

    EXECUTOR SECTION:
    ---------------------------------------------------------------------------------
    GUI Label                                    | st.session_state Key Pattern     | Type
    ---------------------------------------------------------------------------------
    Execution method checkboxes                  | exec_{index}                     | bool (checkbox, multi)

    DEPENDENCIES SECTION:
    ---------------------------------------------------------------------------------
    GUI Label                                    | st.session_state Key Pattern     | Type
    ---------------------------------------------------------------------------------
    Dependency checkboxes                        | dep_{key}                        | bool (checkbox, multi)
    Dependency details                           | dep_{key}_details                | str (text_input)

    TIMELINE SECTION:
    ---------------------------------------------------------------------------------
    GUI Label                                    | st.session_state Key             | Type
    ---------------------------------------------------------------------------------
    Development approach                         | timeline_build_buy               | str (radio, single)
    Direct staff on project                      | timeline_staff_count             | int (number_input)
    Professional services staff                  | timeline_external_staff_count    | int (number_input)
    Staffing plan (markdown)                     | timeline_staffing_plan           | str (text_area)
    Holiday calendar                             | timeline_holiday_region          | str (selectbox, single)
    Project start date                           | timeline_start_date              | date (date_input)
    Milestone rows                               | timeline_milestones              | list[dict] (dynamic)
    Milestone name (row N)                       | _tl_name_{N}                     | str (text_input)
    Milestone duration (row N)                   | _tl_duration_{N}                 | int (number_input)
    Milestone notes (row N)                      | _tl_notes_{N}                    | str (text_input)

    SHARED KEYS:
    ---------------------------------------------------------------------------------
    Key                                          | Type                             | Description
    ---------------------------------------------------------------------------------
    """
    # Page config (use same favicon as landing page for consistency)
    st.set_page_config(
        page_title="Solution Wizard",
        page_icon="images/EIA_Favicon.png",
        layout="wide",
    )

    # Global sidebar branding (shared across pages)
    utils.render_global_sidebar()

    # Colors for main content separators
    hr_color_dict = utils.hr_colors()

    # JSON upload/reset controls now live in the main page body
    with st.expander("Load Saved Solution Wizard (JSON)", expanded=False):
        # Sidebar import/reset controls.
        #
        # - Reset to defaults: clears wizard-related session state and restores defaults.
        # - Upload naf_report_*.json: allows Merge/Overwrite to rehydrate a previous session.
        # - Filename must match naf_report_*.json; otherwise show guidance.

        # Reset to defaults
        if st.button(
            "Reset to defaults",
            use_container_width=True,
            key="wizard_reset_defaults_btn",
        ):
            prefixes = (
                "pres_",
                "intent_",
                "obs_",
                "orch_",
                "collector_",
                "collection_tool_",
                "collection_tools_",
                "exec_",
                "my_role_",
                "dep_",
                "_tl_",
                "_timeline_",
                "obs_tool_",
                "obs_state_",
                "collector_method_",
                "collector_auth_",
                "collector_handle_",
                "collector_norm_",
                "stakeholders_",
            )
            for k in list(st.session_state.keys()):
                if any([k.startswith(p) for p in prefixes]):
                    st.session_state.pop(k, None)
            # Force-uncheck known checkbox/toggle keys in case Streamlit retains widget states
            for k in list(st.session_state.keys()):
                if k.startswith(
                    (
                        "pres_user_",
                        "pres_interact_",
                        "pres_tool_",
                        "pres_auth_",
                        "intent_dev_",
                        "intent_prov_",
                        "obs_state_",
                        "obs_tool_",
                        "collector_method_",
                        "collector_auth_",
                        "collector_handle_",
                        "collector_norm_",
                        "collection_tool_",
                        "collection_tools_",
                    )
                ):
                    st.session_state[k] = False
            # Disable any custom enable toggles
            for k in [
                "pres_user_custom_enable",
                "pres_interact_custom_enable",
                "pres_tool_custom_enable",
                "pres_auth_other_enable",
                "intent_dev_custom_enable",
                "intent_prov_custom_enable",
                "obs_tool_other_enable",
                "collector_methods_other_enable",
                "collector_auth_other_enable",
                "collector_handling_other_enable",
                "collector_norm_other_enable",
                "collection_tools_other_enable",
                "stakeholders_other_enable",
            ]:
                st.session_state[k] = False
            for k in [
                "automation_title",
                "automation_description",
                "expected_use",
                "out_of_scope",
                "timeline_build_buy",
                "timeline_staff_count",
                "timeline_external_staff_count",
                "timeline_staffing_plan",
                "timeline_holiday_region",
                "timeline_start_date",
                "timeline_milestones",
                "collector_devices",
                "collector_metrics",
                "collector_cadence",
                "orch_choice",
                "orch_details_text",
                "obs_go_no_go",
                "obs_add_logic_choice",
                "obs_add_logic_text",
                "stakeholders_choices",
                "stakeholders_other_text",
            ]:
                st.session_state.pop(k, None)
            # Minimal sane defaults
            st.session_state["dep_network_infra"] = True
            st.session_state["dep_revision_control"] = True
            st.session_state["dep_revision_control_details"] = "GitHub"
            # Also set My Role radios to sentinel explicitly
            st.session_state["my_role_who"] = "— Select one —"
            st.session_state["my_role_skills"] = "— Select one —"
            st.session_state["my_role_dev"] = "— Select one —"
            st.session_state.pop("my_role_who_other", None)
            st.session_state.pop("my_role_skills_other", None)
            st.session_state.pop("my_role_dev_other", None)
            # Initiative defaults (use _wizard_ keys to persist across pages)
            st.session_state["_wizard_automation_title"] = (
                "My new network automation project"
            )
            st.session_state["_wizard_automation_description"] = (
                "Here is a short description of my my new network automation project"
            )
            st.session_state["_wizard_problem_statement"] = ""
            st.session_state["_wizard_expected_use"] = (
                "This automation will be used whenever this task needs to be executed."
            )
            st.session_state["_wizard_error_conditions"] = ""
            st.session_state["_wizard_assumptions"] = ""
            st.session_state["_wizard_deployment_strategy"] = DEFAULT_DEPLOYMENT_STRATEGY_PLACEHOLDER
            st.session_state["_wizard_deployment_strategy_other"] = ""
            st.session_state["_wizard_deployment_strategy_description"] = ""
            st.session_state["_wizard_out_of_scope"] = ""
            st.session_state["_wizard_category"] = DEFAULT_CATEGORY_PLACEHOLDER
            st.session_state["_wizard_category_other"] = ""
            st.session_state["no_move_forward"] = ""
            # Set no_move_forward_reasons to placeholder for reset
            st.session_state["no_move_forward_reasons"] = [
                "— Select one or more risks —"
            ]
            # no separate details field; report is generated
            # Orchestration defaults so select resets visually
            st.session_state["orch_choice"] = "— Select one —"
            st.session_state["orch_details_text"] = ""
            st.rerun()

        # Sample JSON download removed per request

        uploaded = st.file_uploader(
            "Upload naf_report_*.json", type=["json"], key="wizard_upload_json"
        )
        if uploaded is not None:
            fname = (uploaded.name or "").strip()
            if not fname.lower().endswith(".json"):
                st.error(
                    "Invalid file. Please upload a .json file exported from this tool."
                )
            elif not fname.lower().startswith("naf_report_"):
                st.info(
                    "Tip: Expected a file named like 'naf_report_*.json' (use the Save Solution Artifacts download). Rename the file or download a fresh export."
                )
            else:
                if st.button(
                    "Apply uploaded JSON",
                    type="primary",
                    key="wizard_apply_upload_btn",
                ):
                    try:
                        data = json.load(uploaded)
                        if not isinstance(data, dict):
                            st.error(
                                "Uploaded JSON is not a valid Solution Wizard export (expected an object)."
                            )
                        else:
                            # Clear ALL existing wizard-related state before applying (Overwrite mode)
                            prefixes = (
                                "pres_",
                                "intent_",
                                "obs_",
                                "orch_",
                                "collector_",
                                "collection_tool_",
                                "collection_tools_",
                                "exec_",
                                "my_role_",
                                "dep_",
                                "_tl_",
                                "_timeline_",
                                "obs_tool_",
                                "obs_state_",
                                "collector_method_",
                                "collector_auth_",
                                "collector_handle_",
                                "collector_norm_",
                                "_wizard_",
                                "_widget_",
                                "stakeholders_",
                            )
                            for k in list(st.session_state.keys()):
                                if any([k.startswith(p) for p in prefixes]):
                                    st.session_state.pop(k, None)
                            # Force-uncheck known checkbox/toggle keys
                            for k in list(st.session_state.keys()):
                                if k.startswith(
                                    (
                                        "pres_user_",
                                        "pres_interact_",
                                        "pres_tool_",
                                        "pres_auth_",
                                        "intent_dev_",
                                        "intent_prov_",
                                        "obs_state_",
                                        "obs_tool_",
                                        "collector_method_",
                                        "collector_auth_",
                                        "collector_handle_",
                                        "collector_norm_",
                                        "collection_tool_",
                                        "collection_tools_",
                                    )
                                ):
                                    st.session_state[k] = False
                            for k in [
                                "pres_user_custom_enable",
                                "pres_interact_custom_enable",
                                "pres_tool_custom_enable",
                                "pres_auth_other_enable",
                                "intent_dev_custom_enable",
                                "intent_prov_custom_enable",
                                "obs_tool_other_enable",
                                "collector_methods_other_enable",
                                "collector_auth_other_enable",
                                "collector_handling_other_enable",
                                "collector_norm_other_enable",
                                "collection_tools_other_enable",
                                "stakeholders_other_enable",
                            ]:
                                st.session_state[k] = False
                            # Set Orchestration radio to sentinel
                            st.session_state["orch_choice"] = "— Select one —"
                            st.session_state["orch_details_text"] = ""
                            # Also set My Role radios to sentinel explicitly
                            st.session_state["my_role_who"] = "— Select one —"
                            st.session_state["my_role_skills"] = "— Select one —"
                            st.session_state["my_role_dev"] = "— Select one —"
                            st.session_state.pop("my_role_who_other", None)
                            st.session_state.pop("my_role_skills_other", None)
                            st.session_state.pop("my_role_dev_other", None)
                            for k in [
                                "automation_title",
                                "automation_description",
                                "expected_use",
                                "out_of_scope",
                                "no_move_forward",
                                "no_move_forward_reasons",
                                "timeline_milestones",
                                "timeline_build_buy",
                                "timeline_staff_count",
                                "timeline_external_staff_count",
                                "timeline_staffing_plan",
                                "timeline_holiday_region",
                                "timeline_start_date",
                                "collector_devices",
                                "collector_metrics",
                                "collector_cadence",
                                "orch_choice",
                                "orch_details_text",
                                "stakeholders_choices",
                                "stakeholders_other_text",
                            ]:
                                st.session_state.pop(k, None)

                            # Load Initiative data
                            ini = data.get("initiative", {}) or {}
                            if ini.get("author") is not None:
                                st.session_state["_wizard_author"] = str(
                                    ini.get("author") or ""
                                )
                            if ini.get("title") is not None:
                                st.session_state["_wizard_automation_title"] = str(
                                    ini.get("title") or ""
                                )
                            if ini.get("description") is not None:
                                st.session_state["_wizard_automation_description"] = (
                                    str(ini.get("description") or "")
                                )
                            if ini.get("problem_statement") is not None:
                                st.session_state["_wizard_problem_statement"] = str(
                                    ini.get("problem_statement") or ""
                                )
                            if ini.get("expected_use") is not None:
                                st.session_state["_wizard_expected_use"] = str(
                                    ini.get("expected_use") or ""
                                )
                            if ini.get("error_conditions") is not None:
                                st.session_state["_wizard_error_conditions"] = str(
                                    ini.get("error_conditions") or ""
                                )
                            if ini.get("assumptions") is not None:
                                st.session_state["_wizard_assumptions"] = str(
                                    ini.get("assumptions") or ""
                                )
                            if ini.get("deployment_strategy") is not None:
                                deploy_strategy = str(
                                    ini.get("deployment_strategy") or ""
                                )
                                # Check if the deployment strategy is in the predefined list
                                deploy_yaml_path = (
                                    Path(__file__).parent.parent
                                    / "deployment_strategies.yml"
                                )
                                try:
                                    with open(deploy_yaml_path, "r") as f:
                                        deploy_data = yaml.safe_load(f)
                                    deploy_options = (
                                        list(deploy_data.keys()) if deploy_data else []
                                    )
                                except Exception:
                                    deploy_options = []

                                if deploy_strategy in deploy_options:
                                    # It's a standard strategy
                                    st.session_state["_wizard_deployment_strategy"] = (
                                        deploy_strategy
                                    )
                                    st.session_state[
                                        "_wizard_deployment_strategy_other"
                                    ] = ""
                                elif (
                                    deploy_strategy
                                    and deploy_strategy
                                    != DEFAULT_DEPLOYMENT_STRATEGY_PLACEHOLDER
                                ):
                                    # It's a custom strategy, put it in "Other"
                                    st.session_state["_wizard_deployment_strategy"] = (
                                        "Other"
                                    )
                                    st.session_state[
                                        "_wizard_deployment_strategy_other"
                                    ] = deploy_strategy
                                else:
                                    # Empty or placeholder
                                    st.session_state["_wizard_deployment_strategy"] = (
                                        DEFAULT_DEPLOYMENT_STRATEGY_PLACEHOLDER
                                    )
                                    st.session_state[
                                        "_wizard_deployment_strategy_other"
                                    ] = ""
                            if ini.get("deployment_strategy_description") is not None:
                                st.session_state[
                                    "_wizard_deployment_strategy_description"
                                ] = str(
                                    ini.get("deployment_strategy_description") or ""
                                )
                            if ini.get("category") is not None:
                                # Check if the category is in the predefined list
                                yaml_path = (
                                    Path(__file__).parent.parent
                                    / "use_case_categories.yml"
                                )
                                try:
                                    with open(yaml_path, "r") as f:
                                        categories_data = yaml.safe_load(f)
                                    category_options = (
                                        list(categories_data.keys())
                                        if categories_data
                                        else []
                                    )
                                except Exception:
                                    category_options = []

                                category_value = ini.get("category")
                                if category_value in category_options:
                                    st.session_state["_wizard_category"] = (
                                        category_value
                                    )
                                    st.session_state["_wizard_category_other"] = ""
                                else:
                                    st.session_state["_wizard_category"] = "Other"
                                    st.session_state["_wizard_category_other"] = (
                                        category_value or ""
                                    )
                            if ini.get("out_of_scope") is not None:
                                st.session_state["_wizard_out_of_scope"] = str(
                                    ini.get("out_of_scope") or ""
                                )
                            if ini.get("no_move_forward") is not None:
                                st.session_state["no_move_forward"] = ini.get(
                                    "no_move_forward"
                                )
                            if ini.get("no_move_forward_reasons") is not None:
                                # Set the widget key directly
                                vals = ini.get("no_move_forward_reasons") or []
                                if isinstance(vals, list):
                                    st.session_state["no_move_forward_reasons"] = vals
                                else:
                                    st.session_state["no_move_forward_reasons"] = []
                            # ignore legacy initiative.solution_details_md in uploads

                            # My Role
                            my_role = data.get("my_role", {}) or {}
                            who = (my_role.get("who") or "").strip()
                            skills = (my_role.get("skills") or "").strip()
                            dev = (my_role.get("developer") or "").strip()
                            # For each, set radio to value or 'Other' and capture other text
                            if who:
                                known_who = {
                                    "I’m a network engineer.",
                                    "I’m a software developer.",
                                    "I manage technical projects or teams.",
                                }
                                if who in known_who:
                                    st.session_state["my_role_who"] = who
                                else:
                                    st.session_state["my_role_who"] = "Other (fill in)"
                                    st.session_state["my_role_who_other"] = who
                            if skills:
                                known_sk = {
                                    "I have some scripting skills and basic software development experience.",
                                    "I am an advanced software developer.",
                                    "I provide techncial management on network and automation projects.",
                                }
                                if skills in known_sk:
                                    st.session_state["my_role_skills"] = skills
                                else:
                                    st.session_state["my_role_skills"] = (
                                        "Other (fill in)"
                                    )
                                    st.session_state["my_role_skills_other"] = skills
                            if dev:
                                known_dev = {
                                    "I’ll do it myself.",
                                    "My in-house team and I will build it.",
                                    "We will have outside experts build it, but I’ll provide technical oversight.",
                                }
                                if dev in known_dev:
                                    st.session_state["my_role_dev"] = dev
                                else:
                                    st.session_state["my_role_dev"] = "Other (fill in)"
                                    st.session_state["my_role_dev_other"] = dev

                            # Stakeholders
                            stakeholders = data.get("stakeholders", {}) or {}
                            if stakeholders.get("choices") is not None:
                                # Ensure choices is a dictionary
                                choices = stakeholders.get("choices")
                                if isinstance(choices, dict):
                                    # Use choices as-is since we no longer support old category names
                                    st.session_state["stakeholders_choices"] = choices
                                else:
                                    st.session_state["stakeholders_choices"] = {}
                            else:
                                st.session_state["stakeholders_choices"] = {}
                            if stakeholders.get("other") is not None:
                                st.session_state["stakeholders_other_text"] = str(
                                    stakeholders.get("other") or ""
                                )

                            # Presentation
                            pres = data.get("presentation", {}) or {}
                            pres_sel = pres.get("selections", {}) or {}
                            for u in pres_sel.get("users", []) or []:
                                st.session_state[f"pres_user_{u}"] = True
                            known_interact = {"CLI", "Web GUI", "Other GUI", "API"}
                            for it in pres_sel.get("interactions", []) or []:
                                if it in known_interact:
                                    st.session_state[f"pres_interact_{it}"] = True
                                else:
                                    st.session_state["pres_interact_custom_enable"] = (
                                        True
                                    )
                                    st.session_state["pres_interact_custom"] = it
                            known_tools = {
                                "Python",
                                "Python Web Framework (Streamlit, Flask, etc.)",
                                "General Web Framework",
                                "Automation Framework",
                                "REST API",
                                "GraphQL API",
                                "Custom API",
                            }
                            for t in pres_sel.get("tools", []) or []:
                                if t in known_tools:
                                    st.session_state[f"pres_tool_{t}"] = True
                                else:
                                    st.session_state["pres_tool_custom_enable"] = True
                                    st.session_state["pres_tool_custom"] = t
                            known_auth = {
                                "No Authentication (suitable only for demos and very specific use cases)",
                                "Repository authorization/sharing",
                                "Built-in Authentication via Username/Password or TOKEN",
                                "Custom Authentication to external system (AD, SSH Keys, OAUTH2)",
                            }
                            for a in pres_sel.get("auth", []) or []:
                                if a in known_auth:
                                    st.session_state[f"pres_auth_{a}"] = True
                                else:
                                    st.session_state["pres_auth_other_enable"] = True
                                    st.session_state["pres_auth_other_text"] = a

                            # Intent
                            intent = data.get("intent", {}) or {}
                            intent_sel = intent.get("selections", {}) or {}
                            known_dev = {
                                "Templates",
                                "Policies",
                                "Service Profiles",
                                "Model-driven (data models)",
                                "Declarative (YAML/JSON)",
                                "Forms/GUI",
                                "Domain-specific language (DSL)",
                                "GitOps workflow (PRs/Reviews)",
                                "API-driven",
                                "Import from Source of Truth (CMDB/IPAM/Inventory/Git)",
                            }
                            unknown_devs = []
                            for v in intent_sel.get("development", []) or []:
                                if v in known_dev:
                                    st.session_state[f"intent_dev_{v}"] = True
                                else:
                                    unknown_devs.append(v)
                            if unknown_devs:
                                st.session_state["intent_dev_custom_enable"] = True
                                st.session_state["intent_dev_custom"] = ", ".join(
                                    unknown_devs
                                )
                            known_prov = {
                                "Text file",
                                "Serialized format (JSON, YAML)",
                                "CSV",
                                "Excel",
                                "API",
                            }
                            unknown_prov = []
                            for v in intent_sel.get("provided", []) or []:
                                if v in known_prov:
                                    st.session_state[f"intent_prov_{v}"] = True
                                else:
                                    unknown_prov.append(v)
                            if unknown_prov:
                                st.session_state["intent_prov_custom_enable"] = True
                                st.session_state["intent_prov_custom"] = ", ".join(
                                    unknown_prov
                                )

                            # Observability
                            obs = data.get("observability", {}) or {}
                            obs_sel = obs.get("selections", {}) or {}
                            for m in obs_sel.get("methods", []) or []:
                                st.session_state[f"obs_state_{m}"] = True
                            known_obs_tools = {
                                "Open Source",
                                "Commercial/Enterprise Product",
                                "Network Vendor Product (Cisco Catalyst Center, Arista CVP, PAN Panorama,etc.)",
                                "Custom Python Scripts",
                            }
                            for t in obs_sel.get("tools", []) or []:
                                if t in known_obs_tools:
                                    st.session_state[f"obs_tool_{t}"] = True
                                else:
                                    st.session_state["obs_tool_other_enable"] = True
                                    st.session_state["obs_tool_other_text"] = t
                            if obs_sel.get("go_no_go_text") is not None:
                                st.session_state["obs_go_no_go"] = obs_sel.get(
                                    "go_no_go_text"
                                )
                            st.session_state["obs_add_logic_choice"] = (
                                "Yes"
                                if obs_sel.get("additional_logic_enabled")
                                else "No"
                            )
                            if obs_sel.get("additional_logic_text") is not None:
                                st.session_state["obs_add_logic_text"] = obs_sel.get(
                                    "additional_logic_text"
                                )

                            # Orchestration
                            orch_sel = (data.get("orchestration", {}) or {}).get(
                                "selections", {}
                            )
                            if orch_sel.get("choice") is not None:
                                st.session_state["orch_choice"] = orch_sel.get("choice")
                            if orch_sel.get("details") is not None:
                                st.session_state["orch_details_text"] = orch_sel.get(
                                    "details"
                                )

                            # Collector
                            col_sel = (data.get("collector", {}) or {}).get(
                                "selections", {}
                            )
                            for m in col_sel.get("methods", []) or []:
                                for known in [
                                    "SNMP",
                                    "CLI/SSH",
                                    "NETCONF",
                                    "gNMI",
                                    "REST API",
                                    "Webhooks",
                                    "Syslog",
                                    "Streaming Telemetry",
                                ]:
                                    if m == known:
                                        st.session_state[
                                            f"collector_method_{known}"
                                        ] = True
                                        break
                                else:
                                    st.session_state[
                                        "collector_methods_other_enable"
                                    ] = True
                                    st.session_state["collector_methods_other"] = m
                            for a in col_sel.get("auth", []) or []:
                                for known in [
                                    "Username/Password",
                                    "SSH Keys",
                                    "OAuth2",
                                    "API Token",
                                    "mTLS",
                                ]:
                                    if a == known:
                                        st.session_state[f"collector_auth_{known}"] = (
                                            True
                                        )
                                        break
                                else:
                                    st.session_state["collector_auth_other_enable"] = (
                                        True
                                    )
                                    st.session_state["collector_auth_other"] = a
                            for h in col_sel.get("handling", []) or []:
                                for known in [
                                    "None",
                                    "Rate limiting",
                                    "Retries",
                                    "Exponential backoff",
                                    "Buffering/Queue",
                                ]:
                                    if h == known:
                                        st.session_state[
                                            f"collector_handle_{known}"
                                        ] = True
                                        break
                                else:
                                    st.session_state[
                                        "collector_handling_other_enable"
                                    ] = True
                                    st.session_state["collector_handling_other"] = h
                            for n in col_sel.get("normalization", []) or []:
                                for known in [
                                    "None",
                                    "Timestamping",
                                    "Tagging/labels",
                                    "Topology enrichment",
                                    "Schema mapping",
                                ]:
                                    if n == known:
                                        st.session_state[f"collector_norm_{known}"] = (
                                            True
                                        )
                                        break
                                else:
                                    st.session_state["collector_norm_other_enable"] = (
                                        True
                                    )
                                    st.session_state["collector_norm_other"] = n
                            for t in col_sel.get("tools", []) or []:
                                for known in [
                                    "None",
                                    "Open Source",
                                    "Commercial/Enterprise Product",
                                    "Network Vendor Product (Cisco Catalyst Center, Arista CVP, PAN Panorama, etc.)",
                                    "Custom Python Scripts",
                                ]:
                                    if t == known:
                                        st.session_state[f"collection_tool_{known}"] = (
                                            True
                                        )
                                        break
                                else:
                                    st.session_state[
                                        "collection_tools_other_enable"
                                    ] = True
                                    st.session_state["collection_tools_other"] = t
                            if col_sel.get("devices") is not None:
                                st.session_state["collector_devices"] = str(
                                    col_sel.get("devices")
                                )
                            if col_sel.get("metrics_per_sec") is not None:
                                st.session_state["collector_metrics"] = str(
                                    col_sel.get("metrics_per_sec")
                                )
                            if col_sel.get("cadence") is not None:
                                st.session_state["collector_cadence"] = str(
                                    col_sel.get("cadence")
                                )

                            # Executor
                            exec_sel = (data.get("executor", {}) or {}).get(
                                "selections", {}
                            )
                            exec_opts = [
                                "Automating CLI interaction with Python automation frameworks (Netmiko, Napalm, Nornir, PyATS)",
                                "Automating execution with a tool like Ansible",
                                "Custom Python scripts",
                                "Via manufacturer management application (Cisco DNA Center, Arista CVP)",
                            ]
                            for m in exec_sel.get("methods", []) or []:
                                for i, known in enumerate(exec_opts):
                                    if m == known:
                                        st.session_state[f"exec_{i}"] = True
                                        break
                                else:
                                    # Custom executor method
                                    st.session_state["exec_custom_enable"] = True
                                    st.session_state["exec_custom_text"] = m

                            # Dependencies
                            dep_list = data.get("dependencies", []) or []
                            label_to_key = {
                                "Network Infrastructure": "network_infra",
                                "Network Controllers": "network_controllers",
                                "Revision Control system": "revision_control",
                                "ITSM/Change Management System": "itsm",
                                "Authentication System": "authn",
                                "IPAMS Systems": "ipams",
                                "Inventory Systems": "inventory",
                                "Design Data/Intent Systems": "design_intent",
                                "Observability System": "observability",
                                "Vendor Tool/Management System": "vendor_mgmt",
                            }
                            for d in dep_list:
                                lbl = (d or {}).get("name")
                                details = (d or {}).get("details", "")
                                key = label_to_key.get(lbl)
                                if key:
                                    st.session_state[f"dep_{key}"] = True
                                    if details:
                                        st.session_state[f"dep_{key}_details"] = details

                            # Timeline basics
                            tl = data.get("timeline", {}) or {}
                            if tl.get("build_buy") is not None:
                                st.session_state["timeline_build_buy"] = tl.get(
                                    "build_buy"
                                )
                            if tl.get("staff_count") is not None:
                                st.session_state["timeline_staff_count"] = int(
                                    tl.get("staff_count") or 0
                                )
                            if tl.get("external_staff_count") is not None:
                                st.session_state["timeline_external_staff_count"] = int(
                                    tl.get("external_staff_count") or 0
                                )
                            if tl.get("staffing_plan_md") is not None:
                                st.session_state["timeline_staffing_plan"] = tl.get(
                                    "staffing_plan_md"
                                )
                            if tl.get("holiday_region") is not None:
                                st.session_state["timeline_holiday_region"] = (
                                    tl.get("holiday_region") or "None"
                                )
                            if tl.get("start_date"):
                                parsed = None
                                try:
                                    parsed = datetime.datetime.strptime(
                                        str(tl.get("start_date")), "%Y-%m-%d"
                                    ).date()
                                except Exception:
                                    try:
                                        parsed = datetime.datetime.fromisoformat(
                                            str(tl.get("start_date"))
                                        ).date()
                                    except Exception:
                                        parsed = None
                                if parsed is not None:
                                    st.session_state["timeline_start_date"] = parsed

                            # Timeline milestones from items
                            items = tl.get("items") or []
                            if isinstance(items, list) and items:
                                # Clear existing row-level timeline widget keys so widgets adopt new values
                                for k in list(st.session_state.keys()):
                                    if k.startswith(
                                        (
                                            "_tl_name_",
                                            "_tl_duration_",
                                            "_tl_notes_",
                                            "_tl_del_",
                                        )
                                    ):
                                        st.session_state.pop(k, None)
                                ms = []
                                for it in items:
                                    try:
                                        nm = str((it or {}).get("name") or "").strip()
                                        dur = int((it or {}).get("duration_bd") or 0)
                                        notes = str((it or {}).get("notes") or "")
                                    except Exception:
                                        nm, dur, notes = (
                                            str((it or {}).get("name") or ""),
                                            0,
                                            str((it or {}).get("notes") or ""),
                                        )
                                    ms.append(
                                        {
                                            "name": nm,
                                            "duration": dur,
                                            "notes": notes,
                                        }
                                    )
                                if ms:
                                    st.session_state["timeline_milestones"] = ms
                                    # Seed row-level widget keys to reflect uploaded values
                                    for i, r in enumerate(ms):
                                        st.session_state[f"_tl_name_{i}"] = r.get(
                                            "name", ""
                                        )
                                        st.session_state[f"_tl_duration_{i}"] = int(
                                            r.get("duration", 0)
                                        )
                                        st.session_state[f"_tl_notes_{i}"] = r.get(
                                            "notes", ""
                                        )

                            # LEGACY: Store all wizard data in backing storage for inter-page navigation
                            # No longer needed with single-page operation
                            # TODO: Remove this entirely after confirming stability
                            st.session_state["_wizard_data"] = {
                                "my_role_who": st.session_state.get("my_role_who"),
                                "my_role_skills": st.session_state.get(
                                    "my_role_skills"
                                ),
                                "my_role_dev": st.session_state.get("my_role_dev"),
                                "my_role_who_other": st.session_state.get(
                                    "my_role_who_other"
                                ),
                                "my_role_skills_other": st.session_state.get(
                                    "my_role_skills_other"
                                ),
                                "my_role_dev_other": st.session_state.get(
                                    "my_role_dev_other"
                                ),
                                "stakeholders_choices": st.session_state.get(
                                    "stakeholders_choices"
                                ),
                                "stakeholders_other_text": st.session_state.get(
                                    "stakeholders_other_text"
                                ),
                                "orch_choice": st.session_state.get("orch_choice"),
                                "orch_details_text": st.session_state.get(
                                    "orch_details_text"
                                ),
                                "_wizard_automation_title": st.session_state.get(
                                    "_wizard_automation_title"
                                ),
                                "_wizard_automation_description": st.session_state.get(
                                    "_wizard_automation_description"
                                ),
                                "_wizard_category": st.session_state.get(
                                    "_wizard_category"
                                ),
                                "_wizard_category_other": st.session_state.get(
                                    "_wizard_category_other"
                                ),
                                "_wizard_problem_statement": st.session_state.get(
                                    "_wizard_problem_statement"
                                ),
                                "_wizard_expected_use": st.session_state.get(
                                    "_wizard_expected_use"
                                ),
                                "_wizard_error_conditions": st.session_state.get(
                                    "_wizard_error_conditions"
                                ),
                                "_wizard_assumptions": st.session_state.get(
                                    "_wizard_assumptions"
                                ),
                                "_wizard_deployment_strategy": st.session_state.get(
                                    "_wizard_deployment_strategy"
                                ),
                                "_wizard_deployment_strategy_other": st.session_state.get(
                                    "_wizard_deployment_strategy_other"
                                ),
                                "_wizard_deployment_strategy_description": st.session_state.get(
                                    "_wizard_deployment_strategy_description"
                                ),
                                "_wizard_out_of_scope": st.session_state.get(
                                    "_wizard_out_of_scope"
                                ),
                                "no_move_forward": st.session_state.get(
                                    "no_move_forward"
                                ),
                                "no_move_forward_reasons": st.session_state.get(
                                    "no_move_forward_reasons"
                                ),
                                "obs_go_no_go": st.session_state.get("obs_go_no_go"),
                                "obs_add_logic_choice": st.session_state.get(
                                    "obs_add_logic_choice"
                                ),
                                "obs_add_logic_text": st.session_state.get(
                                    "obs_add_logic_text"
                                ),
                                "collector_devices": st.session_state.get(
                                    "collector_devices"
                                ),
                                "collector_metrics": st.session_state.get(
                                    "collector_metrics"
                                ),
                                "collector_cadence": st.session_state.get(
                                    "collector_cadence"
                                ),
                            }
                            # Also store all checkbox and widget states that need to persist
                            widget_keys = [
                                k
                                for k in st.session_state.keys()
                                if any(
                                    k.startswith(p)
                                    for p in (
                                        "pres_user_",
                                        "pres_interact_",
                                        "pres_tool_",
                                        "pres_auth_",
                                        "intent_dev_",
                                        "intent_prov_",
                                        "obs_state_",
                                        "obs_tool_",
                                        "collector_method_",
                                        "collector_auth_",
                                        "collector_handle_",
                                        "collector_norm_",
                                        "collection_tool_",
                                        "collection_tools_",
                                        "collector_methods_",
                                        "collector_handling_",
                                        "exec_",
                                        "dep_",
                                        "_tl_",
                                        "_timeline_",
                                    )
                                )
                            ]
                            st.session_state["_wizard_checkboxes"] = {
                                k: st.session_state.get(k) for k in widget_keys
                            }

                            # Mark that JSON was loaded (for debugging/verification)
                            st.session_state["_json_loaded"] = True
                            st.success(
                                "Applied uploaded JSON to this session. Widgets will reflect values now."
                            )
                            st.rerun()

                    except Exception as e:
                        st.error(f"Failed to load JSON: {e}")

    # --------------- END of SIDEBAR -----------------

    # LEGACY: Restore widget keys from backing storage (no longer needed with single page)
    # This was required when navigating between pages because Streamlit clears widget state
    # TODO: Consider removing this entirely after confirming single-page operation is stable
    if "_wizard_data" in st.session_state:
        wd = st.session_state["_wizard_data"]
        for key, value in wd.items():
            if value is not None and key not in st.session_state:
                st.session_state[key] = value

    if "_wizard_checkboxes" in st.session_state:
        wc = st.session_state["_wizard_checkboxes"]
        for key, value in wc.items():
            if key not in st.session_state:
                st.session_state[key] = value

    # Build a local payload for this run (no persistence/state-sharing)
    payload = {}

    # Title with NAF icon
    title_cols = st.columns([0.08, 0.92])
    with title_cols[0]:
        st.image("images/naf_icon.png", width="stretch")
    with title_cols[1]:
        st.markdown("**Network Automation Forum's Network Automation Framework**")

    # Intro: two-column layout (left: diagram, right: description)
    col_img, col_text = st.columns([1, 1])
    with col_img:
        st.image(
            "images/naf_arch_framework_figure.png",
            width="stretch",
        )
        st.caption(
            "Source: https://github.com/Network-Automation-Forum/reference/blob/main/docs/Framework/Framework.md"
        )

        st.info("🔽  Expand each section to get started!")

    with col_text:
        st.subheader("Solution Wizard")
        st.markdown(
            """
            The Solution Wizard will help you define the WHY, WHO, HOW, and WHAT of your automation project. It will help you think through your automation project using the Network Automation Forum's (NAF) [Network Automation Framework](https://reference.networkautomation.forum/Framework/Framework/) (yes NAF NAF).

            - **Purpose:** Guide structured thinking across the NAF components so you identify stakeholders, scope, data flows, and build/buy/support decisions.
            - **Second set of eyes:** Use it as a checklist to ensure you’ve considered all key components; the framework helps make sure nothing critical is missed.
            - **Authoring aid:** Your selections here can help generate a high level concept document quickly to share with co-workers, management, and stakeholders.

            Remember: To complete the Business Case Calculator or develop any Business Case effectively, you should have a clear understanding of what the automation will do (what problem is it solving), who it will serve, and how it will be built (or bought) and supported going forward.

            Tip:  If you can't answer some of these questions from a technical perspective, just note that the function is needed and use the Custom option to describe what you can

            """
        )

    # -------- Inputs --------

    # Automation Project Title & Short Description
    with st.expander(
        "Automation Project Problem Statement & Description (Why is this Automation needed?)",
        expanded=False,
    ):
        # Includes title, short description/scope, expected use, out of scope, and detailed description.

        # Initialize defaults - use _wizard_ keys directly as widget keys
        # When JSON is uploaded, these keys are cleared and reset, so widgets pick up new values
        if "_wizard_author" not in st.session_state:
            try:
                # Try to get system username
                st.session_state["_wizard_author"] = getpass.getuser()
            except Exception:
                # Fallback to personalizing content
                st.session_state["_wizard_author"] = os.environ.get("USER", os.environ.get("USERNAME", "System User"))
        if "_wizard_automation_title" not in st.session_state:
            st.session_state["_wizard_automation_title"] = (
                "My new network automation project"
            )
        if "_wizard_automation_description" not in st.session_state:
            st.session_state["_wizard_automation_description"] = (
                "Here is a short description of my my new network automation project"
            )
        if "_wizard_problem_statement" not in st.session_state:
            st.session_state["_wizard_problem_statement"] = ""
        if "_wizard_expected_use" not in st.session_state:
            st.session_state["_wizard_expected_use"] = (
                "This automation will be used whenever this task needs to be executed."
            )
        if "_wizard_error_conditions" not in st.session_state:
            st.session_state["_wizard_error_conditions"] = ""
        if "_wizard_assumptions" not in st.session_state:
            st.session_state["_wizard_assumptions"] = ""
        if "_wizard_deployment_strategy" not in st.session_state:
            st.session_state["_wizard_deployment_strategy"] = DEFAULT_DEPLOYMENT_STRATEGY_PLACEHOLDER
        if "_wizard_deployment_strategy_other" not in st.session_state:
            st.session_state["_wizard_deployment_strategy_other"] = ""
        if "_wizard_deployment_strategy_description" not in st.session_state:
            st.session_state["_wizard_deployment_strategy_description"] = ""
        if "_wizard_out_of_scope" not in st.session_state:
            st.session_state["_wizard_out_of_scope"] = ""
        if "_wizard_category" not in st.session_state:
            st.session_state["_wizard_category"] = DEFAULT_CATEGORY_PLACEHOLDER
        if "_wizard_category_other" not in st.session_state:
            st.session_state["_wizard_category_other"] = ""

        # Author field (above title)
        st.text_input(
            "Author",
            key="_wizard_author",
            help="Name of the person creating this automation initiative",
        )
        
        col_ib1, col_ib2 = st.columns([2, 3])
        with col_ib1:
            st.text_input(
                "Automation initiative title",
                key="_wizard_automation_title",
            )
        with col_ib2:
            st.text_area(
                "Short description / scope",
                height=80,
                key="_wizard_automation_description",
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
        placeholder = DEFAULT_CATEGORY_PLACEHOLDER
        category_options_with_placeholder = [placeholder] + category_options
        current_cat = st.session_state.get("_wizard_category", "") or placeholder
        if current_cat not in category_options_with_placeholder:
            current_cat = "Other"
        cat = st.selectbox(
            "Category",
            options=category_options_with_placeholder,
            index=(
                category_options_with_placeholder.index(current_cat)
                if current_cat in category_options_with_placeholder
                else 0
            ),
            key="_wizard_category",
            help=(
                "Select a category from the list. Choose 'Other' if your initiative "
                "doesn't fit the predefined categories."
            ),
        )
        if cat == placeholder:
            st.info("💡 Please select a category from the list above.")
            initiative_category = ""
        elif cat == "Other":
            cat_other = st.text_input(
                "Custom category",
                value=(
                    st.session_state.get("_wizard_category_other", "")
                    if st.session_state.get("_wizard_category", "")
                    not in category_options
                    else ""
                ),
                key="_wizard_category_other",
            )
            initiative_category = cat_other or cat
        else:
            initiative_category = cat

        st.text_area(
            "Problem Statement (Markdown supported)",
            height=80,
            key="_wizard_problem_statement",
            help="Describe the circumstances under which this automation will be used.",
        )

        st.text_area(
            "Expected Use/Triggers (Markdown supported)",
            height=80,
            key="_wizard_expected_use",
            help="Describe the circumstances under which this automation will be used or triggered.",
        )

        st.text_area(
            "Error Conditions (Markdown supported)",
            height=80,
            key="_wizard_error_conditions",
            help="Note any expected error conditions that need to be addressed in the initial version",
        )

        st.text_area(
            "Assumptions (Markdown supported)",
            height=80,
            key="_wizard_assumptions",
            help="List any assumptions made for this automation initiative.",
        )

        st.text_area(
            "Out of Scope (optional)",
            height=80,
            key="_wizard_out_of_scope",
            help="List areas intentionally excluded from this initiative.",
        )

        # Standard Deployment Strategy (load from YAML file)
        deploy_yaml_path = Path(__file__).parent.parent / "deployment_strategies.yml"
        try:
            with open(deploy_yaml_path, "r") as f:
                deploy_data = yaml.safe_load(f)
            deploy_options = list(deploy_data.keys()) if deploy_data else []
        except Exception:
            deploy_options = []
        # Add placeholder and "Other" options
        deploy_placeholder = DEFAULT_DEPLOYMENT_STRATEGY_PLACEHOLDER
        deploy_options_with_placeholder = (
            [deploy_placeholder] + deploy_options + ["Other"]
        )

        # Initialize the session state if not set
        if "_wizard_deployment_strategy" not in st.session_state:
            st.session_state["_wizard_deployment_strategy"] = deploy_placeholder
        if "_wizard_deployment_strategy_other" not in st.session_state:
            st.session_state["_wizard_deployment_strategy_other"] = ""

        current_deploy = st.session_state.get(
            "_wizard_deployment_strategy", deploy_placeholder
        )
        if current_deploy not in deploy_options_with_placeholder and current_deploy != deploy_placeholder:
            # If the current value is not in the list and not the placeholder, move it to "Other"
            st.session_state["_wizard_deployment_strategy_other"] = current_deploy
            current_deploy = "Other"
            st.session_state["_wizard_deployment_strategy"] = "Other"

        deploy_sel = st.selectbox(
            "Standard Deployment Strategy",
            options=deploy_options_with_placeholder,
            index=(
                deploy_options_with_placeholder.index(current_deploy)
                if current_deploy in deploy_options_with_placeholder
                else 0
            ),
            key="_wizard_deployment_strategy",
            help="Select a standard deployment strategy from the list or choose 'Other' to enter a custom strategy.",
        )

        # Show text input if "Other" is selected
        if deploy_sel == "Other":
            st.text_input(
                "Custom Deployment Strategy",
                key="_wizard_deployment_strategy_other",
                help="Enter your custom deployment strategy name.",
                placeholder="e.g., Pilot Program",
            )
        elif deploy_sel == deploy_placeholder:
            st.info("💡 Please select a deployment strategy from the list above.")

        st.text_area(
            "Deployment Strategy Description (optional)",
            height=80,
            key="_wizard_deployment_strategy_description",
            help="Additional details about how the automation will be deployed.",
        )

        # Standard reasons multiselect (required)
        standard_reasons = [
            "We are not improving the way our customers interact with us for service provisioning",
            "We are not improving the speed and quality of our service provisioning",
            "We are not meeting feature or service demands from our customers",
            "We will continue to pay for 3rd party support for this task",
            "This task will continue to be executed individually in an inconsistent and ad-hoc manner with varying degrees of success and documentation",
            "This task will continue to take far longer than it should resulting in poor customer satisfaction",
            "We risk continuing to add technical debt to the logical infrastructure",
        ]

        # Initialize default if not set (widget key is set directly during JSON upload)
        if "no_move_forward_reasons" not in st.session_state:
            st.session_state["no_move_forward_reasons"] = [
                "— Select one or more risks —"
            ]

        # Add placeholder as first option
        risk_placeholder = "— Select one or more risks —"
        risk_options_with_placeholder = [risk_placeholder] + standard_reasons

        no_move_forward_reasons = st.multiselect(
            "Risk of not doing the automation",
            options=risk_options_with_placeholder,
            key="no_move_forward_reasons",
            help="Select at least one standard reason that applies.",
        )

        # Remove placeholder if selected
        if risk_placeholder in no_move_forward_reasons:
            no_move_forward_reasons = [
                x for x in no_move_forward_reasons if x != risk_placeholder
            ]

        # Show warning if no standard reasons selected
        if not no_move_forward_reasons:
            st.info("💡 Please select at least one standard reason.")

        # Initialize default if not set
        if "no_move_forward" not in st.session_state:
            st.session_state["no_move_forward"] = ""

        no_move_forward = st.text_area(
            "Additional risks in not moving forward (optional)",
            height=80,
            key="no_move_forward",
        )

        # Get the actual deployment strategy value
        actual_deployment_strategy = st.session_state.get(
            "_wizard_deployment_strategy", ""
        )
        if actual_deployment_strategy == "Other":
            actual_deployment_strategy = st.session_state.get(
                "_wizard_deployment_strategy_other", ""
            )

        # DUPLICATE: This payload building logic is now handled by wizard_data.build_wizard_payload()
        # TODO: Consider replacing this with a call to wizard_data.build_wizard_payload(st.session_state)
        payload["initiative"] = {
            "author": st.session_state.get("_wizard_author", ""),
            "title": st.session_state.get("_wizard_automation_title", ""),
            "description": st.session_state.get("_wizard_automation_description", ""),
            "category": initiative_category,
            "problem_statement": st.session_state.get("_wizard_problem_statement", ""),
            "expected_use": st.session_state.get("_wizard_expected_use", ""),
            "error_conditions": st.session_state.get("_wizard_error_conditions", ""),
            "assumptions": st.session_state.get("_wizard_assumptions", ""),
            "deployment_strategy": (
                actual_deployment_strategy
                if actual_deployment_strategy != DEFAULT_DEPLOYMENT_STRATEGY_PLACEHOLDER
                else ""
            ),
            "deployment_strategy_description": st.session_state.get(
                "_wizard_deployment_strategy_description", ""
            ),
            "out_of_scope": st.session_state.get("_wizard_out_of_scope", ""),
            "no_move_forward": no_move_forward,
            "no_move_forward_reasons": no_move_forward_reasons,
        }

    with st.expander("Stakeholders (Who is supporting the project?)", expanded=False):
        # Capture who is filling in the wizard and their skill/role context.
        #
        # Populates payload.my_role and is used to gate exporting and highlights visibility.

        SENTINEL_SELECT = "— Select one —"
        # Q1: Who’s filling out this wizard?
        st.header("My Role")
        st.subheader("Who’s filling out this wizard?")
        role_opts = [
            SENTINEL_SELECT,
            "I’m a network engineer.",
            "I’m a security engineer.",
            "I’m a software developer.",
            "I manage technical projects or teams.",
            "Other (fill in)",
        ]
        # Initialize if not set
        if "my_role_who" not in st.session_state:
            st.session_state["my_role_who"] = SENTINEL_SELECT
        role_choice = st.radio(
            "Select one",
            role_opts,
            key="my_role_who",
        )
        role_other = ""
        if role_choice == "Other (fill in)":
            role_other = st.text_input("Please describe", key="my_role_who_other")

        # Q2: What best describes your technical skills?
        st.subheader("What best describes your technical skills?")
        skill_opts = [
            SENTINEL_SELECT,
            "I have some scripting skills and basic software development experience.",
            "I am an advanced software developer.",
            "I provide techncial management on network and automation projects.",
            "Other (fill in)",
        ]
        # Initialize if not set
        if "my_role_skills" not in st.session_state:
            st.session_state["my_role_skills"] = SENTINEL_SELECT
        skill_choice = st.radio(
            "Select one",
            skill_opts,
            key="my_role_skills",
        )
        skill_other = ""
        if skill_choice == "Other (fill in)":
            skill_other = st.text_input("Please describe", key="my_role_skills_other")

        # Q3: Who will actually develop the network automation?
        st.subheader("Who will actually develop the network automation?")
        dev_opts = [
            SENTINEL_SELECT,
            "I’ll do it myself.",
            "My in-house team and I will build it.",
            "We will have outside experts build it, but I’ll provide technical oversight.",
            "Other (fill in)",
        ]
        # Initialize if not set
        if "my_role_dev" not in st.session_state:
            st.session_state["my_role_dev"] = SENTINEL_SELECT
        dev_choice = st.radio(
            "Select one",
            dev_opts,
            key="my_role_dev",
        )
        dev_other = ""
        if dev_choice == "Other (fill in)":
            dev_other = st.text_input("Please describe", key="my_role_dev_other")

        payload["my_role"] = {
            "who": _norm_role_choice(role_choice, role_other, SENTINEL_SELECT),
            "skills": _norm_role_choice(skill_choice, skill_other, SENTINEL_SELECT),
            "developer": _norm_role_choice(dev_choice, dev_other, SENTINEL_SELECT),
        }

        st.markdown("---")
        st.header("Stakeholders")
        if "stakeholders_choices" not in st.session_state or not isinstance(
            st.session_state.get("stakeholders_choices"), dict
        ):
            st.session_state["stakeholders_choices"] = {}
        if "stakeholders_other_text" not in st.session_state:
            st.session_state["stakeholders_other_text"] = ""

        catalog = _load_stakeholders_catalog()
        choices = st.session_state["stakeholders_choices"]
        stakeholder_help = {
            "Technical Stakeholders": "Select which engineering or operations teams are responsible for building, operating, or securing the systems that this automation will affect.\n\nUse this when identifying the technical groups that will design, implement, or maintain the solution.",
            "User and Customer Stakeholders": "Select which internal users or external customers will rely on the outcomes of this automation in their day-to-day work.\n\nUse this to capture the teams whose workflows, support experience, or service consumption will change.",
            "Governance and Risk Stakeholders": "Select which governance, security, or risk functions must review, approve, or oversee this automation effort.\n\nUse this for groups that manage policies, audits, or regulatory obligations impacted by the change.",
            "Business and Leadership Stakeholders": "Select which business owners, executives, or project leaders are sponsoring, funding, or directing this automation effort.\n\nUse this to identify decision-makers accountable for business outcomes, budget, and prioritization.",
            "External/Vendor/Partner Stakeholders": "Select which external vendors, consulting partners, or regulatory bodies are materially involved in delivering, integrating, or approving this automation.\n\nUse this for third parties that provide technology, services, or oversight required for success.",
        }
        rendered = {}
        for cat, opts in (catalog or {}).items():
            if not isinstance(cat, str):
                continue
            if not isinstance(opts, list):
                continue
            st.subheader(cat)
            key = f"stakeholders_choice_{_sanitize_title(cat)}"
            # Initialize from restored choices if available
            if key not in st.session_state and cat in choices:
                st.session_state[key] = (
                    choices[cat] if choices[cat] else SENTINEL_SELECT
                )
            elif key not in st.session_state:
                st.session_state[key] = SENTINEL_SELECT
            select_opts = [SENTINEL_SELECT] + [str(o) for o in opts if str(o).strip()]
            # Calculate the correct index based on the current value
            current_value = st.session_state.get(key, SENTINEL_SELECT)
            try:
                index = (
                    select_opts.index(current_value)
                    if current_value in select_opts
                    else 0
                )
            except ValueError:
                index = 0
            st.selectbox(
                "",
                options=select_opts,
                index=index,
                key=key,
                help=stakeholder_help.get(cat, ""),
            )
            val = st.session_state.get(key) or ""
            rendered[cat] = "" if val == SENTINEL_SELECT else val

        choices.update(rendered)
        st.session_state["stakeholders_choices"] = choices

        st.subheader("Other")
        st.text_input(
            "Other stakeholder(s)",
            key="stakeholders_other_text",
        )

        payload["stakeholders"] = {
            "choices": st.session_state.get("stakeholders_choices") or {},
            "other": (st.session_state.get("stakeholders_other_text") or "").strip(),
        }

    # Collapsible guiding questions
    if False:
        with st.expander("Guiding Questions by Framework Component", expanded=False):
            """
            Reference prompts to help users think through each framework component.
            """
            st.markdown(
                """
                - **Presentation**
                  - Provides user interfaces (dashboards/GUI, ITSM, chat, CLI) and access controls for interacting with the system.
                  - Can allow both read and write interactions and integrates with other components as needed.

                - **Intent**
                  - Defines the logic and the persistence layer for the desired state of the network (config and operational expectations).
                  - Represents network aspects in structured form, supports CRUD via standard APIs, uses neutral models, and can include validation, aggregation, service decomposition, and artifact generation.

                - **Observability**
                  - Persists the actual network state and provides logic to process it.
                  - Offers programmatic access and query for analytics, detects drift vs. intent, and can enrich data with context (e.g., EoL, CVEs, maintenance).

                - **Orchestrator**
                  - Coordinates and sequences automation tasks across components in response to events.
                  - Can be event‑driven, support dry‑run, scheduling, rollback/compensation, logging/traceability, and correlation.

                - **Collector**
                  - Retrieves the actual state (reads) from the network via APIs/CLIs and telemetry (e.g., SNMP, syslog, flows, streaming telemetry) and can normalize data across vendors.

                - **Executor**
                  - Performs the network changes (writes) guided by intent.
                  - Works with write interfaces (CLI/SSH, NETCONF, gNMI/gNOI, REST), supports transactional/dry‑run flows, and can operate in imperative or declarative styles with idempotency.

                """
            )

    utils.thick_hr(color=hr_color_dict["naf_yellow"], thickness=5)
    st.markdown(
        "***Expand each section to work through the framework components.  The NAF Framework will help define how your automation will work.***"
    )

    # Presentation section
    with st.expander("Presentation", expanded=False):
        # Presentation layer inputs: users, interactions, tools, and auth.
        # Drives narrative under payload.presentation and summary rendering.

        st.markdown(
            """
        **Presentation Layer Characteristics**
        - Provides robust, flexible authentication and authorization.
        - Can take many forms: GUIs, ITSM/change systems, chat/messaging, portals, reports.
        - May support read and write: view data, initiate tasks, approve changes.
        - Interfaces with other framework blocks as needed; it is the primary human touchpoint, without requiring a single pane of glass.
            """
        )
        st.subheader("Intended users")
        cols = st.columns(3)
        user_opts = [
            "Network Engineers",
            "IT",
            "Operations",
            "Help Desk",
            "Other IT Organizations",
            "Any User",
            "Authorized Users",
            "Automation Pipeline",
        ]
        user_checks = {}
        for i, opt in enumerate(user_opts):
            with cols[i % 3]:
                user_checks[opt] = st.checkbox(opt, key=f"pres_user_{opt}")
        with cols[0]:
            custom_users_enabled = st.checkbox(
                "Custom (fill in)", key="pres_user_custom_enable"
            )
            custom_users = ""
            if custom_users_enabled:
                custom_users = st.text_input("Custom users", key="pres_user_custom")

        st.subheader("How will your users interact with your solution?")
        cols2 = st.columns(3)
        interact_opts = [
            "CLI",
            "Purpose-built Web GUI",
            "Other GUI",
            "API",
            "Commercial Product/GUI",
            "Open Source Product/GUI",
        ]
        interact_checks = {}
        for i, opt in enumerate(interact_opts):
            with cols2[i % 3]:
                interact_checks[opt] = st.checkbox(opt, key=f"pres_interact_{opt}")
        with cols2[0]:
            custom_interact_enabled = st.checkbox(
                "Custom (fill in)", key="pres_interact_custom_enable"
            )
            custom_interact = ""
            if custom_interact_enabled:
                custom_interact = st.text_input(
                    "Custom interaction", key="pres_interact_custom"
                )

        st.subheader("What tools will the Presentation layer use?")
        cols3 = st.columns(3)
        tool_opts = [
            "Python",
            "Python Web Framework (Streamlit, Flask, etc.)",
            "General Web Framework",
            "Automation Framework",
            "REST API",
            "GraphQL API",
            "Custom API",
        ]
        tool_checks = {}
        for i, opt in enumerate(tool_opts):
            with cols3[i % 3]:
                tool_checks[opt] = st.checkbox(opt, key=f"pres_tool_{opt}")
        with cols3[0]:
            custom_tool_enabled = st.checkbox(
                "Custom (fill in)", key="pres_tool_custom_enable"
            )
            custom_tool = ""
            if custom_tool_enabled:
                custom_tool = st.text_input("Custom tool(s)", key="pres_tool_custom")

        st.subheader("How will your users authenticate?")
        cols4 = st.columns(2)
        auth_opts_pres = [
            "No Authentication (suitable only for demos and very specific use cases)",
            "Repository authorization/sharing",
            "Built-in (to the automation) Authentication via Username/Password or TOKEN",
            "Custom Authentication to external system (AD, SSH Keys, OAUTH2)",
        ]
        auth_checks_pres = {}
        for i, opt in enumerate(auth_opts_pres):
            with cols4[i % 2]:
                auth_checks_pres[opt] = st.checkbox(opt, key=f"pres_auth_{opt}")
        with cols4[0]:
            auth_other_enabled = st.checkbox(
                "Other (fill in details)", key="pres_auth_other_enable"
            )
            auth_other = ""
            if auth_other_enabled:
                auth_other = st.text_input(
                    "Other authentication details", key="pres_auth_other_text"
                )

        # Narrative synthesis
        selected_users = [k for k, v in user_checks.items() if v]
        if custom_users_enabled and custom_users.strip():
            selected_users.append(custom_users.strip())

        selected_interactions = [k for k, v in interact_checks.items() if v]
        if custom_interact_enabled and custom_interact.strip():
            selected_interactions.append(custom_interact.strip())

        selected_tools = [k for k, v in tool_checks.items() if v]
        if custom_tool_enabled and custom_tool.strip():
            selected_tools.append(custom_tool.strip())

        selected_auth_pres = [k for k, v in auth_checks_pres.items() if v]
        if auth_other_enabled and auth_other.strip():
            selected_auth_pres.append(auth_other.strip())

        users_sentence = f"This solution targets {_join(selected_users)}."
        interaction_sentence = (
            f"Users will interact with the solution via {_join(selected_interactions)}."
        )
        tools_sentence = (
            f"The presentation layer will be built using {_join(selected_tools)}."
        )
        auth_sentence_pres = (
            f"Presentation authentication will use {_join(selected_auth_pres)}."
        )

        utils.thick_hr(color="#6785a0", thickness=3)
        st.markdown("**Preview Solution Highlights**")
        any_selected = bool(
            selected_users
            or selected_interactions
            or selected_tools
            or selected_auth_pres
        )
        if not any_selected:
            st.info(
                "Make selections above to see highlights for the Presentation section."
            )
        else:
            st.markdown(
                "\n".join(
                    [
                        f"- {users_sentence}",
                        f"- {interaction_sentence}",
                        f"- {tools_sentence}",
                        f"- {auth_sentence_pres}",
                    ]
                )
            )

        payload["presentation"] = {
            "users": users_sentence,
            "interaction": interaction_sentence,
            "tools": tools_sentence,
            "auth": auth_sentence_pres,
            "selections": {
                "users": selected_users,
                "interactions": selected_interactions,
                "tools": selected_tools,
                "auth": selected_auth_pres,
            },
        }

    # Intent section
    with st.expander("Intent", expanded=False):
        # Intent inputs: what will be developed vs what exists today.
        # Populates payload.intent and influences highlights and export.q

        st.markdown(
            """
            Intent or the abstracted version of what you are trying to do
            - Represents any network aspect in a structured form (addressing, DC infrastructure, routing, virtual services, secrets, operational limits, templates/mappings, policies, artifacts).
            - Supports full CRUD operations and exposes a standard, well-documented API (e.g., REST, GraphQL).
            - Uses neutral models that derive into vendor-specific configurations.
            - Provides a unified desired-state view across potentially distributed data sources.
            - Includes governance metadata (timestamps, origin, ownership, validity windows).
            - Ideally transactional with custom validation and versioned access.
            - May include intended state logic: validation, aggregation/replication, service decomposition, combine data to generate config artifacts.

            ***When first starting out abstraction may be low and so intent could be as simple as a file with vlan numbers and names you want to provision.***
            """
        )
        st.subheader("How will Intent be developed?")
        cols = st.columns(3)
        intent_dev_opts = [
            "Templates",
            "Policies",
            "Service Profiles",
            "Model-driven (data models)",
            "Declarative (YAML/JSON)",
            "Forms/GUI",
            "Domain-specific language (DSL)",
            "GitOps workflow (PRs/Reviews)",
            "API-driven",
            "Import from Source of Truth (CMDB/IPAM/Inventory/Git)",
        ]
        intent_checks = {}
        for i, opt in enumerate(intent_dev_opts):
            with cols[i % 3]:
                intent_checks[opt] = st.checkbox(opt, key=f"intent_dev_{opt}")
        intent_custom_enabled = st.checkbox(
            "Custom (fill in)", key="intent_dev_custom_enable"
        )
        intent_custom = ""
        if intent_custom_enabled:
            intent_custom = st.text_input(
                "Custom intent development approach", key="intent_dev_custom"
            )

        # How will intent be consumed by automation?
        st.subheader("How will intent be consumed by automation?")
        cols_p = st.columns(3)
        intent_prov_opts = [
            "Text file",
            "Serialized format (JSON, YAML)",
            "CSV",
            "Excel",
            "API",
        ]
        intent_prov_checks = {}
        for i, opt in enumerate(intent_prov_opts):
            with cols_p[i % 3]:
                intent_prov_checks[opt] = st.checkbox(opt, key=f"intent_prov_{opt}")
        with cols_p[0]:
            intent_prov_custom_enabled = st.checkbox(
                "Custom (fill in)", key="intent_prov_custom_enable"
            )
            intent_prov_custom = ""
            if intent_prov_custom_enabled:
                intent_prov_custom = st.text_input(
                    "Custom provider format", key="intent_prov_custom"
                )

        # Narrative synthesis (Intent)
        selected_intent_devs = [k for k, v in intent_checks.items() if v]
        if intent_custom_enabled and intent_custom.strip():
            selected_intent_devs.append(intent_custom.strip())

        selected_intent_prov = [k for k, v in intent_prov_checks.items() if v]
        if intent_prov_custom_enabled and intent_prov_custom.strip():
            selected_intent_prov.append(intent_prov_custom.strip())

        intent_sentence = (
            f"Intent will be developed using {_join(selected_intent_devs)}."
        )
        intent_provided_sentence = (
            f"Intent will be provided via {_join(selected_intent_prov)}."
        )

        utils.thick_hr(color="#6785a0", thickness=3)
        st.markdown("**Preview Solution Highlights**")
        any_selected_intent = bool(selected_intent_devs or selected_intent_prov)
        if not any_selected_intent:
            st.info("Make selections above to see highlights for the Intent section.")
        else:
            st.markdown(
                "\n".join(
                    [
                        f"- {intent_sentence}",
                        f"- {intent_provided_sentence}",
                    ]
                )
            )

        payload["intent"] = {
            "development": intent_sentence,
            "provided": intent_provided_sentence,
            "selections": {
                "development": selected_intent_devs,
                "provided": selected_intent_prov,
            },
        }

    # Observability section
    with st.expander("Observability", expanded=False):
        # Observability inputs: health signals, go/no-go logic, and tools.
        # Populates payload.observability with selections and narrative strings.

        st.markdown(
            """
            - Supports historical data persistence with powerful programmatic access for analytics, reporting, and troubleshooting.
            - Provides a capable query language to extract and explore data.
            - Surfaces current-state insights and emits events when drift is detected between observed and intended state; events may be handled by humans or routed to Orchestration.
            - Data may be enriched with context from intended state and third parties (e.g., EoL, CVEs, maintenance notices) to improve correlation and analysis.
            """
        )
        st.subheader("How will you determine network state?")
        cols_obs = st.columns(3)
        state_methods_opts = [
            "Manual",
            "Purpose-built Python Script",
            "API call",
        ]
        state_methods_checks = {}
        for i, opt in enumerate(state_methods_opts):
            with cols_obs[i % 3]:
                state_methods_checks[opt] = st.checkbox(opt, key=f"obs_state_{opt}")

        st.subheader("Describe the basic go/no go logic")
        go_no_go_text = st.text_area(
            "Go/No-Go criteria",
            key="obs_go_no_go",
            placeholder="e.g., Proceed if all pre-checks pass and no policy violations are detected",
        )

        st.subheader(
            "Will there be additional logic applied to state to determine if the automation can move forward?"
        )
        add_logic_choice = st.radio(
            "Additional gating logic?",
            ["No", "Yes"],
            horizontal=True,
            key="obs_add_logic_choice",
        )
        add_logic_text = ""
        if add_logic_choice == "Yes":
            add_logic_text = st.text_area(
                "Describe additional logic", key="obs_add_logic_text"
            )

        st.subheader("What tools will be used to support the observability layer?")
        cols_tools = st.columns(3)
        obs_tools_opts = [
            "Open Source Software",
            "Commercial/Enterprise Product",
            "Network Vendor Product (Cisco Catalyst Center, Arista CVP, etc.)",
            "Custom Python Scripts",
        ]
        obs_tools_checks = {}
        for i, opt in enumerate(obs_tools_opts):
            with cols_tools[i % 3]:
                obs_tools_checks[opt] = st.checkbox(opt, key=f"obs_tool_{opt}")
        obs_tools_other_enabled = st.checkbox(
            "Other (fill in)", key="obs_tool_other_enable"
        )
        obs_tools_other = ""
        if obs_tools_other_enabled:
            obs_tools_other = st.text_input(
                "Other observability tool(s)", key="obs_tool_other_text"
            )

        # Compile selected observability tools before narrative
        selected_tools_obs = [k for k, v in obs_tools_checks.items() if v]
        if obs_tools_other_enabled and (obs_tools_other or "").strip():
            selected_tools_obs.append(obs_tools_other.strip())

        # Build method and go/no-go narratives
        selected_methods = [k for k, v in state_methods_checks.items() if v]
        methods_sentence = (
            f"Network state will be determined via {_join(selected_methods)}."
        )
        go_no_go_sentence = (
            f"Go/No-Go criteria: {(go_no_go_text or '').strip() or 'TBD'}."
        )

        if add_logic_choice == "Yes":
            additional_logic_sentence = f"Additional gating logic will be applied: {add_logic_text.strip() or 'TBD'}."
        else:
            additional_logic_sentence = (
                "No additional gating logic beyond the defined go/no-go criteria."
            )
        tools_sentence_obs = (
            f"Observability will be supported by {_join(selected_tools_obs)}."
        )

        utils.thick_hr(color="#6785a0", thickness=3)
        st.markdown("**Preview Solution Highlights**")
        lines = []
        if selected_methods:
            lines.append(f"- {methods_sentence}")
        if (go_no_go_text or "").strip():
            lines.append(f"- {go_no_go_sentence}")
        if add_logic_choice == "Yes" and (add_logic_text or "").strip():
            lines.append(f"- {additional_logic_sentence}")
        if selected_tools_obs:
            lines.append(f"- {tools_sentence_obs}")
        if not lines:
            st.info(
                "Make selections above to see highlights for the Observability section."
            )
        else:
            st.markdown("\n".join(lines))

        payload["observability"] = {
            "methods": methods_sentence,
            "go_no_go": go_no_go_sentence,
            "additional_logic": additional_logic_sentence,
            "tools": tools_sentence_obs,
            "selections": {
                "methods": selected_methods,
                "go_no_go_text": go_no_go_text,
                "additional_logic_enabled": add_logic_choice == "Yes",
                "additional_logic_text": add_logic_text,
                "tools": selected_tools_obs,
            },
        }

        # Orchestration section

    # Orchestration section
    with st.expander("Orchestration", expanded=False):

        # Orchestration strategy: select No, internal scripts, or describe details.
        # Generates an orchestration summary used for preview and export and gates downloads.

        st.markdown(
            """
            Orchestration coordinates processes across framework components to create end-to-end workflows.
            Key capabilities typically include:
            - Event-driven execution (sync, async, scheduled)
            - Safe rollback/compensation on errors
            - Dry-run previews before execution
            - Scheduling (one-time or recurring)
            - Logging, tracing, and audit visibility
            - Optional event correlation and inference
            """
        )

        st.subheader("Will the solution utilize orchestration?")

        ORCH_SENTINEL = "— Select one —"
        _orch_options = [
            ORCH_SENTINEL,
            "No",
            "Yes – internal via custom scripts and logic",
            "Yes – provide details",
        ]
        # Initialize if not set
        if "orch_choice" not in st.session_state:
            st.session_state["orch_choice"] = ORCH_SENTINEL
        orch_choice = st.radio(
            "Select an option",
            _orch_options,
            key="orch_choice",
            horizontal=False,
        )

        orch_details = ""
        if orch_choice == "Yes – provide details":
            orch_details = st.text_area(
                "Describe the orchestration approach",
                key="orch_details_text",
                placeholder="e.g., Use a workflow engine to trigger validations, approvals, execution, and post-checks; event-driven via webhooks; nightly reconciliations; rollback on failure; full traceability.",
            )

        # Narrative synthesis
        if orch_choice == ORCH_SENTINEL:
            orch_sentence = ""
        elif orch_choice == "No":
            # Render a proper bullet for 'No'
            orch_sentence = "No Orchestration will be used in this project."
        elif orch_choice == "Yes – internal via custom scripts and logic":
            orch_sentence = "Orchestration will be implemented internally using custom scripts and logic to coordinate end-to-end workflows."
        elif orch_choice == "Yes – provide details":
            orch_sentence = (
                f"Orchestration will be utilized: {orch_details.strip() or 'TBD'}."
            )
        else:
            orch_sentence = ""

        utils.thick_hr(color="#6785a0", thickness=3)
        st.markdown("**Preview Solution Highlights**")
        if orch_choice == ORCH_SENTINEL:
            st.info(
                "Make selections above to see highlights for the Orchestration section."
            )
        else:
            _orch_lines = []
            if orch_sentence.strip():
                _orch_lines.append(f"- {orch_sentence}")
            if _orch_lines:
                st.markdown("\n".join(_orch_lines))

        payload["orchestration"] = {
            "summary": orch_sentence,
            "selections": {
                "choice": orch_choice,
                "details": orch_details,
            },
        }

    # Collector section
    with st.expander("Collector", expanded=False):
        # Collection layer: methods, auth, handling, normalization/scale, and tools.
        # Populates payload.collector and contributes to highlights and export.

        st.markdown(
            """
            The collection layer focuses on retrieving the actual state of the network over time and ideally presenting it in a normalized format.
            - The collector can be thought of as a "read only" version of the executor.
            - It includes capabilities for retrieving live data from the network using read interfaces.
            - Retrieved data should be normalized across vendors and collection methods in a time series format.
            """
        )
        st.subheader("Collection methods (protocols/APIs)")
        st.caption("Build your own approaches (protocols, handling, normalization)")
        cols_c1 = st.columns(3)
        collect_method_opts = [
            "SNMP",
            "CLI/SSH",
            "NETCONF",
            "gNMI",
            "REST API",
            "Webhooks",
            "Syslog",
            "Streaming Telemetry",
        ]
        collect_checks = {}
        for i, opt in enumerate(collect_method_opts):
            with cols_c1[i % 3]:
                collect_checks[opt] = st.checkbox(opt, key=f"collector_method_{opt}")
        methods_other_enable = st.checkbox(
            "Other (fill in)", key="collector_methods_other_enable"
        )
        methods_other_text = ""
        if methods_other_enable:
            methods_other_text = st.text_input(
                "Other protocol/API", key="collector_methods_other"
            )

        st.subheader("Authentication")
        cols_c2 = st.columns(3)
        auth_opts = ["Username/Password", "SSH Keys", "OAuth2", "API Token", "mTLS"]
        auth_checks = {}
        for i, opt in enumerate(auth_opts):
            with cols_c2[i % 3]:
                auth_checks[opt] = st.checkbox(opt, key=f"collector_auth_{opt}")
        auth_other_enable = st.checkbox(
            "Other (fill in)", key="collector_auth_other_enable"
        )
        auth_other_text = ""
        if auth_other_enable:
            auth_other_text = st.text_input(
                "Other authentication method(s)", key="collector_auth_other"
            )

        st.subheader("Traffic handling")
        cols_c3 = st.columns(3)
        handling_opts = [
            "None",
            "Rate limiting",
            "Retries",
            "Exponential backoff",
            "Buffering/Queue",
        ]
        handling_checks = {}
        for i, opt in enumerate(handling_opts):
            with cols_c3[i % 3]:
                handling_checks[opt] = st.checkbox(opt, key=f"collector_handle_{opt}")
        handling_other_enable = st.checkbox(
            "Other (fill in)", key="collector_handling_other_enable"
        )
        handling_other_text = ""
        if handling_other_enable:
            handling_other_text = st.text_input(
                "Other traffic handling approach(es)", key="collector_handling_other"
            )

        st.subheader("Normalization and schemas")
        cols_c4 = st.columns(3)
        norm_opts = [
            "None",
            "Timestamping",
            "Tagging/labels",
            "Topology enrichment",
            "Schema mapping",
        ]
        norm_checks = {}
        for i, opt in enumerate(norm_opts):
            with cols_c4[i % 3]:
                norm_checks[opt] = st.checkbox(opt, key=f"collector_norm_{opt}")
        norm_other_enable = st.checkbox(
            "Other (fill in)", key="collector_norm_other_enable"
        )
        norm_other_text = ""
        if norm_other_enable:
            norm_other_text = st.text_input(
                "Other normalization/schema approach(es)", key="collector_norm_other"
            )

        # Visual divider indicating build vs buy/use existing
        st.divider()
        _or_c1, _or_c2, _or_c3 = st.columns([1, 1, 1])
        with _or_c2:
            st.markdown("**OR**")

        # Collection tools (moved here from separate section)
        st.subheader("Collection tools")
        st.caption("Buy/use existing platforms (collection tools)")
        cols_ct = st.columns(3)
        tool_opts = [
            "None",
            "Open Source Software",
            "Commercial/Enterprise Product",
            "In-house Software",
        ]
        tool_checks = {}
        for i, opt in enumerate(tool_opts):
            with cols_ct[i % 3]:
                tool_checks[opt] = st.checkbox(opt, key=f"collection_tool_{opt}")
        tools_other_enable = st.checkbox(
            "Other (fill in)", key="collection_tools_other_enable"
        )
        tools_other_text = ""
        if tools_other_enable:
            tools_other_text = st.text_input(
                "Other collection tool(s)", key="collection_tools_other"
            )

        st.subheader("Expected scale")
        col_s1, col_s2, col_s3 = st.columns(3)
        with col_s1:
            devices = st.text_input(
                "Devices (approx)", key="collector_devices", placeholder="e.g., 500"
            )
        with col_s2:
            metrics = st.text_input(
                "Metrics/sec (approx)",
                key="collector_metrics",
                placeholder="e.g., 50k",
                help=(
                    "Approximate number of time-series datapoints ingested per second across all devices/feeds. "
                    "Examples: interface counters, CPU/memory samples, route counts, flow records, or parsed log lines. "
                    "This is not the number of API calls; it is the count of individual metrics collected per second (e.g., 50k = 50,000/sec)."
                ),
            )
        with col_s3:
            cadence = st.text_input(
                "Polling/stream cadence",
                key="collector_cadence",
                placeholder="e.g., 30s polling; streaming realtime",
            )

        selected_methods = [k for k, v in collect_checks.items() if v]
        if methods_other_enable and (methods_other_text or "").strip():
            selected_methods.append(methods_other_text.strip())
        selected_auth = [k for k, v in auth_checks.items() if v]
        if auth_other_enable and (auth_other_text or "").strip():
            selected_auth.append(auth_other_text.strip())
        selected_handling = [k for k, v in handling_checks.items() if v]
        if handling_other_enable and (handling_other_text or "").strip():
            selected_handling.append(handling_other_text.strip())
        selected_norm = [k for k, v in norm_checks.items() if v]
        if norm_other_enable and (norm_other_text or "").strip():
            selected_norm.append(norm_other_text.strip())
        selected_tools = [k for k, v in tool_checks.items() if v]
        if tools_other_enable and (tools_other_text or "").strip():
            selected_tools.append(tools_other_text.strip())

        methods_sentence = f"Collection will use {_join(selected_methods)}."
        auth_sentence = f"Authentication will leverage {_join(selected_auth)}."
        handling_sentence = f"Traffic handling will include {_join(selected_handling)}."
        norm_sentence = f"Collected data will be normalized via {_join(selected_norm)}."
        scale_sentence = f"Expected scale: ~{devices or 'TBD'} devices, ~{metrics or 'TBD'} metrics/sec, cadence {cadence or 'TBD'}."
        tools_sentence_coll = f"Collection tools will include {_join(selected_tools)}."

        utils.thick_hr(color="#6785a0", thickness=3)
        st.markdown("**Preview Solution Highlights**")
        any_selected_coll = bool(
            selected_methods
            or selected_auth
            or selected_handling
            or selected_norm
            or selected_tools
            or (devices or metrics or cadence)
        )
        if not any_selected_coll:
            st.info(
                "Make selections above to see highlights for the Collector section."
            )
        else:
            st.markdown(
                "\n".join(
                    [
                        f"- {methods_sentence}",
                        f"- {auth_sentence}",
                        f"- {handling_sentence}",
                        f"- {norm_sentence}",
                        f"- {scale_sentence}",
                        f"- {tools_sentence_coll}",
                    ]
                )
            )

        payload["collector"] = {
            "methods": methods_sentence,
            "auth": auth_sentence,
            "handling": handling_sentence,
            "normalization": norm_sentence,
            "scale": scale_sentence,
            "tools": tools_sentence_coll,
            "selections": {
                "methods": selected_methods,
                "auth": selected_auth,
                "handling": selected_handling,
                "normalization": selected_norm,
                "devices": devices,
                "metrics_per_sec": metrics,
                "cadence": cadence,
                "tools": selected_tools,
            },
        }

    # Executor section
    with st.expander("Executor", expanded=False):
        """
        Execution Block: Describes how intent/changes will be applied to the network.
        """
        st.markdown(
            """
            The executor executes the actual changes to the network.
            - It MUST be capable of interacting with any supported network write interfaces (e.g., SSH/CLI, NETCONF, gNMI/gNOI, REST APIs).
            - It SHOULD support operations that alter network state, from deploying full/partial configs to device actions (reboots, upgrades).
            - Task input SHOULD originate from the intended state or be derived via data from Observability.
            - It SHOULD provide a dry‑run capability and support transactional execution.
            - It MAY support both imperative and declarative approaches, and operations SHOULD be idempotent.
            """
        )
        st.subheader("How will your solution execute change?")
        cols_exec = st.columns(2)
        exec_opts = [
            "Automating CLI interaction with Python automation frameworks (Netmiko, Napalm, Nornir, PyATS)",
            "Using Open Source Software (Ansible, Terraform, etc.)",
            "Using Custom Python scripts",
            "Using Network Vendor Product (Cisco DNA Center, Arista CVP)",
            "Using a Commercial/Enterprise Product",
        ]
        exec_checks = {}
        for i, opt in enumerate(exec_opts):
            with cols_exec[i % 2]:
                exec_checks[opt] = st.checkbox(opt, key=f"exec_{i}")
        with cols_exec[0]:
            exec_custom_enable = st.checkbox(
                "Custom (describe in detail)", key="exec_custom_enable"
            )
            exec_custom_text = ""
            if exec_custom_enable:
                exec_custom_text = st.text_area(
                    "Custom execution approach", key="exec_custom_text"
                )

        selected_exec = [k for k, v in exec_checks.items() if v]
        if exec_custom_enable and exec_custom_text.strip():
            selected_exec.append(exec_custom_text.strip())

        exec_sentence = f"Execution will be performed using {_join(selected_exec)}."

        utils.thick_hr(color="#6785a0", thickness=3)
        st.markdown("**Preview Solution Highlights**")
        any_selected_exec = bool(selected_exec)
        if not any_selected_exec:
            st.info("Make selections above to see highlights for the Executor section.")
        else:
            st.markdown(
                "\n".join(
                    [
                        f"- {exec_sentence}",
                    ]
                )
            )

        payload["executor"] = {
            "methods": exec_sentence,
            "selections": {
                "methods": selected_exec,
            },
        }

    # Transition to external interfaces and planning
    utils.thick_hr(color=hr_color_dict["naf_yellow"], thickness=5)
    st.markdown(
        "While the framework helps you think about the technical implementation, for a complete project let's now consider external interfaces, staffing, and timelines."
    )

    # Dependencies & External Interfaces
    with st.expander("Dependencies & External Interfaces", expanded=False):
        # Dependencies selector: external systems and interfaces this solution relies on.

        st.caption(
            "Select the external systems this automation will interact with and add details where applicable."
        )
        dep_defs = [
            {
                "key": "network_infra",
                "label": "Network Infrastructure",
                "default": True,
                "details": False,
                "help": "The automation will act on some or all of the organization's network infrastructure (switches, appliances, routers, etc.).",
            },
            {
                "key": "network_controllers",
                "label": "Network Controllers",
                "default": False,
                "details": True,
            },
            {
                "key": "revision_control",
                "label": "Revision Control system",
                "default": True,
                "details": True,
                "help": "e.g. GitHub, GitLab, Bitbucket",
            },
            {
                "key": "itsm",
                "label": "ITSM/Change Management System",
                "default": False,
                "details": True,
            },
            {
                "key": "authn",
                "label": "Authentication System",
                "default": False,
                "details": True,
            },
            {
                "key": "ipams",
                "label": "IPAMS Systems",
                "default": False,
                "details": True,
            },
            {
                "key": "inventory",
                "label": "Inventory Systems",
                "default": False,
                "details": True,
                "help": "Source of truth/CMDB/inventory (e.g., NetBox, InfraHub, ServiceNow CMDB). What data do you read/write?",
            },
            {
                "key": "design_intent",
                "label": "Design Data/Intent Systems",
                "default": False,
                "details": True,
                "help": "Systems holding golden intent or design models (InfraHub, Custom DB).",
            },
            {
                "key": "observability",
                "label": "Observability System",
                "default": False,
                "details": True,
                "help": "Telemetry/monitoring/logs/traces (e.g., SuzieQ, Prometheus).",
            },
            {
                "key": "vendor_mgmt",
                "label": "Vendor Tool/Management System",
                "default": False,
                "details": True,
                "help": "(e.g., Cisco DNAC, Wireless Controllers, Miraki, Arista CVP, Aruba Central, Juniper Apstra).",
            },
        ]

        deps_selected = []
        for d in dep_defs:
            # Initialize checkbox state if not set
            dep_key = f"dep_{d['key']}"
            if dep_key not in st.session_state:
                st.session_state[dep_key] = d.get("default", False)
            checked = st.checkbox(
                d["label"],
                key=dep_key,
                help=d.get("help"),
            )
            if checked and d.get("details"):
                default_detail = d.get("default_detail", "")
                if d["key"] == "revision_control":
                    default_detail = "GitHub"
                # Initialize detail text if not set
                detail_key = f"dep_{d['key']}_details"
                if detail_key not in st.session_state:
                    st.session_state[detail_key] = default_detail
                detail_text = st.text_input(
                    f"Details for {d['label']}",
                    key=detail_key,
                )
            else:
                detail_text = ""
            if checked:
                deps_selected.append(
                    {"name": d["label"], "details": (detail_text or "").strip()}
                )

        payload["dependencies"] = deps_selected

    # Staffing, Timeline, & Milestones
    with st.expander("Staffing, Timeline, & Milestones", expanded=False):
        # Planning inputs: staffing counts/plan, start date, and milestone durations.
        # Drives computed schedule and optional Gantt export.

        st.caption(
            "Capture a high-level plan with durations in business days. Start date drives scheduled dates."
        )
        st.info(
            "Duration should reflect expected staffing. For example, if a step is 10 business days of work but two people will work in parallel, you may model it as 5–6 days to allow for coordination overhead."
        )

        st.subheader("Staffing plan")
        st.caption(
            "Provide expected direct staffing and a short plan. Markdown is supported."
        )

        # Build/Buy/Hybrid selection
        build_buy_options = [
            "Build In-House",
            "Build with Professional Services or other external resources (Buy)",
            "Hybrid",
        ]
        if "timeline_build_buy" not in st.session_state:
            st.session_state["timeline_build_buy"] = "Build In-House"
        build_buy_choice = st.radio(
            "Development approach",
            options=build_buy_options,
            key="_timeline_build_buy",
            horizontal=True,
            help="Select whether this solution will be built in-house, purchased, or a combination.",
        )
        st.session_state["timeline_build_buy"] = build_buy_choice

        col_sp1, col_sp2, col_sp3 = st.columns([1, 1, 2])
        with col_sp1:
            staff_count = st.number_input(
                "Direct staff on project",
                min_value=0,
                value=int(st.session_state.get("timeline_staff_count", 1)),
                step=1,
                key="_timeline_staff_count",
                help="Number of direct employees from your team or from another team in your organization.",
            )
            st.session_state["timeline_staff_count"] = int(staff_count)
        with col_sp2:
            external_staff_count = st.number_input(
                "Professional services staff",
                min_value=0,
                value=int(st.session_state.get("timeline_external_staff_count", 0)),
                step=1,
                key="_timeline_external_staff_count",
                help="Number of external staff working on project (e.g., staff augmentation or professional services engagement).",
            )
            st.session_state["timeline_external_staff_count"] = int(
                external_staff_count
            )
        with col_sp3:
            staffing_plan = st.text_area(
                "Staffing plan (markdown supported)",
                value=str(st.session_state.get("timeline_staffing_plan", "")),
                height=120,
                key="_timeline_staffing_plan",
            )
            st.session_state["timeline_staffing_plan"] = staffing_plan

        # Holiday calendar selector (lightweight)
        region_options = [
            "None",
            "United States",
            "Canada",
            "United Kingdom",
            "Germany",
            "India",
            "Australia",
        ]
        # Initialize if not set
        if "_timeline_holiday_region" not in st.session_state:
            st.session_state["_timeline_holiday_region"] = st.session_state.get(
                "timeline_holiday_region", "None"
            )
        holiday_region = st.selectbox(
            "Holiday calendar",
            options=region_options,
            help="Used to skip public holidays when computing business days.",
            key="_timeline_holiday_region",
        )
        st.session_state["timeline_holiday_region"] = holiday_region

        def _build_holiday_set(start_year: int, years_ahead: int = 2):
            # Note: This function must remain nested as it depends on holiday_region closure
            if _hol is None or holiday_region == "None":
                return set()
            years = list(range(start_year, start_year + max(1, years_ahead) + 1))
            cal = None
            try:
                if holiday_region == "United States":
                    cal = _hol.UnitedStates(years=years)
                elif holiday_region == "Canada":
                    cal = _hol.Canada(years=years)
                elif holiday_region == "United Kingdom":
                    cal = _hol.UnitedKingdom(years=years)
                elif holiday_region == "Germany":
                    cal = _hol.Germany(years=years)
                elif holiday_region == "India":
                    cal = _hol.India(years=years)
                elif holiday_region == "Australia":
                    cal = _hol.Australia(years=years)
            except Exception:
                cal = None
            return set(cal.keys()) if cal else set()

        # Start date
        default_start = st.session_state.get("timeline_start_date")
        start_date = st.date_input(
            "Project start date",
            value=default_start or datetime.datetime.today().date(),
            key="_timeline_start_date_input",
        )
        st.session_state["timeline_start_date"] = start_date

        # Milestones state
        if "timeline_milestones" not in st.session_state:
            st.session_state["timeline_milestones"] = [
                {"name": "Planning", "duration": 5, "notes": ""},
                {"name": "Design", "duration": 10, "notes": ""},
                {"name": "Build", "duration": 10, "notes": ""},
                {"name": "Test", "duration": 5, "notes": ""},
                {"name": "Pilot", "duration": 5, "notes": ""},
                {"name": "Production Rollout", "duration": 10, "notes": ""},
            ]

        # Controls
        c_a, c_b = st.columns([1, 1])
        with c_a:
            if st.button("Add milestone row", key="_timeline_add_row"):
                st.session_state["timeline_milestones"].append(
                    {"name": "", "duration": 0, "notes": ""}
                )
        with c_b:
            st.caption(
                "Use the fields below to edit milestone name, duration (business days), and notes."
            )

        # Render rows
        to_delete = []
        for idx, row in enumerate(list(st.session_state["timeline_milestones"])):
            rcols = st.columns([3, 2, 5, 1])
            with rcols[0]:
                row_name = st.text_input(
                    "Milestone",
                    value=str(row.get("name", "")),
                    key=f"_tl_name_{idx}",
                )
            with rcols[1]:
                row_duration = st.number_input(
                    "Duration (business days)",
                    min_value=0,
                    value=int(row.get("duration", 0)),
                    step=1,
                    key=f"_tl_duration_{idx}",
                )
            with rcols[2]:
                row_notes = st.text_input(
                    "Notes/comments",
                    value=str(row.get("notes", "")),
                    key=f"_tl_notes_{idx}",
                )
            with rcols[3]:
                del_flag = st.checkbox("Delete", key=f"_tl_del_{idx}")
                if del_flag:
                    to_delete.append(idx)

            # Persist edits back to state
            st.session_state["timeline_milestones"][idx] = {
                "name": row_name,
                "duration": int(row_duration),
                "notes": row_notes,
            }

        # Apply deletions (from end to start)
        for i in sorted(to_delete, reverse=True):
            if 0 <= i < len(st.session_state["timeline_milestones"]):
                st.session_state["timeline_milestones"].pop(i)

        # Build schedule
        schedule = []
        cursor = start_date
        holiday_set = _build_holiday_set(start_date.year, years_ahead=3)
        total_bd = 0
        for row in st.session_state["timeline_milestones"]:
            name = (row.get("name") or "").strip()
            dur = int(row.get("duration") or 0)
            notes = row.get("notes") or ""
            if not name and dur <= 0:
                continue
            start = cursor
            end = _add_business_days(start, dur, holiday_set) if dur > 0 else start
            schedule.append(
                {
                    "name": name or "(Unnamed)",
                    "duration_bd": dur,
                    "start": start,
                    "end": end,
                    "notes": notes,
                }
            )
            cursor = end  # next starts after this completes
            total_bd += max(0, dur)

        # Summary & display
        if schedule:
            st.markdown("**Timeline summary (business days only)**")
            st.write(
                f"Start: {start_date.strftime('%Y-%m-%d')} • Total duration: {total_bd} business days • Projected completion: {schedule[-1]['end'].strftime('%Y-%m-%d')}"
            )
            # Success/info callouts
            st.success(
                f"Expected delivery date: {schedule[-1]['end'].strftime('%Y-%m-%d')}"
            )
            months_est = (
                total_bd / 21.75 if total_bd else 0.0
            )  # approx working days per month
            years_est = months_est / 12.0 if months_est else 0.0
            st.info(
                f"Approximate duration: {months_est:.1f} months ({years_est:.2f} years) based on business days"
            )

            st.markdown("**Milestones schedule**")
            for item in schedule:
                st.write(
                    f"- {item['name']}: {item['start'].strftime('%Y-%m-%d')} → {item['end'].strftime('%Y-%m-%d')} ({item['duration_bd']} bd)"
                )

            # Optional: Visual timeline
            show_chart = st.checkbox(
                "Show Gantt chart", value=True, key="_timeline_show_chart"
            )
            if show_chart:
                df = pd.DataFrame(
                    [
                        {
                            "Task": it["name"],
                            "Start": it["start"],
                            "Finish": it["end"],
                            "Duration (bd)": it["duration_bd"],
                        }
                        for it in schedule
                    ]
                )
                if not df.empty:
                    fig = px.timeline(
                        df,
                        x_start="Start",
                        x_end="Finish",
                        y="Task",
                        color="Task",
                        color_discrete_sequence=px.colors.qualitative.Set3,
                    )
                    fig.update_yaxes(autorange="reversed")  # earliest at top
                    fig.update_layout(height=380, margin=dict(l=0, r=0, t=30, b=0))
                    st.plotly_chart(fig, width="stretch")

                    # Offer download of the Gantt chart as a standalone HTML file
                    gantt_html = fig.to_html(full_html=True, include_plotlyjs="cdn")
                    gantt_fname = f"WizardTimeline_{datetime.datetime.utcnow().strftime('%Y%m%d_%H%M%S')}Z.html"
                    dl_clicked = st.download_button(
                        label="Download Gantt chart (HTML)",
                        data=gantt_html,
                        file_name=gantt_fname,
                        mime="text/html",
                        width="stretch",
                        key="wizard_timeline_download_btn",
                    )
                    # no-op on click; no session state to update
        else:
            st.info("Add at least one milestone to build a timeline.")

        payload["timeline"] = {
            "start_date": start_date.strftime("%Y-%m-%d"),
            "total_business_days": total_bd,
            "projected_completion": (
                schedule[-1]["end"].strftime("%Y-%m-%d") if schedule else None
            ),
            "build_buy": st.session_state.get("timeline_build_buy", "Build In-House"),
            "staff_count": int(st.session_state.get("timeline_staff_count", 0)),
            "external_staff_count": int(
                st.session_state.get("timeline_external_staff_count", 0)
            ),
            "staffing_plan_md": st.session_state.get("timeline_staffing_plan", ""),
            "holiday_region": holiday_region,
            "items": [
                {
                    "name": i["name"],
                    "duration_bd": i["duration_bd"],
                    "start": i["start"].strftime("%Y-%m-%d"),
                    "end": i["end"].strftime("%Y-%m-%d"),
                    "notes": i["notes"],
                }
                for i in schedule
            ],
        }

    # Determine if there is meaningful content across sections
    any_content = _has_any_content(payload)
    # Fallback: if the user has selected an orchestration choice (including 'No') via session_state,
    # treat that as meaningful content to enable export even before other narratives populate.
    try:
        _orch_choice_ss = (st.session_state.get("orch_choice") or "").strip()
        if _orch_choice_ss and _orch_choice_ss != "— Select one —":
            any_content = True
    except Exception:
        pass

    # Dependencies: do not render immediately on the main page; include only in the generated summary
    deps = payload.get("dependencies", [])
    if deps:
        deps_slim = [
            {
                "name": (d or {}).get("name"),
                "details": (d or {}).get("details", "").strip(),
            }
            for d in deps
            if (d or {}).get("name")
        ]
        default_deps = [
            {"name": "Network Infrastructure", "details": ""},
            {"name": "Revision Control system", "details": "GitHub"},
        ]

        looks_default_deps = _sorted_deps(deps_slim) == _sorted_deps(default_deps)
        if not looks_default_deps:
            any_content = True

    if not any_content:
        # Use same gate as sidebar to decide whether to show the reminder
        sel = {
            "pres": (payload.get("presentation", {}) or {}).get("selections", {}),
            "intent": (payload.get("intent", {}) or {}).get("selections", {}),
            "obs": (payload.get("observability", {}) or {}).get("selections", {}),
            "orch": (payload.get("orchestration", {}) or {}).get("selections", {}),
            "coll": (payload.get("collector", {}) or {}).get("selections", {}),
            "exec": (payload.get("executor", {}) or {}).get("selections", {}),
        }

        has_any_selection = any(_has_list_selections(v) for v in sel.values())
        role_nonempty = any(
            ((payload.get("my_role", {}) or {}).get(k) or "").strip()
            for k in ("who", "skills", "developer")
        )
        ini = payload.get("initiative", {}) or {}
        default_title = DEFAULT_TITLE
        default_desc = DEFAULT_DESCRIPTION
        _title = (ini.get("title") or "").strip()
        _desc = (ini.get("description") or "").strip()
        ini_nondefault = bool(
            (_title and _title != default_title) or (_desc and _desc != default_desc)
        )
        orch_sel = (payload.get("orchestration", {}) or {}).get("selections", {}) or {}
        orch_choice = (orch_sel.get("choice") or "").strip() or (
            st.session_state.get("orch_choice") or ""
        ).strip()
        orch_details = (orch_sel.get("details") or "").strip()
        # Treat any non-sentinel choice (including 'No') as a meaningful change for gating
        orch_nondefault = bool(orch_choice and orch_choice != "— Select one —")
        if not (
            has_any_selection or ini_nondefault or orch_nondefault or role_nonempty
        ):
            st.info(
                "Start filling in the sections above to see Solution Highlights here. Once you provide inputs, you will also be able to download the Wizard JSON."
            )

    # Markdown summary builder & export — only when there is meaningful content
    if any_content:
        # Build a concise markdown summary from current payload
        summary_parts = []
        # My Role (show if any field present)
        my_role = payload.get("my_role", {}) or {}
        role_lines = []
        if (my_role.get("who") or "").strip():
            role_lines.append(f"- Who: {my_role.get('who')}")
        if (my_role.get("skills") or "").strip():
            role_lines.append(f"- Skills: {my_role.get('skills')}")
        if (my_role.get("developer") or "").strip():
            role_lines.append(f"- Developer: {my_role.get('developer')}")
        summary_parts.append(_section_md("My Role", role_lines))
        # Initiative (suppress known defaults)
        ini = payload.get("initiative", {})
        ini_lines = []
        default_title = DEFAULT_TITLE
        default_desc = DEFAULT_DESCRIPTION
        _title = (ini.get("title") or "").strip()
        _desc = (ini.get("description") or "").strip()
        _out = (ini.get("out_of_scope") or "").strip()
        if _title and _title != default_title:
            ini_lines.append(f"- Title: {_title}")
        if _desc and _desc != default_desc:
            ini_lines.append(f"- Scope: {_desc}")
        if _out:
            ini_lines.append(f"- Out of scope: {_out}")
        # If details_md exists, we keep it for the export doc, but don't render here to avoid duplication
        summary_parts.append(_section_md("Initiative", ini_lines))

        # Presentation
        pres = payload.get("presentation", {})
        pres_lines = []
        for k in ("users", "interaction", "tools", "auth"):
            v = pres.get(k)
            if v and is_meaningful(v):
                pres_lines.append(f"- {v}")
        summary_parts.append(_section_md("Presentation", pres_lines))

        # Intent
        intent = payload.get("intent", {})
        intent_lines = []
        for k in ("development", "provided"):
            v = intent.get(k)
            if v and is_meaningful(v):
                intent_lines.append(f"- {v}")
        summary_parts.append(_section_md("Intent", intent_lines))

        # Observability
        obs = payload.get("observability", {})
        obs_lines = []
        for k in ("methods", "go_no_go", "additional_logic", "tools"):
            v = obs.get(k)
            if v and is_meaningful(v):
                obs_lines.append(f"- {v}")
        summary_parts.append(_section_md("Observability", obs_lines))

        # Orchestration
        orch = payload.get("orchestration", {})
        orch_lines = []
        v = orch.get("summary")
        if v and is_meaningful(v):
            orch_lines.append(f"- {v}")
        summary_parts.append(_section_md("Orchestration", orch_lines))

        # Collector
        collector = payload.get("collector", {})
        col_lines = []
        for k in ("methods", "auth", "handling", "normalization", "scale", "tools"):
            v = collector.get(k)
            if v and is_meaningful(v):
                col_lines.append(f"- {v}")
        summary_parts.append(_section_md("Collector", col_lines))

        # Executor
        executor = payload.get("executor", {})
        exe_lines = []
        v = executor.get("methods")
        if v and is_meaningful(v):
            exe_lines.append(f"- {v}")
        summary_parts.append(_section_md("Executor", exe_lines))

        # Dependencies (suppress default pair)
        deps = payload.get("dependencies", [])
        dep_lines = []
        if deps:
            deps_slim = [
                {
                    "name": (d or {}).get("name"),
                    "details": (d or {}).get("details", "").strip(),
                }
                for d in deps
                if (d or {}).get("name")
            ]
            default_deps = [
                {"name": "Network Infrastructure", "details": ""},
                {"name": "Revision Control system", "details": "GitHub"},
            ]

            if _sorted_deps(deps_slim) != _sorted_deps(default_deps):
                for d in deps_slim:
                    name = d.get("name")
                    details = d.get("details")
                    if name:
                        dep_lines.append(
                            f"- {name}{(': ' + details) if details else ''}"
                        )
        summary_parts.append(
            _section_md("Dependencies & External Interfaces", dep_lines)
        )

        # Timeline (only when there are milestone items or staffing plan text)
        tl = payload.get("timeline", {})
        tl_lines = []
        items = tl.get("items") or []
        tl_staff_md = (tl.get("staffing_plan_md") or "").strip()
        if items:
            staff_ct = tl.get("staff_count")
            start = tl.get("start_date")
            end = tl.get("projected_completion")
            total_bd = tl.get("total_business_days")
            tl_lines.append(
                f"- Staff {staff_ct if staff_ct is not None else 'TBD'} • Start {start or 'TBD'} • Total {total_bd if total_bd is not None else 'TBD'} bd • Completion {end or 'TBD'}"
            )
            for i in items[:15]:
                tl_lines.append(
                    f"  - {i.get('name')}: {i.get('start')} → {i.get('end')} ({i.get('duration_bd')} bd)"
                )
            summary_parts.append(
                _section_md("Staffing, Timeline, & Milestones", tl_lines)
            )
        if tl_staff_md:
            summary_parts.append("\n## Staffing Plan\n")
            summary_parts.append(tl_staff_md + "\n")

        summary_md = ("".join(summary_parts)).strip()
        if summary_md:
            with st.expander("Detailed solution description (Preview)", expanded=False):
                """
                Live preview of the report that will be written into the ZIP (naf_report_*.md).
                """
                st.caption(
                    "Preview of the full report that will be included in the download (images removed for preview)."
                )
                
                # Render the Jinja template for preview
                template_preview = _render_template_preview(payload, summary_md)
                st.markdown(template_preview)

    if any_content:
        # Build a comprehensive payload including defaults for any missing sections
        final_payload = dict(payload)
        final_payload = dict(payload) if isinstance(payload, dict) else {}
        # Ensure initiative exists (without solution_details_md)
        if "initiative" not in final_payload or not isinstance(
            final_payload.get("initiative"), dict
        ):
            final_payload["initiative"] = {}

        # Defaults for sections
        if "my_role" not in final_payload:
            final_payload["my_role"] = {"who": "", "skills": "", "developer": ""}
        if "presentation" not in final_payload:
            final_payload["presentation"] = {
                "users": "",
                "interaction": "",
                "tools": "",
                "auth": "",
                "selections": {
                    "users": [],
                    "interactions": [],
                    "tools": [],
                    "auth": [],
                },
            }

        if "intent" not in final_payload:
            final_payload["intent"] = {
                "development": "",
                "provided": "",
                "selections": {
                    "development": [],
                    "provided": [],
                },
            }

        if "observability" not in final_payload:
            final_payload["observability"] = {
                "methods": "",
                "go_no_go": "",
                "additional_logic": "",
                "tools": "",
                "selections": {
                    "methods": [],
                    "go_no_go_text": "",
                    "additional_logic_enabled": False,
                    "additional_logic_text": "",
                    "tools": [],
                },
            }

        if "orchestration" not in final_payload:
            final_payload["orchestration"] = {
                "summary": "",
                "selections": {
                    "choice": "No",
                    "details": "",
                },
            }

        if "executor" not in final_payload:
            final_payload["executor"] = {
                "methods": "",
                "selections": {"methods": []},
            }

        if "collector" not in final_payload:
            final_payload["collector"] = {
                "methods": "",
                "auth": "",
                "handling": "",
                "normalization": "",
                "scale": "",
                "tools": "",
                "selections": {
                    "methods": [],
                    "auth": [],
                    "handling": [],
                    "normalization": [],
                    "devices": "",
                    "metrics_per_sec": "",
                    "cadence": "",
                    "tools": [],
                },
            }

        if "dependencies" not in final_payload:
            final_payload["dependencies"] = [
                {"name": "Network Infrastructure", "details": ""},
                {"name": "Revision Control system", "details": "GitHub"},
            ]

        if "timeline" not in final_payload:
            # Construct a default timeline with computed dates (weekdays only, no holidays)
            start = datetime.datetime.today().date()
            default_items = [
                {"name": "Planning", "duration_bd": 5, "notes": ""},
                {"name": "Design", "duration_bd": 10, "notes": ""},
                {"name": "Build", "duration_bd": 10, "notes": ""},
                {"name": "Test", "duration_bd": 5, "notes": ""},
                {"name": "Pilot", "duration_bd": 5, "notes": ""},
                {"name": "Production Rollout", "duration_bd": 10, "notes": ""},
            ]
            cursor = start
            schedule = []
            total_bd = 0
            for it in default_items:
                dur = int(it["duration_bd"])
                s = cursor
                e = _add_business_days(s, dur) if dur > 0 else s
                schedule.append(
                    {
                        "name": it["name"],
                        "duration_bd": dur,
                        "start": s.strftime("%Y-%m-%d"),
                        "end": e.strftime("%Y-%m-%d"),
                        "notes": it.get("notes", ""),
                    }
                )
                cursor = e
                total_bd += max(0, dur)

            final_payload["timeline"] = {
                "start_date": start.strftime("%Y-%m-%d"),
                "total_business_days": total_bd,
                "projected_completion": cursor.strftime("%Y-%m-%d"),
                "staff_count": 1,
                "holiday_region": "None",
                "items": schedule,
            }

        sdd_template_env = None
        sdd_ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            templates_dir = (Path(__file__).parent.parent / "templates").resolve()
            env = Environment(
                loader=FileSystemLoader(str(templates_dir)),
                autoescape=False,
            )
            tmpl = env.get_template("Solution_Design_Report.j2")
            context = {
                "generated_timestamp": sdd_ts,
                "highlights": summary_md,
                "initiative": final_payload.get("initiative", {}),
                "my_role": final_payload.get("my_role", {}),
                "stakeholders": final_payload.get("stakeholders", {}),
                "presentation": final_payload.get("presentation", {}),
                "intent": final_payload.get("intent", {}),
                "observability": final_payload.get("observability", {}),
                "orchestration": final_payload.get("orchestration", {}),
                "collector": final_payload.get("collector", {}),
                "executor": final_payload.get("executor", {}),
                "dependencies": final_payload.get("dependencies", []),
                "timeline": final_payload.get("timeline", {}),
                "staffing_plan": (final_payload.get("timeline", {}) or {}).get(
                    "staffing_plan_md", ""
                ),
                "gantt_image_path": None,
            }
            sdd_template_env = (env, tmpl, context)
        except Exception:
            # Fallback minimal doc if template can't be loaded
            basic_doc = ["# Solution Design Document", f"Generated: {sdd_ts}"]
            if (summary_md or "").strip():
                basic_doc.append("## Highlights")
                basic_doc.append(summary_md)
            sdd_doc_md = "\n\n".join(basic_doc).encode("utf-8")

        # Rebuild a color Gantt chart from payload timeline
        gantt_png_bytes = None
        gantt_html_bytes = None
        try:
            tl = final_payload.get("timeline", {})
            rows = []
            for it in (tl.get("items") or [])[:100]:
                rows.append(
                    {
                        "Task": it.get("name", "Task"),
                        "Start": it.get("start"),
                        "Finish": it.get("end"),
                    }
                )
            if rows:
                df = pd.DataFrame(rows)
                fig = px.timeline(
                    df,
                    x_start="Start",
                    x_end="Finish",
                    y="Task",
                    color="Task",
                    color_discrete_sequence=px.colors.qualitative.Set3,
                )
                fig.update_yaxes(autorange="reversed")
                # Try PNG first (requires kaleido)
                try:
                    gantt_png_bytes = fig.to_image(format="png", scale=2)
                except Exception:
                    gantt_png_bytes = None
                # Always prepare HTML fallback
                gantt_html_bytes = fig.to_html(
                    full_html=True, include_plotlyjs="cdn"
                ).encode("utf-8")
        except Exception:
            pass

        # Inform the user when PNG export failed (typically missing kaleido)
        try:
            has_rows = bool(rows)
        except Exception:
            has_rows = False
        if has_rows and gantt_png_bytes is None:
            st.info(
                "Gantt PNG could not be generated. To include a PNG in the ZIP, install the 'kaleido' package (e.g., pip install -U kaleido) and rerun."
            )

        # Define title for ZIP filenames
        ini = final_payload.get("initiative", {}) or {}
        _title = (ini.get("title") or "").strip()
        title_for_zip = (
            re.sub(r"[^A-Za-z0-9_-]+", "_", (_title or "solution")).strip("_")
            or "solution"
        )
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

        # Create JSON bytes for ZIP
        final_json_bytes = json.dumps(final_payload, indent=2).encode("utf-8")

        # Define ZIP filename
        zip_name = f"naf_report_{title_for_zip}_{ts}.zip"

        # Create ZIP in-memory
        zip_buf = io.BytesIO()
        with zipfile.ZipFile(zip_buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
            json_name = f"naf_report_{title_for_zip}_{ts}.json"
            md_name = f"naf_report_{title_for_zip}_{ts}.md"
            zf.writestr(json_name, final_json_bytes)
            # Write markdown after potential Gantt generation so template can reference image name
            try:
                env, tmpl, context = sdd_template_env  # type: ignore
                # Update gantt_image_path based on actual artifact (store under images/)
                context["gantt_image_path"] = (
                    "images/Gantt.png" if gantt_png_bytes else None
                )
                rendered = tmpl.render(**context)
                sdd_doc_md = rendered.encode("utf-8")
                # Safety: if render produced empty/whitespace, write a minimal doc
                if not (sdd_doc_md or b"").strip():
                    basic_doc = ["# Solution Design Document", f"Generated: {sdd_ts}"]
                    _hl = (context.get("highlights") or "").strip()
                    if _hl:
                        basic_doc.append("## Highlights")
                        basic_doc.append(_hl)
                    sdd_doc_md = ("\n\n".join(basic_doc)).encode("utf-8")
            except Exception:
                # If earlier fallback created sdd_doc_md, use it; else create a minimal fallback now
                if "sdd_doc_md" not in locals():
                    sdd_doc_md = (
                        "# Solution Design Document\n\n" + f"Generated: {sdd_ts}"
                    ).encode("utf-8")
            zf.writestr(md_name, sdd_doc_md)
            if gantt_png_bytes:
                zf.writestr("images/Gantt.png", gantt_png_bytes)
            elif gantt_html_bytes:
                # Provide an HTML fallback if PNG isn't available (no kaleido)
                zf.writestr("Gantt.html", gantt_html_bytes)

            # Include branding icon if available so Markdown image resolves
            try:
                icon_path = (
                    Path(__file__).parent.parent / "images" / "naf_icon.png"
                ).resolve()
                if icon_path.exists():
                    with open(icon_path, "rb") as f:
                        zf.writestr("images/naf_icon.png", f.read())
            except Exception:
                pass

        zip_bytes = zip_buf.getvalue()
        # Export (single ZIP download) only when summary has meaningful content
        # and at least one selection array is non-empty (to avoid pure-default narratives)
        sel = {
            "pres": (payload.get("presentation", {}) or {}).get("selections", {}),
            "intent": (payload.get("intent", {}) or {}).get("selections", {}),
            "obs": (payload.get("observability", {}) or {}).get("selections", {}),
            "orch": (payload.get("orchestration", {}) or {}).get("selections", {}),
            "coll": (payload.get("collector", {}) or {}).get("selections", {}),
            "exec": (payload.get("executor", {}) or {}).get("selections", {}),
        }
        role_nonempty = any(
            ((payload.get("my_role", {}) or {}).get(k) or "").strip()
            for k in ("who", "skills", "developer")
        )

        has_any_selection = (
            any(_has_list_selections(v) for v in sel.values()) or role_nonempty
        )
        ini = payload.get("initiative", {}) or {}
        default_title = DEFAULT_TITLE
        default_desc = DEFAULT_DESCRIPTION
        _title = (ini.get("title") or "").strip()
        _desc = (ini.get("description") or "").strip()
        ini_nondefault = bool(
            (_title and _title != default_title) or (_desc and _desc != default_desc)
        )
        orch_sel = (payload.get("orchestration", {}) or {}).get("selections", {}) or {}
        orch_choice = (orch_sel.get("choice") or "").strip() or (
            st.session_state.get("orch_choice") or ""
        ).strip()
        orch_details = (orch_sel.get("details") or "").strip()
        # Treat any non-sentinel choice (including 'No') as a meaningful change for gating
        orch_nondefault = bool(orch_choice and orch_choice != "— Select one —")
        if has_any_selection or ini_nondefault or orch_nondefault or role_nonempty:
            with st.expander("Save Solution Artifacts", expanded=True):
                st.caption("Download your current scenario (JSON + Markdown + Gantt)")
                st.download_button(
                    label="📦 Download (JSON + Markdown + Gantt)",
                    data=zip_bytes,
                    file_name=zip_name,
                    mime="application/zip",
                    use_container_width=True,
                    key="wizard_zip_download_btn",
                )
        else:
            with st.expander("Save Solution Artifacts", expanded=False):
                st.info(
                    "Start filling in the sections above to see Solution Highlights here. Once you provide inputs, you will also be able to download the Wizard JSON."
                )
    else:
        # Build a minimal ZIP when a non-sentinel Orchestration choice exists, even if summary is empty
        sel = {
            "pres": (payload.get("presentation", {}) or {}).get("selections", {}),
            "intent": (payload.get("intent", {}) or {}).get("selections", {}),
            "obs": (payload.get("observability", {}) or {}).get("selections", {}),
            "orch": (payload.get("orchestration", {}) or {}).get("selections", {}),
            "coll": (payload.get("collector", {}) or {}).get("selections", {}),
            "exec": (payload.get("executor", {}) or {}).get("selections", {}),
        }

        has_any_selection = any(_has_list_selections(v) for v in sel.values())
        role_nonempty = any(
            ((payload.get("my_role", {}) or {}).get(k) or "").strip()
            for k in ("who", "skills", "developer")
        )
        ini = payload.get("initiative", {}) or {}
        default_title = DEFAULT_TITLE
        default_desc = DEFAULT_DESCRIPTION
        _title = (ini.get("title") or "").strip()
        _desc = (ini.get("description") or "").strip()
        ini_nondefault = bool(
            (_title and _title != default_title) or (_desc and _desc != default_desc)
        )
        orch_sel = (payload.get("orchestration", {}) or {}).get("selections", {}) or {}
        orch_choice = (orch_sel.get("choice") or "").strip() or (
            st.session_state.get("orch_choice") or ""
        ).strip()
        orch_nondefault = bool(orch_choice and orch_choice != "— Select one —")
        if orch_nondefault and not (
            has_any_selection or ini_nondefault or role_nonempty
        ):
            # Minimal payload & ZIP (JSON + minimal MD)
            final_payload = dict(payload) if isinstance(payload, dict) else {}
            if "initiative" not in final_payload or not isinstance(
                final_payload.get("initiative"), dict
            ):
                final_payload["initiative"] = {}
            final_payload_bytes = json.dumps(final_payload, indent=2).encode("utf-8")

            # Define title for ZIP filenames
            ini = final_payload.get("initiative", {}) or {}
            _title = (ini.get("title") or "").strip()
            title_for_zip = (
                re.sub(r"[^A-Za-z0-9_-]+", "_", (_title or "solution")).strip("_")
                or "solution"
            )
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

            # Define ZIP filename for minimal payload path
            zip_name = f"naf_report_{title_for_zip}_{ts}.zip"

            zip_buf = io.BytesIO()
            with zipfile.ZipFile(
                zip_buf, mode="w", compression=zipfile.ZIP_DEFLATED
            ) as zf:
                # Enforce naf_report_ prefix for artifacts
                zf.writestr(
                    f"naf_report_{title_for_zip}_{ts}.json", final_payload_bytes
                )
                zf.writestr(
                    f"naf_report_{title_for_zip}_{ts}.md",
                    ("# Solution Design Document\n\n").encode("utf-8"),
                )
                # Include branding icon if available in minimal ZIP as well
                try:
                    icon_path = (
                        Path(__file__).parent.parent / "images" / "naf_icon.png"
                    ).resolve()
                    if icon_path.exists():
                        with open(icon_path, "rb") as f:
                            zf.writestr("images/naf_icon.png", f.read())
                except Exception:
                    pass
            zip_bytes = zip_buf.getvalue()
            with st.expander("Save Solution Artifacts", expanded=True):
                st.caption("Download your current scenario (JSON + Markdown + Gantt)")
                st.download_button(
                    label="📦 Download (JSON + Markdown + Gantt)",
                    data=zip_bytes,
                    file_name=zip_name,
                    mime="application/zip",
                    use_container_width=True,
                    key="wizard_zip_download_btn",
                )
        else:
            # Reminder when no content yet
            with st.expander("Save Solution Artifacts", expanded=False):
                st.info(
                    "Start filling in the sections above to see Solution Highlights here. Once you provide inputs, you will also be able to download the Wizard JSON."
                )

    # Diagram removed per request; SDD export available above.


# Run the wizard when this page is loaded by Streamlit
solution_wizard_main()
