<p align="center">
  <img src="images/naf_icon.png" alt="NAF" width="80" style="vertical-align:middle;margin-right:12px;" />
  <img src="images/EIA_Favicon.png" alt="EIA" width="80" style="vertical-align:middle;" />
</p>

# NAF Solution Wizard

An interactive Streamlit app to design network automation solutions using the NAF framework. It guides you through Presentation, Intent, Observability, Orchestration, Collector, and Executor sections, plus Dependencies and a planning Timeline, then generates a consolidated report and a bundled ZIP containing:

- JSON export (naf_report_*.json)
- Markdown report (naf_report_*.md) generated from your inputs
- Optional Gantt.png (if Plotly+kaleido is available)

## Features

- Guided expanders with sensible defaults; suppresses placeholder text in highlights
- Live “Detailed solution description” preview (markdown) of the export
- Single ZIP download including JSON + MD (+ PNG when available)
- Import back a previous `naf_report_*.json` (Merge/Overwrite)

## Requirements

- Python 3.9+
- Streamlit, Plotly, Jinja2
- Optional: `kaleido` for static PNG Gantt export

## Installation

### Using uv (recommended)

1. Install uv if needed:
   - macOS/Linux: `curl -LsSf https://astral.sh/uv/install.sh | sh`
2. From the project folder:
   - Create/resolve env and install: `uv sync`
   - Run the app: `uv run streamlit run naf_naf_solution_wizard.py`

### Using pip

1. Create and activate a virtual environment:
   - `python -m venv .venv`
   - macOS/Linux: `source .venv/bin/activate`
   - Windows: `.venv\Scripts\activate`
2. Install dependencies:
   - `pip install -U streamlit jinja2 plotly pandas kaleido`
3. Run the app:
   - `streamlit run naf_naf_solution_wizard.py`

## How to use the Wizard

1. Open the app (see commands above).
2. In the left sidebar, use “Load Saved Solution Wizard (JSON)” to reset or import a previous `naf_report_*.json`.
3. Work through the expanders:
   - Presentation: target users, interaction patterns, tools, and auth
   - Intent: what will be developed and what you already have
   - Observability: health signals, go/no‑go logic, tools
   - Orchestration: choose “No” or describe your orchestration approach
   - Collector: methods, auth, normalization, scale, collection tools
   - Executor: change/intent execution methods
   - Dependencies: systems/interfaces required
   - Staffing, Timeline, & Milestones: dates and staffing plan; Gantt will be generated
4. The main page shows Solution Highlights and a collapsible "Detailed solution description" preview.
5. When any meaningful input is present, the sidebar shows “Save Solution Artifacts” to download a ZIP with:
   - `naf_report_*.json` (includes `naf_report_md` at the top level)
   - `naf_report_*.md` (rendered report)
   - `Gantt.png` if Plotly+kaleido can render PNGs
6. To re‑load, use the upload control and ensure the file name matches `naf_report_*.json`.

## Wizard Blocks (Expanders)

- Load Saved Solution Wizard (JSON)
- My Role
- Automation Project Title & Description
- Guiding Questions by Framework Component
- Presentation
- Intent
- Observability
- Orchestration
- Collector
- Executor
- Dependencies & External Interfaces
- Staffing, Timeline, & Milestones
- Detailed solution description (Markdown supported)

## Notes & Tips

- If Gantt.png is missing, install `kaleido` and retry.
- The disclaimer link at the bottom uses a markdown link for single‑file apps.
- Orchestration = “No” is treated as a valid selection (bullet in preview and enables export).

## License

Python (see headers in source files).