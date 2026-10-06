from dash import dcc, html
import dash_bootstrap_components as dbc


def grid_download_button(item):
    label = "Download grid"
    button = dbc.Col(
        dbc.Button(
            label,
            id=f"download_{item}_grid_btn",
            color="light",
            className="px-1 py-1 border shadow-sm",
            style={
                "whiteSpace": "nowrap",
            },
        ),
        className="justify-content-center",
        md=3,
    )
    return button


D_range_card = dbc.Col(
    dbc.Card(
        [
            dbc.CardHeader(
                "Design Space over Dilution Rate (D)",
                className="mb-0",
                style={"borderBottom": "none"},
            ),
            dcc.Graph(
                id="D_range_plot",  #
                style={"width": "100%"},
            ),
            html.Div(
                grid_download_button("D_range"),
                className="d-flex justify-content-center mt-2 mb-2",
            ),
        ],
        className="shadow-sm",
    ),
    md=6,
)

Contour_card = dbc.Col(
    dbc.Card(
        [
            dbc.CardHeader(
                "Design Space over feed and volume split at D",
                className="mb-0",
                style={"borderBottom": "none"},
            ),
            dcc.Loading(
                dcc.Graph(
                    id="contour_plot",
                    style={"width": "100%"},
                )
            ),
            html.Div(
                grid_download_button("contour"),
                className="d-flex justify-content-center mt-2 mb-2",
            ),
        ],
        className="shadow-sm",
    ),
    md=6,
)


time_evolution_card_onestage = dbc.Col(
    dbc.Card(
        [
            dbc.CardHeader(
                id="onestage_header",
                className="mb-0",
                style={"borderBottom": "none"},
            ),
            dbc.CardBody(
                [
                    dcc.Loading(
                        html.Div(
                            dcc.Graph(
                                id="onestage_fig",
                                style={"width": "100%"},
                            ),
                        ),
                    ),
                ],
                className="shadow-sm p-0",
            ),
        ],
    ),
    md=4,
)


time_evolution_card_cascade = dbc.Col(
    dbc.Card(
        [
            dbc.CardHeader(
                id="cascade_header",
                className="mb-0",
                style={"borderBottom": "none"},
            ),
            dbc.CardBody(
                [
                    dcc.Loading(
                        html.Div(
                            dcc.Graph(
                                id="cascade_fig",
                                style={
                                    "width": "100%",
                                },
                            ),
                        ),
                    ),
                ],
                className="shadow-sm p-0",
            ),
        ],
    ),
    md=8,
)

titer_alerts = dbc.Row(
    dbc.Col(
        [
            # minimum titer constraint: status of the last run
            dbc.Alert(id="titer_alert", is_open=False, className="mt-3 mb-0"),
            # D range click outside the feasible titer region
            dbc.Alert(
                id="titer_click_alert",
                color="warning",
                is_open=False,
                dismissable=True,
                duration=8000,
                className="mt-3 mb-0",
            ),
        ],
        md=12,
    ),
    # no vertical padding, so it takes no space while the alerts are closed
    className="px-4",
)

results_layout = html.Div(
    children=[
        titer_alerts,
        dbc.Row(
            [
                dbc.Col(
                    [
                        # Top row with sweep plots
                        dbc.Row(
                            [D_range_card, Contour_card],
                            className="justify-content-center",
                        ),
                        # Bottom row with time evolution plots
                        dbc.Row(
                            [time_evolution_card_onestage, time_evolution_card_cascade],
                            className="mt-4",
                        ),
                    ],
                    md=8,
                ),
                # RIGHT SECTION (process summary)
                dbc.Col(
                    [
                        html.H5(className="card-title"),
                        html.Div(
                            id="summary_card_container",
                        ),
                    ],
                    md=4,
                ),
            ],
            className="px-4 pb-4 pt-3",
        ),
    ],
)
