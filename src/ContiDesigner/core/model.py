from itertools import accumulate

import numpy as np
from scipy.integrate import solve_ivp
from contextlib import contextmanager
from ..utils import helpers
from . import ODEs, kinetics


class ContiModel:

    def __init__(self, params):
        self._model_initialized = False
        self.norm = params.get("norm", False)
        self._set_params(params)

    def cascade_ODEs(self, t, state):
        return ODEs.cascade_ODEs(self, t, state)

    def one_stage_ODEs(self, t, state):
        return ODEs.one_stage_ODEs(self, t, state)

    def multi_stage_ODEs(self, t, state):
        return ODEs.multi_stage_ODEs(self, t, state)

    def production(self, i=1, mu=None, s=1):
        return kinetics.production(self, i=i, mu=mu, s=s)

    def sigma(self, i=1, mu=None, s=1):
        return kinetics.sigma(self, i=i, mu=mu, s=s)

    def limit_rate(self, rate, state):
        return kinetics.limit_rate(self, rate, state)

    def _assign_param(self, container, name, value):
        container[name] = value
        setattr(self, name, value)

    def _multistage_params(self):
        Vs = self.Vs
        Fs = self.Fs
        self.V_total = sum(Vs)
        self.F_total = Fs[-1]
        D_total = self.F_total / self.V_total
        Ds = [f / v for f, v in zip(Fs, Vs)]
        nys = [(self.V_total - v) / self.V_total for v in Vs]
        phis = []
        for i in range(self.N_reactors):
            # for phi we care about the inflow from the previous reactor
            phi = Fs[i - 1] / self.F_total
            phis.append(phi)
        # phi is the same for s1 as for s2 
        phis[0] = phis[1]

        multistage_params = {
            "V_total": self.V_total,
            "F_total": self.F_total,
            "D_total": D_total,
            "Ds": Ds,
            "phis": phis,
            "nys": nys,
        }
        return multistage_params

    # collect the numeric parameters which must be given as input
    def collect_obligate_numeric_params(self):
        numeric_params = {}
        required = [
            "mu_max",
            "delta",
            "Yxs_1",
            "Yps_1",
            "Yas_1",
            "m_1",
            "pi0_s1",
            "pi1_s1",
            "V_total",
            "sf1",
            "sf2_max",
        ]
        if self.N_reactors > 2:
            required += ["Fs", "Vs", "pi0s", "pi1s", "sfs"]
        for param in required:
            if param in self.params:
                value = self.params[param]
                if isinstance(value, (float, int)) and np.isfinite(value):
                    self._assign_param(numeric_params, param, float(value))
                # also needs to work for lists now
                elif isinstance(value, list) and all(
                    isinstance(v, (float, int)) and np.isfinite(v) for v in value
                ):
                    self._assign_param(numeric_params, param, [float(v) for v in value])
                else:
                    raise ValueError(f"Invalid value for parameter: {param}")
        return numeric_params

    def collect_optional_numeric_params(self, init=False):
        """
        Collects optional numeric parameters if they are provided.
        """
        numeric_params = {}
        if init:
            optional = [
                "Ks",
                "Ki",
                "Yxs_2",
                "Yps_2",
                "Yas_2",
                "m_2",
                "pi0_s2",
                "pi1_s2",
                "D_total",
                "phi",
                "ny",
                "sf_onestage",
                "sf2",
                "x_max",
                "n1",
                "p_max",
                "n2",
            ]
        else:
            optional = ["D_total", "phi", "ny"]
        for param in optional:
            if param in self.params:
                value = self.params[param]
                if isinstance(value, (float, int)) and np.isfinite(value):
                    self._assign_param(numeric_params, param, float(value))
        return numeric_params

    def assign_default_values(self):
        """
        Resolve structural parameter system and assign defaults.
        If sweep_mode=True, skip back-calculating Fs, Vs, Ds, phi, ny.
        """
        numeric_params = {}
        p = self.params
        N = self.N_reactors

        def resolve_value(name, candidates):
            """
            Resolve a variable from multiple candidate expressions.
            candidates: list of possible values (None allowed)
            Ensures consistency if more than one is defined.
            """
            values = [v for v in candidates if v is not None]

            if not values:
                return None

            first = values[0]
            for v in values[1:]:
                assert abs(first - v) < 1e-12, f"Inconsistent definitions for {name}"

            return first

        def _assign(name, val):
            p[name] = val
            self._assign_param(numeric_params, name, float(val))

        def require(name, value):
            if value is None:
                raise ValueError(f"Cannot resolve parameter: {name}")
            return value

        if N == 2:
            F_total = p.get("F_total")
            F1 = p.get("F1")
            F2 = p.get("F2")
            V_total = p.get("V_total")
            V1 = p.get("V1")
            V2 = p.get("V2")
            D_total = p.get("D_total")
            D1 = p.get("D1")
            D2 = p.get("D2")
            phi = p.get("phi")
            ny = p.get("ny")
            V_total = resolve_value(
                "V_total",
                [
                    V_total,
                    V1 + V2 if V1 is not None and V2 is not None else None,
                    (
                        F_total / D_total
                        if F_total is not None and D_total is not None
                        else None
                    ),
                    V2 / ny if V2 is not None and ny is not None else None,
                ],
            )
            phi = resolve_value(
                "phi",
                [
                    phi,
                    (F1 / F_total if F1 is not None and F_total is not None else None),
                ],
            )
            if phi is None:
                phi = 0.5
            ny = resolve_value(
                "ny",
                [
                    ny,
                    (V2 / V_total if V2 is not None and V_total is not None else None),
                ],
            )
            if ny is None:
                ny = 0.5
            V2 = resolve_value(
                "V2",
                [
                    V2,
                    (ny * V_total if ny is not None and V_total is not None else None),
                ],
            )
            V1 = resolve_value(
                "V1",
                [
                    V1,
                    (V_total - V2 if V_total is not None and V2 is not None else None),
                ],
            )
            D_total = resolve_value(
                "D_total",
                [
                    D_total,
                    (
                        F_total / V_total
                        if F_total is not None and V_total is not None
                        else None
                    ),
                ],
            )
            if D_total is None:
                D_total = p["mu_max"] * 0.5  # default to half of mu_max if not defined
            D1 = resolve_value(
                "D1",
                [
                    D1,
                    (
                        phi / (1 - ny) * D_total
                        if phi is not None and ny is not None and D_total is not None
                        else None
                    ),
                ],
            )
            D2 = resolve_value(
                "D2",
                [
                    D2,
                    (D_total / ny if D_total is not None and ny is not None else None),
                ],
            )
            F_total = resolve_value(
                "F_total",
                [
                    F_total,
                    F1 + F2 if F1 is not None and F2 is not None else None,
                    (
                        D_total * V_total
                        if D_total is not None and V_total is not None
                        else None
                    ),
                    F1 / phi if F1 is not None and phi is not None else None,
                ],
            )
            F1 = resolve_value(
                "F1",
                [
                    F1,
                    (
                        phi * F_total
                        if phi is not None and F_total is not None
                        else None
                    ),
                ],
            )
            F2 = resolve_value(
                "F2",
                [
                    F2,
                    (F_total - F1 if F_total is not None and F1 is not None else None),
                ],
            )
            # Final check
            require("F1", F1)
            require("F2", F2)
            require("V1", V1)
            require("V2", V2)
            require("D_total", D_total)
            require("D1", D1)
            require("D2", D2)
            require("phi", phi)
            require("ny", ny)
            derived_params = {
                "F_total": F_total,
                "F1": F1,
                "F2": F2,
                "V_total": V_total,
                "V1": V1,
                "V2": V2,
                "D_total": D_total,
                "D1": D1,
                "D2": D2,
                "phi": phi,
                "ny": ny,
            }
            for k, v in derived_params.items():
                _assign(k, v)

        else:
            # for more than 2 reactors, we do not check consistency, just assign what is provided
            multistage_params = self._multistage_params()
            self._assign_param(numeric_params, "Ds", multistage_params["Ds"])
            self._assign_param(numeric_params, "phis", multistage_params["phis"])
            self._assign_param(numeric_params, "nys", multistage_params["nys"])
            self._assign_param(numeric_params, "V_total", multistage_params["V_total"])
            self._assign_param(numeric_params, "F_total", multistage_params["F_total"])
            self._assign_param(numeric_params, "D_total", multistage_params["D_total"])
        # Non-structural defaults (sf2, etc.) are always fine to assign
        if not self.norm:
            defaults = {
                "stage2_mu_factor": 0.1,
                "Yxs_2": self.Yxs_1,
                "Yps_2": self.Yps_1,
                "Yas_2": self.Yas_1,
                "m_2": self.m_1,
                "pi0_s2": self.pi0_s1,
                "pi1_s2": self.pi1_s1,
                "sf2": self.sf2_max,
                "sf_onestage": self.sf1,
                "n1": 0.5,
                "n2": 0.5,
            }
            for k, v in defaults.items():
                if k not in p or p[k] is None:
                    p[k] = v
                self._assign_param(numeric_params, k, float(p[k]))

        return numeric_params

    def collect_derived_params(self, init=False, sweep_mode=False):
        derived = {}
        if init:
            # first-time initialization
            self._assign_param(derived, "D_max", self.dilution_range_D()[0])
            self.D_values = self.dilution_range_D()[1]
            self._assign_param(derived, "D1_max", self.dilution_range_D1()[0])
            self.D1_range = self.dilution_range_D1()[1]
            self._assign_param(
                derived, "stage2_mu_factor", self.params.get("stage2_mu_factor", 0.1)
            )
            self._assign_param(derived, "mu_s2", self.mu_stage2())
        else:
            if self.N_reactors == 2:
                # we are sweeping now, and D_total, phi and ny have been updated.
                self._assign_param(derived, "F_total", self.D_total * self.V_total)
                self._assign_param(derived, "V1", float(self.V_total * (1 - self.ny)))
                self._assign_param(derived, "V2", float(self.V_total * self.ny))
                self._assign_param(derived, "D1", float(self.calculate_D1()))
                self._assign_param(derived, "F1", float(self.D1 * self.V1))
                self._assign_param(derived, "D2", float(self.calculate_D2()))
                self._assign_param(derived, "F2", float(self.F_total - self.F1))
            else:
                for i in range(self.N_reactors):
                    pass
        return derived

    def collect_nonnumeric_input_params(self):
        # collect non-numeric parameters, mostly boolean flags
        nonnum = {}
        # Inhibition
        self.is_substrate_inhibited = self.params.get("is_substrate_inhibited", False)
        self.is_biomass_inhibited = self.params.get("is_biomass_inhibited", False)
        self.is_product_inhibited = self.params.get("is_product_inhibited", False)
        self.N_reactors = self.params.get("N_reactors", 2)

        self.growth_flags = self.params.get("growth_flags", None)
        if self.growth_flags is not None:
            assert (
                len(self.growth_flags) == self.N_reactors
            ), "growth_flags length must match N_reactors"
        elif self.N_reactors == 2:
            self.growth_flags = [True, self.params.get("growth_stage2", False)]
        else:
            self.growth_flags = [True] + [False] * (self.N_reactors - 1)

        nonnum.update(
            {
                "is_substrate_inhibited": self.is_substrate_inhibited,
                "is_biomass_inhibited": self.is_biomass_inhibited,
                "is_product_inhibited": self.is_product_inhibited,
                "growth_flags": self.growth_flags,
            }
        )
        return nonnum

    def collect_numeric_params(self, init=False):
        """
        Collects all numeric parameters, both obligate and optional.
        """
        out = self.collect_obligate_numeric_params()
        out.update(self.collect_optional_numeric_params(init=init))

        return out

    def _set_params(self, params):
        """
        Organizes parameter initialization for the bioreactor models.
        Distinguishes between:
        - obligate numeric params
        - optional numeric params
        - nonnumeric/boolean flags
        - derived parameters
        """
        self.params = params.copy()
        if not self._model_initialized:
            # others and nonnumeric
            self.nonnumeric_input_params = self.collect_nonnumeric_input_params()
            self.growth_initial_state = self.params.get(
                "growth_initial_state", [0.1, 0, 0]
            )
            self.prod_initial_state = self.params.get("prod_initial_state", [0, 0, 0])
            self.initial_state = self.growth_initial_state + self.prod_initial_state * (
                self.N_reactors - 1
            )
            self.t_span = self.params.get("t_span", np.linspace(0, 500, 501))

            self.numeric_input_params = self.collect_numeric_params(init=True)
            self.numeric_input_params.update(self.assign_default_values())

            self.numeric_input_params.update(self.collect_derived_params(init=True))
            self._model_initialized = True
        else:  # sweep! D, phi, ny must be updated.
            self.numeric_input_params = self.collect_numeric_params(init=False)
            self.numeric_input_params.update(self.collect_derived_params(init=False))

        self.handle_zero_values()

    def handle_zero_values(self):
        # Some parameters may be zero without breaking the model
        # We can simplify this scenario, e.g. if Yps is 0, then there is no product formation
        # Which parameters may be zero?
        # mu_s2
        # production rates
        # maintenance rate
        # All Yields
        # If a yield is zero, then the corresponding rate is also zero

        for i in [1, 2]:
            Yps = getattr(self, f"Yps_{i}")
            Yas = getattr(self, f"Yas_{i}")
            if Yps == 0:
                setattr(self, f"pi0_s{i}", 0)
                setattr(self, f"pi1_s{i}", 0)
            if Yas == 0:
                setattr(self, f"m_{i}", 0)
        if self.Yxs_2 == 0:
            self.mu_s2 = 0

    @contextmanager
    def temporary_params(self, temp_params):
        # Save current params
        old_params = self.params.copy()

        # Update params with temporary values
        self.params.update(temp_params)
        self._set_params(self.params)
        # print(f"in contextmanager: D1={self.D1}, D2={self.D2}, phi={self.phi}, ny={self.ny}")

        try:
            yield
        finally:
            # Restore old params
            self.params = old_params
            self._set_params(self.params)

    def dilution_range_D(self, norm=False):
        # set a linspace of dilution rates from 0 to 1,
        # that will be limited by the maximum dilution rate
        D_range = np.linspace(0, 1, 101)
        mu_eff = self.limit_rate(self.mu_max, [0, self.sf1, 0])
        D_max = mu_eff - self.delta
        if D_max < 0:
            D_max = 0
        if norm:
            D_max = D_max / self.mu_max
        D_values = D_range[D_range <= D_max]
        return D_max, D_values

    def dilution_range_D1(self, norm=False):
        ## since D1 is always bigger than D_total
        ## so it also needs to be limited
        buffer = 0#0.15
        D_range = np.linspace(0, 1, 101)
        mu_eff = self.limit_rate(self.mu_max, [0, self.sf1, 0])
        D1_max_total = mu_eff - self.delta
        D1_max = D1_max_total * (
            1 - buffer
        )  # add a buffer to avoid numerical issues at the limit
        if norm:
            D1_max = D1_max / self.mu_max
        D1_range = D_range[D_range <= D1_max]
        return D1_max, D1_range

    def calculate_D1(self):
        if np.isclose(self.ny, 1.0):
            return np.nan
        # D1 = self.phi / self.ny * self.F_total / self.V_total
        D1 = self.phi / (1 - self.ny) * self.F_total / self.V_total
        if D1 > self.D1_max:
            return np.nan
        return D1

    def calculate_D2(self):
        if np.isnan(self.D1):
            return np.nan
        if np.isclose(self.phi, 1.0):
            return np.nan
        if np.isclose(self.ny, 0):
            return np.nan
        # D2 = 1 / (1 - self.ny) * self.F_total / self.V_total
        D2 = self.F_total / self.V_total / self.ny
        if self.growth_flags[
            1
        ]:  # if growth in stage 2, then D2 must be smaller than mu_s2 - delta
            # D2 must be larger than mu_s2 - delta i think
            if D2 <= (self.mu_s2 - self.delta):
                return np.nan
        if np.isfinite(D2):
            return D2
        else:
            return np.nan

    def mu_stage2(self):
        mu_list = []
        for i in range(1, self.N_reactors):
            if self.growth_flags[i]:
                mu_list.append(self.mu_max * self.stage2_mu_factor)
            else:
                mu_list.append(0)
        if len(mu_list) == 1:
            return mu_list[0]
        return mu_list

    def check_steady_state(self, dydt):
        return np.linalg.norm(dydt) < 1e-8

    def simulate_process(
        self,
        cascade=True,
        steady_state=False,
        only_stage1=False,
        return_trajectory=True,
    ):
        t_span = self.t_span.copy()
        max_time = 3e3
        max_iter = 100
        if return_trajectory:
            T_segments = []
            Y_segments = []
        if self.N_reactors > 2:
            odes = self.multi_stage_ODEs
            y0 = self.growth_initial_state.copy() + [0, 0, 0] * (self.N_reactors - 1)
        else:
            odes = self.cascade_ODEs if cascade else self.one_stage_ODEs
            if cascade and not only_stage1:
                y0 = self.initial_state.copy()
            else:
                y0 = self.growth_initial_state.copy()
        for i in range(max_iter):
            sol = solve_ivp(
                fun=odes,
                t_span=(t_span[0], t_span[-1]),
                y0=y0,
                rtol=1e-5,
                atol=1e-8,
                method="BDF",
            )
            if not sol.success:
                raise RuntimeError(sol.message)
            y_last = sol.y[:, -1]
            dydt = odes(0, y_last)
            # append all points if first segment, else skip first point to avoid duplicates
            if return_trajectory:
                if i == 0:
                    T_segments.append(sol.t)
                    Y_segments.append(sol.y)
                else:
                    T_segments.append(sol.t[1:])
                    Y_segments.append(sol.y[:, 1:])

            if steady_state and self.check_steady_state(dydt):
                break

            if t_span[-1] > max_time:
                break

            # extend t_span for next iteration
            t_span = np.linspace(t_span[-1], t_span[-1] * 1.5, len(t_span))
            y0 = y_last  # continue from last state

        if return_trajectory:
            # concatenate safely
            T = np.concatenate(T_segments)
            Y = np.hstack(Y_segments)
            return T, Y
        else:
            return y_last
