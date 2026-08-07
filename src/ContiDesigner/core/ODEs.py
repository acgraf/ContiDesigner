from ..utils import helpers
import numpy as np


def x1_ODE(model, state, mu, onestage=False):
    x, s, p = state[0:3]
    if onestage:
        dxdt = +mu * x - (model.delta + model.D_total) * x
        return dxdt
    else:
        if model.N_reactors == 2:
            phi = model.phi
            ny = model.ny
        elif model.N_reactors > 2:
            phi = model.phis[0]
            ny = model.nys[0]
        growth = +mu * x
        death = -model.delta * x
        dilution = -phi * helpers.save_divide(model.D_total, (1 - ny)) * x
        dxdt_s1 = growth + death + dilution
        return dxdt_s1


def s1_ODE(model, state, mu, onestage=False):
    x, s, p = state[0:3]
    if onestage:
        dsdt = -model.sigma(0, mu, s) * x + model.D_total * (model.sf_onestage - s)
        return dsdt
    else:
        if model.N_reactors == 2:
            phi = model.phi
            ny = model.ny
        elif model.N_reactors > 2:
            phi = model.phis[0]
            ny = model.nys[0]
        consumption = -model.sigma(0, mu, s) * x
        feed = +phi * helpers.save_divide(model.D_total, (1 - ny)) * model.sf1
        dilution = -phi * helpers.save_divide(model.D_total, (1 - ny)) * s
        dsdt_s1 = consumption + feed + dilution
        return dsdt_s1


def p1_ODE(model, state, mu, onestage=False):
    x, s, p = state[0:3]
    if onestage:
        dpdt = +model.production(0, mu, s) * x - model.D_total * p
        return dpdt
    else:
        if model.N_reactors == 2:
            phi = model.phi
            ny = model.ny
        else:
            phi = model.phis[0]
            ny = model.nys[0]
        
        production = +model.production(0, mu, s) * x
        dilution = -phi * helpers.save_divide(model.D_total, (1 - ny)) * p

        dpdt_s1 = production + dilution

        return dpdt_s1


def x2_ODE(model, state, i=1):
    x_s1, s_s1, p_s1, x_s2, s_s2, p_s2 = state
    if model.N_reactors == 2:
        phi = model.phi
        ny = model.ny
        mu_s2 = model.mu_s2
        dilution = - helpers.save_divide(model.D_total, ny) * x_s2
        inflow = + helpers.save_divide(model.D_total, ny) * phi * x_s1
    else:
        mu_s2 = model.mu_s2[i - 1]
        dilution = - model.Fs[i] / model.Vs[i] * x_s2
        inflow = + model.Fs[i-1] / model.Vs[i] * x_s1
    growth = + mu_s2 * x_s2
    death = - model.delta * x_s2
    dxdt_s2 = growth + death + dilution + inflow
    return dxdt_s2


def s2_ODE(model, state, i=1):
    x_s1, s_s1, p_s1, x_s2, s_s2, p_s2 = state
    if model.N_reactors == 2:
        phi = model.phi
        ny = model.ny
        mu_s2 = model.mu_s2
        sf2 = model.sf2
        dilution = - helpers.save_divide(model.D_total, ny) * s_s2
        inflow = model.D_total / ny * phi * s_s1
        feed = + model.D_total / ny * (1 - phi) * sf2
    else:
        mu_s2 = model.mu_s2[i - 1]
        sf2 = model.sfs[i]
        dilution = - model.Fs[i] / model.Vs[i] * s_s2
        inflow = + model.Fs[i-1] / model.Vs[i] * s_s1
        feed = + (model.Fs[i] - model.Fs[i-1]) / model.Vs[i] * sf2

    # s_s2 = max(s_s2, 1e-6)  # prevent negative substrate
    consumption = - model.sigma(i, mu_s2, s_s2) * x_s2
    dsdt_s2 = (
        consumption
        + dilution
        + inflow
        + feed
    )
    if s_s2 <= 1e-6 and dsdt_s2 < 1e-6:
        dsdt_s2 = 0.0
    return dsdt_s2


def p2_ODE(model, state, i=1):
    x_s1, s_s1, p_s1, x_s2, s_s2, p_s2 = state
    if model.N_reactors == 2:
        phi = model.phi
        ny = model.ny
        mu_s2 = model.mu_s2
        inflow = + phi * model.D_total / ny * p_s1 
        dilution = - helpers.save_divide(model.D_total, ny) * p_s2
    else:
        phi = model.phis[i]
        ny = model.nys[i]
        mu_s2 = model.mu_s2[i - 1]
        inflow = + model.Fs[i-1] / model.Vs[i] * p_s1
        dilution = - model.Fs[i] / model.Vs[i] * p_s2
    s_s2 = max(s_s2, 1e-6)  # prevent negative substrate
    production = + model.production(i, mu_s2, s_s2) * x_s2 
    dpdt_s2 = (
        production
        + inflow
        + dilution
    )
    return dpdt_s2


def multi_stage_ODEs(model, t, state):
    N = model.N_reactors
    derivatives = []
    for i in range(N):
        idx = 3 * i
        if i == 0:
            local_state = state[idx : idx + 3]
            mu = model.limit_rate(model.mu_max, local_state)
            dxdt = x1_ODE(model, local_state, mu)
            dsdt = s1_ODE(model, local_state, mu)
            dpdt = p1_ODE(model, local_state, mu)
        else:
            # previous + current
            prev_idx = 3 * (i - 1)
            prev_state = state[prev_idx : prev_idx + 3]
            curr_state = state[idx : idx + 3]
            combined_state = np.concatenate([prev_state, curr_state])
            combined_state = [
                max(0, i) for i in combined_state
            ]  # prevent negative values

            dxdt = x2_ODE(model, combined_state, i=i)
            dsdt = s2_ODE(model, combined_state, i=i)
            dpdt = p2_ODE(model, combined_state, i=i)
        derivatives.extend([dxdt, dsdt, dpdt])
    return derivatives


def cascade_ODEs(model, t, state):
    """
    Defines the system of ODEs.
    Returns the rate of change of each state variable.
    """
    mu_s1 = model.limit_rate(model.mu_max, state[0:3])
    dxdt_s1 = x1_ODE(model, state, mu_s1)
    dsdt_s1 = s1_ODE(model, state, mu_s1)
    dpdt_s1 = p1_ODE(model, state, mu_s1)
    # stop here if state has length 3
    if len(state) == 3:
        return [dxdt_s1, dsdt_s1, dpdt_s1]
    dxdt_s2 = x2_ODE(model, state, i=1)
    dsdt_s2 = s2_ODE(model, state, i=1)
    dpdt_s2 = p2_ODE(model, state, i=1)
    return [
        dxdt_s1,
        dsdt_s1,
        dpdt_s1,
        dxdt_s2,
        dsdt_s2,
        dpdt_s2,
    ]


def one_stage_ODEs(model, t, state):
    mu = model.limit_rate(model.mu_max, state)
    dxdt = x1_ODE(model, state, mu, onestage=True)
    dsdt = s1_ODE(model, state, mu, onestage=True)
    dpdt = p1_ODE(model, state, mu, onestage=True)
    return [dxdt, dsdt, dpdt]
