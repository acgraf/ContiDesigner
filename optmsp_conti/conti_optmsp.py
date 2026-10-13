"""
ContiDesigner's two-stage PHB model written as OptMSP modules, plus the
helpers that all scripts in this folder share.

How the mapping works
---------------------
OptMSP optimizes over (module indices, switching times). With one stage there
are no switching times, so the only decision is *which module* to run. We
create one module per design point (D, phi, nu), run each module to steady
state, and let OptMSP's brute force (or IHS) over module indices act as a
search over the design space of the continuous process.

Model: ContiDesigner Eqs. (4)-(7) for N = 2. Monod growth in stage 1 (no
inhibition), growth-arrested stage 2 (mu_s2 = 0). Stage 2 is fed at
sf2_max / (1 + SF2_BUFFER); X2 and P2 do not depend on sf2, and S2 < 0 means
stage 2 would need more than that, i.e. its feed plus ContiDesigner's 5 %
buffer would exceed sf2_max: the point is infeasible (ContiDesigner's rule).

ContiDesigner also rejects stage-1 steady states that relax too slowly: the
largest Jacobian eigenvalue must be below -0.01 1/h and below -0.2 D1 (decay
within 5 residence times; rejects points just below washout).
`stage1_decay_rate` computes that eigenvalue from the port's own ODEs and
`is_robust` applies the criterion.

All scripts are run from this folder; they write to results/data and
results/figures.
"""
import os, sys
import numpy as np
import pandas as pd
import scipy.integrate

DATA, FIGURES = "results/data", "results/figures"
os.makedirs(DATA, exist_ok=True)
os.makedirs(FIGURES, exist_ok=True)

T_END = 3000           # h, simulated time per design point
LAMBDA_MAX = -0.01     # ContiDesigner's stability threshold for stage 1, 1/h
LAMBDA_REL = 0.2       # ... and lambda1 < -LAMBDA_REL * D1 (relative criterion)
X_MIN = 1e-3           # outlet biomass below this counts as washout
SF2_BUFFER = 0.05      # ContiDesigner's safety buffer on the stage-2 feed

X1, S1, P1, X2, S2, P2 = range(6)
OUTLET = [X2, S2, P2]                  # what OptMSP reports as End_X, End_S, End_P
Y0_TWOSTAGE = np.array([0.1, 0, 0, 0, 0, 0], float)
Y0_ONESTAGE = np.array([0.1, 0, 0], float)


# --------------------------------------------------------------------------
# Model
# --------------------------------------------------------------------------
def phb_params():
    """ContiDesigner's PHB parameters, with its defaults for stage 2."""
    from ContiDesigner.utils.defaults import DEFAULT_PROCESSES
    q = dict(DEFAULT_PROCESSES["PHB"])
    for k2, k1 in [("Yxs_2", "Yxs_1"), ("Yps_2", "Yps_1"), ("Yas_2", "Yas_1"),
                   ("rho_2", "rho_1"), ("pi1_s2", "pi1_s1"), ("pi0_s2", "pi0_s1")]:
        q.setdefault(k2, q[k1])
    q.setdefault("mu_s2", 0.0)
    return q


def mu1(q, s):
    """Monod growth rate in stage 1."""
    s = max(0.0, s)
    return q["mu_max"] * s / (q["Ks"] + s)


def sigma(q, stage, mu):
    """Specific substrate consumption (growth + Luedeking-Piret product + maintenance)."""
    i = str(stage)
    pi = q["pi1_s" + i] * mu + q["pi0_s" + i]
    return mu / q["Yxs_" + i] + pi / q["Yps_" + i] + q["rho_" + i] / q["Yas_" + i]


def D1_max(q):
    """Washout bound of a chemostat fed with sf1 (stage 1)."""
    return mu1(q, q["sf1"]) - q["delta"]


def onestage_robust(q, D):
    """One-stage steady state at D exists (no washout) and passes the stability filter."""
    y = simulate(onestage_module(q, D), Y0_ONESTAGE, 50 / max(D, 1e-4) + T_END)
    return bool(y[0] > X_MIN and is_robust(stage1_decay_rate(q, D, y), D))


def D_max(q, D_step=0.01, n_bisect=40):
    """Upper end of the D sweep: the largest D at which the one-stage reference
    (same total volume and feed, so its dilution rate is D) has a steady state
    that passes the stability filter, as ContiDesigner's Solver.stable_D_max.
    Below the washout bound D1_max: the relative criterion (lambda1 < -0.2 D)
    rejects the band just below washout. Scan in steps of D_step, then bisection."""
    D_grid = np.arange(D_step, D1_max(q), D_step)
    ok = [onestage_robust(q, D) for D in D_grid]
    if not any(ok):
        return np.nan
    i = max(k for k, v in enumerate(ok) if v)
    lo, hi = D_grid[i], D_grid[i + 1] if i + 1 < len(D_grid) else D1_max(q)
    for _ in range(n_bisect):
        mid = 0.5 * (lo + hi)
        lo, hi = (mid, hi) if onestage_robust(q, mid) else (lo, mid)
    return float(lo)


def twostage_module(q, D, phi, nu):
    """Two-stage process at one design point, as an OptMSP module f(t, y)."""
    D1, D2 = phi / (1 - nu) * D, D / nu
    delta, mu2, sf1 = q["delta"], q["mu_s2"], q["sf1"]
    sf2 = sf2_fed(q)
    sig2 = sigma(q, 2, mu2)

    def f(t, y):
        x1, s1, p1, x2, _, p2 = (max(0.0, v) for v in y)
        s2 = y[S2]                     # sign kept: S2 < 0 flags infeasibility
        m = mu1(q, s1)
        return [
            (m - delta - D1) * x1,
            -sigma(q, 1, m) * x1 + D1 * (sf1 - s1),
            (q["pi1_s1"] * m + q["pi0_s1"]) * x1 - D1 * p1,
            phi * D2 * x1 + (mu2 - delta - D2) * x2,
            phi * D2 * s1 - sig2 * x2 + D2 * ((1 - phi) * sf2 - s2),
            phi * D2 * p1 + (q["pi1_s2"] * mu2 + q["pi0_s2"]) * x2 - D2 * p2,
        ]
    f.design = dict(D=D, phi=phi, nu=nu, D1=D1, D2=D2)
    return f


def onestage_module(q, D):
    """One-stage chemostat (also: stage 1 alone at D1 = D)."""
    delta, sf = q["delta"], q["sf1"]

    def f(t, y):
        x, s, p = (max(0.0, v) for v in y)
        m = mu1(q, s)
        return [(m - delta - D) * x,
                -sigma(q, 1, m) * x + D * (sf - s),
                (q["pi1_s1"] * m + q["pi0_s1"]) * x - D * p]
    f.design = dict(D=D, D1=D)
    return f


def twostage_grid(q, D_values, phi_values, nu_values):
    """One module per design point, skipping points where stage 1 washes out."""
    return [twostage_module(q, D, phi, nu)
            for D in D_values for phi in phi_values for nu in nu_values
            if phi / (1 - nu) * D <= D1_max(q)]


def simulate(f, y0, t_end=T_END, rtol=1e-8):
    """Integrate with LSODA until steady state (max relative dy/dt < rtol) or t_end."""
    def steady(t, y):
        return np.max(np.abs(f(0, y)) / (1 + np.abs(y))) - rtol
    steady.terminal, steady.direction = True, -1
    r = scipy.integrate.solve_ivp(f, (0, t_end), y0, method="LSODA", events=[steady],
                                  rtol=1e-8, atol=1e-10)
    return r.y[:, -1]


def is_feasible(x_out, s_out):
    """No washout and no negative outlet substrate."""
    return (np.asarray(x_out) > X_MIN) & (np.asarray(s_out) >= 0)


def stage1_decay_rate(q, D1, y1, h=1e-6):
    """Largest real eigenvalue of the stage-1 Jacobian at state y1 = [X1, S1, P1]
    (central finite differences on the port's ODEs)."""
    f = onestage_module(q, D1)
    J = np.empty((3, 3))
    for j in range(3):
        e = np.zeros(3)
        e[j] = h * max(1.0, abs(y1[j]))
        J[:, j] = (np.array(f(0, y1 + e)) - np.array(f(0, y1 - e))) / (2 * e[j])
    return np.max(np.linalg.eigvals(J).real)


def is_robust(lambda1, D1):
    """ContiDesigner's stage-1 stability filter (NaN counts as not robust)."""
    lambda1, D1 = np.asarray(lambda1, float), np.asarray(D1, float)
    return (lambda1 < LAMBDA_MAX) & (lambda1 < -LAMBDA_REL * D1)


def sf2_fed(q):
    """Stage-2 feed concentration of the simulations: the highest feed whose
    buffered value is still within sf2_max."""
    return q["sf2_max"] / (1 + SF2_BUFFER)


def sf2_needed(q, phi, s2, buffer=0.0):
    """Lowest stage-2 feed concentration that still gives S2 >= 0, from a
    simulation fed at sf2_fed(q) (S2 changes with slope 1 - phi in the feed
    concentration). buffer=SF2_BUFFER gives ContiDesigner's sf2_min."""
    s = np.clip(sf2_fed(q) - np.asarray(s2) / (1 - np.asarray(phi)), 0, None)
    return s * (1 + buffer)


# --------------------------------------------------------------------------
# OptMSP
# --------------------------------------------------------------------------
def import_optmsp():
    """Import OptMSPfunctions from $OPTMSP_DIR (default ~/gitti/OptMSP)."""
    path = os.environ.get("OPTMSP_DIR", os.path.expanduser("~/gitti/OptMSP"))
    sys.path.insert(0, os.path.join(path, "MultiStagePackage"))
    import OptMSPfunctions as om
    om.np.Inf = om.np.inf              # OptMSP uses np.Inf, removed in NumPy 2
    return om


def brute_force(om, modules, y0):
    """OptMSP's do_brute_force_num, one module per row, with the design point
    and STY added. OptMSP's solver is hard-coded to RK45, which is too slow on
    this stiff system, so LSODA is swapped in for the duration of the call."""
    rk45 = om.sp.integrate.solve_ivp

    def lsoda(fun, t_span, y0, **kw):
        kw.pop("max_step", None)
        kw.pop("dense_output", None)
        return rk45(fun, t_span, y0, method="LSODA", rtol=1e-8, atol=1e-10, **kw)

    def never(t, y):                   # do_brute_force_num needs one event
        return 1.0
    om.sp.integrate.solve_ivp = lsoda
    try:
        df = om.do_brute_force_num([(i,) for i in range(len(modules))], modules, 1, 0, T_END, 0,
                                   y0, [never], indexes=OUTLET if len(y0) == 6 else [0, 1, 2],
                                   decimal=8)
    finally:
        om.sp.integrate.solve_ivp = rk45
    idx = df.Models.str.strip("[]").astype(int) - 1        # OptMSP counts from 1
    design = pd.DataFrame([modules[i].design for i in idx])
    df = pd.concat([design, df.reset_index(drop=True)], axis=1)
    df["STY"] = np.where(is_feasible(df.End_X, df.End_S), df.D * df.End_P, 0.0)
    return df


def steady_state_option(models, combi, times, s0, *args, **kwargs):
    """Custom OptMSP `calc_option` for Optimizer: run the chosen module to steady
    state. Returns [states..., D, t_end]: the objective needs D for the STY, and
    t_end = times[1] tells OptMSP the stage ran to the end."""
    f = models[int(combi[0])]
    return list(simulate(f, s0, times[1])) + [f.design["D"], times[1]]


def sty_objective(res, *args):
    """OptMSP objective: STY = D * P2, or 0 if infeasible.
    res = [6 states, D, t_end, finished] from steady_state_option."""
    return float(res[6] * res[P2]) if is_feasible(res[X2], res[S2]) else 0.0


def optimizer_class(om):
    """OptMSP's Optimizer reports max_stage - 2 = -1 inequality constraints
    for one stage, which pygmo rejects; this subclass reports 0."""
    class Optimizer(om.Optimizer):
        def get_nic(self):
            return 0
    return Optimizer


# --------------------------------------------------------------------------
# Output
# --------------------------------------------------------------------------
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
