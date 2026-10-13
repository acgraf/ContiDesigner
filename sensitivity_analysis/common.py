"""
Shared code of the PHB sensitivity analysis: optimise a parameter set,
draw uncertain parameters, save figures.

All scripts are run from this folder; they write to results/data and
results/figures.
"""
import copy, os
import numpy as np
import pandas as pd
from scipy.optimize import minimize, minimize_scalar
from ContiDesigner.core.model import ContiModel
from ContiDesigner.core.solver import Solver
from ContiDesigner.plot import colors
from ContiDesigner.utils.defaults import DEFAULT_PROCESSES

DATA, FIGURES = "results/data", "results/figures"
os.makedirs(DATA, exist_ok=True)
os.makedirs(FIGURES, exist_ok=True)

BASE = copy.deepcopy(DEFAULT_PROCESSES["PHB"])

# Uncertain parameters: the physiological parameters of the strain.
# Not varied: Yas_1 (only rho_1 / Yas_1 enters the model, so rho_1 covers it),
# pi0_s1 (nominal 0, no relative perturbation possible), sf1 and sf2_max
# (operating settings, not properties of the strain). The PHB defaults have no
# stage-2 yields or maintenance, so ContiDesigner uses the stage-1 values for
# stage 2: varying Yxs_1, Yps_1 or rho_1 changes both stages (same organism).
PARAMETERS = ["mu_max", "Ks", "delta", "Yxs_1", "Yps_1", "pi1_s1", "pi0_s2", "rho_1"]
RSD = 0.10             # relative standard deviation of the parameter uncertainty

RED, BLUE, GREY = colors.red, colors.blue, "rgb(120,120,120)"
PENALTY = 1e6


def optimise(params, warm_start=None):
    """Optimal two-stage and one-stage process for one parameter set.

    D is limited to Solver.stable_D_max (the one-stage reference must exist and
    pass the stability check), as in the app; D1 to D1_max.

    Two-stage: Nelder-Mead from warm_start (a (D, phi, nu)) or, if that is
    infeasible or not given, from the best point of a coarse 14 x 16 x 16
    lattice. One-stage: scan of D, then a bounded 1-D search.
    """
    out = dict(STY_TS=np.nan, STY_OS=np.nan, dSTY=np.nan, D_opt=np.nan, phi_opt=np.nan,
               nu_opt=np.nan, titer=np.nan, D_OS=np.nan, titer_OS=np.nan, Y_fed=np.nan)
    model = ContiModel(copy.deepcopy(params))
    solver = Solver(model)
    D_max = solver.stable_D_max()   # D_total bound, as in the app
    D1_max = model.D1_max            # washout bound of stage 1
    if not np.isfinite(D_max):
        return out

    # one stage
    def neg_sty_os(D):
        with model.temporary_params({"D_total": float(D)}):
            P = solver.calculate_steady_states(onestage=True)[2]
        return -D * P if np.isfinite(P) and P >= 0 else PENALTY

    Ds = np.linspace(D_max / 60, D_max * 0.999, 60)
    vals = [neg_sty_os(D) for D in Ds]
    i = int(np.argmin(vals))
    if vals[i] < PENALTY:
        r = minimize_scalar(neg_sty_os, bounds=(Ds[max(i - 1, 0)], Ds[min(i + 1, 59)]),
                            method="bounded", options={"xatol": 1e-9})
        D_os, f_os = (r.x, r.fun) if r.fun < vals[i] else (Ds[i], vals[i])
        out.update(STY_OS=-f_os, D_OS=float(D_os), titer_OS=-f_os / D_os)

    # two stage
    def neg_sty_ts(x):
        D, phi, nu = map(float, x)
        if not (0 < D <= D_max and 0 < phi <= 1 and 0 < nu < 1) or phi / (1 - nu) * D > D1_max:
            return PENALTY
        with model.temporary_params({"D_total": D, "phi": phi, "ny": nu}):
            P2 = solver.calculate_steady_states()[5]
        return -D * P2 if np.isfinite(P2) and P2 >= 0 else PENALTY

    x0, f0 = None, PENALTY
    if warm_start is not None:
        x0, f0 = np.array(warm_start, float), neg_sty_ts(warm_start)
    if f0 >= PENALTY:
        for D in np.linspace(D_max / 14, D_max * 0.999, 14):
            for phi in np.linspace(1 / 16, 1, 16):
                for nu in np.linspace(1 / 16, 1 - 1 / 16, 16):
                    f = neg_sty_ts([D, phi, nu])
                    if f < f0:
                        x0, f0 = np.array([D, phi, nu]), f
    if f0 >= PENALTY:
        return out
    r = minimize(neg_sty_ts, x0, method="Nelder-Mead",
                 options={"xatol": 1e-8, "fatol": 1e-12, "maxiter": 3000})
    x, f = (r.x, r.fun) if r.fun < f0 else (x0, f0)
    D, phi, nu = map(float, x)
    out.update(STY_TS=-f, D_opt=D, phi_opt=phi, nu_opt=nu)
    if out["STY_OS"] > 0:
        out["dSTY"] = out["STY_TS"] / out["STY_OS"] - 1

    with model.temporary_params({"D_total": D, "phi": phi, "ny": nu}):
        P2 = solver.calculate_steady_states()[5]
        fed = model.F1 * model.sf1 + model.F2 * model.sf2    # F2: fresh stage-2 feed
        out.update(titer=P2, Y_fed=P2 * model.F_total / fed)
    return out


def draw_parameters(n, seed=0):
    """n parameter sets, each parameter ~ N(nominal, RSD * nominal), independent.
    Draws with a non-positive value are redrawn (at RSD = 10 % this is rare)."""
    rng = np.random.default_rng(seed)
    draws = []
    while len(draws) < n:
        d = {p: rng.normal(BASE[p], RSD * BASE[p]) for p in PARAMETERS}
        if min(d.values()) > 0:
            draws.append(d)
    return draws


def log_runtime(task, tool, seconds, n_evaluations):
    """Write one row to results/data/runtimes.csv, replacing an older row
    with the same task and tool."""
    path = f"{DATA}/runtimes.csv"
    df = pd.read_csv(path) if os.path.isfile(path) else pd.DataFrame(columns=["task", "tool"])
    df = df[~((df.task == task) & (df.tool == tool))]
    row = pd.DataFrame([dict(task=task, tool=tool, seconds=round(seconds, 2), n_evaluations=n_evaluations)])
    pd.concat([df, row], ignore_index=True).to_csv(path, index=False)
    print(f"[runtime] {task} / {tool}: {seconds:.1f} s for {n_evaluations} evaluations")


def save_figure(fig, name):
    """Write results/figures/<name>.html and .png."""
    fig.write_html(f"{FIGURES}/{name}.html", include_plotlyjs="cdn")
    try:
        fig.write_image(f"{FIGURES}/{name}.png", scale=2)
    except Exception as e:                    # kaleido >= 1 needs Chrome: plotly_get_chrome
        print(f"PNG for {name} skipped: {str(e).strip().splitlines()[0]}")
