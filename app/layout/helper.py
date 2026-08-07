from dash import dcc, html

symbols = {
    "mu_max": r"\mu^{\max}",
    "delta": r"\delta",
    "Ks": r"K^{\mathrm{S}}",
    "pinot_1": r"\pi_1^{0}",
    "pimu_1": r"\pi_1^{\mu}",
    "Yxs_1": r"Y_1^{\mathrm{X/S}}",
    "Yps_1": r"Y_1^{\mathrm{P/S}}",
    "Yxs_2": r"Y_2^{\mathrm{x/s}}",
    "x_max": r"X^{\mathrm{max}}",
}

labels = {
    "mu_max": [
        dcc.Markdown(r"$\mu^{\max}$", mathjax=True, className="mb-0"),
        html.Span("[1/h]", className="text-muted"),
    ],
    "delta": [
        dcc.Markdown(r"$\delta$", mathjax=True, className="mb-0"),
        html.Span("[1/h]", className="text-muted"),
    ],
    "Ks": [
        dcc.Markdown(r"$K^\mathrm{S}$", mathjax=True, className="mb-0"),
        html.Span("[g/L]", className="text-muted"),
    ],
    "pinot_1": [
        dcc.Markdown(r"$\pi_1^{0}$", mathjax=True, className="mb-0"),
        html.Span("[1/h]", className="text-muted"),
    ],
    "pimu_1": [
        dcc.Markdown(r"$\pi_1^{\mu}$", mathjax=True, className="mb-0"),
        html.Span("[-]", className="text-muted"),
    ],
    "rho_1": [
        dcc.Markdown(r"$\rho_1$", mathjax=True, className="mb-0"),
        html.Span("[1/h]", className="text-muted"),
    ],
    "pinot_2": [
        dcc.Markdown(r"$\pi_2^{0}$", mathjax=True, className="mb-0"),
        html.Span("[1/h]", className="text-muted"),
    ],
    "pimu_2": [
        dcc.Markdown(r"$\pi_2^{\mu}$", mathjax=True, className="mb-0"),
        html.Span("[-]", className="text-muted"),
    ],
    "rho_2": [
        dcc.Markdown(r"$\rho_2$", mathjax=True, className="mb-0"),
        html.Span("[1/h]", className="text-muted"),
    ],
    "Yxs_1": [
        dcc.Markdown(r"$Y_1^{\mathrm{X/S}}$", mathjax=True, className="mb-0"),
        html.Span("[g/g]", className="text-muted"),
    ],
    "Yps_1": [
        dcc.Markdown(r"$Y_1^{\mathrm{P/S}}$", mathjax=True, className="mb-0"),
        html.Span("[g/g]", className="text-muted"),
    ],
    "Yas_1": [
        dcc.Markdown(r"$Y_1^{\mathrm{ATP/S}}$", mathjax=True, className="mb-0"),
        html.Span("[g/g]", className="text-muted"),
    ],
    "Yxs_2": [
        dcc.Markdown(r"$Y_2^{\mathrm{x/s}}$", mathjax=True, className="mb-0"),
        html.Span("[g/g]", className="text-muted"),
    ],
    "Yps_2": [
        dcc.Markdown(r"$Y_2^{\mathrm{p/s}}$", mathjax=True, className="mb-0"),
        html.Span("[g/g]", className="text-muted"),
    ],
    "Yas_2": [
        dcc.Markdown(r"$Y_2^{\mathrm{ATP/S}}$", mathjax=True, className="mb-0"),
        html.Span("[g/g]", className="text-muted"),
    ],
    "V": [
        dcc.Markdown(r"$V$", mathjax=True, className="mb-0"),
        html.Span("[L]", className="text-muted"),
    ],
    "sf1": [
        dcc.Markdown(r"$S^F_1$", mathjax=True, className="mb-0"),
        html.Span("[g/L]", className="text-muted"),
    ],
    "sf2_max": [
        dcc.Markdown(r"$S^{\mathrm{F, max}}_2$", mathjax=True, className="mb-0"),
        html.Span("[g/L]", className="text-muted"),
    ],
    "x_max": [
        dcc.Markdown(r"$X^{\mathrm{max}}$", mathjax=True, className="mb-0"),
        html.Span("[g/L]", className="text-muted"),
    ],
    "p_max": [
        dcc.Markdown(r"$P^{\mathrm{max}}$", mathjax=True, className="mb-0"),
        html.Span("[g/L]", className="text-muted"),
    ],
    "Ki": [
        dcc.Markdown(r"$K^\mathrm{I}$", mathjax=True, className="mb-0"),
        html.Span("[g/L]", className="text-muted"),
    ],
}
