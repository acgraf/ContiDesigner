import numpy as np
import pandas as pd
from ..utils import helpers
from scipy.optimize import root
from scipy.integrate import solve_ivp
from . import steadystate_eqs
from . import stability


class Solver:
    def __init__(self, model):
        self.model = model
        self._last_ss = None
        self.calculate_steady_states()

    def calculate_x_OS(self):
        return steadystate_eqs.calculate_x_OS(self.model)

    def calculate_p_OS(self, x1):
        return steadystate_eqs.calculate_p_OS(self.model, x1)

    def calculate_s_OS(self):
        return steadystate_eqs.calculate_s_OS(self.model)

    def calculate_x_OS_SI(self):
        return steadystate_eqs.calculate_x_OS_SI(self.model)

    def calculate_p_OS_SI(self, x1):
        return steadystate_eqs.calculate_p_OS_SI(self.model, x1)

    def calculate_s_OS_SI(self):
        return steadystate_eqs.calculate_s_OS_SI(self.model)

    def calculate_x1(self):
        return steadystate_eqs.calculate_x1(self.model)

    def calculate_p1(self, x1):
        return steadystate_eqs.calculate_p1(self.model, x1)

    def calculate_s1(self):
        return steadystate_eqs.calculate_s1(self.model)

    def calculate_x1_SI(self):
        return steadystate_eqs.calculate_x1_SI(self.model)

    def calculate_p1_SI(self, x1):
        return steadystate_eqs.calculate_p1_SI(self.model, x1)

    def calculate_s1_SI(self):
        return steadystate_eqs.calculate_s1_SI(self.model)

    def calculate_x2(self, x1, i=2):
        return steadystate_eqs.calculate_x2(self.model, x1, i)

    def calculate_p2(self, x1, p1, i=2):
        return steadystate_eqs.calculate_p2(self.model, x1, p1, i)

    def calculate_s2(self, x1, s1, i=2):
        return steadystate_eqs.calculate_s2(self.model, x1, s1, i)

    def min_sf2(self, x2, s1, i=1):
        if self.model.N_reactors == 2:
            ny, phi = self.model.ny, self.model.phi
            mu_s2 = self.model.mu_s2
        else:
            ny, phi = self.model.phis[i], self.model.nys[i]
            mu_s2 = self.model.mu_s2[i - 1]
        D_total = self.model.D_total
        sf2_max = self.model.sf2_max
        numerator = (
            helpers.save_divide(self.model.m_2, self.model.Yas_2)
            + helpers.save_divide(mu_s2, self.model.Yxs_2)
            + helpers.save_divide(
                self.model.pi0_s2 + mu_s2 * self.model.pi1_s2,
                self.model.Yps_2,
            )
        )
        sf2lim = helpers.save_divide(1, (phi - 1)) * (
            phi * s1 - ny * x2 * helpers.save_divide(numerator, D_total)
        )
        # if the calculated sf2lim is negative, set it to zero
        # this can be the case little need for substrate and theres a lot of substrate
        # coming from stage 1 (high F1)
        # add 5% as a safety buffer, so the substrate steady state cannot go below zero

        if np.isclose(sf2lim, 0) or sf2lim < 0:
            return 0

        sf2lim = min(sf2lim, sf2_max)
        sf2lim_buffered = sf2lim * 1.05
        sf2lim_buffered = min(sf2lim_buffered, sf2_max)

        self.model.numeric_input_params["sf2"] = sf2lim_buffered

        return sf2lim_buffered
    
    def calculate_steady_states_norm(self, cascade=True):
        if cascade == False:
            x1 = self.calculate_x_OS_norm()
            s1 = self.calculate_s_OS_norm()
            p1 = self.calculate_p_OS_norm(x1=x1)
            return [x1, s1, p1]
        else:
            if np.isnan(self.model.D1) or np.isnan(self.model.D2):
                return [np.nan] * 6
            x1 = self.calculate_x1_norm()
            s1 = self.calculate_s1_norm()
            p1 = self.calculate_p1_norm(x1=x1)
            x2 = self.calculate_x2_norm(x1=x1)
            p2 = self.calculate_p2_norm(x1=x1, p1=p1)
            s2 = self.calculate_s2_norm(x1=x1, s1=s1)
            return [x1, s1, p1, x2, s2, p2]  # , [0,0]

    def calculate_steady_states(self, cascade=True):
        N = self.model.N_reactors

        if self.model.norm == True:
            return self.calculate_steady_states_norm(cascade=cascade)
        if cascade == False:
            if self.model.is_substrate_inhibited:
                x1 = self.calculate_x_OS_SI()
                s1 = self.calculate_s_OS_SI()
                p1 = self.calculate_p_OS_SI(x1=x1)
            else:
                x1 = self.calculate_x_OS()
                s1 = self.calculate_s_OS()
                p1 = self.calculate_p_OS(x1=x1)
            # We only do stability analysis for cases without inhibition for now. 
            lam = stability.dominant_eigenvalue(self.model, [x1, s1, p1], stage=1)
            self.last_lambda1 = lam
            if not stability.is_robust(lam):
                return [np.nan] * 3
            
            if self.model.is_product_inhibited or self.model.is_biomass_inhibited:
                guess1 = [x1, s1, p1]

                guess1 = [max(i, 1e-6) for i in guess1]

                def F1(state):
                    return self.model.one_stage_ODEs(0, state)

                sol_onestage = root(F1, guess1, method="hybr")
                x1, s1, p1 = sol_onestage.x
                if x1 > 1e-4:
                    self._last_ss = [x1, s1, p1]
                # fallback to ODE integration if invalid
                if not sol_onestage.success:  # or (x1 < 1e-12):
                    y = self.model.simulate_process(
                        cascade=False, steady_state=True, return_trajectory=False
                    )
                    x1, s1, p1 = y[:3]
            if not np.isfinite(s1) or s1 < 0:
                return [np.nan] * 3
            

            states = [x1, s1, p1]
            return states
        else:
            if self.model.N_reactors == 2:
                if np.isnan(self.model.D1) or np.isnan(self.model.D2):
                    return [np.nan] * (3 * N)  # [np.nan, np.nan]

            # calculate this always (for now)
            if self.model.is_substrate_inhibited:
                x1 = self.calculate_x1_SI()
                s1 = self.calculate_s1_SI()
                p1 = self.calculate_p1_SI(x1=x1)
            else:
                x1 = self.calculate_x1()
                s1 = self.calculate_s1()
                p1 = self.calculate_p1(x1=x1)

            if self.model.is_product_inhibited or self.model.is_biomass_inhibited:
                guess2 = [x1, s1, p1]

                guess2 = [max(i, 1e-6) for i in guess2]

                def F2(state):
                    return self.model.cascade_ODEs(0, state)

                sol_cascade = root(F2, guess2, method="hybr")
                x1, s1, p1 = sol_cascade.x
                if x1 > 1e-4:
                    self._last_ss = [x1, s1, p1]
                if not sol_cascade.success:  # or (x1 < 1e-12):
                    y = self.model.simulate_process(
                        cascade=True,
                        steady_state=True,
                        only_stage1=True,
                        return_trajectory=False,
                    )
                    x1, s1, p1 = y[:3]
            if not np.isfinite(s1) or s1 < 0:
                return [np.nan] * (3 * self.model.N_reactors)
            lam1 = stability.dominant_eigenvalue(self.model, [x1, s1, p1], stage=1)
            self.last_lambda1 = lam1
            if not stability.is_robust(lam1):
                return [np.nan] * (3 * self.model.N_reactors)

            states = [x1, s1, p1]
            x_prev, s_prev, p_prev = x1, s1, p1
            for i in range(1, self.model.N_reactors):
                x_new = self.calculate_x2(x1=x_prev, i=i)
                p_new = self.calculate_p2(x1=x_prev, p1=p_prev, i=i)
                sf_new = self.min_sf2(x2=x_new, s1=s_prev, i=i)
                self.model.sf2 = sf_new
                s_new = self.calculate_s2(x1=x_prev, s1=s_prev, i=i)
                EPS = 1e-8
                if s_new < EPS:
                    if self.model.N_reactors > 2:
                        print(
                            f"Warning: Not enough substrate for stage {i + 1}. setting s to 0"
                        )
                        s_new = 0
                    else:
                        return [np.nan] * (3 * self.model.N_reactors)
                states.extend([x_new, s_new, p_new])
                # propagate forward
                x_prev, s_prev, p_prev = x_new, s_new, p_new
            return states

    def sweep(
        self,
        sweep1_name,
        sweep1_values,
        sweep2_name=None,
        sweep2_values=None,
    ):
        sweep2_values = sweep2_values if sweep2_values is not None else [None]
        results = []
        for val1 in sweep1_values:
            for val2 in sweep2_values:
                with self.model.temporary_params(
                    {sweep1_name: val1, sweep2_name: val2}
                ):
                    results.append(self.compute_sweep_values())
        df = pd.DataFrame(results)
        df = df.apply(pd.to_numeric)
        return df

    def compute_sweep_values(self):
        # first calculate the steady states with the formulas
        steady_states = self.calculate_steady_states()
        xx, ss, pp, xx2, ss2, pp2 = steady_states
        xx_onestage, ss_onestage, pp_onestage = self.calculate_steady_states(
            cascade=False
        )

        STY_1 = self.calculate_STY(pp, self.model.D1)
        STY_2 = self.calculate_STY(pp2, self.model.D2)
        STY_onestage = self.calculate_STY(pp_onestage, self.model.D_total)
        if np.isnan(self.model.D2):
            STY_cascade = np.nan
        else:
            STY_cascade = self.calculate_STY(pp2, self.model.D_total)
        delta_STY_D = self.calculate_delta_STY_D(STY_onestage, STY_cascade)

        return {
            "D1": self.model.D1,
            "V1": self.model.V1,
            "X1": xx,
            "D1X1": xx * self.model.D1,
            "S1": ss,
            "P1": pp,
            "STY_1": STY_1,
            "D2": self.model.D2,
            "V2": self.model.V2,
            "X2": xx2,
            "S2": ss2,
            "P2": pp2,
            "STY_2": STY_2,
            "sf2_min": self.model.sf2,
            "phi": self.model.phi,
            "ny": self.model.ny,
            "STY_cascade": STY_cascade,
            "D_total": self.model.D_total,
            "V_total": self.model.V_total,
            "X_onestage": xx_onestage,
            "DX_onestage": xx_onestage * self.model.D_total,
            "S_onestage": ss_onestage,
            "P_onestage": pp_onestage,
            "STY_onestage": STY_onestage,
            "delta_STY_D": delta_STY_D,
        }

    def steady_state_across_D(self):
        return self.sweep("D_total", self.model.D_values[1:])

    def steady_state_across_phi_ny(self):
        return self.sweep(
            "phi",
            np.arange(0.01, 1.01, 0.02),
            "ny",
            np.arange(0.01, 1.01, 0.02),
        )

    def find_optimum_D_total(self, max_param="X_onestage"):
        if max_param not in [
            "X_onestage",
            "P_onestage",
            "STY_onestage",
            "DX_onestage",
            "DX_1",
            "P1",
            "X1",
            "STY_1",
        ]:
            raise ValueError(
                "max_param must be one of 'X_onestage', "
                "'P_onestage', 'STY_onestage', 'DX_onestage'"
            )
        steady_states = self.steady_state_across_D()
        steady_states["DX_onestage"] = (
            steady_states["D_total"] * steady_states["X_onestage"]
        )

        steady_states["DX_1"] = steady_states["D1"] * steady_states["X1"]
        param_max = steady_states[max_param].iloc[steady_states[max_param].idxmax()]
        D_optimum = steady_states["D_total"].iloc[steady_states[max_param].idxmax()]
        return param_max, D_optimum, steady_states

    def find_optimum_phi_ny(
        self, max_D=None, max_param="STY_cascade", secondary_param="X_onestage"
    ):
        if max_D is None:
            _, max_D = self.find_optimum_D_total()

        with self.model.temporary_params({"D_total": max_D}):
            steady_states = self.steady_state_across_phi_ny()
            if max_param not in steady_states.columns:
                raise ValueError(
                    f"max_param must be one of {steady_states.columns.tolist()}"
                )
            best = steady_states[max_param].max()
            if not np.isfinite(best):
                # no (phi, ny) pair is feasible at this D_total
                return np.nan, np.nan, steady_states, np.nan
            best_state = steady_states.loc[steady_states[max_param].idxmax()]
            # near_opt = steady_states[steady_states[max_param] >= best]
            # best_state = near_opt.iloc[0]
            phi_param_max = best_state["phi"]
            ny_param_max = best_state["ny"]
            optimal_process = best_state
            delta_STY_D = optimal_process["delta_STY_D"]
        return phi_param_max, ny_param_max, steady_states, delta_STY_D

    def optimize_phi_ny_across_D(
        self, max_param="STY_cascade", secondary_param="X1", tol=0.01
    ):
        """
        Sweep across D_total values, and for each, optimize phi and ny
        to maximize the given max_param (default STY_cascade).
        Returns a DataFrame with:
            D_total, X_onestage, S_onestage, P_onestage,
            phi_opt, ny_opt, X2_opt, S2_opt, P2_opt, STY_cascade_opt
        """
        results = []

        # Loop through each D_total value
        for D_val in self.model.D_values[1:]:
            with self.model.temporary_params({"D_total": D_val}):
                # Optimize phi, ny for this D_total
                phi_opt, ny_opt, phi_ny_grid, rel_improv = self.find_optimum_phi_ny(
                    max_D=D_val, max_param=max_param, secondary_param=secondary_param
                )
                if not (np.isfinite(phi_opt) and np.isfinite(ny_opt)):
                    continue          # skip this D_total
                # With optimal phi, ny, recompute steady states analytically
                with self.model.temporary_params({"phi": phi_opt, "ny": ny_opt}):
                    steady_states = self.calculate_steady_states()
                    X1, S1, P1, X2, S2, P2 = steady_states

                    # Also compute the onestage steady states
                    steady_states_onestage = self.calculate_steady_states(cascade=False)
                    X_onestage, S_onestage, P_onestage = steady_states_onestage

                    # Compute STY_cascade for consistency
                    STY_onestage = self.calculate_STY(P_onestage, self.model.D_total)
                    STY_1 = self.calculate_STY(P1, self.model.D1)
                    STY_2 = self.calculate_STY(P2, self.model.D2)
                    STY_cascade = self.calculate_STY(P2, self.model.D_total)

                    DX_onestage = self.calculate_STY(X_onestage, self.model.D_total)
                    D1X1 = self.calculate_STY(X1, self.model.D1)

                results.append(
                    {
                        "D_total": self.model.D_total,
                        "X_onestage": X_onestage,
                        "DX_onestage": DX_onestage,
                        "S_onestage": S_onestage,
                        "P_onestage": P_onestage,
                        "STY_onestage": STY_onestage,
                        "phi_opt": phi_opt,
                        "ny_opt": ny_opt,
                        "D1_opt": self.model.D1,
                        "D2_opt": self.model.D2,
                        "X1_opt": X1,
                        "D1X1": D1X1,
                        "S1_opt": S1,
                        "P1_opt": P1,
                        "X2_opt": X2,
                        "S2_opt": S2,
                        "P2_opt": P2,
                        "STY_cascade": STY_cascade,
                        "STY_1": STY_1,
                        "STY_2": STY_2,
                    }
                )

        df = pd.DataFrame(results)

        # Identify best D_total according to STY_cascade
        best_D_total_idx = df["STY_cascade"].idxmax()
        D_opt_cascade = df.loc[best_D_total_idx]["D_total"]
        STY_cascade_max = df.loc[best_D_total_idx]["STY_cascade"]

        # Identify best D_total according to STY_onestage
        best_D_onestage_idx = df["STY_onestage"].idxmax()
        D_opt_onestage = df.loc[best_D_onestage_idx]["D_total"]
        STY_onestage_max = df.loc[best_D_onestage_idx]["STY_onestage"]

        # Apply the “2-stage gives no benefit” rule
        if STY_cascade_max <= STY_onestage_max * (1 + tol):
            D_opt = D_opt_onestage
        else:
            D_opt = D_opt_cascade

        return df, D_opt, STY_cascade_max

    def calculate_STY(self, p, D):
        STY = p * D
        return STY

    def calculate_delta_STY_D(self, STY_onestage, STY_cascade):
        if np.isnan(STY_cascade) or np.isnan(STY_onestage):
            return np.nan
        denom = max(abs(STY_onestage), 1e-12)
        delta_STY_D = helpers.save_divide(STY_cascade, denom) - 1
        return delta_STY_D

    def total_substrate_consumed(self, ss_os=None, ss2=None, cascade=True):
        if cascade:
            S_in = (
                self.model.F1 * self.model.sf_onestage + self.model.F2 * self.model.sf2
            )
            S_out = ss2 * self.model.F_total  # bc its the combined feed rate out
            S_consumed = S_in - S_out
        else:
            S_in = self.model.F_total * self.model.sf_onestage
            S_out = self.model.F_total * ss_os
            S_consumed = S_in - S_out
        return S_consumed
