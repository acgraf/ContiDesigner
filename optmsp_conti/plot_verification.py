"""How do the search methods do on the PHB two-stage process? Best STY found vs number of
model evaluations: differential evolution on the ODEs (run_continuous.py),
OptMSP's Optimizer + IHS (run_ihs.py), OptMSP brute force (run_phb.py) and
ContiDesigner's grid (ref_contidesigner.py).

Inputs: continuous_optimum.csv, continuous_history.csv, ihs_results.csv, runtimes.csv
Output: figure verification_methods
"""
import pandas as pd
import plotly.graph_objects as go
from conti_optmsp import save_figure, DATA

BLUE, ORANGE, RED, GREY, GREEN = "#1f77b4", "#ff7f0e", "#d62728", "#7f7f7f", "#2ca02c"
cont = pd.read_csv(f"{DATA}/continuous_optimum.csv")
hist = pd.read_csv(f"{DATA}/continuous_history.csv")
ihs = pd.read_csv(f"{DATA}/ihs_results.csv")
runtimes = pd.read_csv(f"{DATA}/runtimes.csv").set_index("task")
best = cont[cont.objective == "ode"].STY.max()
grid = cont[cont.objective == "grid_ContiDesigner"].iloc[0]

fig = go.Figure()
for seed, h in hist.groupby("seed"):
    fig.add_trace(go.Scatter(x=h.n_evaluations, y=h.best_STY, mode="lines", legendgroup="de",
                             name="Differential evolution on the ODEs", showlegend=bool(seed == 1),
                             line=dict(color=GREEN, width=1.2), opacity=0.8))
for task, name, color, symbol in [
        ("PHB two-stage default grid (D step 0.01, phi/nu step 0.02)", "ContiDesigner grid (default)", BLUE, "diamond"),
        ("PHB two-stage default grid (D step 0.01, phi/nu step 0.02; D1 <= D1_max)", "OptMSP brute force, same grid", ORANGE, "square")]:
    fig.add_trace(go.Scatter(x=[runtimes.n_evaluations[task]], y=[grid.STY], mode="markers", name=name,
                             marker=dict(size=13, color=color, symbol=symbol, line=dict(width=1, color="black"))))
fig.add_trace(go.Scatter(x=ihs.n_evaluations, y=ihs.STY, mode="markers", name="OptMSP Optimizer + IHS, same grid",
                         marker=dict(size=10, color=GREY, symbol="circle-open", line=dict(width=2))))
fig.add_hline(y=best, line=dict(color=RED, dash="dash", width=1),
              annotation_text="continuous optimum", annotation_position="bottom right")
lowest = min(hist.best_STY.quantile(0.2), ihs.STY.min())
fig.update_xaxes(type="log", title_text="Model evaluations")
fig.update_yaxes(title_text="Best STY<sub>TS</sub> found [g/L/h]", range=[lowest - 0.02, best + 0.01])
fig.update_layout(template="simple_white", width=900, height=520,
                  legend=dict(orientation="h", y=-0.2, x=0.5, xanchor="center"),
                  margin=dict(l=70, r=20, t=30, b=40))
save_figure(fig, "verification_methods")
