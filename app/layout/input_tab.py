from sqlite3 import Row
from dash import dcc, html
import dash_bootstrap_components as dbc
from ContiDesigner.utils.defaults import DEFAULT_PROCESS_INFO, DEFAULT_PROCESSES 
from app.layout.helper import labels
from app.information import tooltips


def labeled_input(label, input_id):
    """Create a labeled input with an optional tooltip."""
    input_props = {
        "id": input_id,
        "className": "form-control-sm border-1 shadow-sm",
        "style": {"backgroundColor": "#f9f9f9"},
        "type": "number",
        "required": False,
        "min": 0,
    }
    return html.Div(
        [
            dbc.Label(
                html.Span(
                    label,
                    className="d-flex justify-content-between align-items-center w-100",
                ),
                html_for=input_id,
                id=f"label_{input_id}",
                # className="fw-semibold mb-1",
                className="fw-bold mb-1",
                style={"width": "100%"},
            ),
            dbc.Input(**input_props),
            dbc.Tooltip(
                tooltips.get(input_id),
                target=f"label_{input_id}",
                placement="left",
            ),
        ],
        className="mb-2",
    )


def input_col(label, input_id, md=6):
    return dbc.Col(labeled_input(label, input_id), md=md)


def section_card(title, description, content):
    return dbc.Card(
        dbc.CardBody(
            [
                html.H3(title, className="fw-bold mb-2"),
                html.P(description, className="text-muted small mb-4"),
                content,
            ]
        ),
        className="shadow-sm rounded-4 mb-1 pb-3 px-3 w-100",
        style={
            "backgroundColor": "#fefefe",
            "border": "1px solid #e0e0e0",
        },
    )


About_tab = [
    html.H4("About ContiDesigner", className="fw-bold"),
    html.P(
        "This tool simulates one- and two-stage continuous bioprocesses using "
        "steady-state models. Adjust kinetic, yield, and process parameters  "
        "to explore their impact on biomass growth and product formation.  "
        "Compare single-stage vs. cascaded setups to identify optimal configurations.",
        className="text-muted small",
    ),
]
HowtoUse_tab = [
    html.H5("How to Use", className="fw-semibold"),
    html.Ul(
        [
            html.Li(
                "Enter your kinetic, yield and process specific parameters in the right-hand panels."
            ),
            html.Li("Hover over labels to read explanations for each parameter."),
            html.Li("Click 'Submit Parameters' to run the model simulation."),
            html.Li("Use 'Defaults' to load pre-set example processes."),
        ],
        className="text-muted small",
    ),
]

Tip_tab = [
    html.Div(
        [
            html.H6("Tip", className="fw-bold", style={"color": "#555"}),
            html.P(
                "Start with Defaults to explore features, then input your kinetics. "
                "For two-stage designs to outperform one-stage: growth-decoupled "
                "production rate in stage 2 must exceed stage 1. "
                "Test by tweaking production rates. ",
                className="text-muted small",
            ),
        ],
        className="p-3 rounded-3",
        style={
            "backgroundColor": "#f0f0f0",
            "borderLeft": "4px solid #6c757d",
        },
    ),
]

more_info_tab = [
    html.P(
        "For detailed model information, visit the "
        "information tab.",  # read the publication (link), " \
        # "or check the GitHub repository (link).", #TBD
        className="text-muted small fst-italic",
    ),
]

input_column_header = dbc.Col(
    [
        html.H2(
            "Process Input Parameters",
            className="text-center fw-bold my-4",
            style={"color": "#222"},
        ),
        html.P(
            [
                "Specify the kinetic, yield, and process parameters for your "
                "bioprocess model below. ",
                html.Br(),
                "Hover over the labels for explanations of each parameter.",
            ],
            className="text-muted text-center",
        ),
    ],
    md=12,
)

greek_letters = {
    "mu": "\u03bc",
    "delta": "\u03b4",
    "pi": "\u03c0",
    "rho": "\u03c1",
}


md_gen = 12
general_params = dbc.Col(
    [
        input_col(
            labels["mu_max"],
            "mu_max",
            md=md_gen,
        ),
        input_col(
            labels["delta"],
            "delta",
            md=md_gen,
        ),
        input_col(
            labels["Ks"],
            "Ks",
            md=md_gen,
        ),
    ],
    md=12,
)

md_tab = 12
stage_1_tab = (
    dbc.Row(
        [
            dbc.Col(
                [
                    input_col(
                        labels["pinot_1"],
                        "pi0_s1",
                        md=md_tab,
                    ),
                    input_col(
                        labels["pimu_1"],
                        "pi1_s1",
                        md=md_tab,
                    ),
                    input_col(
                        labels["rho_1"],
                        "m_1",
                        md=md_tab,
                    ),
                ],
                md=6,
            ),
            dbc.Col(
                [
                    input_col(
                        labels["Yxs_1"],
                        "Yxs_1",
                        md=md_tab,
                    ),
                    input_col(
                        labels["Yps_1"],
                        "Yps_1",
                        md=md_tab,
                    ),
                    input_col(
                        labels["Yas_1"],
                        "Yas_1",
                        md=md_tab,
                    ),
                ],
                md=6,
            ),
        ],
        className="g-4 mt-1 px-4",
    ),
)

stage_2_tab = (
    dbc.Row(
        [
            dbc.Col(
                [
                    input_col(
                        labels["pinot_2"],
                        "pi0_s2",
                        md=md_tab,
                    ),
                    input_col(
                        labels["pimu_2"],
                        "pi1_s2",
                        md=md_tab,
                    ),
                    input_col(
                        labels["rho_2"],
                        "m_2",
                        md=md_tab,
                    ),
                ],
                md=6,
            ),
            dbc.Col(
                [
                    input_col(
                        labels["Yxs_2"],
                        "Yxs_2",
                        md=md_tab,
                    ),
                    input_col(
                        labels["Yps_2"],
                        "Yps_2",
                        md=md_tab,
                    ),
                    input_col(
                        labels["Yps_2"],
                        "Yas_2",
                        md=md_tab,
                    ),
                ],
                md=6,
            ),
        ],
        className="g-4 mt-1 px-4",
    ),
)

stage_tabs = dbc.Col(
    dbc.Card(
        dbc.CardBody(
            dbc.Tabs(
                [
                    dbc.Tab(
                        stage_1_tab,
                        label="Stage 1: Growth",
                        label_style={"color": "#6c757d"},
                        active_label_style={
                            "color": "#212529",
                            "backgroundColor": "#fafafa",
                        },
                    ),
                    dbc.Tab(
                        stage_2_tab,
                        label="Stage 2: Production",
                        label_style={"color": "#6c757d"},
                        active_label_style={
                            "color": "#212529",
                            "backgroundColor": "#fafafa",
                        },
                    ),
                ],
                className="mb-0 w-100",
                style={
                    "backgroundColor": "#fafafa",  # card background
                    "borderBottom": "1px solid #dee2e6",  # bottom border
                },
            ),
        ),
        className="border rounded-3 shadow-sm",
        style={"backgroundColor": "#fafafa"},
    ),
    md=12,
)

card_outer = dbc.Col(
    dbc.Card(
        [
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Div(
                                [
                                    "Physiological",
                                    html.Span(
                                        "Parameters",
                                        style={
                                            "display": "block",
                                            "margin-left": "1.5rem",
                                        },
                                    ),
                                ],
                                className="fw-bold",
                                style={
                                    "font-size": "1.5rem",
                                    "padding-bottom": "1rem",
                                },
                            ),
                            dbc.Row(
                                [
                                    general_params,
                                ],
                                className="g-3 px-4",
                            ),
                        ],
                        md=4,
                    ),
                    dbc.Col(
                        html.Div(
                            stage_tabs,
                        ),
                        md=8,
                    ),
                ],
            ),
        ],
        className="shadow-sm border rounded-4 p-3",
    ),
    className="ms-4 my-4",
    style={
        "flex": "0 0 auto",
    },
)


checkbox_growth_s2 = dbc.Col(
    [
        dbc.Checkbox(
            id="growth_stage2",
            value=False,
            label="Enable growth in production stage",
        ),
        dbc.Tooltip(
            tooltips["growth_stage2_checkbox"],
            target="growth_stage2",
            placement="right",
        ),
    ],
    md=12,
)

toggle_substrate_inhibition = dbc.Col(
    [
        dbc.Switch(
            id="is_substrate_inhibited",
            value=False,
            label="Substrate",
        ),
        dbc.Tooltip(
            tooltips["is_substrate_inhibited"],
            target="is_substrate_inhibited",
            placement="right",
        ),
        html.Div(
            [
                dbc.Label(
                    html.Span(
                        labels["Ki"],
                        className="d-flex justify-content-between align-items-center w-100",
                    ),
                    html_for="Ki",
                    id="label_Ki",
                    className="fw-semibold",
                    style={"width": "100%"},
                ),
                dbc.Input(
                    id="Ki",
                    value=None,
                    min=0,
                    className="form-control-sm border-1 shadow-sm",
                    style={"backgroundColor": "#f9f9f9"},
                    type="number",
                    required=False,
                ),
                dbc.Tooltip(
                    tooltips.get("Ki"),
                    target="label_Ki",
                    placement="right",
                ),
            ],
            id="Ki_container",
            style={"display": "none"},
        ),
    ]
)


toggle_biomass_inhibition = dbc.Col(
    [
        dbc.Switch(
            id="is_biomass_inhibited",
            value=False,
            label="Biomass",
        ),
        dbc.Tooltip(
            tooltips["is_biomass_inhibited"],
            target="is_biomass_inhibited",
            placement="right",
        ),
        html.Div(
            [
                dbc.Label(
                    html.Span(
                        labels["x_max"],
                        className="d-flex justify-content-between align-items-center w-100",
                    ),
                    html_for="x_max",
                    id="label_x_max",
                    className="fw-semibold",
                    style={"width": "100%"},
                ),
                dbc.Input(
                    id="x_max",
                    type="number",
                    value=None,
                    min=0,
                    className="form-control-sm border-1 shadow-sm",
                    style={"backgroundColor": "#f9f9f9"},
                    required=False,
                ),
                dbc.Tooltip(
                    tooltips.get("x_max"),
                    target="label_x_max",
                    placement="right",
                ),
            ],
            id="x_max_container",
        ),
    ]
)


toggle_product_inhibition = dbc.Col(
    [
        dbc.Switch(
            id="is_product_inhibited",
            value=False,
            label="Product",
        ),
        dbc.Tooltip(
            tooltips["is_product_inhibited"],
            target="is_product_inhibited",
            placement="right",
        ),
        html.Div(
            [
                dbc.Label(
                    html.Span(
                        labels["p_max"],
                        className="d-flex justify-content-between align-items-center w-100",
                    ),
                    html_for="p_max",
                    id="label_p_max",
                    className="fw-semibold",
                    style={"width": "100%"},
                ),
                dbc.Input(
                    id="p_max",
                    value=None,
                    min=0,
                    className="form-control-sm border-1 shadow-sm",
                    style={"backgroundColor": "#f9f9f9"},
                    type="number",
                    required=False,
                ),
                dbc.Tooltip(
                    tooltips.get("p_max"),
                    target="label_p_max",
                    placement="right",
                ),
            ],
            id="p_max_container",
            style={"display": "none"},
        ),
    ]
)

process_settings = dbc.Col(
    section_card(
        "Process Settings",
        "Define operational conditions for the reactor system.",
        dbc.Row(
            [
                input_col(labels["V"], "V_total", md=4),
                input_col(labels["sf1"], "sf1", md=4),
                input_col(
                    labels["sf2_max"],
                    "sf2_max",
                    md=4,
                ),
                html.Hr(className="my-2"),
                dbc.Row(
                    dbc.Col(
                        html.Span(
                            html.Strong("Choose inhibition type:"),
                            style={"font-size": "1.05rem"},
                        ),
                        md=12,
                    )
                ),
                toggle_substrate_inhibition,
                toggle_biomass_inhibition,
                toggle_product_inhibition,
                html.Hr(className="my-2"),
                checkbox_growth_s2,
            ],
            className="g-2",
        ),
    ),
    className="me-4 mt-4",
)


Submit_button = dbc.Col(
    dbc.Button(
        "Submit Parameters",
        id="run",
        color="dark",
        className="px-4 py-2 shadow-sm",
    ),
    width="auto",
)

Defaults_button = dbc.Col(
    dbc.Button(
        "Defaults",
        id="open_defaults_modal",
        color="secondary",
        className="px-4 py-2 shadow-sm",
    ),
    width="auto",
)

Clear_button = dbc.Col(
    dbc.Button(
        "Clear",
        id="clear_btn",
        color="light",
        className="px-4 py-2 border shadow-sm",
    ),
    width="auto",
)

buttons_row = dbc.Row(
    [
        Submit_button,
        Defaults_button,
        Clear_button,
    ],
    className="justify-content-center",
)
left_params_card = dbc.Col(
    [card_outer, buttons_row],
    md=7,
)

right_params_card = dbc.Col(
    [process_settings],
    md=5,
)

param_inputs = dbc.Row(
    [left_params_card, right_params_card],
    className="g-4",
)

input_column = [input_column_header] + [param_inputs]

defaults_options = [
    {
        "label": html.Div(
            [
                html.Strong(
                    [
                        DEFAULT_PROCESS_INFO[k]["title"],
                        *(
                            [
                                " in ",
                                html.I(DEFAULT_PROCESS_INFO[k]["organism"]),
                            ]
                            if DEFAULT_PROCESS_INFO[k]["organism"]
                            else []
                        ),
                    ]
                ),
                html.Br(),
                html.Small(
                    [
                        DEFAULT_PROCESS_INFO[k]["description"],
                        html.Br(),
                        *[
                            item
                            for i, (ref, url) in enumerate(
                                zip(
                                    DEFAULT_PROCESS_INFO[k]["reference"],
                                    DEFAULT_PROCESS_INFO[k]["reference_url"],
                                )
                            )
                            for item in (
                                (["; "] if i > 0 else [])
                                + [html.A(ref, href=url, target="_blank")]
                            )
                        ],
                    ],
                    className="text-muted",
                ),
            ],
            className="mb-3",
        ),
        "value": k,
    }
    for k in DEFAULT_PROCESSES.keys()
]

defaults_modal = dbc.Modal(
    [
        dbc.ModalHeader("Select a default process"),
        dbc.ModalBody(
            [
                dbc.RadioItems(
                    id="default_process_selection",
                    options=defaults_options,
                    value=None,
                    inline=False,
                    className="mt-2",
                ),
            ],
        ),
        dbc.ModalFooter(
            [
                dbc.Button(
                    "Apply selected defaults",
                    id="apply_defaults_btn",
                    color="secondary",
                ),
                dbc.Button("Cancel", id="cancel_defaults_btn", color="light"),
            ],
        ),
    ],
    id="defaults_modal",
    is_open=False,
)

wait_modal = dbc.Modal(
    [
        dbc.ModalHeader("Wait for it..."),
        dbc.ModalBody(
            [
                html.P(
                    "Simulating the bioprocess with the provided parameters. This may take a moment."
                ),
                dbc.Spinner(size="lg", color="primary"),
            ],
        ),
    ],
    id="wait_modal",
    is_open=False,
)

input_layout = html.Div(
    [
        dbc.Container(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            About_tab
                            + [html.Hr()]
                            + HowtoUse_tab
                            + Tip_tab
                            + [html.Hr()]
                            + more_info_tab,
                            md=3,
                            style={
                                "border": "1px solid #e0e0e0",
                                "padding": "30px 30px 30px 30px",
                            },
                            className="shadow-sm",
                        ),
                        dbc.Col(
                            [
                                *input_column,
                            ],
                            md=9,
                            className="px-4",
                        ),
                    ],
                ),
                defaults_modal,
                wait_modal,
            ],
            fluid=True, 
        ),
    ],
)
