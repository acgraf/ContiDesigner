"""PHB case through OptMSP, on ContiDesigner grid:
D = 0.01 ... D_max (step 0.01; D_max: largest D with a stable one-stage
reference, as ContiDesigner's stable_D_max), phi, nu = 0.01 ... 0.99 (step 0.02).

1. Two-stage: OptMSP brute force, one module per grid point.
2. One-stage reference: OptMSP brute force over D.
3. For each point the stage-1 decay rate lambda1 (largest Jacobian eigenvalue,
   from the port's own ODEs). This gives ContiDesigner's stability filter
   (lambda1 < -0.01 1/h and < -0.2 D1) and shows whether 3000 h was long enough to reach
   steady state (exp(lambda1 * 3000 h) is the transient that is left).
4. Per-D optimum, compared with ContiDesigner (ref_PHB.csv).

Outputs: optmsp_bruteforce_grid.csv, comparison_optmsp_vs_contidesigner.csv
"""
import time
import numpy as np, pandas as pd
from conti_optmsp import *

om = import_optmsp()
q = phb_params()
D_top = D_max(q)                       # stable one-stage bound, as ContiDesigner
D_values = np.round(np.arange(0.01, D_top + 1e-12, 0.01), 2)
D_values = D_values[D_values <= D_top]       # rounding must not step past it
grid = np.round(np.arange(0.01, 1.0, 0.02), 2)


def add_lambda1(df):
    """Stage 1 only depends on D1, so it is simulated once per distinct D1
    (long enough to be at steady state)."""
    lam = {}
    for D1 in df.D1.unique():
        y = simulate(onestage_module(q, D1), Y0_ONESTAGE, 50 / max(D1, 1e-4) + T_END)
        lam[D1] = stage1_decay_rate(q, D1, y) if y[0] > X_MIN else np.nan
    df["lambda1"] = df.D1.map(lam)
    df["robust"] = is_robust(df.lambda1, df.D1)
    df["STY_robust"] = np.where(df.robust, df.STY, 0.0)
    return df


# 1. two-stage brute force, one D at a time to show progress
t0 = time.time()
parts = []
for D in D_values:
    parts.append(brute_force(om, twostage_grid(q, [D], grid, grid), Y0_TWOSTAGE))
    print(f"D={D:.2f}: {len(parts[-1])} modules, best STY {parts[-1].STY.max():.4f} "
          f"({time.time() - t0:.0f} s)", flush=True)
bf = pd.concat(parts, ignore_index=True)
log_runtime("PHB two-stage default grid (D step 0.01, phi/nu step 0.02; D1 <= D1_max)",
            "OptMSP brute force (LSODA, 3000 h each)", time.time() - t0, len(bf))

# 2. one-stage brute force
os_df = brute_force(om, [onestage_module(q, D) for D in D_values if D < D1_max(q)], Y0_ONESTAGE)

# 3. stage-1 decay rates
t0 = time.time()
bf = add_lambda1(bf)
os_df = add_lambda1(os_df)
log_runtime("PHB stage-1 stability diagnostics", "port ODEs + finite-difference Jacobian",
            time.time() - t0, bf.D1.nunique())
bf.to_csv(f"{DATA}/optmsp_bruteforce_grid.csv", index=False)

# 4. per-D optimum, with ContiDesigner's stability filter (best) and without (raw)
best = bf.loc[bf.groupby("D").STY_robust.idxmax()].set_index("D")
raw = bf.loc[bf.groupby("D").STY.idxmax()].set_index("D")
ref = pd.read_csv(f"{DATA}/ref_PHB.csv").set_index("D_total")
os_df = os_df.set_index("D")
cmp = pd.DataFrame({
    "phi_optmsp": best.phi, "nu_optmsp": best.nu, "D1_optmsp": best.D1, "D2_optmsp": best.D2,
    "X2_optmsp": best.End_X, "P2_optmsp": best.End_P, "STY_twostage_optmsp": best.STY_robust,
    "lambda1_optmsp": best.lambda1,
    "phi_optmsp_nofilter": raw.phi, "nu_optmsp_nofilter": raw.nu,
    "STY_twostage_optmsp_nofilter": raw.STY,
    "phi_conti": ref.phi_opt.round(2), "nu_conti": ref.ny_opt.round(2), "P2_conti": ref.P2_opt,
    "STY_twostage_conti": ref.STY_twostage, "STY_onestage_conti": ref.STY_onestage,
    "X_onestage_optmsp": os_df.End_X, "P_onestage_optmsp": os_df.End_P,
    "STY_onestage_optmsp": os_df.STY,
    "STY_onestage_optmsp_robust": os_df.STY_robust.replace(0, np.nan),
    "lambda1_onestage": os_df.lambda1,
}).rename_axis("D").reset_index()
cmp["same_design"] = np.isclose(cmp.phi_optmsp, cmp.phi_conti) & np.isclose(cmp.nu_optmsp, cmp.nu_conti)
cmp["rel_diff_STY_twostage"] = cmp.STY_twostage_optmsp / cmp.STY_twostage_conti - 1
cmp["rel_diff_STY_onestage"] = cmp.STY_onestage_optmsp_robust / cmp.STY_onestage_conti - 1
cmp.to_csv(f"{DATA}/comparison_optmsp_vs_contidesigner.csv", index=False)
print(cmp.round(4).to_string())

feasible = bf.STY > 0
g = bf.loc[bf.STY_robust.idxmax()]
print(f"\nSame (phi, nu) at {cmp.same_design.sum()} of {len(cmp)} D values; "
      f"max |rel. diff STY_twostage| = {cmp.rel_diff_STY_twostage.abs().max():.1e}")
print(f"Feasible in OptMSP: {feasible.sum()} points, of which {(feasible & ~bf.robust).sum()} fail "
      f"ContiDesigner's stability filter (lambda1 < {LAMBDA_MAX} and < -{LAMBDA_REL} D1); "
      f"{(np.exp(bf.lambda1 * T_END) > 1e-3).sum()} points had not reached steady state "
      f"after {T_END} h (transient left > 0.1 %).")
print(f"Global OptMSP brute-force optimum: D={g.D}, phi={g.phi}, nu={g.nu}, D1={g.D1:.3f}, "
      f"D2={g.D2:.3f}, X2={g.End_X:.2f}, P2={g.End_P:.2f}, STY={g.STY:.4f}, "
      f"lambda1={g.lambda1:.3f} 1/h")
