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


from NAF_NAF_Solution_Wizard import solution_wizard_main


# When this file is run as a Streamlit page, simply delegate to the
# existing Solution Wizard implementation.
solution_wizard_main()
