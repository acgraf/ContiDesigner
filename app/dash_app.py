import dash
import dash_bootstrap_components as dbc
from flask_caching import Cache
from app.layout import main_layout
import app.modeling as modeling

from app.callbacks_controlflow import register_callbacks_controlflow
from app.callbacks_modeling import register_callbacks_modeling
from app.callbacks_results import register_callbacks_results

"""
Main entry point for ContiDesigner Dash app.

Creates the Dash app, sets layout, initializes cache, and registers
control‑flow, modeling, and results callbacks.
"""

app = dash.Dash(
    __name__,
    requests_pathname_prefix="/ContiDesigner/",
    routes_pathname_prefix="/ContiDesigner/",
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css",
    ],
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
    suppress_callback_exceptions=True,
)
app.layout = main_layout.layout
server = app.server

modeling.cache = Cache(
    server,
    config={
        "CACHE_TYPE": "filesystem",
        "CACHE_DIR": "dash_cache",
    },
)

# register callbacks after layout and cache
register_callbacks_controlflow(app)
register_callbacks_modeling(app)
register_callbacks_results(app)

if __name__ == "__main__":
    app.run(debug=False, host="127.0.0.1", port=8051)
