"""ContiDesigner's own grid optimization of the PHB case: the reference."""
import time
from ContiDesigner.core.model import ContiModel
from ContiDesigner.core.solver import Solver
from ContiDesigner.utils.defaults import DEFAULT_PROCESSES
from conti_optmsp import log_runtime, DATA

t0 = time.time()
model = ContiModel(dict(DEFAULT_PROCESSES["PHB"]))
df, D_opt, STY_max = Solver(model).optimize_phi_ny_across_D()
log_runtime("PHB two-stage default grid (D step 0.01, phi/nu step 0.02)", "ContiDesigner optimize_phi_ny_across_D (closed form)",
            time.time() - t0, len(df) * 50 * 50)
df.to_csv(f"{DATA}/ref_PHB.csv", index=False)
print(df[["D_total", "phi_opt", "ny_opt", "D1_opt", "D2_opt", "P2_opt", "STY_twostage",
          "STY_onestage"]].round(4).to_string())
