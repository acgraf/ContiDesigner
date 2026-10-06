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
    titer_note=None,
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
            line=dict(color="blue", dash="dash"),
            yaxis="y",
            hovertemplate=(
                "X<sub>OS</sub> = %{y:.2f} g/L " "<br>D = %{x:.3f} /h" "<extra></extra>"
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
            line=dict(color="orange", dash="dash"),
            yaxis="y",
            hovertemplate=(
                "P<sub>OS</sub> = %{y:.2f} g/L" "<br>D = %{x:.3f} /h" "<extra></extra>"
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
            line=dict(color="red", dash="dash"),
            marker=dict(size=1, opacity=0),
            yaxis="y2",
            hovertemplate=(
                "STY<sub>OS</sub> = %{y:.2f} g/L/h"
                "<br>D = %{x:.3f} /h"
                "<extra></extra>"
            ),
        )
    )

    # hover note for two-stage points below the minimum titer
    if titer_note is None:
        titer_note = [""] * len(D)
    custom_data = np.array(list(zip(phi, ny, titer_note)), dtype=object)
    # CASCADE
    # biomass 2
    fig.add_trace(
        go.Scatter(
            x=D,
            y=X2,
            mode="lines+markers",
            marker=dict(size=1, opacity=0),
            name="Biomass (Two-stage)",
            line=dict(color="blue"),
            yaxis="y",
            customdata=custom_data,
            hovertemplate=(
                "X<sub>2</sub> = %{y:.2f} g/L"
                "<br>D = %{x:.3f} /h"
                "<br>ϕ = %{customdata[0]:.2f}"
                "<br>ν = %{customdata[1]:.2f}"
                "%{customdata[2]}"
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
            line=dict(color="orange"),
            yaxis="y",
            customdata=custom_data,
            hovertemplate=(
                "P<sub>2</sub> = %{y:.2f} g/L "
                "<br>D = %{x:.3f} /h"
                "<br>ϕ = %{customdata[0]:.2f}"
                "<br>ν = %{customdata[1]:.2f}"
                "%{customdata[2]}"
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
            line=dict(color="red"),
            marker=dict(size=1, opacity=0),
            yaxis="y2",
            customdata=custom_data,
            hovertemplate=(
                "D = %{x:.3f} /h<br>STY<sub>TS</sub> = %{y:.2f} g/L/h"
                "<br>ϕ = %{customdata[0]:.2f}"
                "<br>ν = %{customdata[1]:.2f}"
                "%{customdata[2]}"
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


def _add_titer_constraint(fig, D, titer_ok, titer_min):
    """
    Grey out the D_total values where no two-stage process reaches titer_min
    (titer_ok False; the curves there show the unconstrained optimum) and draw
    titer_min on the concentration axis.
    """
    D = np.asarray(D, dtype=float)
    feasible = np.asarray(titer_ok, dtype=bool)
    # each grid point covers the interval up to the midpoints to its neighbours
    edges = np.concatenate(([0], (D[1:] + D[:-1]) / 2, [D[-1]]))
    i = 0
    while i < len(D):
        if feasible[i]:
            i += 1
            continue
        j = i
        while j + 1 < len(D) and not feasible[j + 1]:
            j += 1
        fig.add_vrect(
            x0=edges[i],
            x1=edges[j + 1],
            fillcolor="grey",
            opacity=0.2,
            layer="below",
            line_width=0,
        )
        i = j + 1
    # keep the titer line visible, also when it lies above all predictions
    ylim = fig.layout.yaxis.range
    if ylim is not None and titer_min * 1.05 > ylim[1]:
        fig.update_layout(yaxis_range=[ylim[0], titer_min * 1.1])
    fig.add_hline(
        y=titer_min,
        line=dict(color="darkorange", dash="dot", width=2.5),
        opacity=1,  # template shape defaults would fade the line
        annotation_text=f"P<sub>2</sub><sup>min</sup> = {titer_min:g} g/L",
        annotation_position="top left",
        annotation_font_color="darkorange",
    )
    return fig


def plot_D_range(plotter, Data=None, titer_min=None):
    """
    Plot steady-state figures (cascade or one-stage).
    Cascade: two separate figures (growth + production reactors)
    One-stage: single figure.
    titer_min: optional minimum product titer; D_total values without a
    two-stage process reaching it are greyed out, the two-stage curves there
    show the unconstrained optimum.
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
    titer_ok = None
    titer_note = None
    if titer_min is not None and "titer_ok" in conti_opt_ss:
        titer_ok = conti_opt_ss["titer_ok"].astype(bool).values
        titer_note = np.where(
            titer_ok, "", "<br><i>below P<sub>2</sub><sup>min</sup></i>"
        )
    fig = go.Figure()
    fig = _plot_D_range_panel(
        fig,
        D=conti_opt_ss["D_total"],
        X=conti_opt_ss["X_onestage"],
        S=conti_opt_ss["S_onestage"],
        P=conti_opt_ss["P_onestage"],
        X2=conti_opt_ss["X2_opt"],
        P2=conti_opt_ss["P2_opt"],
        STY=conti_opt_ss["STY_onestage"],
        STY_cascade=conti_opt_ss["STY_cascade"],
        STY_2=conti_opt_ss["STY_2"],
        phi=conti_opt_ss["phi_opt"],
        ny=conti_opt_ss["ny_opt"],
        titer_note=titer_note,
        title="Steady states across dilution rate + corresponding optimized cascade",
        xlabel="Dilution rate [1/h]",
        xlim=[0, np.nanmax(conti_opt_ss["D_total"])],
        ylim=[
            0,
            np.nanmax(
                [
                    *conti_opt_ss["X_onestage"],
                    *conti_opt_ss["S_onestage"],
                    *conti_opt_ss["P_onestage"],
                    *conti_opt_ss["X2_opt"],
                    *conti_opt_ss["P2_opt"],
                ]
            )
            * 1.05,
        ],
        ylim_sty=[
            0,
            np.nanmax(
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
    if titer_ok is not None:
        fig = _add_titer_constraint(fig, conti_opt_ss["D_total"], titer_ok, titer_min)
    return fig
