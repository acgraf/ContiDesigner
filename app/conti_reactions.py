reaction_definitions_onestage = {
    "X_s1":[
        {
            "id":"x1_growth",
            "rate":"mu_max * X_s1",
        },
        {
            "id":"x1_death",
            "rate":"-delta * X_s1",
        },
        {
            "id":"x1_dilution",
            "rate":"- D_total * X_s1",
        },
        ],

    "S_s1":[
        {
            "id":"s1_feed",
            "rate":" D_total * sf_onestage",
        },
        {
            "id":"s1_consumption",
            "rate":"- (mu_max / Yxs_1 + (pi1_s1 * mu_max + pi0_s1)/Yps_1 + m_1 /Yas_1)* X_s1",
        },
        {
            "id":"s1_dilution",
            "rate":"- D_total * S_s1",
        },
        ],

    "P_s1":[
        {
            "id":"p1_production",
            "rate":"(pi1_s1 * mu_max + pi0_s1) * X_s1",
        },
        {
            "id":"p1_dilution",
            "rate":"- D_total * P_s1",
        },
        ],
}

reaction_definitions_cascade = {
    "X_s1":[
        {
            "id":"x1_growth",
            "rate":"mu_max * X_s1",
        },
        {
            "id":"x1_death",
            "rate":"-delta * X_s1",
        },
        {
            "id":"x1_dilution",
            "rate":"-phi * D_total/(1 - ny) * X_s1",
        },
        ],

    "S_s1":[
        {
            "id":"s1_feed",
            "rate":"phi * D_total/(1 - ny) * sf1",
        },
        {
            "id":"s1_consumption",
            "rate":"- (mu_max / Yxs_1 + "
            "(pi1_s1 * mu_max + pi0_s1)/Yps_1 + m_1 /Yas_1)* X_s1",
        },
        {
            "id":"s1_dilution",
            "rate":"-phi * D_total/(1 - ny) * S_s1",
        },
        ],

    "P_s1":[
        {
            "id":"p1_production",
            "rate":"(pi1_s1*mu_max + pi0_s1) * X_s1",
        },
        {
            "id":"p1_dilution",
            "rate":"-phi * D_total/(1 - ny) * P_s1",
        },
        ],
    "X_s2":[
        {
            "id":"x2_growth",
            "rate":"mu_s2 * X_s2",
        },
        {
            "id":"x2_feed",
            "rate":"phi * D_total / ny * X_s1",
        },
        {
            "id":"x2_death",
            "rate":"-delta * X_s2",
        },
        {
            "id":"x2_dilution",
            "rate":"- D_total/ny * X_s2",
        },
        ],

    "S_s2":[
        {
            "id":"s2_feed1",
            "rate":"phi * D_total / ny  * S_s1",
        },
        {
            "id":"s2_feed2",
            "rate":"D_total * (1-phi) / ny  * sf2",
        },
        {
            "id":"s2_consumption",
            "rate":"- (mu_s2/Yxs_2 + "
            "(pi1_s2 * mu_s2 + pi0_s2)/Yps_2 + m_2/Yas_2) * X_s2",  
        },
        {
            "id":"s2_dilution",
            "rate":"- D_total/ny * S_s2",
        },
        ],

    "P_s2":[
        {
            "id":"p2_production",
            "rate":"(pi1_s2 * mu_s2 + pi0_s2) * X_s2",
        },
        {
            "id":"p2_feed",
            "rate":"phi * D_total / ny * P_s1",
        },
        {
            "id":"p2_dilution",
            "rate":"- D_total/ny * P_s2",
        },
        ],
}
