#!/usr/bin/python3 -tt
from __future__ import annotations

# Project: naf_naf_solution_wizard
# Filename: 90_Terms_and_Definitions.py
# claudiadeluna
# PyCharm

__author__ = "Claudia de Luna (claudia@indigowire.net)"
__version__ = ": 1.0 $"
__date__ = "12/13/25"
__copyright__ = "Copyright (c) 2025 Claudia"
__license__ = "Python"


from pathlib import Path

import streamlit as st
import yaml

import utils

# Page config for consistent favicon across all pages
st.set_page_config(
    page_title="Terms & Definitions",
    page_icon="images/naf_favicon-96x96.png",
    layout="wide",
)


def main() -> None:
    """Render the Terms & Definitions page with expanders for categories, strategies, and tools."""

    # Shared sidebar branding
    utils.render_global_sidebar()

    st.title("Terms & Definitions")
    st.caption(
        "Reference definitions for use case categories, deployment strategies, and automation tools."
    )

    # --- Use Case Categories ---
    with st.expander("Categories", expanded=False):
        yaml_path = Path(__file__).parent.parent / "use_case_categories.yml"
        try:
            with open(yaml_path, "r") as f:
                categories_data = yaml.safe_load(f)
            if categories_data and isinstance(categories_data, dict):
                table_data = [
                    {"Name": category, "Definition": description}
                    for category, description in categories_data.items()
                ]
                st.table(table_data)
            else:
                st.info("No use case categories found.")
        except FileNotFoundError:
            st.warning(f"File not found: `{yaml_path}`")
        except Exception as e:
            st.error(f"Error loading use case categories: {e}")

    # --- Deployment Strategies ---
    with st.expander("Deployment Strategies", expanded=False):
        deploy_path = Path(__file__).parent.parent / "deployment_strategies.yml"
        try:
            with open(deploy_path, "r") as f:
                deploy_data = yaml.safe_load(f)
            if deploy_data and isinstance(deploy_data, dict):
                table_data = [
                    {"Name": strategy, "Definition": description}
                    for strategy, description in deploy_data.items()
                ]
                st.table(table_data)
            else:
                st.info("No deployment strategies found.")
        except FileNotFoundError:
            st.warning(f"File not found: `{deploy_path}`")
        except Exception as e:
            st.error(f"Error loading deployment strategies: {e}")

    # --- Tools ---
    # with st.expander("Automation Tools", expanded=False):
    #     tools_path = Path(__file__).parent.parent / "tools.yml"
    #     try:
    #         with open(tools_path, "r") as f:
    #             tools_data = yaml.safe_load(f)
    #         if tools_data and isinstance(tools_data, dict):
    #             tools_dict = tools_data.get("tools", {})
    #             if tools_dict and isinstance(tools_dict, dict):
    #                 for tool_category, tool_list in tools_dict.items():
    #                     st.markdown(f"### {tool_category}")
    #                     if isinstance(tool_list, list):
    #                         table_data = []
    #                         for tool in tool_list:
    #                             if isinstance(tool, dict):
    #                                 name = tool.get("name", "Unknown")
    #                                 url = tool.get("url", "")
    #                                 notes = tool.get("notes", "")
    #                                 # Build name with link for definition
    #                                 if url:
    #                                     name_display = f"[{name}]({url})"
    #                                 else:
    #                                     name_display = name
    #                                 table_data.append({
    #                                     "Name": name_display,
    #                                     "Definition": notes
    #                                 })
    #                         if table_data:
    #                             st.markdown(
    #                                 "| Name | Definition |\n|------|------------|\n"
    #                                 + "\n".join(
    #                                     f"| {row['Name']} | {row['Definition']} |"
    #                                     for row in table_data
    #                                 )
    #                             )
    #                     st.markdown("")  # Add spacing between categories
    #             else:
    #                 st.info("No tools found in the 'tools' key.")
    #         else:
    #             st.info("No tools data found.")
    #     except FileNotFoundError:
    #         st.warning(f"File not found: `{tools_path}`")
    #     except yaml.YAMLError as e:
    #         st.error(f"YAML syntax error in tools.yml: {e}")
    #         st.info("The tools.yml file contains unquoted colons in string values. Please quote strings containing colons.")
    #     except Exception as e:
    #         st.error(f"Error loading tools: {e}")


if __name__ == "__main__":  # pragma: no cover - Streamlit entry
    main()
