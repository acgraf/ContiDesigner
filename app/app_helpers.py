import dash
import hashlib
import json
import plotly.graph_objects as go
import plotly.io as pio

def triggered_id():  # which  UI element triggered the callback
    """
    Return the ID of the component that triggered the callback.
    """
    return dash.callback_context.triggered_id


def safe_load_fig(fig):
    if isinstance(fig, str):
        return json.loads(fig)
    return fig


def fig_to_dict(fig):
    if hasattr(fig, "to_dict"):
        return fig.to_dict()
    return fig


def make_cache_key(params):
    """
    Generate a unique cache key based on the relevant simulation parameters.
    Only uses keys from INPUT_MAP.
    """
    # pick only relevant params and default to None if missing
    relevant_params = {k: params.get(k) for k in INPUT_MAP}

    # turn into a deterministic string
    key_str = json.dumps(relevant_params, sort_keys=True)
    # hash it to make key
    key = "run_" + hashlib.md5(key_str.encode("utf-8")).hexdigest()
    return key

def check_input_params(params_store):
    checked_inputs = {"missing": [], "present": []}
    optional = ["Yxs_2", "Yps_2", "Yas_2", "m_2", "pi0_s2", "pi1_s2"]
    optional.append("Ki") if not params_store["is_substrate_inhibited"] else None
    optional.append("x_max") if not params_store["is_biomass_inhibited"] else None
    optional.append("p_max") if not params_store["is_product_inhibited"] else None
    for key, val in params_store.items():
        if key in optional or isinstance(val, bool):
            continue
        if val in (None, "", " "):
            checked_inputs["missing"].append(key)
            # if it was red, make it normal again
        else:
            checked_inputs["present"].append(key)
    return checked_inputs

def build_figures(plotter, D_range=False, contour=None):
    # this just builds the 4 figures
    # and is called by run_simulation and by clicks in the D range or contour plot
    cascade_fig = plotter.plot_time_evolution(cascade=True)
    onestage_fig = plotter.plot_time_evolution(cascade=False)
    if contour:
        contour_fig = plotter.plot_contour("phi_ny", "delta_STY_D", Data=contour)
    else:
        contour_fig = None
    if D_range:
        D_range_fig = plotter.plot_D_range(Data=D_range)
    else:
        D_range_fig = None
    return onestage_fig, cascade_fig, D_range_fig, contour_fig

def from_store(store_data):
    # this converts stored figure dict back to a plotly figure
    if not store_data:
        return go.Figure()
    try:
        # If it’s already a JSON string (from to_json)
        if isinstance(store_data, str):
            return pio.from_json(store_data)
        # If it’s a dict (like when Dash deserializes JSON automatically)
        elif isinstance(store_data, dict):
            return pio.from_json(json.dumps(store_data))
        else:
            return go.Figure(store_data)
    except Exception as e:
        print(f"[from_store] Failed to load figure: {e}")



# Mapping from UI input IDs to internal model parameter names.
INPUT_MAP = {
    "mu_max": "mu_max",
    "pi1_s1": "pi1_s1",
    "Ks": "Ks",
    "pi0_s1": "pi0_s1",
    "delta": "delta",
    "pi0_s2": "pi0_s2",
    "Yxs_1": "Yxs_1",
    "Yps_1": "Yps_1",
    "Yas_1": "Yas_1",
    "Yxs_2": "Yxs_2",
    "Yps_2": "Yps_2",
    "Yas_2": "Yas_2",
    "m_1": "m_1",
    "m_2": "m_2",
    "V_total": "V_total",
    "sf1": "sf1",
    "sf2_max": "sf2_max",
    "Ki": "Ki",
    "x_max": "x_max",
    "p_max": "p_max",
    "growth_stage2": "growth_stage2",
    "is_substrate_inhibited": "is_substrate_inhibited",
    "is_biomass_inhibited": "is_biomass_inhibited",
    "is_product_inhibited": "is_product_inhibited",
}
