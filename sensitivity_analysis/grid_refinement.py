"""Grid-refinement study of ContiDesigner's PHB optimum.

ContiDesigner's closed-form steady states on finer and finer grids, built
exactly like ContiDesigner's: D = Solver.stable_D_values() with D_step = hD
(hD, 2 hD, ... <= stable_D_max, the largest D at which the one-stage
reference exists and passes the stability check) and
phi, nu = 0.01, 0.01 + h, ... < 1 as in
Solver.steady_state_across_phi_ny. The grids are nested. Level 2 (hD = 0.01, h = 0.02)
is the app's default grid; level 3 (hD = 0.005, h = 0.01) is the app's
"Fine grid" option, used in the paper. Levels 1-3 cover
the whole design space; levels 4-5 would need millions of points, so they only
cover +-3 steps of the previous level around its optimum (scope = local).
Each level is compared with the continuous optimum (run continuous_optimum.py
first).

Outputs: grid_refinement.csv (figure: figures.py)
"""
import time
import numpy as np, pandas as pd
from ContiDesigner.core.model import ContiModel
from ContiDesigner.core.solver import Solver
from ContiDesigner.utils.defaults import DEFAULT_PROCESSES
from common import log_runtime, DATA

LEVELS = [  # (hD, h for phi and nu, scope)
    (0.02, 0.04, "global"),
    (0.01, 0.02, "global"),        # app default
    (0.005, 0.01, "global"),       # app "Fine grid" option, used in the paper
    (0.0025, 0.005, "local"),
    (0.00125, 0.0025, "local"),
]
WINDOW = 3


def window(values, centre, half_width):
    return values[np.abs(values - centre) <= half_width + 1e-12]


rows, prev = [], None
for level, (hD, h, scope) in enumerate(LEVELS, start=1):
    model = ContiModel({**DEFAULT_PROCESSES["PHB"], "D_step": hD, "phi_ny_step": h})
    solver = Solver(model)
    D_vals = solver.stable_D_values()          # as Solver.optimize_phi_ny_across_D
    grid = np.arange(0.01, 1.01, h)            # as Solver.steady_state_across_phi_ny
    phi_vals = nu_vals = grid[grid < 1 - 1e-9]
    if scope == "local":                       # around the previous optimum
        prev_hD, prev_h = LEVELS[level - 2][:2]
        D_vals = window(D_vals, prev["D"], WINDOW * prev_hD)
        phi_vals = window(phi_vals, prev["phi"], WINDOW * prev_h)
        nu_vals = window(nu_vals, prev["nu"], WINDOW * prev_h)

    t0, best, n = time.time(), dict(STY=-np.inf), 0
    for D in D_vals:
        for phi in phi_vals:
            for nu in nu_vals:
                with model.temporary_params({"D_total": D, "phi": phi, "ny": nu}):
                    sty = solver.compute_sweep_values()["STY_twostage"]
                n += 1
                if np.isfinite(sty) and sty > best["STY"]:
                    best = dict(STY=sty, D=D, phi=phi, nu=nu)
    seconds = time.time() - t0
    log_runtime(f"grid refinement level {level} (hD={hD}, h={h}, {scope})",
                "ContiDesigner closed form", seconds, n)

    rows.append(dict(level=level, hD=hD, h_phi_nu=h, scope=scope, n_points=n, seconds=seconds,
                     D_opt=best["D"], phi_opt=best["phi"], nu_opt=best["nu"], STY_opt=best["STY"],
                     D1_opt=best["phi"] / (1 - best["nu"]) * best["D"], D2_opt=best["D"] / best["nu"],
                     rel_change_STY_vs_previous=best["STY"] / prev["STY"] - 1 if prev else np.nan))
    prev = best
    print(f"level {level} ({scope}, hD={hD}, h={h}): {n} points, STY={best['STY']:.5f} at "
          f"D={best['D']:.5f}, phi={best['phi']:.4f}, nu={best['nu']:.4f} ({seconds:.0f} s)", flush=True)

df = pd.DataFrame(rows)
cont = pd.read_csv(f"{DATA}/continuous_optimum.csv")
best = cont.loc[cont.STY.idxmax()]
df["rel_diff_STY_vs_paper_grid"] = df.STY_opt / df.STY_opt[df.level == 3].iloc[0] - 1
df["rel_diff_STY_vs_continuous"] = df.STY_opt / best.STY - 1
df.to_csv(f"{DATA}/grid_refinement.csv", index=False)
print(df[["level", "scope", "n_points", "D_opt", "phi_opt", "nu_opt", "STY_opt",
          "rel_diff_STY_vs_continuous"]].round(5).to_string(index=False))
