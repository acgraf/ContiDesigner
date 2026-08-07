# %%
import numpy as np
import copy
from ContiDesigner.core import model as conti_model
from ContiDesigner.core import solver as conti_solver
from ContiDesigner.plot import plotter as conti_plotter
from ContiDesigner.utils.defaults import DEFAULT_PROCESSES
import plotly.express as px

import plotly.graph_objects as go
import pandas as pd
import copy

# %%
# %%
params = copy.deepcopy(DEFAULT_PROCESSES["PHB"])

def calc_D1_D2_df(df_base):
    df = copy.deepcopy(df_base)
    df["D1"] = df["D_total"] * df["phi_opt"] / (1 - df["ny_opt"])
    df["D2"] = df["D_total"] / df["ny_opt"]
    df["D1_r"] = np.round(df["D1"], 3)
    df["D2_r"] = np.round(df["D2"], 3)
    return df


model = conti_model.ContiModel(params)

solver = conti_solver.Solver(model)

plotter = conti_plotter.Plotter(model, solver)

df, _, _ = solver.optimize_phi_ny_across_D(max_param="STY_cascade")
df = calc_D1_D2_df(df)

# %%
df_X1, D_X1, a = solver.optimize_phi_ny_across_D(max_param="X1")
df_D1X1, D_DXmax, b = solver.optimize_phi_ny_across_D(max_param="D1X1")

df_P1, D_P1, c = solver.optimize_phi_ny_across_D(max_param="P1")
df_STY1, D_STY1, d = solver.optimize_phi_ny_across_D(max_param="STY_1")
# %%
df_X1 = calc_D1_D2_df(df_X1)
df_D1X1 = calc_D1_D2_df(df_D1X1)
df_P1 = calc_D1_D2_df(df_P1)
df_STY1 = calc_D1_D2_df(df_STY1)
# %%
max_D1_X1 = df_X1["D1"].max()
max_D1_D1X1 = df_D1X1["D1"].max()
max_D1_P1 = df_P1["D1"].max()
max_D1_STY1 = df_STY1["D1"].max()
# %%

params_5R = copy.deepcopy(DEFAULT_PROCESSES["PHB"])
params_5R["sf2_max"] = 200
model_5R = conti_model.ContiModel(params_5R)

solver_5R = conti_solver.Solver(model_5R)

plotter_5R = conti_plotter.Plotter(model_5R, solver_5R)

df_5R, _, _ = solver_5R.optimize_phi_ny_across_D(
    max_param="STY_cascade", secondary_param="STY_2"
)


# %%
fig_STY = plotter.plot_D_range(Data=df)
wanted_names = {
    "STY (One-stage)",
    "STY (Cascade)",
}

fig_STY.data = tuple(t for t in fig_STY.data if getattr(t, "name", "") in wanted_names)

for trace in fig_STY.data:
    trace.yaxis = "y"

name_map = {
    "STY (One-stage)": "STY<sub>one-stage</sub>",
    "STY (Cascade)": "STY<sub>two-stage</sub> (s<sub>2</sub><sup>F max </sup> = 500 g/L)",
}


for trace in fig_STY.data:
    title = dict(
        font=dict(size=16),
    )
    yaxis = (
        dict(
            title=dict(text="STY [g/L/h]", font=dict(size=16)),
            range=[
                0,
                max(
                    df["STY_onestage"].max(),
                    df["STY_cascade"].max(),
                    df_5R["STY_cascade"].max(),
                )
                * 1.4,
            ],
        ),
    )
    legend = dict(
        xanchor="left",
        x=0,
        yanchor="top",
        orientation="v",
        y=1.0,
        font=dict(size=16),
    )

fig_STY.add_trace(
    go.Scatter(
        x=df_5R["D_total"],
        y=df_5R["STY_cascade"],
        mode="lines",
        line=dict(dash="dot", color="red"),
        name="STY<sub>two-stage</sub> (s<sub>2</sub><sup>F max</sup> = 200 g/L)",
        yaxis="y",
    ),
)

fig_STY.add_trace(
    go.Scatter(
        x=[0.03],
        y=[1.72],
        mode="markers",
        marker=dict(symbol="x", size=10, color="black"),
        name="STY<sub>five-stage</sub> (Experimental)",
    ),
)


for trace in fig_STY.data:
    trace.name = name_map.get(trace.name, trace.name)
fig_STY.update_layout(
    width=700,
    height=600,
    xaxis=dict(
        title=dict(
            font=dict(size=16),
        )
    ),
    yaxis=dict(
        title=dict(text="STY [g/L/h]", font=dict(size=16)),
        range=[0, max(df["STY_onestage"].max(), df["STY_cascade"].max()) * 1.3],
    ),
    legend=dict(
        xanchor="left",
        x=0,
        yanchor="top",
        orientation="v",
        y=1.0,
        font=dict(size=16),
    ),
)


fig_STY.show()

# %%
fig_D1_D2 = copy.deepcopy(fig_STY)
fig_D1_D2.data = None
fig_D1_D2.update_layout(
    yaxis2=None,
    yaxis=dict(
        title=dict(
            text="Dilution rate [1/h]",
        ),
        range=[0, df["D2_r"].max()],
    ),
    legend=dict(
        orientation="h",
        yanchor="top",
        y=-0.15,
        xanchor="center",
        x=0.45,
        traceorder="normal",
    )
)



def add_constant_D(fig, df, D):
    D_str, D_val = D
    x_min = df["D_total"].min()
    x_max = df["D_total"].max()
    textis = {
        "D1_X1": "D<sub>1</sub>(X<sub>1</sub><sup>max</sup>)",
        "D1_DX": "D<sub>1</sub>(D<sub>1</sub>X<sub>1</sub><sup>max</sup>)",
        "D1_P1": "D<sub>1</sub>(P<sub>1</sub><sup>max</sup>)",
        "D1_STY1": "D<sub>1</sub>(STY<sub>1</sub><sup>max</sup>)",
    }

    markers = {
        "D1_X1": "circle",
        "D1_DX": "square",
        "D1_P1": "diamond",
        "D1_STY1": "cross",
    }
    marker_positions = {
        "D1_X1": 0.1,
        "D1_DX": 0.15,
        "D1_P1": 0.2,
        "D1_STY1": 0.25,
    }

    name = textis[D_str]
    # threshold line
    fig.add_trace(
        go.Scatter(
            x=[x_min, x_max],
            y=[D_val, D_val],
            mode="lines",
            line=dict(
                dash="dot",
                color="black",
                width=1,
            ),
            showlegend=False,
        )
    )

    # marker with legend entry
    fig.add_trace(
        go.Scatter(
            x=[x_max * marker_positions[D_str]],
            y=[D_val],
            mode="markers+lines",
            marker=dict(
                symbol=markers[D_str],
                size=8,
                color="black",
            ),
            line=dict(
                dash="dot",
                color="black",
                width=1,
            ),
            name=name,
            showlegend=True,
        )
    )


add_constant_D(fig_D1_D2, df, ["D1_X1", max_D1_X1])

add_constant_D(fig_D1_D2, df, ["D1_DX", max_D1_D1X1])

add_constant_D(fig_D1_D2, df, ["D1_P1", max_D1_P1])

add_constant_D(fig_D1_D2, df, ["D1_STY1", max_D1_STY1])


fig_D1_D2.add_trace(
    go.Scatter(
        x=df["D_total"],
        y=df["D_total"],
        mode="lines",
        line=dict(color="black"),
        name="D",
        yaxis="y",
    )
)


fig_D1_D2.add_trace(
    go.Scatter(
        x=df["D_total"],
        y=df["D1_r"],
        mode="lines",
        line=dict(dash="dash", color="forestgreen"),
        name="D<sub>1</sub>",
        yaxis="y",
    )
)

fig_D1_D2.add_trace(
    go.Scatter(
        x=df["D_total"],
        y=df["D2_r"],
        mode="lines",
        line=dict(dash="dash", color="darkorange"),
        name="D<sub>2</sub>",
        yaxis="y",
    ),
)

fig_D1_D2


# %%
