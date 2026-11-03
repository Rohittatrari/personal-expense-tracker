"""
Build script to package the Streamlit application for GitHub Pages using stlite (Pyodide WebAssembly).
Generates a standalone self-contained dist/index.html that runs 100% in the browser.
"""

import os
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DIST_DIR = BASE_DIR / "dist"
DIST_DIR.mkdir(exist_ok=True)

PYTHON_FILES = [
    "app.py",
    "config.py",
    "database.py",
    "transactions.py",
    "analytics.py",
    "visualizations.py",
    "sample_data.py",
]

files_dict = {}
for fname in PYTHON_FILES:
    fpath = BASE_DIR / fname
    if fpath.exists():
        files_dict[fname] = fpath.read_text(encoding="utf-8")

# Read requirements (stlite includes streamlit core, so only external libraries needed)
req_path = BASE_DIR / "requirements.txt"
requirements = ["pandas", "numpy", "matplotlib", "plotly"]
if req_path.exists():
    lines = [
        l.strip()
        for l in req_path.read_text(encoding="utf-8").splitlines()
        if l.strip() and not l.startswith("#") and not l.lower().startswith("streamlit")
    ]
    if lines:
        requirements = lines

index_html_content = f"""<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta http-equiv="X-UA-Compatible" content="IE=edge" />
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no" />
    <title>Personal Expense Tracker</title>
    <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>💰</text></svg>">
    <link
      rel="stylesheet"
      href="https://cdn.jsdelivr.net/npm/@stlite/mountable@0.73.1/build/stlite.css"
    />
    <style>
      body {{
        margin: 0;
        padding: 0;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        background-color: #f8f9fa;
      }}
      #loading-overlay {{
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: #ffffff;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        z-index: 99999;
        transition: opacity 0.5s ease;
      }}
      .spinner {{
        width: 50px;
        height: 50px;
        border: 4px solid #e9ecef;
        border-top: 4px solid #2E86AB;
        border-radius: 50%;
        animation: spin 1s linear infinite;
        margin-bottom: 20px;
      }}
      @keyframes spin {{
        0% {{ transform: rotate(0deg); }}
        100% {{ transform: rotate(360deg); }}
      }}
      .loading-title {{
        font-size: 1.3rem;
        font-weight: 600;
        color: #2b2d42;
        margin-bottom: 8px;
      }}
      .loading-subtitle {{
        font-size: 0.9rem;
        color: #6c757d;
      }}
    </style>
  </head>
  <body>
    <div id="loading-overlay">
      <div class="spinner"></div>
      <div class="loading-title">💰 Personal Expense Tracker</div>
      <div class="loading-subtitle">Starting Python environment in your browser...</div>
    </div>

    <div id="root"></div>

    <script src="https://cdn.jsdelivr.net/npm/@stlite/mountable@0.73.1/build/stlite.js"></script>
    <script>
      const files = {json.dumps(files_dict)};
      const requirements = {json.dumps(requirements)};

      stlite.mount({{
        entrypoint: "app.py",
        files: files,
        requirements: requirements,
      }}, document.getElementById("root")).then(() => {{
        const overlay = document.getElementById("loading-overlay");
        if (overlay) {{
          overlay.style.opacity = "0";
          setTimeout(() => overlay.remove(), 500);
        }}
      }}).catch((err) => {{
        console.error("stlite initialization error:", err);
        const subtitle = document.querySelector(".loading-subtitle");
        if (subtitle) {{
          subtitle.textContent = "Error loading application: " + err.message;
          subtitle.style.color = "#e74c3c";
        }}
      }});
    </script>
  </body>
</html>
"""

output_file = DIST_DIR / "index.html"
output_file.write_text(index_html_content, encoding="utf-8")
print(f"Successfully generated {output_file} (size: {len(index_html_content)} bytes)")

# Also update docs/index.html so both deployment methods are kept in sync
docs_dir = BASE_DIR / "docs"
docs_dir.mkdir(exist_ok=True)
(docs_dir / "index.html").write_text(index_html_content, encoding="utf-8")
print(f"Also updated {docs_dir / 'index.html'}")
