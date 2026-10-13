"""Figures of the sensitivity analysis, drawn from the CSVs in results/data

  montecarlo        box plots: optimal STY of both processes, and how much the
                    optimal design moves, when the parameters are uncertain
"""
# %%
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from common import BASE, DATA, RSD, RED, BLUE, GREY, optimise, save_figure

LAYOUT = dict(template="simple_white", font=dict(size=14), showlegend=False)
BOX = dict(boxpoints=False, line=dict(color="black", width=1.5))

# nominal optimum (same optimise(BASE) as in montecarlo.py)
nominal = optimise(BASE)


# --- montecarlo ---------------------------------------------------------------
mc = pd.read_csv(f"{DATA}/montecarlo.csv")
fig = make_subplots(rows=1, cols=2, horizontal_spacing=0.15, column_widths=[0.45, 0.55],
                    subplot_titles=["Best STY of each process", "Optimal two-stage design"])
for col, name, color in [("STY_OS", "One-stage", BLUE), ("STY_TS", "Two-stage", RED)]:
    fig.add_box(y=mc[col], name=name, fillcolor=color, **BOX, row=1, col=1)
for col, name in [("D_opt", "D"), ("phi_opt", "ϕ"), ("nu_opt", "ν")]:
    fig.add_box(y=100 * (mc[col] / nominal[col] - 1), name=name, fillcolor=GREY, **BOX, row=1, col=2)
fig.add_hline(y=0, line_dash="dot", line_color="black", row=1, col=2)
fig.update_yaxes(title_text="optimal STY [g/L/h]", rangemode="tozero", row=1, col=1)
fig.update_yaxes(title_text="deviation from the nominal optimum [%]", row=1, col=2)
fig.update_layout(**LAYOUT, width=900, height=450,
                  title=f"Re-optimised for {len(mc):,} parameter sets ({RSD:.0%} uncertainty)")
save_figure(fig, "montecarlo")

