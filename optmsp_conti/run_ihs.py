"""OptMSP's intended search mode on the PHB two-stage process: Optimizer + pygmo IHS.

OptMSP's decision variable is an integer module index, so IHS searches the
grid of run_phb.py, flattened into one index (D, then phi, then nu).
Neighbouring indices are neighbours in nu only, so IHS has no useful notion of
distance in phi or D. This shows how OptMSP's own optimizer does on this
problem; it is not an optimality check (that is run_continuous.py).

Output: ihs_results.csv (one row per seed)
"""
import time
import numpy as np, pandas as pd
import pygmo as pg
from conti_optmsp import *

GENERATIONS, POPULATION, SEEDS = 2000, 30, [1, 2, 3, 4, 5]
om = import_optmsp()
q = phb_params()
D_top = D_max(q)                       # stable one-stage bound, as ContiDesigner
D_values = np.round(np.arange(0.01, D_top + 1e-12, 0.01), 2)
D_values = D_values[D_values <= D_top]       # rounding must not step past it
grid = np.round(np.arange(0.01, 1.0, 0.02), 2)
mods = twostage_grid(q, D_values, grid, grid)
sty_grid = pd.read_csv(f"{DATA}/ref_PHB.csv").STY_twostage.max()

rows, t_all = [], time.time()
for seed in SEEDS:
    t0 = time.time()
    problem = pg.problem(optimizer_class(om)(Y0_TWOSTAGE, mods, OUTLET, 0, T_END, 1, 0, sty_objective,
                                             "max", calc_option=steady_state_option))
    pop = pg.algorithm(pg.ihs(gen=GENERATIONS, seed=seed)).evolve(pg.population(problem, POPULATION, seed=seed))
    d, sty, n = mods[int(pop.champion_x[0])].design, -pop.champion_f[0], pop.problem.get_fevals()
    rows.append(dict(seed=seed, generations=GENERATIONS, D=d["D"], phi=d["phi"], nu=d["nu"], STY=sty,
                     n_evaluations=n, fraction_of_grid=n / len(mods), seconds=time.time() - t0,
                     found_grid_optimum=np.isclose(sty, sty_grid, rtol=1e-6)))
    print(f"IHS seed {seed}: STY={sty:.4f} at D={d['D']}, phi={d['phi']}, nu={d['nu']} "
          f"({n} evals = {n / len(mods):.1%} of the grid, {time.time() - t0:.0f} s)", flush=True)

df = pd.DataFrame(rows)
log_runtime("PHB two-stage grid via OptMSP Optimizer",
            f"OptMSP Optimizer + pygmo IHS ({GENERATIONS} generations, pop {POPULATION})",
            time.time() - t_all, df.n_evaluations.sum())
df.to_csv(f"{DATA}/ihs_results.csv", index=False)
