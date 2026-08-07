"""
Local stability analysis of steady states.

The cascade is unidirectional (no recycle), so the stage-1 equations depend
only on stage-1 states. The full 6x6 Jacobian is therefore block lower
triangular and its spectrum is the union of the spectra of J1 and J2. Each
block can be analysed on its own.

For now, one route to a Jacobian is provided:

  * analytic  -- fast, but only valid for the base case (Monod growth in
                 stage 1, no inhibition, growth-arrested stage 2, N = 2).
`dominant_eigenvalue` picks the right one automatically.
"""

import numpy as np

LAMBDA_MAX_THRESHOLD = -0.01

_FD_REL_STEP = np.sqrt(np.finfo(float).eps)


class ClampedStateError(ValueError):
    """Raised when a state sits on a non-smooth boundary of the ODE system."""


def _fd_step(state):
    """Per-component step size, scaled to each state variable's magnitude."""
    return _FD_REL_STEP * np.maximum(np.abs(np.asarray(state, dtype=float)), 1.0)


def check_smooth(model, state, margin):
    """
    The ODE system contains max()/threshold clamps (substrate floored at 0,
    inhibition factors floored at 0, stage-2 substrate zeroing). Central
    differences straddle those boundaries and return meaningless numbers,
    so refuse to differentiate within `margin` of one.
    """
    x, s, p = state[0], state[1], state[2]
    if s <= margin[1]:
        raise ClampedStateError(f"s1={s:.3e} is at the substrate floor")
    if model.is_biomass_inhibited and x >= model.x_max - margin[0]:
        raise ClampedStateError(f"x1={x:.3e} is at x_max={model.x_max:.3e}")
    if model.is_product_inhibited and p >= model.p_max - margin[2]:
        raise ClampedStateError(f"p1={p:.3e} is at p_max={model.p_max:.3e}")


def jacobian_fd(f, state):
    """
    Central-difference Jacobian of f at state.

    f must accept and return sequences of the same length. Costs 2n
    evaluations of f (6 for a 3-state stage).
    """
    x0 = np.asarray(state, dtype=float)
    n = x0.size
    h = _fd_step(x0)
    J = np.empty((n, n))
    for j in range(n):
        e = np.zeros(n)
        e[j] = h[j]
        J[:, j] = (np.asarray(f(x0 + e)) - np.asarray(f(x0 - e))) / (2.0 * h[j])
    return J


def stage1_jacobian_analytic(model, state):
    """
    Analytic stage-1 Jacobian. Base case only: Monod growth, no inhibition.

    ODEs:
        dx/dt = (mu - delta - D1) x
        ds/dt = D1 (sf1 - s) - sigma x
        dp/dt = (pi1 mu + pi0) x - D1 p
    """
    if model.is_substrate_inhibited or model.is_biomass_inhibited or model.is_product_inhibited:
        raise ValueError(
            "analytic stage-1 Jacobian is only valid without inhibition; "
            "use the finite-difference route"
        )
    x1, s1, _p1 = state
    D1 = model.D1
    mu = model.limit_rate(model.mu_max, state)
    sigma = model.sigma(0, mu, s1)

    dmu_ds = model.mu_max * model.Ks / (model.Ks + s1) ** 2
    dsigma_ds = dmu_ds * (1.0 / model.Yxs_1 + model.pi1_s1 / model.Yps_1)

    J = np.zeros((3, 3))
    J[0, 0] = mu - model.delta - D1
    J[0, 1] = dmu_ds * x1
    J[0, 2] = 0.0

    J[1, 0] = -sigma
    J[1, 1] = -x1 * dsigma_ds - D1       # the -D1 dilution term
    J[1, 2] = 0.0

    J[2, 0] = model.pi0_s1 + mu * model.pi1_s1
    J[2, 1] = x1 * model.pi1_s1 * dmu_ds
    J[2, 2] = -D1
    return J


def stage2_jacobian_analytic(model, state):
    """
    Analytic stage-2 Jacobian for the two-reactor case.

    Valid while production and maintenance in stage 2 are substrate
    independent (zero order), which makes the block lower triangular.
    Growth in stage 2 (mu_s2 != 0) is supported.
    """
    if model.N_reactors != 2:
        raise ValueError(
            "analytic stage-2 Jacobian assumes N_reactors == 2; the multistage "
            "path applies a substrate limiter to production, so sigma2 depends "
            "on s2. Use the finite-difference route."
        )
    _x2, s2, _p2 = state
    D2 = model.D2
    mu2 = model.mu_s2
    sigma = model.sigma(1, mu2, s2)
    production = model.production(1, mu2, s2)

    J = np.zeros((3, 3))
    J[0, 0] = mu2 - model.delta - D2       # mu_s2 now included
    J[1, 0] = -sigma
    J[1, 1] = -D2
    J[2, 0] = production
    J[2, 2] = -D2
    return J


def _needs_fd(model):
    return bool(
        model.is_substrate_inhibited
        or model.is_biomass_inhibited
        or model.is_product_inhibited
        or model.N_reactors != 2
    )


def stage1_jacobian(model, state, force_fd=False):
    """Stage-1 Jacobian, analytic where valid and finite-difference otherwise."""
    if force_fd or _needs_fd(model):
        check_smooth(model, state, _fd_step(state))
        return jacobian_fd(lambda z: model.cascade_ODEs(0, list(z)), state)
    return stage1_jacobian_analytic(model, state)


def dominant_eigenvalue(model, state, stage=1, force_fd=False):
    """
    Largest real part among the eigenvalues of the given stage's Jacobian.

    Returns nan if the Jacobian cannot be formed (state on a clamp boundary,
    or non-finite state), so callers can reject the point explicitly rather
    than acting on a meaningless number.
    """
    state = np.asarray(state, dtype=float)
    if not np.all(np.isfinite(state)):
        return np.nan
    try:
        if stage == 1:
            J = stage1_jacobian(model, state, force_fd=force_fd)
        else:
            J = stage2_jacobian_analytic(model, state)
    except (ClampedStateError, ValueError, ZeroDivisionError, FloatingPointError):
        return np.nan
    if not np.all(np.isfinite(J)):
        return np.nan
    return float(np.max(np.linalg.eigvals(J).real))


def is_robust(lambda_max, threshold=LAMBDA_MAX_THRESHOLD):
    """A steady state is accepted only if it relaxes fast enough."""
    return bool(np.isfinite(lambda_max) and lambda_max < threshold)