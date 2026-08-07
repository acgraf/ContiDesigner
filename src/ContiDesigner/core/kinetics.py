from ..utils import helpers

EPS = 1e-5


def biomass_inhibition(model, x):
    """Biomass inhibition factor."""
    # ensure non-negative values
    factor = max(0.0, 1 - x / model.x_max)
    return factor**model.n1


def product_inhibition(model, p):
    """Product inhibition factor."""
    # ensure non-negative values
    factor = max(0.0, 1 - p / model.p_max)
    return factor**model.n2


def substrate_inhibition(model, s):
    """Substrate inhibition factor."""
    S = max(0.0, s)
    limit = S / (model.Ks + S + S**2 / model.Ki)
    return limit


def substrate_limit_MM(model, substrate):
    """Monod substrate limitation factor."""
    S = max(0, substrate)
    return S / (model.Ks + S)


def limit_rate(model, rate, state):
    biomass, substrate, product = state

    substrate_factor = (
        substrate_inhibition(model, substrate)
        if model.is_substrate_inhibited
        else substrate_limit_MM(model, substrate)
    )

    biomass_factor = (
        biomass_inhibition(model, biomass) if model.is_biomass_inhibited else 1.0
    )

    product_factor = (
        product_inhibition(model, product) if model.is_product_inhibited else 1.0
    )

    return rate * substrate_factor * biomass_factor * product_factor


def sigma(model, i=1, mu=None, s=1):
    """Calculate substrate consumption coefficient."""
    if i == 0:
        Yxs = model.Yxs_1
        Yps = model.Yps_1
        Yas = model.Yas_1
        m = model.m_1
    else:
        Yxs = model.Yxs_2
        Yps = model.Yps_2
        Yas = model.Yas_2
        m = model.m_2
    return (
        helpers.save_divide(mu, Yxs)
        + helpers.save_divide(production(model, i, mu, s), Yps)
        + helpers.save_divide(m, Yas)
    )


def production(model, i=1, mu=None, s=1):
    """Calculate product formation rate"""
    if model.N_reactors == 2:
        if i == 0:
            pi0, pi1 = model.pi0_s1, model.pi1_s1
        else:
            pi0, pi1 = model.pi0_s2, model.pi1_s2
        limit = 1  # no limit
    else:
        # We do not optimize multistage reactors with n>2, so we need to make sure the substrate does not go below 0.
        pi0 = model.pi0s[i]
        pi1 = model.pi1s[i]
        limit = s / (1e-5 + s)
    return (pi1 * mu + pi0) * limit
