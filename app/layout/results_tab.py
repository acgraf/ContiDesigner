from dash import dcc, html
import dash_bootstrap_components as dbc


def grid_download_button(item):
    # same look as the download buttons in the summary cards
    return dbc.Button(
        "Download grid",
        id=f"download_{item}_grid_btn",
        color="light",
        className="px-4 py-2 border shadow-sm",
        style={"whiteSpace": "nowrap"},
    )


def fill_graph(graph_id, min_height, loading=True):
    """Graph that fills the free height of its card.

    The graph is positioned absolutely, so it adds no height of its own: the
    row height is set by the summary card next to it (or by min_height), and
    all cards in the row (h-100) end at the same height.
    responsive=True lets plotly follow the container (it unsets a fixed
    figure height).
    """
    fill = {"position": "absolute", "inset": 0}
    graph = dcc.Graph(
        id=graph_id,
        responsive=True,
        style={"width": "100%", "height": "100%"} if loading else fill,
    )
    if loading:
        graph = dcc.Loading(graph, parent_style=fill)
    return html.Div(
        graph,
        style={"position": "relative", "flex": "1 1 auto", "minHeight": min_height},
    )


def plot_card(header, graph, footer=None, md=4):
    header_kwargs = header if isinstance(header, dict) else {"children": header}
    return dbc.Col(
        dbc.Card(
            [
                dbc.CardHeader(
                    **header_kwargs,
                    className="mb-0",
                    style={"borderBottom": "none"},
                ),
                graph,
            ]
            + ([footer] if footer else []),
            className="shadow-sm h-100",
        ),
        md=md,
    )


def grid_download_footer(item):
    return html.Div(
        grid_download_button(item),
        className="d-flex justify-content-center pt-2 pb-3",
    )


# sweep plots: as high as the optimal summary card, at least 300 px of graph
D_range_card = plot_card(
    "Design Space over Dilution Rate (D)",
    fill_graph("D_range_plot", "300px", loading=False),
    grid_download_footer("D_range"),
)

Contour_card = plot_card(
    "Design Space over feed and volume split at D",
    fill_graph("contour_plot", "300px"),
    grid_download_footer("contour"),
)

# time evolution: as high as the selected summary card, at least 400 px of
# graph (keeps them readable while no process is selected)
time_evolution_card_onestage = plot_card(
    {"id": "onestage_header"},
    fill_graph("onestage_fig", "400px"),
    md=4,
)

time_evolution_card_cascade = plot_card(
    {"id": "cascade_header"},
    fill_graph("cascade_fig", "400px"),
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
        # Top row: sweep plots and the optimal process summary. They share one
        # row, so the three cards (h-100) stretch to the same height.
        dbc.Row(
            [
                D_range_card,
                Contour_card,
                dbc.Col(id="optimal_summary_container", md=4),
            ],
            className="px-4 pt-3",
        ),
        # Bottom row: time evolution plots and the selected process summary
        dbc.Row(
            [
                dbc.Col(
                    dbc.Row(
                        [time_evolution_card_onestage, time_evolution_card_cascade],
                        className="h-100",
                    ),
                    md=8,
                ),
                dbc.Col(id="selected_summary_container", md=4),
            ],
            className="px-4 pb-4 mt-4",
        ),
    ],
)
