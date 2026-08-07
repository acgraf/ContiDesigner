import plotly.graph_objects as go


def get_marker_props(contour, is_optimal, D_opt=None, D_value=None, x=None):
    """
    Return symbol, color, and size for a marker based on its type and context.
    """
    size = 14 if is_optimal else 10
    symbol = "diamond"
    color = "black"

    if contour:
        if is_optimal:
            if D_value == D_opt:
                symbol = "star"
                color = "violet"
            else:
                symbol = "triangle-up"
                color = "#17a2b8"
        else:
            symbol = "diamond"
            color = "black"
    else:
        if is_optimal:
            symbol = "star"
            color = "violet"
        elif x == D_opt:
            symbol = None  # skip marker
            color = None
        else:
            symbol = "diamond"
            color = "black"

    return symbol, color, size


def format_hover_text(contour, is_optimal, x, y, D_value=None, z=None):
    if contour:
        if is_optimal:
            return f"Optimal TS at D = {D_value} /h<br>with ϕ = {x:.2f}, ν = {y:.2f}<br>ΔSTY = {(z):.2f}"
        else:
            return f"Selected TS at D = {D_value}<br>with ϕ = {x:.2f} and ν = {y:.2f}"
    else:
        return ""


def add_trace(
    fig, x, y, mode, name, symbol=None, color=None, size=None, text="", axis="y"
):
    kwargs = dict(
        x=x,
        y=y,
        mode=mode,
        name=name,
        showlegend=False,
        yaxis=axis,
    )
    if mode == "markers":
        kwargs.update(
            marker_symbol=symbol,
            marker_color=color,
            marker_size=size,
            text=text,
            textposition="top center",
            hoverinfo="text",
        )
    elif mode == "lines":
        kwargs.update(line=dict(color=color, dash="dash"))
    fig.add_trace(go.Scattergl(**kwargs))
    return fig


def remove_traces(fig, prefix):
    fig.data = tuple(
        trace
        for trace in fig.data
        if not (trace.name and trace.name.startswith(prefix))
    )
    return fig


def add_highlight_marker(
    fig,
    x,
    y,
    D_opt,
    is_optimal=False,
    secondary_y=False,
    contour=False,
    z=None,
    D_value=None,
):
    #  Remove previous selected markers
    fig = remove_traces(fig, "selected")

    #  Determine marker properties
    symbol, color, size = get_marker_props(contour, is_optimal, D_opt, D_value, x)
    if symbol is None:
        return fig  # skip plotting

    #  Determine hover text
    hover_text = format_hover_text(contour, is_optimal, x, y, D_value, z)

    #  Axis selection
    axis = "y2" if secondary_y else "y"
    xaxis_range = fig.layout.xaxis.range or [min(fig.data[0].x), max(fig.data[0].x)]
    yaxis_layout = "yaxis2" if axis == "y2" else "yaxis"
    yaxis_range = getattr(fig.layout, yaxis_layout).range or [
        min(fig.data[0].y),
        max(fig.data[0].y),
    ]

    #  Contour plot
    if contour:
        marker_name = "optimal_cascade" if is_optimal else "selected_cascade"
        line_name = "optimal_line" if is_optimal else "selected_line"

        # check overlap with optimal
        if not is_optimal:
            for trace in fig.data:
                if trace.name and trace.name.startswith("optimal"):
                    trace_x = trace.x[0] if hasattr(trace, "x") else None
                    trace_y = trace.y[0] if hasattr(trace, "y") else None
                    if trace_x == x and trace_y == y:
                        return fig

        # marker
        fig = add_trace(
            fig, [x], [y], "markers", marker_name, symbol, color, size, hover_text
        )
        # vertical line
        fig = add_trace(
            fig, [x, x], [yaxis_range[0], y], "lines", line_name, color=color
        )
        # horizontal line
        fig = add_trace(
            fig, [xaxis_range[0], x], [y, y], "lines", line_name, color=color
        )

    #  D_range plot
    else:
        marker_name = "optimal_marker" if is_optimal else "selected_marker"
        line_name = "optimal_line" if is_optimal else "selected_line"
        start_x = xaxis_range[0] if axis == "y" else xaxis_range[1]

        # marker
        fig = add_trace(
            fig,
            [x],
            [y],
            "markers",
            marker_name,
            symbol,
            color,
            size,
            hover_text,
            axis=axis,
        )
        # horizontal line
        fig = add_trace(
            fig, [start_x, x], [y, y], "lines", line_name, color=color, axis=axis
        )
        # vertical line
        fig = add_trace(
            fig, [x, x], [yaxis_range[0], y], "lines", line_name, color=color, axis=axis
        )

    return fig
