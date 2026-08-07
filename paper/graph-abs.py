# %%
import numpy as np

from ContiDesigner.core import model as conti_model
from ContiDesigner.core import solver as conti_solver
from ContiDesigner.plot import plotter as conti_plotter
from ContiDesigner.utils.defaults import DEFAULT_PROCESSES

import plotly.graph_objects as go
import pandas as pd

params = DEFAULT_PROCESSES["PHB"]
# %%
params["sf2_max"] = 120 
model = conti_model.ContiModel(params)

solver = conti_solver.Solver(model)

plotter = conti_plotter.Plotter(model, solver)

df, D_opt, _ = solver.optimize_phi_ny_across_D(max_param="STY_cascade", secondary_param="STY_2")

phi_opt, ny_opt, _, _ = solver.find_optimum_phi_ny(max_D=D_opt)

df_cont = solver.steady_state_across_phi_ny()
df_contour = pd.DataFrame(df_cont)

# %%
fig_STY = plotter.plot_D_range(Data=df)

# Find the cascade trace
cascade_trace = next(
    tr for tr in fig_STY.data
    if tr.name == "STY (Cascade)"
)

# Find the point closest to D_opt
idx = np.argmin(np.abs(np.asarray(cascade_trace.x) - D_opt))
y_opt = cascade_trace.y[idx]

# Add the star
fig_STY.add_trace(
    go.Scatter(
        x=[D_opt],
        y=[y_opt],
        mode="markers",
        yaxis = "y2",
        marker=dict(
            symbol="star",
            size=16,
            color="violet",
        ),
        showlegend=False,
        hoverinfo="skip"
    )
)


# Horizontal line
fig_STY.add_trace(
    go.Scatter(
        x=[0, D_opt],
        y=[y_opt, y_opt],
        mode="lines",
        yaxis="y2",
        showlegend=False,
        hoverinfo="skip",
        line=dict(color="violet", dash="dash")
    )
)

# Vertical line
fig_STY.add_trace(
    go.Scatter(
        x=[D_opt, D_opt],
        y=[0, y_opt],
        mode="lines",
        yaxis="y2",
        showlegend=False,
        hoverinfo="skip",
        line=dict(color="violet", dash="dash")
    )
)

fig_STY.update_xaxes(
    dict(
        #title_text="Feed distribution ratio towards reactor 1",
        title_font = dict(size=16)
    )
)
fig_STY.update_yaxes(
    dict(
        #title_text="Volume distribution towards reactor 2",
        title_font = dict(size=16)
    )
)
fig_STY
# %%
fig_contour = plotter.plot_contour(Data = df_contour) 


fig_contour.update_layout(
    plot_bgcolor="white", 
    paper_bgcolor="white"
    )
fig_contour.update_xaxes(
    dict(
        title_text="Feed distribution ratio towards reactor 1",
        title_font = dict(size=16)
    )
)
fig_contour.update_yaxes(
    dict(
        title_text="Volume distribution towards reactor 2",
        title_font = dict(size=16)
    )
)
fig_contour.update_traces(
    colorbar=dict(
        title=dict(
            text="Relative two-stage advantage",
            side="right",
            font=dict(size=16)
        )
    )
)#
fig_contour.add_trace(
    go.Scatter(
        x=[phi_opt],
        y=[ny_opt],
        mode="markers",
        showlegend = False,
        marker=dict(
            symbol="star",
            size=16,
            color="violet",
            #line=dict(color="black", width=1)
        )
    )
)

# Horizontal line
fig_contour.add_trace(
    go.Scatter(
        x=[0, phi_opt],
        y=[ny_opt, ny_opt],
        mode="lines",
        showlegend=False,
        hoverinfo="skip",
        line=dict(color="violet", dash="dash")
    )
)

# Vertical line
fig_contour.add_trace(
    go.Scatter(
        x=[phi_opt, phi_opt],
        y=[0, ny_opt],
        mode="lines",
        showlegend=False,
        hoverinfo="skip",
        line=dict(color="violet", dash="dash")
    )
)