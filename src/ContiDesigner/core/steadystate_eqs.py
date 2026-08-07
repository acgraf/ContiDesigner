from ..utils import helpers
import numpy as np


def calculate_x_OS(model):
    D_total = model.D_total
    numerator = model.sf_onestage * model.mu_max * (D_total - model.D_max)
    denominator = (
        (model.D_max + model.delta)
        * (D_total + model.delta - model.mu_max)
        * (
            (
                helpers.save_divide(D_total + model.delta, model.Yxs_1)
                + helpers.save_divide(
                    (model.pi0_s1 + (D_total + model.delta) * model.pi1_s1),
                    model.Yps_1,
                )
                + helpers.save_divide(model.m_1, model.Yas_1)
            )
            / D_total
        )
    )
    xx = helpers.save_divide(numerator, denominator)
    return xx


def calculate_p_OS(model, x1):
    D_total = model.D_total
    numerator = model.pi0_s1 + model.pi1_s1 * (D_total + model.delta)
    denominator = D_total
    pp = x1 * helpers.save_divide(numerator, denominator)
    return pp


def calculate_s_OS(model):
    D_total = model.D_total
    numerator = (
        model.sf_onestage
        * (D_total + model.delta)
        * (model.D_max + model.delta - model.mu_max)
    )
    denominator = (model.D_max + model.delta) * (
        D_total + model.delta - model.mu_max
    )
    ss = helpers.save_divide(numerator, denominator)
    return ss


# with substrate inhibition
def calculate_x_OS_SI(model):
    D_total = model.D_total
    D_delta = D_total + model.delta
    numerator1 = D_total * (
        D_delta * (2 * model.sf_onestage + model.Ki) - model.Ki * model.mu_max
    )
    sqrt_term = model.Ki**2 * (D_total + model.delta - model.mu_max) ** 2 + (
        4
        * model.sf_onestage
        * D_delta**2
        * (
            (model.Ki + model.sf_onestage) * (model.D_max + model.delta)
            - model.Ki * model.mu_max
        )
    ) / (model.D_max + model.delta)
    numerator2 = D_total * np.sqrt(sqrt_term)
    denominator = (
        2
        * D_delta
        * (
            helpers.save_divide(D_delta, model.Yxs_1)
            + helpers.save_divide(model.m_1, model.Yas_1)
            + helpers.save_divide((D_delta * model.pi1_s1 + model.pi0_s1), model.Yps_1)
        )
    )
    xx = helpers.save_divide(numerator1 + numerator2, denominator)
    return xx


def calculate_p_OS_SI(model, x1):
    return calculate_p_OS(model, x1=x1)


def calculate_s_OS_SI(model):
    D_total = model.D_total
    D_delta = D_total + model.delta
    Dmax_delta = model.D_max + model.delta
    sqrt_term = model.Ki**2 * (D_total + model.delta - model.mu_max) ** 2 + (
        4
        * model.sf_onestage
        * D_delta**2
        * ((model.Ki + model.sf_onestage) * Dmax_delta - model.Ki * model.mu_max)
    ) / (Dmax_delta)
    sqrt_term = max(sqrt_term, 0) 
    numerator = -(
        model.Ki * (D_total + model.delta - model.mu_max) + np.sqrt(sqrt_term)
    )
    denominator = 2 * D_delta
    ss = helpers.save_divide(numerator, denominator)
    return ss


# CASCADE

# with Michaelis Menten kinetics


def calculate_x1(model):
    if model.N_reactors > 2:
        phi, ny = model.phis[0], model.nys[0]
        pi0_s1, pi1_s1 = model.pi0s[0], model.pi1s[0]
    else:
        phi = model.phi
        ny = model.ny
        pi0_s1, pi1_s1 = model.pi0_s1, model.pi1_s1

    D_total = model.D_total
    numerator = (
        model.sf1
        * model.mu_max
        * phi
        * (model.D_max * (ny - 1) + D_total * phi)
    )
    denominator = (
        (model.D_max + model.delta)
        * ((model.delta - model.mu_max) * (ny - 1) - D_total * phi)
        * (
            (ny - 1)
            * (
                helpers.save_divide(model.m_1, model.Yas_1)
                + helpers.save_divide(model.delta, model.Yxs_1)
                + helpers.save_divide(
                    (pi0_s1 + model.delta * pi1_s1),
                    model.Yps_1,
                )
            )
            / D_total
            - (
                helpers.save_divide(1, model.Yxs_1)
                + helpers.save_divide(pi1_s1, model.Yps_1)
            )
            * phi
        )
    )
    xx = helpers.save_divide(numerator, denominator)
    return xx


def calculate_s1(model):
    if model.N_reactors > 2:
        phi, ny = model.phis[0], model.nys[0]
    else:
        phi = model.phi
        ny = model.ny
    D_total = model.D_total
    numerator = (
        model.sf1
        * (model.D_max + model.delta - model.mu_max)
        * (model.delta * (ny - 1) - D_total * phi)
    )
    denominator = (model.D_max + model.delta) * (
        (model.delta - model.mu_max) * (ny - 1) - D_total * phi
    )
    ss = helpers.save_divide(numerator, denominator)
    return ss


def calculate_p1(model, x1):
    if model.N_reactors > 2:
        phi, ny = model.phis[0], model.nys[0]
        pi0_s1, pi1_s1 = model.pi0s[0], model.pi1s[0]
    else:
        phi = model.phi
        ny = model.ny
        pi0_s1, pi1_s1 = model.pi0_s1, model.pi1_s1
    D_total = model.D_total
    D_phi = D_total * phi
    numerator = (1 - ny) * (
        pi0_s1 + model.delta * pi1_s1
    ) + D_phi * pi1_s1
    denominator = D_phi
    pp = x1 * helpers.save_divide(numerator, denominator)
    return pp


# with substrate inhibition


def calculate_x1_SI(model):
    if model.N_reactors > 2:
        phi, ny = model.phis[0], model.nys[0]
        pi0_s1, pi1_s1 = model.pi0s[0], model.pi1s[0]
    else:
        phi = model.phi
        ny = model.ny
        pi0_s1, pi1_s1 = model.pi0_s1, model.pi1_s1
    D_total = model.D_total
    ny_1 = ny - 1
    D_phi = D_total * phi
    Dmax_delta = model.D_max + model.delta
    sigma_term = (
        helpers.save_divide(model.m_1, model.Yas_1)
        + helpers.save_divide(model.delta, model.Yxs_1)
        + helpers.save_divide(pi0_s1 + model.delta * pi1_s1, model.Yps_1)
    )
    numerator1 = (D_phi - model.delta * ny_1) * (
        2 * model.sf1 + model.Ki
    ) + model.Ki * model.mu_max * ny_1
    sqrt_term_1 = (
        4
        * model.sf1
        * ((model.Ki + model.sf1) * Dmax_delta - model.Ki * model.mu_max)
        * (model.delta * (-ny_1) + D_phi) ** 2
    ) / Dmax_delta
    sqrt_term_2 = (
        model.Ki**2 * (model.delta + model.mu_max * ny_1 - model.delta * ny + D_phi) ** 2
    )
    numerator2 = np.sqrt(sqrt_term_1 + sqrt_term_2)
    denominator = (
        2
        * (model.delta * helpers.save_divide(-ny_1, D_phi) + 1)
        * (
            -(ny_1 * sigma_term)
            + D_total
            * (
                helpers.save_divide(1, model.Yxs_1)
                + helpers.save_divide(pi1_s1, model.Yps_1)
            )
            * phi
        )
    )
    xx = helpers.save_divide(numerator1 + numerator2, denominator)
    return xx


def calculate_p1_SI(model, x1):
    return calculate_p1(model, x1=x1)


def calculate_s1_SI(model):
    if model.N_reactors > 2:
        phi, ny = model.phis[0], model.nys[0]
    else:
        phi = model.phi
        ny = model.ny
    D_total = model.D_total
    ny_1 = ny - 1
    D_phi = D_total * phi
    Dmax_delta = model.D_max + model.delta
    sqrt_term_1 = (
        4
        * model.sf1
        * ((model.Ki + model.sf1) * Dmax_delta - model.Ki * model.mu_max)
        * (model.delta * (-ny_1) + D_phi) ** 2
    ) / Dmax_delta
    sqrt_term_2 = (
        model.Ki**2
        * (model.delta * (-ny_1) + model.mu_max * ny_1 + model.delta * ny + D_phi) ** 2
    )
    numerator = -(
        model.Ki * (D_phi + model.delta * (-ny_1) + model.mu_max * ny_1)
        + np.sqrt(sqrt_term_1 + sqrt_term_2)
    )
    denominator = 2 * (D_phi + model.delta * (-ny_1))
    ss = helpers.save_divide(numerator, denominator)
    return ss


# stage 2 calculations


def calculate_x2(model, x1, i=1):
    if model.N_reactors > 2:
        phi, ny = model.phis[i], model.nys[i]
        mu_s2 = model.mu_s2[i-1]
    else:
        phi = model.phi
        ny = model.ny
        mu_s2 = model.mu_s2
    D_total = model.D_total
    numerator = D_total * x1 * phi
    denominator = D_total + model.delta * ny - mu_s2 * ny
    xx2 = helpers.save_divide(numerator, denominator)
    return xx2


def calculate_s2(model, x1, s1, i=1):
    if model.N_reactors > 2:
        phi, ny = model.phis[i], model.nys[i]
        pi0_s2, pi1_s2 = model.pi0s[i], model.pi1s[i]
        mu_s2 = model.mu_s2[i-1]
        sf2 = model.sfs[i]
    else:
        phi, ny = model.phi, model.ny
        pi0_s2, pi1_s2 = model.pi0_s2, model.pi1_s2
        mu_s2 = model.mu_s2
        sf2 = model.sf2
    D_total = model.D_total
    if model.growth_flags[i]: # if growth in stage 2, then we need to account for the fact that mu_s2 is not zero
        numerator1 = D_total * s1 * phi
        denominator = D_total + (model.delta - mu_s2) * ny
        numerator2 = (
            (
                helpers.save_divide(model.m_2, model.Yas_2) * x1
                + s1 * (mu_s2 - model.delta)
                + x1
                * (
                    helpers.save_divide(mu_s2, model.Yxs_2)
                    + helpers.save_divide(
                        pi0_s2 + mu_s2 * pi1_s2,
                        model.Yps_2,
                    )
                )
            )
            * ny
            * phi
        )
        ss2 = (
            sf2 * (1 - phi)
            + helpers.save_divide(numerator1, denominator)
            - helpers.save_divide(numerator2, denominator)
        )
        return ss2
    else:
        numerator = s1 * (
            helpers.save_divide(D_total, ny) + model.delta
        ) - x1 * (
            helpers.save_divide(model.m_2, model.Yas_2)
            + helpers.save_divide(pi0_s2, model.Yps_2)
        )
        denominator = D_total + model.delta * ny
        ss2 = sf2 * (1 - phi) + (phi * ny * helpers.save_divide(numerator, denominator))
        return ss2


def calculate_p2(model, x1, p1, i=1):
    if model.N_reactors > 2:
        phi, ny = model.phis[i], model.nys[i]
        pi0_s2, pi1_s2 = model.pi0s[i], model.pi1s[i]
        mu_s2 = model.mu_s2[i-1]
    else:
        phi, ny = model.phi, model.ny
        pi0_s2, pi1_s2 = model.pi0_s2, model.pi1_s2
        mu_s2 = model.mu_s2
    D_total = model.D_total
    numerator = pi0_s2 + mu_s2 * pi1_s2
    denominator = helpers.save_divide(D_total, ny) + (model.delta - mu_s2)
    pp2 = phi * (p1 + x1 * helpers.save_divide(numerator, denominator))
    return pp2
