import numpy as np
import pandas as pd
import plotly.graph_objects as go
import io


def _plot_D_range_panel(
    fig,
    D,
    X,
    S,
    P,
    X1,
    X2,
    P2,
    STY,
    STY_cascade,
    STY_2,
    phi,
    ny,
    title,
    xlabel,
    xlim,
    ylim,
    ylim_sty,
    extra_trace=None,
):
    """ """
    # ONESTAGE
    # biomass
    fig.add_trace(
        go.Scatter(
            x=D,
            y=X,
            mode="lines+markers",
            marker=dict(size=1, opacity=0),
            name="Biomass (One-stage)",
            line=dict(color="blue"),
            yaxis="y",
            hovertemplate=(
                "X<sub>OS</sub> = %{y:.2f} g/L " "<br>D = %{x:.2f} /h" "<extra></extra>"
            ),
        )
    )
    # product
    fig.add_trace(
        go.Scatter(
            x=D,
            y=P,
            mode="lines+markers",
            marker=dict(size=1, opacity=0),
            name="Product (One-stage)",
            line=dict(color="orange"),
            yaxis="y",
            hovertemplate=(
                "P<sub>OS</sub> = %{y:.2f} g/L" "<br>D = %{x:.2f} /h" "<extra></extra>"
            ),
        )
    )
    # STY axis (red)
    fig.add_trace(
        go.Scatter(
            x=D,
            y=STY,
            mode="lines+markers",
            name="STY (One-stage)",
            line=dict(color="red"),
            marker=dict(size=1, opacity=0),
            yaxis="y2",
            hovertemplate=(
                "STY<sub>OS</sub> = %{y:.2f} g/L/h"
                "<br>D = %{x:.2f} /h"
                "<extra></extra>"
            ),
        )
    )

    custom_data = np.stack((phi, ny), axis=-1)
    # CASCADE
    # biomass 2
    fig.add_trace(
        go.Scatter(
            x=D,
            y=X2,
            mode="lines+markers",
            marker=dict(size=1, opacity=0),
            name="Biomass (Two-stage)",
            line=dict(color="blue", dash="dash"),
            yaxis="y",
            customdata=custom_data,
            hovertemplate=(
                "X<sub>2</sub> = %{y:.2f} g/L"
                "<br>D = %{x:.2f} /h"
                "<br>ϕ = %{customdata[0]:.2f}"
                "<br>ν = %{customdata[1]:.2f}"
                "<extra></extra>"
            ),
        )
    )
    # product 2
    fig.add_trace(
        go.Scatter(
            x=D,
            y=P2,
            mode="lines+markers",
            marker=dict(size=1, opacity=0),
            name="Product (Two-stage)",
            line=dict(color="orange", dash="dash"),
            yaxis="y",
            customdata=custom_data,
            hovertemplate=(
                "P<sub>2</sub> = %{y:.2f} g/L "
                "<br>D = %{x:.2f} /h"
                "<br>ϕ = %{customdata[0]:.2f}"
                "<br>ν = %{customdata[1]:.2f}"
                "<extra></extra>"
            ),
            hoverinfo="skip",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=D,
            y=STY_cascade,
            mode="lines+markers",
            name="STY (Two-stage)",
            line=dict(color="red", dash="dash"),
            marker=dict(size=1, opacity=0),
            yaxis="y2",
            customdata=custom_data,
            hovertemplate=(
                "D = %{x:.2f} /h<br>STY<sub>TS</sub> = %{y:.2f} g/L/h"
                "<br>ϕ = %{customdata[0]:.2f}"
                "<br>ν = %{customdata[1]:.2f}"
                "<extra></extra>"
            ),
        )
    )
    # STAGE 1
    custom_data = np.stack((phi, ny), axis=-1)
    # biomass 1
    fig.add_trace(
        go.Scatter(
            x=D,
            y=X1,
            mode="lines+markers",
            marker=dict(size=1, opacity=0),
            name="Biomass (Stage 1)",
            line=dict(color="blue", dash="dot"),
            yaxis="y",
            customdata=custom_data,
            hovertemplate=(
                "X<sub>1</sub> = %{y:.2f} g/L <br>D = %{x:.2f} /h"
                "<br>ϕ = %{customdata[0]:.2f}"
                "<br>ν = %{customdata[1]:.2f}"
                "<extra></extra>"
            ),
        )
    )

    fig.update_layout(
        yaxis=dict(title="Steady-State Concentration [g/L]", range=ylim),
        yaxis2=dict(
            title="STY [g/L/h]",
            overlaying="y",
            side="right",
            position=0.85,
            range=ylim_sty,
            color="red",
        ),
        xaxis=dict(range=xlim),
    )
    # X-axis
    fig.update_xaxes(title_text=xlabel)
    fig.update_xaxes(domain=[0, 0.85])
    return fig


def plot_D_range(plotter, Data=None):
    """
    Plot steady-state figures (cascade or one-stage).
    Cascade: two separate figures (growth + production reactors)
    One-stage: single figure.
    """
    if Data is None:
        conti_opt_ss = plotter.solver.optimize_phi_ny_across_D()[0]
    else:
        if isinstance(Data, str):
            conti_opt_ss = pd.read_json(io.StringIO(Data))
        elif isinstance(Data, dict):
            conti_opt_ss = pd.DataFrame.from_dict(Data)
        else:
            conti_opt_ss = Data
    fig = go.Figure()
    fig = _plot_D_range_panel(
        fig,
        D=conti_opt_ss["D_total"],
        X=conti_opt_ss["X_onestage"],
        S=conti_opt_ss["S_onestage"],
        P=conti_opt_ss["P_onestage"],
        X1=conti_opt_ss["X1_opt"],
        X2=conti_opt_ss["X2_opt"],
        P2=conti_opt_ss["P2_opt"],
        STY=conti_opt_ss["STY_onestage"],
        STY_cascade=conti_opt_ss["STY_cascade"],
        STY_2=conti_opt_ss["STY_2"],
        phi=conti_opt_ss["phi_opt"],
        ny=conti_opt_ss["ny_opt"],
        title="Steady states across dilution rate + corresponding optimized cascade",
        xlabel="Dilution rate [1/h]",
        xlim=[0, np.max(conti_opt_ss["D_total"])],
        ylim=[
            0,
            np.max(
                [
                    *conti_opt_ss["X_onestage"],
                    *conti_opt_ss["S_onestage"],
                    *conti_opt_ss["P_onestage"],
                    *conti_opt_ss["X1_opt"],
                    *conti_opt_ss["X2_opt"],
                    *conti_opt_ss["P2_opt"],
                ]
            )
            * 1.05,
        ],
        ylim_sty=[
            0,
            np.max(
                [
                    *conti_opt_ss["STY_onestage"],
                    *conti_opt_ss["STY_cascade"],
                ]
            )
            * 1.05,
        ],
    )
    fig.update_layout(
        autosize=True,
        margin=dict(l=40, r=10, t=20, b=10),
        template="simple_white",
        legend=dict(orientation="h", y=-0.2, x=0.45, xanchor="center"),
    )
    return fig
