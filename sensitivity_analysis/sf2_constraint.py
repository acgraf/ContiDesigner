"""How the stage-2 feed cap sf2_max sets the PHB optimum, and how much
substrate each process takes in.

The continuous optimum lies on the stage-2 feed constraint: STY rises until
stage 2 would need more than sf2_max, including ContiDesigner's 5 % feed
buffer. Here the continuous optimization (closed form, differential evolution)
is repeated for several sf2_max values, together with
the best one-stage process (continuous in D).
Product yield: on consumed substrate, Solver.calculate_yield
Substrate input per reactor volume and hour:
  two-stage: D * (phi * sf1 + (1 - phi) * sf2),   sf2 = ContiDesigner's (buffered) feed
  one-stage: D * sf1
Output: sf2_constraint.csv
"""

import time
import numpy as np, pandas as pd
from scipy.optimize import differential_evolution, minimize_scalar
from ContiDesigner.core.model import ContiModel
from ContiDesigner.core.solver import Solver
from ContiDesigner.utils.defaults import DEFAULT_PROCESSES
from common import log_runtime, DATA

SF2_MAX = [100, 200, 300, 500, 750, 1000]
rows, t0, n_total = [], time.time(), 0
for sf2_max in SF2_MAX:
    model = ContiModel({**DEFAULT_PROCESSES["PHB"], "sf2_max": sf2_max})
    solver = Solver(model)

    def yield_consumed(D, phi=None, nu=None):
        p = {"D_total": D} if phi is None else {"D_total": D, "phi": phi, "ny": nu}
        with model.temporary_params(p):
            v = solver.compute_sweep_values()
            if phi is None:
                return solver.calculate_yield(
                    v["P_onestage"], v["S_onestage"], onestage=True
                )
            return solver.calculate_yield(v["P2"], v["S2"])

    def values(D, phi=None, nu=None):
        p = {"D_total": D} if phi is None else {"D_total": D, "phi": phi, "ny": nu}
        with model.temporary_params(p):
            return solver.compute_sweep_values()

    def neg_sty_ts(x):
        sty = values(*x)["STY_twostage"]
        return -sty if np.isfinite(sty) else 0.0

    def neg_sty_os(D):
        sty = values(D)["STY_onestage"]
        return -sty if np.isfinite(sty) else 0.0

    D_max = solver.stable_D_max()  # D_total bound, as in the app
    r = differential_evolution(
        neg_sty_ts,
        [(0.001, D_max), (0.001, 0.999), (0.001, 0.999)],
        seed=1,
        popsize=15,
        maxiter=300,
        tol=1e-10,
        atol=0,
        mutation=(0.5, 1.0),
        init="sobol",
        polish=True,
    )
    ro = minimize_scalar(
        neg_sty_os, bounds=(0.001, D_max), method="bounded", options=dict(xatol=1e-7)
    )
    n_total += r.nfev
    D, phi, nu = r.x
    v = values(D, phi, nu)
    sty_ts, sty_os, D_os = v["STY_twostage"], -ro.fun, ro.x
    sin_ts = D * (phi * model.sf1 + (1 - phi) * v["sf2_min"])
    sin_os = D_os * model.sf1

    rows.append(
        dict(
            sf2_max=sf2_max,
            D=D,
            phi=phi,
            nu=nu,
            D1=v["D1"],
            D2=v["D2"],
            STY_twostage=sty_ts,
            P2=v["P2"],
            S2=v["S2"],
            sf2_used=v["sf2_min"],
            substrate_in_TS=sin_ts,
            product_yield_TS=yield_consumed(D, phi, nu),
            D_onestage=D_os,
            STY_onestage=sty_os,
            substrate_in_OS=sin_os,
            product_yield_OS=yield_consumed(D_os),
            STY_ratio_TS_OS=sty_ts / sty_os,
        )
    )
    print(
        f"sf2_max={sf2_max}: STY_TS={sty_ts:.4f} (D={D:.4f}, phi={phi:.4f}, nu={nu:.4f}, "
        f"S2={v['S2']:.2e}), STY_OS={sty_os:.4f}, substrate in TS/OS = "
        f"{sin_ts:.2f}/{sin_os:.2f} g/L/h",
        flush=True,
    )


log_runtime(
    "PHB continuous optimum vs sf2_max (6 values)",
    "differential evolution on ContiDesigner closed form",
    time.time() - t0,
    n_total,
)
pd.DataFrame(rows).to_csv(f"{DATA}/sf2_constraint.csv", index=False)
