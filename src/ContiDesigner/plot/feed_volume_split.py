import numpy as np
import pandas as pd
import plotly.graph_objects as go
from . import colors
import io

io.default = "notebook_connected"

def _phi_ny_plotter(plotter):
    x = "phi"
    label_x = f"ϕ (F<sub>1</sub>/F)"
    y = "ny"
    label_y = f"ν (V<sub>2</sub>/V)"
    title_base = f"D: {np.round(plotter.model.D_total,2)} /h"
    return x, label_x, y, label_y, title_base


def _plotter_STY():
    z = "STY_1"
    cbarlabel = ""
    titlebase_contour = "STY<sub>1</sub> (g/L/h) "
    hover = "STY'"
    return z, cbarlabel, titlebase_contour, hover


def _plotter_delta_STY_D():
    z = "delta_STY_D"
    cbarlabel = "(STY<sub>TS</sub> / STY<sub>OS</sub>) -1"
    titlebase_contour = f"Two stage cascade design space for "
    hover = "ΔSTY"
    return z, cbarlabel, titlebase_contour, hover


def _plotter_STY_cascade():
    z = "STY_cascade"
    cbarlabel = ""
    titlebase_contour = f"D_total ="
    hover = "STY_cascade"
    return z, cbarlabel, titlebase_contour, hover


def _plotter_sweep_dispatch(plotter, sweep):
    mapping = {"phi_ny": _phi_ny_plotter(plotter)}
    return mapping[sweep]


def _plotter_contour_dispatch(contour):
    mapping = {
        "STY1": _plotter_STY(),
        "delta_STY_D": _plotter_delta_STY_D(),
        "STY_cascade": _plotter_STY_cascade(),
    }
    return mapping[contour]


def plot_contour(
    plotter, sweep="phi_ny", contour="delta_STY_D", Data=None, ncontours=40
):
    """
    ----------
    sweep : str
        One of: "D1_phi", "D1_ny", "phi_ny", "phi_D2D1", "DosD1_V1Vos"
    contour : str
        One of: "STY", "STYratio", "p2_to_p1", "delta_STY_D", "x1"
    calc : str
        "analytical" or "numerical"
    ncontours : int
        Number of contour levels
    """
    if Data is None:
        productivity = getattr(plotter.solver, f"steady_state_across_{sweep}")()
        if productivity is None:
            raise ValueError(f"Unknown sweep type: {sweep}")
        df = pd.DataFrame(productivity)
    else:
        if isinstance(Data, pd.DataFrame):
            df = Data
        # load from JSON string or dict
        elif isinstance(Data, str):
            df = pd.read_json(io.StringIO(Data))
        elif isinstance(Data, dict):
            df = pd.DataFrame.from_dict(Data)
        else:
            raise TypeError("Unsupported data type for 'Data'")
    # get axis info
    x_col, label_x, y_col, label_y, title_base = _plotter_sweep_dispatch(plotter, sweep)
    z_col, cbarlabel, titlebase_contour, hover = _plotter_contour_dispatch(contour)
    pivoted = df.pivot(index=y_col, columns=x_col, values=z_col)
    z_grid = pivoted.values
    infeasible_mask = ~np.isfinite(z_grid)
    z_grid = np.where(infeasible_mask, np.nan, z_grid)
    x_vals = pivoted.columns.values
    y_vals = pivoted.index.values
    z_min = np.nanmin(z_grid)
    z_max = np.nanmax(z_grid)
    if z_max > 0 and z_min < 0:
        z_range = z_max - z_min
        zeroposition = (0 - z_min) / z_range
        maxi = (z_max - z_min) / z_range
        mini = -z_min / z_range
        colorscale = [
            [0, colors.blue],
            [zeroposition, colors.mid_color],
            [1, colors.red],
        ]
    elif z_max <= 0:
        colorscale = [
            [0, colors.blue],
            [1, colors.mid_color],
        ]
    elif z_min >= 0:
        colorscale = [
            [0, colors.mid_color],
            [1, colors.red],
        ]
    else:
        print("Unexpected case in contour plotting.")

    sf2_pivot = df.pivot(index=y_col, columns=x_col, values="sf2_min")
    sf2_grid = sf2_pivot.values
    sf_difference = sf2_grid - plotter.model.sf1
    feasible_region = (sf2_grid < plotter.model.sf1).astype(int)
    feasible_masked = np.where(infeasible_mask, np.nan, feasible_region)

    customdata = np.where(
        sf2_grid < plotter.model.sf1,
        r"No process intensification ($s^F_2 ≤ s^F_1$)",
        r"Process intensification ($s^F_2 \le s^F_1$)",
    )

    hover_text = np.array(
        [
            f"{hover}={val:.3g}" if np.isfinite(val) else "Cascade is infeasible"
            for val in z_grid.flat
        ]
    ).reshape(z_grid.shape)
    hovertemplate = (
        f"{label_x} = %{{x}}<br>"
        f"{label_y} = %{{y}}<br>"
        f"{hover} = %{{z:.3g}}<br>"
        "<extra></extra>"
    )
    fig = go.Figure(
        go.Contour(
            z=z_grid,
            x=x_vals,
            y=y_vals,
            colorscale=colorscale,
            ncontours=ncontours,
            zmin=z_min,
            zmax=z_max,
            colorbar=dict(
                title=dict(
                    text=cbarlabel,
                    side="right",
                )
            ),
            text=hover_text,
            hovertemplate=hovertemplate,
            hoverinfo="x+y+text",
            connectgaps=False,
            line=dict(width=0),
        )
    )
    # Add a white line where z=0
    fig.add_trace(
        go.Contour(
            z=z_grid,
            x=x_vals,
            y=y_vals,
            contours=dict(
                start=0,
                end=0,
                size=1,
                coloring="none",
                showlines=True,
            ),
            line=dict(
                color="white",
                width=3,
            ),
            showscale=False,
            hoverinfo="skip",
            showlegend=False,
        )
    )

    fig.add_trace(
        go.Contour(
            z=feasible_masked,
            x=x_vals,
            y=y_vals,
            contours=dict(
                start=0,
                end=0,
                size=1,
                coloring="fill",
            ),
            colorscale=[
                [0.0, "rgba(0,0,0,0)"],  # process intensification -> sf2>sf1
                [
                    1.0,
                    "rgba(255,255,255,0.3)",
                ],  # sf2 = sf1, no process intensification
            ],
            showscale=False,
            hoverinfo="skip",
        )
    )

    fig.update_layout(
        xaxis_title=label_x,
        yaxis_title=label_y,
        template="seaborn",
        autosize=True,
        margin=dict(l=20, r=20, t=20, b=20),
        xaxis=dict(range=[min(x_vals), max(x_vals)], showgrid=False, zeroline=False),
        yaxis=dict(
            range=[min(y_vals), max(y_vals)],
            showgrid=False,
            zeroline=False,
        ),
    )
    return fig
