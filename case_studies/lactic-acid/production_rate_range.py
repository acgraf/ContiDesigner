# %%
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parents[3]))
import numpy as np
import pandas as pd
from multiprocessing import Pool, cpu_count
import copy
import os
import time

import ContiDesigner

ContiModel = ContiDesigner.ContiModel
ContiSolver = ContiDesigner.Solver
ContiPlotter = ContiDesigner.Plotter
DEFAULT_PROCESSES = ContiDesigner.DEFAULT_PROCESSES
# %%


log_file = "run_log_20260806.txt"  # define a separate log file
params_base = DEFAULT_PROCESSES["LA"]
params_base
pi0_s1_ref = params_base["pi0_s1"]#0.1

# %%
def run_single_case(args):
    r0, r1 = args

    # local copy of params
    params = copy.deepcopy(params_base)

    pi0_s1 = pi0_s1_ref
    pi1_s1 = (r1 / (1 - r1)) * pi0_s1/params["mu_max"]
    # pi0_s2 = (r0 / (1 - r0)) * pi0_s1
    # pi0_s2 = r0 * pi0_s1
    pi0_s2 = pi0_s1/r0


    params["pi0_s1"] = pi0_s1
    params["pi0_s2"] = pi0_s2
    params["pi1_s1"] = pi1_s1

    errors = []

    try:
        model = ContiModel(params)
        solver = ContiSolver(model)

        # two-stage
        df, D_ts, sty_ts = solver.optimize_phi_ny_across_D()
        best_D_total = df["STY_cascade"].idxmax()

        phi = df.loc[best_D_total]["phi_opt"]
        ny = df.loc[best_D_total]["ny_opt"]
        x1 = df.loc[best_D_total]["X1_opt"]
    except Exception as e:
        D_ts, sty_ts = np.nan, np.nan
        errors.append(f"two-stage: {e}")

    try:
        # one-stage
        opt_os = solver.find_optimum_D_total(max_param="STY_onestage")
        sty_os, D_os, steady_states= opt_os[0], opt_os[1], opt_os[2]
        max_row = steady_states["STY_onestage"].idxmax()
        print(D_os==steady_states.loc[max_row]["D_total"])
        x_os = steady_states.loc[max_row]["X_onestage"]

    except Exception as e:
        D_os, sty_os = np.nan, np.nan
        errors.append(f"one-stage: {e}")

    TS_adv = (
        sty_ts / sty_os - 1 if np.isfinite(sty_ts) and np.isfinite(sty_os) else np.nan
    )

    return {
        "pi0_s1": pi0_s1,
        "pi0_s2": pi0_s2,
        "pi1_s1": pi1_s1,
        "D_ts": D_ts,
        "phi": phi,
        "ny": ny,
        "x1": x1,
        "sty_ts": sty_ts,
        "D_os": D_os,
        "x_os": x_os,
        "sty_os": sty_os,
        "pi0_ratio": r0,
        "pi1_ratio": r1,
        "TS_adv": TS_adv,
        "errors": "; ".join(errors),
    }


# %%
if __name__ == "__main__":
    pi0_ratio_range = np.linspace(0.01, 1, 100)
    pi1_ratio_range = np.linspace(0.0, 0.99, 100)
    # pi1_ratio_range = [0.9814]

    tasks = [(r0, r1) for r0 in pi0_ratio_range for r1 in pi1_ratio_range]

    nproc = min(cpu_count(), 90)
    output_file = "df_production_rate_range.csv"
    batch_size = 100

    if os.path.exists(output_file):
        df = pd.read_csv(output_file)
        done = set(zip(df["pi0_ratio"], df["pi1_ratio"]))

        results = df.to_dict("records")
        tasks = [(r0, r1) for (r0, r1) in tasks if (r0, r1) not in done]
        #print(f"Resuming from {start_idx} / {len(tasks)}")
        print(f"Resuming: {len(done)} done, {len(tasks)} remaining")
        #tasks = tasks[start_idx:]
    else:
        results = []
    with Pool(processes=nproc) as pool:
        batch_start = time.time()
        total = len(pi0_ratio_range) * len(pi1_ratio_range)
        completed = len(results)
        for i, res in enumerate(pool.imap_unordered(run_single_case, tasks), start=1):
            results.append(res)
            if i % batch_size == 0:
                pd.DataFrame(results).to_csv(output_file, index=False)
                batch_end = time.time()
                elapsed = batch_end - batch_start
                batch_start = time.time()
                completed = len(results)
                msg = (
                        f"{completed}/{total} results saved. "
                        f"Last {batch_size} in {elapsed:.2f} seconds.\n"
                    )
                with open(log_file, "a") as logf:
                    logf.write(msg)

                print(msg.strip(), flush=True)
                
                

    expected = len(pi0_ratio_range) * len(pi1_ratio_range)
    actual = len(
        pd.DataFrame(results)[["pi0_ratio", "pi1_ratio"]].drop_duplicates()
    )

    assert actual == expected, (actual, expected)

    pd.DataFrame(results).to_csv(output_file, index=False)
    with open(log_file, "a") as logf:
        logf.write(f"All {len(results)} results saved.\n")
    print(f"All {len(results)} results saved")