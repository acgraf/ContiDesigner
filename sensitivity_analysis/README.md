# sensitivity_analysis

How accurate and how uncertain is ContiDesigner's PHB optimum?

- `continuous_optimum.py`: optimum off the grid (differential evolution, 5 seeds)
- `grid_refinement.py`: does the optimum depend on the grid resolution?
- `sf2_constraint.py`: how the stage-2 feed cap sf2_max sets the optimum; substrate input and yield
- `montecarlo.py`: uncertainty of the predicted optimum (parameters drawn, process re-optimised for every draw)

The same check with the independent OptMSP implementation is in `../optmsp_conti/`.

Quick start, from inside this folder, in the environment from `../env.yml` with
ContiDesigner installed (`pip install -e ..`):

    python run_all.py                  # all steps, ~25 min
    python run_all.py montecarlo       # only some steps (script names, without .py)

| step | time | output in `results/data/` |
|---|---|---|
| `continuous_optimum.py` | ~30 s | `continuous_optimum.csv` (one row per seed), `continuous_history.csv` |
| `grid_refinement.py` (needs `continuous_optimum`) | ~2.5 min | `grid_refinement.csv` |
| `sf2_constraint.py` | ~30 s | `sf2_constraint.csv` |
| `montecarlo.py` | ~20 min | `montecarlo.csv` (one row per draw), `montecarlo_drivers.csv` |
| `figures.py` | a few s | `results/figures/montecarlo.html` |

Wall times go to `results/data/runtimes.csv`, the console output of each step to
`results/logs/`. For PNG figures also install kaleido (`conda install -c conda-forge kaleido`,
then `plotly_get_chrome`); without it only the HTML is written.

`common.py` holds the shared code: `optimise()` (best two-stage and one-stage
process for one parameter set), `draw_parameters()`, the list of uncertain
parameters and their uncertainty, `log_runtime()` and `save_figure()`.

## Method

Uncertain parameters: mu_max, Ks, delta, Yxs_1, Yps_1, pi1_s1, pi0_s2, rho_1,
independent normal with 10 % relative SD (non-positive draws are redrawn).
Not varied: Yas_1 (only rho_1 / Yas_1 enters the model), pi0_s1 (nominal 0),
sf1 and sf2_max (operating settings). The PHB defaults have no stage-2 yields
or maintenance, so stage 2 uses the stage-1 values: varying Yxs_1, Yps_1 or
rho_1 changes both stages.

`optimise()`: one-stage by a scan of D plus a bounded 1-D search; two-stage by
Nelder-Mead, from the nominal optimum (Monte Carlo) or from the best point of
a 14 x 16 x 16 lattice. D <= Solver.stable_D_max, D1 <= D1_max, with
ContiDesigner's feasibility and stability rules.

The grid levels of `grid_refinement.py` are built like the app's grids; level 2
is the default grid, level 3 the "Fine grid" option used in the paper.
