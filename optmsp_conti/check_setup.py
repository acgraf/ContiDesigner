"""Smoke test: are ContiDesigner (from this repo) and OptMSP installed, and do
the port and ContiDesigner agree on a small grid around the PHB optimum?"""
import os
import numpy as np
import ContiDesigner
from ContiDesigner.core.model import ContiModel
from ContiDesigner.core.solver import Solver
from ContiDesigner.utils.defaults import DEFAULT_PROCESSES
from conti_optmsp import *

# an older ContiDesigner install writes wrong D1_opt / D2_opt to ref_PHB.csv
repo_src = os.path.realpath("../src")
assert os.path.realpath(ContiDesigner.__file__).startswith(repo_src), \
    f"ContiDesigner is imported from {ContiDesigner.__file__}; run  pip install -e ..  first"

om = import_optmsp()
q = phb_params()
mods = twostage_grid(q, [0.06, 0.07, 0.08], np.arange(0.73, 0.82, 0.02), np.arange(0.69, 0.78, 0.02))
df = brute_force(om, mods, Y0_TWOSTAGE)
best = df.loc[df.STY.idxmax()]
print(f"OptMSP:        STY = {best.STY:.4f} at D = {best.D:.2f}, phi = {best.phi:.2f}, nu = {best.nu:.2f}")

model = ContiModel(dict(DEFAULT_PROCESSES["PHB"]))
with model.temporary_params({"D_total": best.D, "phi": best.phi, "ny": best.nu}):
    sty = Solver(model).compute_sweep_values()["STY_twostage"]
print(f"ContiDesigner: STY = {sty:.4f} at the same design point")
assert abs(best.STY - sty) < 1e-3, "MISMATCH"
print("Setup OK")
