"""Uncertainty of the predicted optimum (as in FedBatchDesigner's SI, Section S2).

All uncertain parameters are drawn at once (independent normal, 10 % relative
SD), and both processes are re-optimised for every draw. Shows how precise the
predicted STY, titer and design are, how often the two-stage process wins, and
which parameters drive the result (Spearman rank correlation over the draws).

Outputs: montecarlo.csv (one row per draw), montecarlo_drivers.csv
(figure: figures.py)
"""
import time
import numpy as np, pandas as pd
from scipy.stats import spearmanr
from common import *

N_DRAWS = 2000

nominal = optimise(BASE)
warm = (nominal["D_opt"], nominal["phi_opt"], nominal["nu_opt"])
print("nominal:", {k: round(v, 4) for k, v in nominal.items()})

t0, rows = time.time(), []
for i, draw in enumerate(draw_parameters(N_DRAWS)):
    rows.append({**draw, **optimise({**BASE, **draw}, warm_start=warm)})
    if (i + 1) % 200 == 0:
        print(f"{i + 1}/{N_DRAWS} ({time.time() - t0:.0f} s)", flush=True)
df = pd.DataFrame(rows)
df.to_csv(f"{DATA}/montecarlo.csv", index=False)

# relative deviation from the nominal prediction
METRICS = [  # column, label, panel
    ("D_opt", "Dilution rate D", "Optimal design"),
    ("phi_opt", "Feed split ϕ", "Optimal design"),
    ("nu_opt", "Volume split ν", "Optimal design"),
    ("STY_OS", "One-stage", "Space-time yield"),
    ("STY_TS", "Two-stage", "Space-time yield"),
    ("titer_OS", "One-stage", "Titer"),
    ("titer", "Two-stage", "Titer"),
]
rel = pd.DataFrame({c: df[c] / nominal[c] - 1 for c, *_ in METRICS})
for c, label, panel in METRICS:
    v = rel[c].dropna()
    print(f"{panel:17s} {label:16s} median {v.median():+.3f}  5-95 % [{v.quantile(.05):+.3f}, "
          f"{v.quantile(.95):+.3f}]  within ±{RSD:.0%}: {(v.abs() <= RSD).mean():.1%}")
d = df.dSTY.dropna()
print(f"two-stage better in {(d > 0).mean():.1%} of {len(d)} draws; dSTY median {d.median():+.2f}, "
      f"5-95 % [{d.quantile(.05):+.2f}, {d.quantile(.95):+.2f}] (nominal {nominal['dSTY']:+.2f})")

# which parameters drive the outputs
outputs = ["STY_TS", "STY_OS", "dSTY", "titer"]
drivers = pd.DataFrame({y: [spearmanr(df[p], df[y], nan_policy="omit")[0] for p in PARAMETERS]
                        for y in outputs}, index=PARAMETERS).rename_axis("parameter")
drivers.to_csv(f"{DATA}/montecarlo_drivers.csv")
print("\nSpearman correlation of each parameter with each output:")
print(drivers.round(2).to_string())
