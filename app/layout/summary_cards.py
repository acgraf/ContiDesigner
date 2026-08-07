# import necessary libraries
import dash_bootstrap_components as dbc
from dash import html
from .. import information
import numpy as np

tooltips = information.tooltips


def metric_row(label, one_stage_val, cascade_val, unit=None, tooltip=None, row_id=None):
    """Create a formatted metric row comparing one-stage and cascade values."""
    row_id = row_id or label.replace(" ", "_")

    def fmt(val):
        try:
            return f"{float(val):.2f}"
        except (ValueError, TypeError):
            return str(val)

    label_span = html.Span(label, id=row_id, className="fw-semibold text-secondary")
    row = dbc.Row(
        [
            dbc.Col(label_span, xs=4, md=3),
            dbc.Col(
                html.Span(fmt(one_stage_val), className="text-dark"),
                xs=3,
                md=3,
                className="text-end",
            ),
            dbc.Col(
                html.Span(fmt(cascade_val), className="text-dark"),
                xs=3,
                md=4,
                className="text-end",
            ),
            dbc.Col(
                html.Span(f" {unit}" if unit else "", className="text-dark"),
                xs=2,
                md=2,
                className="text-end",
            ),
        ],
        className="my-1",
    )
    tooltip_comp = (
        dbc.Tooltip(tooltip, target=row_id, placement="right") if tooltip else None
    )
    return html.Div([row, tooltip_comp])


def download_button(item, prefix):
    map = {
        "summary": "Process Summary",
        "sbml_OS": "SBML (One-stage)",
        "sbml_cascade": "SBML (Two-stage)",
    }
    button = dbc.Col(
        dbc.Button(
            map[item],
            id=f"download_{item}_btn_{prefix}",
            color="light",
            className="px-4 py-2 border shadow-sm",
            style={
                "whiteSpace": "nowrap",
            },
        ),
        className="d-flex justify-content-center",
        xs=12,
        md=4,
    )
    return button


def summarize_process(
    steady_states_cascade,
    steady_states_OS,
    params,
    model,
    solver,
    is_optimal=True,
    optimal_for_D=False,
):
    def header_with_icon(icon_class, label):
        return [
            html.I(className=icon_class, style={"marginRight": "6px"}),
            label,
        ]

    icons = {
        "star": "bi bi-star-fill",
        "triangle-up": "bi bi-triangle-fill",
        "diamond": "bi bi-diamond-fill",
    }
    if is_optimal:
        title_text = header_with_icon(icons["star"], "Optimal Process")
        header_style = {"color": "violet"}
    else:
        if optimal_for_D:
            title_text = header_with_icon(
                icons["triangle-up"], f"Optimal Process at D = {model.D_total} /h"
            )
            header_style = {"color": "#17a2b8"}
        else:
            title_text = header_with_icon(
                icons["diamond"], f"Selected Process at D = {model.D_total:.2f} /h"
            )
            header_style = {"color": "black"}
        # special case: when the selected process at the chosen D
        # is also the optimal process at the chosen D
        # this is already handled by the marker in the plot,
        # but also needs to be done in the summary card, so the header reflects that

    prefix = "optimal" if is_optimal else "selected"
    ss = steady_states_cascade
    xx2, ss2, pp2 = ss[3:6]
    ss1 = ss[1]
    sf2_min = model.sf2

    xx, ss, pp = steady_states_OS[0:3]
    prod1 = solver.calculate_STY(pp, model.D_total)
    prod_cascade = solver.calculate_STY(pp2, model.D_total)

    s_OS_consumed = solver.total_substrate_consumed(ss_os=ss, cascade=False)
    s_TS_consumed = solver.total_substrate_consumed(ss2=ss2, cascade=True)
    Yield_OS = pp / s_OS_consumed
    Yield_TS = pp2 / s_TS_consumed


    card_header = dbc.CardHeader(
        [
            html.H5(
                [*title_text],
                id=f"{prefix}_header",
                className=f"mb-0",
                style=header_style,
            ),
            dbc.Tooltip(
                tooltips[f"{prefix}_header"],
                target=f"{prefix}_header",
                placement="right",
            ),
        ],
        className="bg-light border-bottom-0",
    )

    card = dbc.Card(
        [
            card_header,
            dbc.CardBody(
                [
                    html.Div(
                        [
                            dbc.Row(
                                [
                                    dbc.Col(
                                        html.Span(
                                            "",
                                        ),
                                        md=3,
                                    ),
                                    dbc.Col(
                                        html.Span(
                                            "One-stage",
                                            className="fw-bold text-secondary d-block text-end",
                                        ),
                                        md=3,
                                    ),
                                    dbc.Col(
                                        html.Span(
                                            ["Two-stage"],
                                            className="fw-bold text-secondary d-block text-end",
                                        ),
                                        md=4,
                                    ),
                                    dbc.Col(
                                        html.Span(
                                            "",
                                        ),
                                        md=2,
                                    ),
                                ],
                            ),
                            metric_row(
                                "Biomass",
                                xx,
                                xx2,
                                unit="[g/L]",
                                tooltip=tooltips["biomass_concentration"],
                                row_id=f"{prefix}_biomass_concentration",
                            ),
                            metric_row(
                                "Substrate",
                                ss,
                                ss2,
                                unit="[g/L]",
                                tooltip=tooltips["substrate_concentration"],
                                row_id=f"{prefix}_substrate_concentration",
                            ),
                            metric_row(
                                "Product",
                                pp,
                                pp2,
                                unit="[g/L]",
                                tooltip=tooltips["product_concentration"],
                                row_id=f"{prefix}_product_concentration",
                            ),
                            html.Hr(className="my-2"),
                        ],
                        className="mb-3",
                    ),
                    html.Div(
                        [
                            html.H6(
                                "Performance",
                                className="text-muted fw-bold mt-1",
                                style={"color": "#333"},
                            ),
                            metric_row(
                                "Productivity",
                                prod1,
                                prod_cascade,
                                unit="[g/L/h]",
                                tooltip=tooltips["productivity"],
                                row_id=f"{prefix}_productivity",
                            ),
                            metric_row(
                                "Yield",
                                Yield_OS,
                                Yield_TS,
                                unit="[g/g/h]",
                                tooltip=tooltips["yield"],
                                row_id=f"{prefix}_yield",
                            ),
                            html.Hr(className="my-2"),
                        ],
                        className="mb-3",
                    ),
                    html.Div(
                        [
                            html.H6(
                                "Process Settings",
                                className="text-muted fw-bold mt-1",
                                style={"color": "#333"},
                            ),
                            metric_row(
                                "Feed rate",
                                model.F_total,
                                f"{model.F1:.2f}, {model.F2:.2f}",
                                unit="[L/h]",
                                tooltip=tooltips["feed_rate"],
                                row_id=f"{prefix}_feed_rate",
                            ),
                            metric_row(
                                "Substrate Feed",
                                f"{model.sf_onestage:.2f}",
                                f"{model.sf1:.2f}, {sf2_min:.2f}",
                                unit="[g/L]",
                                tooltip=tooltips["substrate_feed"],
                                row_id=f"{prefix}_substrate_feed",
                            ),
                            metric_row(
                                "Volume",
                                model.V_total,
                                f"{model.V1:.2f}, {model.V2:.2f}",
                                unit="[L]",
                                tooltip=tooltips["volume"],
                                row_id=f"{prefix}_volume",
                            ),
                            metric_row(
                                "Dilution Rate",
                                model.D_total,
                                f"{model.D1:.2f}, {model.D2:.2f}",
                                unit="[1/h]",
                                tooltip=tooltips["dilution_rate"],
                                row_id=f"{prefix}_dilution_rate",
                            ),
                            html.Hr(className="my-2"),
                        ],
                        className="mb-3",
                    ),
                    html.Div(
                        [
                            html.H6(
                                "Export & Downloads",
                                className="text-muted fw-bold mtb-1",
                                style={"color": "#333"},
                            ),
                            dbc.Row(
                                [
                                    download_button("summary", prefix),
                                    download_button("sbml_OS", prefix),
                                    download_button("sbml_cascade", prefix),
                                ],
                                className="g-4 mb-0 justify-content-center",
                            ),
                        ],
                    ),
                ],
            ),
        ],
        className="shadow-sm mb-4",
    )

    summary_data = {
        "prefix": prefix,
        "biomass_onestage": xx,
        "biomass_cascade": xx2,
        "substrate_onestage": ss,
        "substrate_cascade": ss2,
        "product_onestage": pp,
        "product_cascade": pp2,
        "productivity_onestage": prod1,
        "productivity_cascade": prod_cascade,
        "feed_rate": model.F_total,
        "feed_rate_stages": [model.F1, model.F1 + model.F2],
        "volume": model.V_total,
        "volume_stages": [model.V1, model.V2],
        "dilution_rate": model.D_total,
        "dilution_rate_stages": [model.D1, model.D2],
        "stage2_substrate": sf2_min,
    }
    if not is_optimal and optimal_for_D:
        # if the selected D is not optimal, but the cascade is optimal
        if params["D_total_opt"] == params["D_total"]:
            card = None

    return card, summary_data
