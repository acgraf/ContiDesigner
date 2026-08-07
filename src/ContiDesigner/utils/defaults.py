DEFAULT_PROCESSES = {
    "PHB": {
        "mu_max": 0.25,
        "delta": 0.0001,
        "Ks": 1.17,
        "Yxs_1": 0.55,
        "Yps_1": 0.477,
        "Yas_1": 1,
        "pi0_s1": 0,
        "pi1_s1": 0.13,
        "pi0_s2": 0.23,
        "m_1": 0.064,
        "sf1": 67,
        "V_total": 9,
        "sf2_max": 500,
    },
    "LA": {
        "mu_max": 0.48,
        "delta": 0,
        # "Ks": 0.035,  # this is the small km from the paper
        "Ks": 1.2,
        "Yxs_1": 0.4,
        "Yps_1": 1,  # = 2 * MW_lactic_acid / MW_glucose # g/g
        "Yas_1": 0,
        "pi0_s1": 0.02,
        "pi1_s1": 2.2,
        "pi0_s2": 0.02,
        "m_1": 0,
        # it's anaerobic fermentation, so cell maintenance is coupled to
        # the production of lactic acid
        "sf1": 60,
        "V_total": 1,
        "is_substrate_inhibited": True,
        "is_biomass_inhibited": True,
        "is_product_inhibited": True,
        "p_max": 98.0,
        "x_max": 30.0,
        "Ki": 164,
        "sf2_max": 500,
    },
}

DEFAULT_PROCESS_INFO = {
    "PHB": {
        "title": "Polyhydroxybutyrate production",
        "organism": "Cupriavidus necator",
        "description": (
            "Case study based on multi-stage continuous fermentation "
            "with nitrogen-limited production stages."
        ),
        "reference": ["Atlić et al. (2011)", "Horvat et al. (2013)"],
        "reference_url": [
            "https://link.springer.com/article/10.1007/s00253-011-3260-0",
            "https://link.springer.com/article/10.1007/s00449-012-0852-8",
        ],
    },
    "LA": {
        "title": "Lactic acid production",
        "organism": None,
        "description": (
            "Case study adapted from a continuous fermentation model "
            "including substrate, product, and biomass inhibition effects."
        ),
        "reference": ["Gordeeva et al. (2019)"],
        "reference_url": [
            "https://link.springer.com/article/10.1134/S0040579519040183"
        ],
    },
}
