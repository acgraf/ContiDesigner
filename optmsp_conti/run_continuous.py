"""Optimum of the PHB two-stage process over continuous (D, phi, nu), off the grid, on
the independent ODE implementation (reviewer: "independent confirmation using
a numerical optimization algorithm").

Differential evolution (5 seeds, population 15, Sobol initialization, L-BFGS-B
polish) on the port's ODEs, simulated to steady state (no ContiDesigner code),
with ContiDesigner's feasibility rules: D1 <= D1_max, no washout, S2 >= 0 at
1.05 sf2 <= sf2_max (5 % feed buffer), and stage-1 decay rate lambda1 < -0.01 1/h and < -0.2 D1. The best point is
evaluated once more through OptMSP's own Optimizer. The same optimization on
ContiDesigner's closed form is ../sensitivity_analysis/continuous_optimum.py.

Outputs: continuous_optimum.csv  one row per seed + the grid optimum
         continuous_history.csv  best STY vs. number of evaluations
"""
import time
import numpy as np, pandas as pd
from scipy.optimize import differential_evolution
from conti_optmsp import *

SEEDS = [1, 2, 3, 4, 5]
om = import_optmsp()
q = phb_params()
BOUNDS = [(0.001, D_max(q)), (0.001, 0.999), (0.001, 0.999)]      # D, phi, nu


def ode_steady_state(D, phi, nu):
    """Steady state of the port's ODEs, or None if stage 1 washes out."""
    if phi / (1 - nu) * D > D1_max(q):
        return None
    return simulate(twostage_module(q, D, phi, nu), Y0_TWOSTAGE)


def ode_sty(x):
    D, phi, nu = x
    y = ode_steady_state(D, phi, nu)
    if y is None or not is_feasible(y[X2], y[S2]):
        return 0.0
    D1 = phi / (1 - nu) * D
    if not is_robust(stage1_decay_rate(q, D1, y[:3]), D1):
        return 0.0
    return D * y[P2]


rows, history, t_all = [], [], time.time()
for seed in SEEDS:
    n = 0

    def neg_sty(x):
        global n
        n += 1
        return -ode_sty(x)

    def log_progress(intermediate_result):
        history.append(dict(objective="ode", seed=seed, n_evaluations=n,
                            best_STY=-intermediate_result.fun))

    t0 = time.time()
    r = differential_evolution(neg_sty, BOUNDS, seed=seed, popsize=15, maxiter=300,
                               tol=1e-10, atol=0, mutation=(0.5, 1.0), recombination=0.7,
                               polish=True, init="sobol", callback=log_progress)
    history.append(dict(objective="ode", seed=seed, n_evaluations=n, best_STY=-r.fun))
    D, phi, nu = r.x
    D1 = phi / (1 - nu) * D
    y = ode_steady_state(D, phi, nu)              # details of the optimum
    rows.append(dict(objective="ode", seed=seed, D=D, phi=phi, nu=nu, D1=D1, D2=D / nu,
                     STY=-r.fun, n_evaluations=n, seconds=time.time() - t0,
                     converged=r.success, X1=y[X1], S1=y[S1], X2=y[X2], S2=y[S2], P2=y[P2],
                     lambda1=stage1_decay_rate(q, D1, y[:3]),
                     sf2_needed=float(sf2_needed(q, phi, y[S2]))))
    print(f"seed {seed}: STY={-r.fun:.5f} at D={D:.4f}, phi={phi:.4f}, nu={nu:.4f} "
          f"({n} evals, {time.time() - t0:.0f} s)", flush=True)
df = pd.DataFrame(rows)
log_runtime("PHB two-stage, continuous (D, phi, nu)",
            "differential evolution on OptMSP-port ODEs (LSODA to steady state)",
            time.time() - t_all, df.n_evaluations.sum())

# the best ODE point once more, through OptMSP's own Optimizer.fitness
best = df.STY.idxmax()
f = twostage_module(q, df.D[best], df.phi[best], df.nu[best])
opt = optimizer_class(om)(Y0_TWOSTAGE, [f], OUTLET, 0, T_END, 1, 0, sty_objective, "max",
                          calc_option=steady_state_option)
df.loc[best, "STY_via_OptMSP_Optimizer"] = -opt.fitness([0])[0]

# ContiDesigner's grid optimum, for comparison
ref = pd.read_csv(f"{DATA}/ref_PHB.csv")
g = ref.loc[ref.STY_twostage.idxmax()]
grid_row = dict(objective="grid_ContiDesigner", D=g.D_total, phi=g.phi_opt, nu=g.ny_opt,
                D1=g.D1_opt, D2=g.D2_opt, STY=g.STY_twostage)
df = pd.concat([df, pd.DataFrame([grid_row])], ignore_index=True)
df["rel_gain_vs_grid"] = df.STY / g.STY_twostage - 1
df.to_csv(f"{DATA}/continuous_optimum.csv", index=False)
pd.DataFrame(history).to_csv(f"{DATA}/continuous_history.csv", index=False)
print(df[["objective", "seed", "D", "phi", "nu", "STY", "rel_gain_vs_grid", "n_evaluations",
          "lambda1"]].round(5).to_string())
