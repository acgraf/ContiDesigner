"""Optimum of the PHB two-stage process over continuous (D, phi, nu), off the grid
(reviewer: "independent confirmation using a numerical optimization algorithm").

Differential evolution (5 seeds, population 15, Sobol initialization, L-BFGS-B
polish) on ContiDesigner's closed-form steady states, with its feasibility and
stability rules. The same optimization on the independent ODE implementation
is in ../optmsp_conti/run_continuous.py.

Outputs: continuous_optimum.csv  one row per seed
         continuous_history.csv  best STY vs. number of evaluations
"""
import time
import numpy as np, pandas as pd
from scipy.optimize import differential_evolution
from ContiDesigner.core.model import ContiModel
from ContiDesigner.core.solver import Solver
from common import BASE, DATA, log_runtime

SEEDS = [1, 2, 3, 4, 5]
model = ContiModel(dict(BASE))
solver = Solver(model)
BOUNDS = [(0.001, solver.stable_D_max()), (0.001, 0.999), (0.001, 0.999)]      # D, phi, nu


def values(x):
    D, phi, nu = x
    with model.temporary_params({"D_total": D, "phi": phi, "ny": nu}):
        return solver.compute_sweep_values()


rows, history, t_all = [], [], time.time()
for seed in SEEDS:
    n = 0

    def neg_sty(x):
        global n
        n += 1
        sty = values(x)["STY_twostage"]
        return -float(sty) if np.isfinite(sty) else 0.0

    def log_progress(intermediate_result):
        history.append(dict(seed=seed, n_evaluations=n, best_STY=-intermediate_result.fun))

    t0 = time.time()
    r = differential_evolution(neg_sty, BOUNDS, seed=seed, popsize=15, maxiter=300,
                               tol=1e-10, atol=0, mutation=(0.5, 1.0), recombination=0.7,
                               polish=True, init="sobol", callback=log_progress)
    history.append(dict(seed=seed, n_evaluations=n, best_STY=-r.fun))
    v = values(r.x)
    rows.append(dict(seed=seed, D=r.x[0], phi=r.x[1], nu=r.x[2], D1=v["D1"], D2=v["D2"],
                     STY=-r.fun, X1=v["X1"], S1=v["S1"], X2=v["X2"], S2=v["S2"], P2=v["P2"],
                     sf2_used=v["sf2_min"], n_evaluations=n, seconds=time.time() - t0,
                     converged=r.success))
    print(f"seed {seed}: STY={-r.fun:.5f} at D={r.x[0]:.4f}, phi={r.x[1]:.4f}, nu={r.x[2]:.4f} "
          f"({n} evals, {time.time() - t0:.0f} s)", flush=True)

df = pd.DataFrame(rows)
log_runtime("PHB two-stage, continuous (D, phi, nu)", "differential evolution on ContiDesigner closed form",
            time.time() - t_all, df.n_evaluations.sum())
df.to_csv(f"{DATA}/continuous_optimum.csv", index=False)
pd.DataFrame(history).to_csv(f"{DATA}/continuous_history.csv", index=False)
print(f"spread over seeds: STY {df.STY.max() - df.STY.min():.1e} g/L/h, "
      f"D {np.ptp(df.D):.1e}, phi {np.ptp(df.phi):.1e}, nu {np.ptp(df.nu):.1e}")
