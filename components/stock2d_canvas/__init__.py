from pathlib import Path

import streamlit.components.v1 as components

# declare_component must run inside an imported module, not directly in a page script
canvas = components.declare_component("stock2d_canvas", path=str(Path(__file__).parent))
