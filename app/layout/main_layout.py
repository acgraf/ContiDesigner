from dash import dcc, html
import dash_bootstrap_components as dbc
from . import input_tab as input_tab
from . import results_tab as results_tab
from . import info_tab as info_tab

# Navbar/Header at the top

navbar_buttons = dbc.Container(
    dbc.Row(
        [
            dbc.Col(dbc.Button("Input", id="input_btn", color="dark", outline=True)),
            dbc.Col(
                dbc.Button("Results", id="results_btn", color="dark", outline=True)
            ),
            dbc.Col(
                dbc.Button("Information", id="info_btn", color="dark", outline=True)
            ),
        ],
        justify="start",
        className="g-2",
        style={"padding": "0.25rem 0"},
    ),
    style={"max-width": "600px", "margin": "0 auto"},
)


navbar = dbc.Navbar(
    dbc.Container(
        [
            dbc.NavbarBrand(
                "ContiDesigner", className="fw-bold", style={"fontSize": "2rem"}
            ),
            navbar_buttons,
        ],
        style={
            "max-width": "800px",
            "margin": "0 auto",
        },
    ),
    color="light",  # background color
    dark=False,
    className="shadow-sm",
)

# --- tabs (content) ---

page_input = html.Div(
    input_tab.input_layout,
    id="page-input",
    style={"display": "block"},  # visible by default
)

page_results = html.Div(
    results_tab.results_layout, id="page-results", style={"display": "none"}
)

page_info = html.Div(info_tab.info_layout, id="page-info", style={"display": "none"})


missing_results_modal = dbc.Modal(
    [
        dbc.ModalHeader("No results yet"),
        dbc.ModalBody("Run the simulation before viewing the results."),
        dbc.ModalFooter(
            dbc.Button(
                "OK", id="close_missing_results", color="dark", className="ms-auto"
            )
        ),
    ],
    id="missing_results_modal",
    is_open=False,
)

layout = html.Div(
    [
        navbar,
        # navbar_buttons,
        page_input,
        page_results,
        missing_results_modal,
        page_info,
        dcc.Store(id="params_store", data={}),  # cache input parameters
        dcc.Store(
            id="shared_state", data={}  # shared_state holds the latest click selection
        ),  # dcc keeps hidden states across callbacks
        dcc.Store(id="selected_D_state", data={}),  # selected D value state
        dcc.Store(id="onestage_fig_store"),  # optimal one-stage figure
        dcc.Store(id="cascade_fig_store"),  # optimal cascade figure
        dcc.Store(id="D_range_fig_store"),  # optimal D range figure
        dcc.Store(id="contour_fig_store"),  # optimal contour figure
        dcc.Store(id="all4figures_run", data={}),  # all figures store
        dcc.Store(id="all4figures_D_range", data={}),  # all figures store
        dcc.Store(id="all4figures_contour", data={}),  # all figures store
        dcc.Store(
            id="optimal_params", data={}
        ),  # cache optparams to avoid recomputation
        dcc.Store(id="optimal_cache", data={}),  # cache optimization results
        dcc.Store(
            id="onestage_fig_selected_store"
        ),  # one-stage figure with selected point
        dcc.Store(
            id="cascade_fig_selected_store"
        ),  # cascade figure with selected point
        dcc.Store(id="optimal_summary_card_store"),  # holds the visual card (dbc.Card)
        dcc.Store(id="selected_summary_card_store"),
        dcc.Store(
            id="selected_summary_card_store_D_range"
        ),  # holds the visual card for selected
        dcc.Store(id="selected_summary_card_store_contour"),
        # NEW: add data stores for CSV export (plain dicts)
        dcc.Store(id="optimal_summary_data_store", data={}),
        dcc.Store(id="selected_summary_data_store", data={}),
        dcc.Store(id="selected_summary_data_store_D_range", data={}),
        dcc.Store(id="selected_summary_data_store_contour", data={}),
        dcc.Store(id="D_grid_store"),
        dcc.Store(id="phi_ny_grid_store", data={}),
        dcc.Store(id="phi_ny_grid_store_selected", data={}),
        dcc.Store(id="optimal_OS_model_sbml_store"),
        dcc.Store(id="selected_OS_model_sbml_store"),
        dcc.Store(id="selected_OS_model_sbml_store_D_range"),
        dcc.Store(id="selected_OS_model_sbml_store_contour"),
        dcc.Store(id="optimal_cascade_model_sbml_store"),
        dcc.Store(id="selected_cascade_model_sbml_store"),
        dcc.Store(id="selected_cascade_model_sbml_store_D_range"),
        dcc.Store(id="selected_cascade_model_sbml_store_contour"),
        dcc.Store(id="checked_inputs_store", data=[]),
        dcc.Download(id="download_summary_file_optimal"),
        dcc.Download(id="download_summary_file_selected"),
        dcc.Download(id="download_sbml_file_optimal_OS"),
        dcc.Download(id="download_sbml_file_selected_OS"),
        dcc.Download(id="download_sbml_file_optimal_cascade"),
        dcc.Download(id="download_sbml_file_selected_cascade"),
        dcc.Download(id="download_D_range_grid_file"),
        dcc.Download(id="download_contour_grid_file"),
    ],
    style={
        "display": "flex",
        "flexDirection": "column",
        "minHeight": "100vh",
        "width": "100%",
        "overflowX": "hidden",
    },
)
