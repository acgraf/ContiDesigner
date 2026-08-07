from dash import dcc, html
import dash_bootstrap_components as dbc
from app.layout.helper import symbols


def render_ODE(x_var="x", t_var="t", rhs=""):
    return dcc.Markdown(
        rf"""
        $$
        \begin{{aligned}}
        \frac{{\mathrm{{d}}{x_var}}}{{\mathrm{{d}}{t_var}}}&={rhs}
        \end{{aligned}}
        $$
        """,
        mathjax=True,
    )


x_1_rs = r"\mu X_1 - \left(\delta + \frac{\phi D}{1-\nu}\right) X_1"

x_2_rs = r"\frac{\phi D}{\nu} X_1 - \left( \delta + \frac{D}{\nu}\right)"

p1_rs = r"\pi X_1 - \frac{\phi D}{1-\nu}P_1"

p2_rs = r"\frac{\phi D}{\nu} P_1 + \pi X_2 - \frac{D}{\nu} P_2"

s1_rs = r"-\sigma X_1 + \frac{\phi D}{1-\nu}\left(S^\mathrm{F}_1 - S_1\right)"

s2_rs = (
    r"\frac{\phi D}{\nu} S_1 - \sigma X_2 \\"
    r"& \phantom{-}+ \frac{D}{\nu} \left[\left(1-\phi\right)S^\mathrm{F}_2 - S_2\right]"
)

ODE_style = {
    "display": "flex",
    "marginTop": "0.1em",
    "fontSize": "1rem",
    "overflowX": "auto",
    "maxWidth": "100%",
}

inhib_style = {
    "marginLeft": "1rem",
    "marginTop": "0.1rem",
    "display": "flex",
    "fontSize": "1rem",
}

ODEs = {}
ODEs["x_1"] = html.P(
    [render_ODE("X_1", "t", x_1_rs)],
    style=ODE_style,
)

ODEs["x_2"] = html.P(
    [render_ODE("X_2", "t", x_2_rs)],
    style=ODE_style,
)

ODEs["p_1"] = html.P(
    [
        render_ODE("P_1", "t", p1_rs),
    ],
    style=ODE_style,
)

ODEs["p_2"] = html.P(
    [
        render_ODE("P_2", "t", p2_rs),
    ],
    style=ODE_style,
)

ODEs["s_1"] = html.P(
    [
        render_ODE("S_1", "t", s1_rs),
    ],
    style=ODE_style,
)

ODEs["s_2"] = html.P(
    [
        render_ODE("S_2", "t", s2_rs),
    ],
    style=ODE_style,
)


mm = r"\frac{S}{K^\mathrm{S} + S}"
s_inh = r"\frac{S}{K^\mathrm{S} + S + \frac{S^2}{K^\mathrm{I}}}"
b_inh = r"\left(1 - \frac{X}{X^\mathrm{max}}\right)^{n_1}"
p_inh = r"\left(1 - \frac{P}{P^\mathrm{max}}\right)^{n_2}"


# ---------------------------------------------------------
def make_equation_card(title, children, style=None):
    """
    Create a standardized equation information card.

    Parameters
    ----------
    title : str
        Card header title.
    latex_body : str
        LaTeX equation content (without $$ wrappers).
    style : dict, optional
        Additional style dictionary for the Markdown container.
    """

    card_style = {
        "marginBottom": "1rem",
    }
    className = "shadow-sm justify-content-center"

    if style:
        card_style.update(style)

    return dbc.Card(
        [
            dbc.CardHeader(
                html.H5(title, style={"margin": 0}), style={"borderBottom": "none"}
            ),
            dbc.CardBody(children if isinstance(children, list) else [children]),
        ],
        style=card_style,
        className=className,
    )


overview_panel = make_equation_card(
    "Core model",
    html.Div(
        [
            dcc.Markdown(
                r"""
            **Model structure**

            The model consists of six ordinary differential equations
            describing biomass, product, and substrate dynamics in each stage.

            Growth is modeled with Monod kinetics, and product formation follows Luedeking-Piret kinetics. 
            Substrate consumption is derived from growth, production, and maintenance requirements.


            **Monod kinetics:**
            $$
            \frac{S}{K^\mathrm{S} + S}
            $$
            
            **Substrate consumption rate**
            $$
            \sigma = \frac{\mu}{Y^\mathrm{{X/S}} + 
            \frac{\mu \pi^\mu + \pi^0}{Y^\mathrm{P/S}} + 
            \frac{\rho}{Y^\mathrm{ATP/S}}
            $$

            **Luedeking-Piret production kinetics**
            $$
            \pi = \pi^0 + \pi^\mu \mu,
            $$
            In the basic model, the second stage is growth arrested ($\mu_2=0$) and thus 
            production is defined as purely non-growth associated ($\pi_2=\pi^0$)
            
            **Key assumptions**

            Stage 1: substrate is assumed to be fully consumed
            $(S_1 \rightarrow 0$)

            Stage 2: substrate requirement is computed from maintenance, 
            production, and, optionally, growth.

            
            """,
                mathjax=True,
            )
        ]
    ),
)

steady_state_panel = make_equation_card(
    "Steady-state model equations",
    dbc.Row(
        [
            dbc.Col(
                [
                    ODEs["x_1"],
                    ODEs["p_1"],
                    ODEs["s_1"],
                ],
                xs=12,
                lg=6,
            ),
            dbc.Col(
                [
                    ODEs["x_2"],
                    ODEs["p_2"],
                    ODEs["s_2"],
                ],
                xs=12,
                lg=6,
            ),
        ]
    ),
)

# Kinetics panel
kinetics_panel = make_equation_card(
    "Kinetic inhibition structure",
    html.Div(
        [
            html.P(
                [
                    html.Strong("Performance note: "),
                    "Adding inhibition modes slows simulation - grid "
                    "search is fast due to steady state equations "
                    "for the base case, but biomass and product inhibition "
                    "requires numerical solving.",
                ]
            ),
            dbc.Container(
                [
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.Strong("Substrate inhibition:"),
                                    dcc.Markdown(
                                        f"$${s_inh}$$", mathjax=True, style=inhib_style
                                    ),
                                ],
                                md=4,
                            ),
                            dbc.Col(
                                [
                                    html.Strong("Biomass inhibition:"),
                                    dcc.Markdown(
                                        f"$${b_inh}$$", mathjax=True, style=inhib_style
                                    ),
                                ],
                                md=4,
                            ),
                            dbc.Col(
                                [
                                    html.Strong("Product inhibition:"),
                                    dcc.Markdown(
                                        f"$${p_inh}$$", mathjax=True, style=inhib_style
                                    ),
                                ],
                                md=4,
                            ),
                        ]
                    ),
                    html.Div(
                        [
                            html.Strong("Combined: "),
                            dcc.Markdown(
                                "$$\\mu = \\mu{max} \\times \\text{inhibition factors}$$",
                                mathjax=True,
                                style=inhib_style,
                            ),
                            html.Div(
                                "Substrate inhibition replaces the Monod term entirely."
                            ),
                        ],
                        style={"marginTop": "1rem"},
                    ),
                ]
            ),
        ]
    ),
)


cascade_panel = make_equation_card(
    "Cascade reactor scheme",
    [
        html.Img(src="./assets/cascade_scheme.png", style={"width": "100%"}),
        dcc.Markdown(
            r"""
            The two stage reactor cascade setup is shown above.
            Stage&nbsp;1 focuses on biomass growth,
            while Stage&nbsp;2 focuses on product formation. The outlet of the first reactor feeds directly
            into the second reactor, and fresh substrate can be added to both reactors via separate
            feed streams.

            The corresponding one-stage setup has the same total volume as the cascade, and its feed
            stream matches the combined feed entering the second reactor. The two-stage configuration
            is parameterized by $\phi$ (volume split) and $\nu$ (feed split).
            """,
            mathjax=True,
            style={"lineHeight": "1.5"},
        ),
    ],
)

info_layout = dbc.Container(
    [
        html.H4("Model assumptions and limitations", className="mb-4"),
        dbc.Row(
            [
                dbc.Col([overview_panel], md=4),
                dbc.Col([kinetics_panel, steady_state_panel], md=5),
                dbc.Col(cascade_panel, md=3),
            ],
            className="g-3",
        ),
    ],
    fluid=True,
    className="py-3 py-md-4 px-2 px-md-4",
)
