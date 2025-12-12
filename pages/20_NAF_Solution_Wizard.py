#!/usr/bin/env python3
"""Streamlit page: NAF Solution Wizard

This page hosts the main Solution Wizard experience for the
Network Automation Forum's Network Automation Framework (NAF).

The implementation lives in ``NAF_NAF_Solution_Wizard.solution_wizard_main``.
"""

from NAF_NAF_Solution_Wizard import solution_wizard_main


# When this file is run as a Streamlit page, simply delegate to the
# existing Solution Wizard implementation.
solution_wizard_main()
