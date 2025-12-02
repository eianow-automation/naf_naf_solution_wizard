#!/usr/bin/python3 -tt
"""
Disclaimer Page

This page presents the application's disclaimer.
"""
import streamlit as st


def main():
    st.set_page_config(page_title="Disclaimer", page_icon="⚠️", layout="wide")
    st.title("Disclaimer")
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
    st.markdown("\n")
    st.page_link("Automation_BusinessCase_App.py", label="Return to Home", icon="🏠")


if __name__ == "__main__":
    main()
