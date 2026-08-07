import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def _plot_reactor(fig, row, col, t_span, X, S, P, STY=None, title="", show_legend=True):
    """Helper: plot reactor concentrations + STY using Plotly with secondary axis."""
    # If any is None, just skip plotting them
    ymax_conc = np.max([X, S, P]) * 1.05
    ymax_sty = np.max(STY) * 1.1 if STY is not None else 1
    # Primary y-axis (left)
    fig.add_trace(
        go.Scatter(
            x=t_span,
            y=X,
            mode="lines",
            name="Biomass",
            line=dict(color="blue"),
            showlegend=show_legend,
        ),
        row=row,
        col=col,
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=t_span,
            y=S,
            mode="lines",
            name="Substrate",
            line=dict(color="green", dash="dot"),
            showlegend=show_legend,
        ),
        row=row,
        col=col,
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=t_span,
            y=P,
            mode="lines",
            name="Product",
            line=dict(color="orange", dash="dash"),
            showlegend=show_legend,
        ),
        row=row,
        col=col,
        secondary_y=False,
    )
    fig.update_yaxes(
        title_text="Concentration [g/L]" if col == 1 else None,
        range=[0, ymax_conc],
        row=row,
        col=col,
        secondary_y=False,
    )
    if STY is not None:
        fig.add_trace(
            go.Scatter(
                x=t_span,
                y=STY,
                mode="lines",
                name="STY",
                line=dict(color="red"),
                showlegend=show_legend,
            ),
            row=row,
            col=col,
            secondary_y=True,
        )
        fig.update_yaxes(
            title_text="STY [g/L/h]",
            range=[0, ymax_sty],
            row=row,
            col=col,
            secondary_y=True,
            color="red",
        )
    fig.update_xaxes(title_text="Time [h]", row=row, col=col)
    fig.update_annotations(selector=dict(text=title), text=title)
    return fig


def plot_time_evolution(plotter, cascade=True):
    N = plotter.model.N_reactors
    if cascade:
        t_span, y = plotter.model.simulate_process(cascade=cascade, steady_state=True)
        columns = []
        for i in range(N):
            stage = f"{i+1}"
            columns.extend([f"X_{stage}", f"S_{stage}", f"P_{stage}"])

        df = pd.DataFrame(y.T, columns=columns, index=t_span)

        max_cols = 2
        n_cols = min(N, max_cols)
        n_rows = (N + max_cols - 1) // max_cols
        # Build specs correctly
        specs = []
        for r in range(n_rows):
            row_specs = []
            for c in range(n_cols):
                idx = r * n_cols + c
                if idx < N:
                    row_specs.append({"secondary_y": True})
                else:
                    row_specs.append(None)
            specs.append(row_specs)
        subplot_titles = []
        for i in range(N):
            if N == 2:
                if i == 0:
                    title = f"Growth reactor (D<sub>1</sub>: {plotter.model.D1:.2f} /h)"
                else:
                    title = (
                        f"Production reactor (D<sub>2</sub>: {plotter.model.D2:.2f} /h)"
                    )
            else:
                title = f"Reactor {i+1} (D<sub>{i+1}</sub>: {getattr(plotter.model, 'Ds')[i]:.2f} /h)"
            subplot_titles.append(title)

        fig = make_subplots(
            rows=n_rows,
            cols=n_cols,
            subplot_titles=subplot_titles,
            specs=specs,
            horizontal_spacing=0.1,
        )
        for i in range(N):
            stage = f"{i+1}"
            X = df[f"X_{stage}"]
            S = df[f"S_{stage}"]
            P = df[f"P_{stage}"]
            row = (i // max_cols) + 1
            col = (i % max_cols) + 1
            if i == N - 1:  # last reactor plots STY
                STY = P * plotter.model.D_total
                show_legend = True
            else:
                STY = None
                show_legend = False
            fig = _plot_reactor(
                fig,
                row,
                col,
                t_span,
                X,
                S,
                P,
                STY,
                show_legend=show_legend,
            )

        fig.update_layout(
            legend=dict(orientation="h", y=-0.2, x=0.5, xanchor="center"),
            height=500 * n_rows / 2 if N > 3 else 500,
            width=810,
            template="simple_white",
        )

    else:
        t_span, y = plotter.model.simulate_process(cascade=False, steady_state=True)

        df = pd.DataFrame(y.T, columns=["X", "S", "P"], index=t_span)
        STY = df["P"] * plotter.model.D_total
        fig = make_subplots(
            rows=1,
            cols=1,
            subplot_titles=(f"One stage (D: {plotter.model.D_total:.2f} /h)",),
            specs=[[{"secondary_y": True}]],
        )
        fig = _plot_reactor(fig, 1, 1, t_span, df["X"], df["S"], df["P"], STY)
        fig.update_layout(
            legend=dict(orientation="h", y=-0.2, x=0.5, xanchor="center"),
            height=500,
            template="simple_white",
        )
    return fig
