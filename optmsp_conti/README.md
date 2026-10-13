# optmsp_conti

Independent check of ContiDesigner's PHB optimum with OptMSP (https://github.com/klamt-lab/OptMSP)

- the two-stage PHB model ported to OptMSP, brute force over ContiDesigner's grid
- OptMSP's own optimizer (pygmo IHS)
- differential evolution on the ported ODEs, off the grid

Everything that only needs ContiDesigner is in `../sensitivity_analysis/`

Quick start, from inside this folder, in the optmsp env (OptMSP cloned to `~/pathtoOptMSP/OptMSP`
or `$OPTMSP_DIR`, ContiDesigner installed with `pip install -e ..`):

    python run_all.py          # all steps, ~1.25 h

Output: CSVs in `results/data/`, figures in `results/figures/`, step logs in `results/logs/`.
