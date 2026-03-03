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


import utils
import streamlit as st


def main() -> None:
    """Landing page for the NAF NAF Solution Wizard.

    This page orients users to the Solution Wizard functionality.
    """

    st.set_page_config(
        page_title="NAF NAF Wizard App",
        page_icon="images/EIA_Favicon.png",
        layout="wide",
    )

    # Shared sidebar branding
    utils.render_global_sidebar()

    st.title("Network Automation Forum (NAF) Network Automation Framework (NAF) Solution Wizard")
    st.markdown(
        """
        This application helps you apply the Network Automation Forum's
        **Network Automation Framework (NAF)** to your automation projects.
        
        Use the **Solution Wizard** to describe how you plan on designing your automation solution:
        """
    )

    st.markdown("### Design Your Automation Solution")
    st.markdown(
        """
        The Solution Wizard guides you through each NAF component as well as additional considerations for your automation solution:
        
        - **Initiative**: Define the problem, scope, expected use, and deployment strategy
        - **Stakeholders**: Identify who is supporting the project
        - **My Role**: Specify your skills and development approach
        - **Dependencies**: List required infrastructure and systems
        - **Timeline**: Plan staffing, milestones, and delivery schedule

        NAF Components:
        - **Presentation**: Define user types, interaction modes, and presentation tools
        - **Intent**: Specify development approaches and provided formats
        - **Observability**: Plan monitoring, go/no-go criteria, and tools
        - **Orchestration**: Design workflow automation
        - **Collector**: Plan data collection methods and tools
        - **Executor**: Define execution methods


        The wizard generates a **complete solution design document** (JSON + Markdown + timeline) that you can share with:
        - Team members who will design or build the automation
        - Stakeholders who need to understand what the automation will do
        - Management who need a concise overview of scope, impact, and effort
        - Other IT Teams with supporting required interfaces and services
        """
    )

    st.markdown("### Start Designing Your Solution")
    
    # Add button to navigate to the wizard page
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 Open Solution Wizard", type="primary", use_container_width=True):
            st.switch_page("pages/20_NAF_Solution_Wizard.py")
    
    st.markdown("### Saving and Loading Your Work")
    st.markdown(
        """
        - The **Solution Wizard** page is where you'll design your automation solution.
        - You can save your work as a JSON file and load it later to continue editing.
        - The JSON file contains all your wizard inputs and can be shared with others.
        - Use the **Load Session** button in the Solution Wizard sidebar to restore a saved design.
        """
    )


if __name__ == "__main__":
    main()
    st.markdown("---")
    st.caption(
        "Disclaimer: Results depend entirely on your inputs. Validate data and use professional judgment."
    )

    with st.expander("⚠️ Read full disclaimer", expanded=False):
        st.markdown(
            """
            The calculations, outputs, and recommendations presented by this application are for informational purposes only. 
            Results are entirely dependent on the inputs provided by the user and any assumptions entered. 
            It is the user's responsibility to validate all inputs, review the outputs for accuracy and suitability, and apply appropriate professional judgment before making decisions based on these results.
            
            By using this application, you acknowledge and agree that:
            - You are solely responsible for the data you enter and for any conclusions or decisions you draw from the results.
            - The authors and contributors make no warranties, express or implied, regarding accuracy, completeness, or fitness for a particular purpose.
            - The authors and contributors shall not be liable for any losses or damages arising from use of or reliance on the results.
            """
        )
