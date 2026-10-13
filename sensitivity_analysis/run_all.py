"""Run the whole sensitivity analysis, step by step. Run it from this folder:

    python run_all.py                # all steps, ~25 min (conti env)

The output of each step goes to results/logs/<step>.log
"""
import os, subprocess, sys, time

STEPS = [
    "continuous_optimum",   # differential evolution off the grid, ~30 s
    "grid_refinement",      # needs continuous_optimum, ~2.5 min
    "sf2_constraint",       # optimum and substrate input vs sf2_max, ~30 s
    "montecarlo",           # uncertainty of the optimum, 2000 draws, ~20 min
    "figures",              # montecarlo figure from the CSV, a few s
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
