"""OptMSP's brute-force results drawn over ContiDesigner's own plots.

comparison_D_range   ContiDesigner's D-range plot (lines), OptMSP's per-D optima (markers)
comparison_phi_nu    STY over (phi, nu) at D = 0.07: OptMSP and ContiDesigner side by side
Inputs: ref_PHB.csv, comparison_optmsp_vs_contidesigner.csv, optmsp_bruteforce_grid.csv
"""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from ContiDesigner.core.model import ContiModel
from ContiDesigner.core.solver import Solver
from ContiDesigner.plot.plotter import Plotter
from ContiDesigner.plot import dilution_range, feed_volume_split, colors
from ContiDesigner.utils.defaults import DEFAULT_PROCESSES
from conti_optmsp import phb_params, sf2_needed, save_figure, DATA

D0 = 0.07                                   # dilution rate of the (phi, nu) landscape
q = phb_params()
model = ContiModel(dict(DEFAULT_PROCESSES["PHB"]))
plotter = Plotter(model, Solver(model))
ref = pd.read_csv(f"{DATA}/ref_PHB.csv")
cmp = pd.read_csv(f"{DATA}/comparison_optmsp_vs_contidesigner.csv")
bf = pd.read_csv(f"{DATA}/optmsp_bruteforce_grid.csv")


# --- figure 1: D range ------------------------------------------------------------
fig = dilution_range.plot_D_range(None, Data=ref)
markers = [  # (y, name, color, symbol, axis)
    (cmp.X2_optmsp, "Biomass (Two-stage, OptMSP)", "blue", "circle-open", "y"),
    (cmp.P2_optmsp, "Product (Two-stage, OptMSP)", "orange", "circle-open", "y"),
    (cmp.STY_twostage_optmsp, "STY (Two-stage, OptMSP)", "red", "circle-open", "y2"),
    (cmp.X_onestage_optmsp, "Biomass (One-stage, OptMSP)", "blue", "square-open", "y"),
    (cmp.P_onestage_optmsp, "Product (One-stage, OptMSP)", "orange", "square-open", "y"),
    (cmp.STY_onestage_optmsp, "STY (One-stage, OptMSP)", "red", "square-open", "y2"),
]
for y, name, color, symbol, axis in markers:
    fig.add_trace(go.Scatter(x=cmp.D, y=y, mode="markers", name=name, yaxis=axis, cliponaxis=False,
                             marker=dict(symbol=symbol, color=color, size=8, line=dict(width=1.5))))
# ContiDesigner sets the axis ranges with np.max, which is NaN as soon as a
# column contains NaN; use nanmax instead
conc = np.concatenate([ref.X_onestage, ref.P_onestage, ref.X1_opt, ref.X2_opt, ref.P2_opt])
sty = np.concatenate([ref.STY_onestage, ref.STY_twostage, cmp.STY_twostage_optmsp, cmp.STY_onestage_optmsp])
fig.update_layout(yaxis_range=[0, 1.05 * np.nanmax(conc)], yaxis2_range=[0, 1.05 * np.nanmax(sty)],
                  yaxis2_tickmode="linear", yaxis2_tick0=0, yaxis2_dtick=0.5,
                  title=dict(text="Lines: ContiDesigner · Markers: OptMSP brute force",
                             x=0.425, xanchor="center", font=dict(size=13)),
                  margin=dict(t=50), height=560, width=900)
save_figure(fig, "comparison_D_range")


# --- figure 2: (phi, nu) landscape at D0 ----------------------------------------
with model.temporary_params({"D_total": D0}):
    conti = plotter.solver.steady_state_across_phi_ny()
conti = conti.assign(phi=conti.phi.round(2), ny=conti.ny.round(2))
sub = bf[np.isclose(bf.D, D0)]
optmsp = pd.DataFrame({"phi": sub.phi.round(2), "ny": sub.nu.round(2),
                       "STY_twostage": np.where(sub.STY > 0, sub.STY, np.nan),   # infeasible: blank
                       "sf2_min": sf2_needed(q, sub.phi, sub.End_S, buffer=0.05)})

panels = [("OptMSP (dynamic simulation to steady state)", optmsp),
          ("ContiDesigner (closed-form steady states)", conti)]
zmin = min(np.nanmin(df.STY_twostage) for _, df in panels)
zmax = max(np.nanmax(df.STY_twostage) for _, df in panels)
fig = make_subplots(rows=1, cols=2, shared_yaxes=True, horizontal_spacing=0.04,
                    subplot_titles=[title for title, _ in panels])
with model.temporary_params({"D_total": D0}):
    for col, (_, df) in enumerate(panels, start=1):
        single = feed_volume_split.plot_contour(plotter, contour="STY_twostage", Data=df)
        single.data[0].update(zmin=zmin, zmax=zmax, autocontour=False,
                              contours=dict(start=zmin, end=zmax, size=(zmax - zmin) / 40),
                              colorscale=[[0, colors.mid_color], [1, colors.red]], showscale=(col == 2),
                              colorbar=dict(title=dict(text="STY<sub>TS</sub> [g/L/h]", side="right"), dtick=0.5))
        for trace in single.data:
            fig.add_trace(trace, row=1, col=col)
        best = df.loc[df.STY_twostage.idxmax()]
        fig.add_trace(go.Scatter(x=[best.phi], y=[best.ny], mode="markers", name="Optimum",
                                 showlegend=(col == 1), legendgroup="opt",
                                 marker=dict(symbol="star", size=14, color=colors.optimal_marker_color,
                                             line=dict(color="white", width=1))), row=1, col=col)

# points with a steady state in OptMSP that ContiDesigner rejects
both = optmsp.merge(conti[["phi", "ny", "STY_twostage"]], on=["phi", "ny"], how="left",
                    suffixes=("", "_conti"))
only_optmsp = both[both.STY_twostage.notna() & both.STY_twostage_conti.isna()]
fig.add_trace(go.Scatter(x=only_optmsp.phi, y=only_optmsp.ny, mode="markers",
                         name="Steady state rejected by ContiDesigner's stability criterion",
                         marker=dict(symbol="x-thin", size=4, line=dict(width=1, color="rgba(60,60,60,0.45)"))),
              row=1, col=1)
fig.update_xaxes(title_text="ϕ (F<sub>1</sub>/F)", range=[0, 1], showgrid=False, zeroline=False)
fig.update_yaxes(range=[0, 1], showgrid=False, zeroline=False)
fig.update_yaxes(title_text="ν (V<sub>2</sub>/V)", row=1, col=1)
fig.update_layout(template="seaborn", height=520, width=1050,
                  title=dict(text=f"Two-stage STY over feed and volume split, D = {D0} h<sup>-1</sup>",
                             x=0.5, xanchor="center", font=dict(size=14)),
                  legend=dict(orientation="h", y=-0.18, x=0.5, xanchor="center"),
                  margin=dict(l=60, r=20, t=80, b=40))
fig.update_annotations(font_size=12)
save_figure(fig, "comparison_phi_nu")

found = both.STY_twostage.notna() & both.STY_twostage_conti.notna()
print(f"D = {D0}: steady state in both {found.sum()}, OptMSP only {len(only_optmsp)}, "
      f"ContiDesigner only {conti.STY_twostage.notna().sum() - found.sum()}, "
      f"max |dSTY| where both {np.abs(both.STY_twostage - both.STY_twostage_conti)[found].max():.1e} g/L/h")
