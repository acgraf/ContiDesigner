# ContiDesigner

ContiDesigner is a Python-based modeling environment for multi-stage continuous bioprocess design.

It is designed for analyzing and designing two-stage continuous processes using steady-state formulations, enabling fast design space exploration.
The default setup models:
- Stage 1: Monod growth
- Stage 2: Growth-arrested production with Luedeking–Piret kinetics  

Several extensions are supported:
- Growth in stage 2 (instead of full arrest)
- Inhibition effects (product, biomass, production)

Note: systems with inhibition are solved numerically and are significantly slower than the analytical steady-state solutions.

## Modes of Use

ContiDesigner can be used in three ways:

- **Python module**  
  For programmatic modeling, simulation, and custom extensions (e.g. new inhibition kinetics)

- **Local Dash app**  
  Interactive exploration with your own implementations

- **Hosted web tool**  
  Available at: [https://chemnettools.anc.univie.ac.at/ContiDesigner/] (no installation required)


## Features

- Steady-state multi-stage continuous process modeling  
- Interactive Dash app for parameter exploration  
- Case studies (e.g., lactic acid, PHB)  
- Comparison of one-stage vs two-stage processes  
- Parameter sweeps with CSV export  
- SBML export for interoperability
- Time evolution plots  
- Visualization and highlighting of operating regimes  
- Optimization studies (primarily via Python module)  

## Installation

Clone the repository and install in editable mode:


```bash
git clone <repo-url!! insert here once done>
cd ContiDesigner
pip install -e .
```

Install the conda env we provide in env.yml

## Usage

### Python module
Example usage (as in case studies):

```python
import ContiDesigner

ContiModel = ContiDesigner.ContiModel
ContiSolver = ContiDesigner.Solver
ContiPlotter = ContiDesigner.Plotter
DEFAULT_PROCESSES = ContiDesigner.DEFAULT_PROCESSES
```

### Web app (local)
Run the app:

```bash
python -m app.dash_app
```
The interface consists of:
- Input panel (parameters)
- Results panel (plots, tables, downloads)
- Information panel
### Web app (hosted)

Access the hosted version: [https://chemnettools.anc.univie.ac.at/ContiDesigner/]

This is the easiest way to explore the tool without setup.


## Project Structure
``` text
ContiDesigner/
├── app/ # Dash application and UI logic
│ ├── dash_app.py # Main app entry point
│ ├── conti_reactions.py # Reaction definitions used for SBML export
│ ├── export_sbml.py # SBML export functionality
│ ├── layout/ # UI components
│ └── assets/ # Static assets 
│
├── src/
│ └── ContiDesigner/ # Core installable Python package
│ ├── core/ # Models, solvers, equations
│ ├── plot/ # Plotting utilities
│ └── utils/ # Helper functions
│
├── case_studies/ # Reproducible examples
│ ├── lactic_acid/ # Lactic acid system
│ └── PHB/ # PHB system

├── paper/ # Plots for the paper (graphical abstract)
│
│
└── README.md
```
## Typical Workflow

1. Define process parameters:
   - Growth: \( \mu_{max} \), Monod constant  
   - Production: Luedeking–Piret coefficients  
   - Maintenance rate  
   - Yields: \( Y^{XS}, Y^{PS}, Y^{AS} \)  
   - Process: total volume, feed concentrations, feed split  

2. Run simulations or optimizations via:
   - Python module (flexible, full control), or  
   - Dash app (interactive exploration)

3. Compare:
   - One-stage vs two-stage setups  
   - Different volume and feed splits 

## Model Assumptions

- Stage 1: substrate is fully consumed  
- Stage 2: substrate demand is determined by maintenance, production, and optional growth  

Process structure:
- Two-stage cascade
- Separate feed streams possible for both stages  

The equivalent one-stage process:
- Same total volume  
- Combined feed equivalent to Stage 2 input  

Key design variables:
- Dilution rate
- Volume split  
- Feed split  



## License
MIT - see `license`

## Author

Andrea Caroline Graf 
(mailto:andrea.caroline.graf@univie.ac.at)
