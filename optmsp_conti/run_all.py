"""Run the whole analysis, step by step. Run it from this folder:

    python run_all.py                   # all steps, ~1.25 h (optmsp env)
    python run_all.py plot_comparison   # only some steps (script names, without .py)

The output of each step goes to results/logs/<step>.log
(follow a running step with  tail -f results/logs/run_phb.log).
"""
import os, subprocess, sys, time

STEPS = [
    "check_setup",          # smoke test, ~1 min
    "ref_contidesigner",    # ContiDesigner's grid optimum -> ref_PHB.csv, ~15 s
    "run_phb",              # OptMSP brute force on the same grid, ~36 min
    "plot_comparison",      # ~1 min
    "run_continuous",       # differential evolution on the ODEs, ~28 min
    "run_ihs",              # OptMSP Optimizer + pygmo IHS, ~6 min
    "plot_verification",    # needs all of the above
]

os.makedirs("results/logs", exist_ok=True)
for step in sys.argv[1:] or STEPS:
    t0 = time.time()
    print(f"{step} ...", end=" ", flush=True)
    with open(f"results/logs/{step}.log", "w") as log:
        result = subprocess.run([sys.executable, f"{step}.py"], stdout=log, stderr=subprocess.STDOUT)
    print(f"{'done' if result.returncode == 0 else 'FAILED'} ({time.time() - t0:.0f} s)")
    if result.returncode != 0:
        sys.exit(f"see results/logs/{step}.log")
