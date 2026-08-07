from dash import Input, Output, State, callback_context, no_update
from dash.exceptions import PreventUpdate
import app.app_helpers as app_helpers
import numpy as np
from ContiDesigner.utils.defaults import DEFAULT_PROCESSES


def register_callbacks_controlflow(app):

    @app.callback(
        [
            Output("page-input", "style"),
            Output("page-results", "style"),
            Output("page-info", "style"),
            Output("input_btn", "color"),
            Output("results_btn", "color"),
            Output("info_btn", "color"),
            Output("missing_results_modal", "is_open"),
        ],
        [
            Input("input_btn", "n_clicks"),
            Input("results_btn", "n_clicks"),
            Input("info_btn", "n_clicks"),
            Input("optimal_params", "data"),
            Input("close_missing_results", "n_clicks"),
            Input("missing_results_modal", "is_open"),
        ],
    )
    def switch_page(n1, n2, n3, optimal_params, close_clicks, modal_open):
        """
        Route between pages and control the missing-results modal.
        Returns visibility styles, active button styles, and modal state.
        """
        ctx = callback_context
        trig = ctx.triggered[0]["prop_id"] if ctx.triggered else None

        if (
            trig == "missing_results_modal.is_open"
            and not modal_open
            and not optimal_params
        ):
            page = "input"
            open_modal = False

        elif trig == "close_missing_results.n_clicks":
            page = "input"
            open_modal = False

        elif trig == "results_btn.n_clicks":
            if not optimal_params:
                page = None
                open_modal = True
            else:
                page = "results"
                open_modal = False

        elif trig == "optimal_params.data":
            page = "results"
            open_modal = False

        elif trig:
            page = trig.split(".")[0].replace("_btn", "")
            open_modal = False

        else:
            page = "input"
            open_modal = False

        visible = {"display": "block"}
        hidden = {"display": "none"}

        inp = visible if page == "input" else hidden
        res = visible if page == "results" else hidden
        inf = visible if page == "info" else hidden

        inp_color = "dark" if page == "input" else "outline-secondary"
        res_color = "dark" if page == "results" else "outline-secondary"
        info_color = "dark" if page == "info" else "outline-secondary"

        return inp, res, inf, inp_color, res_color, info_color, open_modal

    @app.callback(
        Output("defaults_modal", "is_open"),
        Input("open_defaults_modal", "n_clicks"),
        Input("apply_defaults_btn", "n_clicks"),
        Input("cancel_defaults_btn", "n_clicks"),
        State("defaults_modal", "is_open"),
        prevent_initial_call=True,
    )
    def toggle_defaults_modal(open_clicks, apply_clicks, cancel_clicks, is_open):
        # this is triggered when:
        # button open defaults is clicked
        # button apply  defaults is clicked
        # button cancel defaults is clicked
        # the output is wether the modal is open or closed
        # and it needs to know the current state (is_open)
        # State is just an additional input, but does not trigger the callback
        ctx = callback_context
        triggered = ctx.triggered_id

        if triggered == "open_defaults_modal":
            return True  # open the modal
        elif triggered in ["apply_defaults_btn", "cancel_defaults_btn"]:
            return False  # close after apply
        return is_open  # fallback

    @app.callback(
        [Output(i, "value") for i in app_helpers.INPUT_MAP.keys()],
        Input("apply_defaults_btn", "n_clicks"),
        Input("clear_btn", "n_clicks"),
        State("default_process_selection", "value"),
        [State(i, "value") for i in app_helpers.INPUT_MAP.keys()],
        prevent_initial_call=True,
    )
    def update_inputs(apply_clicks, clear_clicks, selected_process, *current_values):
        # is called when the default values are applied or when the clear button is clicked
        # when clear button is clicked, all inputs are reset to None (or False for bools)
        # when apply defaults is clicked, it checks which default process was selected
        # then the corresponding default values are applied to the inputs which are empty
        ctx = callback_context
        triggered = ctx.triggered_id
        bools = [
            "growth_stage2",
            "is_substrate_inhibited",
            "is_biomass_inhibited",
            "is_product_inhibited",
        ]
        # Reset all inputs when Clear button is clicked
        if triggered == "clear_btn":
            return [
                None if i not in bools else False for i in app_helpers.INPUT_MAP.keys()
            ]

        if triggered == "apply_defaults_btn" and selected_process:
            defaults = DEFAULT_PROCESSES.get(selected_process, {}).copy()
            if selected_process == "LA" and "sf_onestage" in defaults:
                defaults["sf"] = defaults.pop("sf_onestage")

            out_values = []
            for param, cur_val in zip(app_helpers.INPUT_MAP.keys(), current_values):
                default_val = defaults.get(param)
                # Only update if current value is None/empty/False
                out_values.append(
                    default_val if cur_val in [None, "", False] else no_update
                )
            return out_values

        # No change
        return [no_update] * len(app_helpers.INPUT_MAP.keys())

    @app.callback(
        Output("onestage_header", "children"),
        Output("cascade_header", "children"),
        Input("shared_state", "data"),
        prevent_initial_call=True,
    )
    def update_header(shared_state):
        if not shared_state:
            return "Time Evolution: Cascade Process"

        D = shared_state.get("D_total")
        phi = shared_state.get("phi_sel")
        ny = shared_state.get("ny_sel")
        onestage_header = f"One-stage process (D= {D:.2f} /h)"
        cascade_header = f"Two-stage process (D= {D:.2f} /h, Φ = {phi:.2f}, ν= {ny:.2f})"
        return onestage_header, cascade_header

    # this function needs a callback, so the params store
    # gets updated any time an input changes
    @app.callback(
        Output("params_store", "data", allow_duplicate=True),
        [Input(i, "value") for i in app_helpers.INPUT_MAP.keys()],
        prevent_initial_call=True,
    )
    def gather_params(*values):
        # values: dict pulled from Dash input components
        # this is called whenever any input changes
        # but since it is also called during the time the user is inputting values
        # it should not raise an error if some values are missing, we do this later
        # this only gathers the params in a format so that the ContiModel can use them
        vals = dict(zip(app_helpers.INPUT_MAP.keys(), values))

        def f(key):
            val = vals.get(key, None)
            try:
                return float(val) if val not in (None, "", "None") else None
            except (TypeError, ValueError):
                return None

        growth_stage2 = bool(vals["growth_stage2"])
        is_substrate_inhibited = bool(vals["is_substrate_inhibited"])
        is_biomass_inhibited = bool(vals["is_biomass_inhibited"])
        is_product_inhibited = bool(vals["is_product_inhibited"])

        params_dict = {
            "mu_max": f("mu_max"),
            "Yxs_1": f("Yxs_1"),
            "Yps_1": f("Yps_1"),
            "Yas_1": f("Yas_1"),
            "m_1": f("m_1"),
            "Yxs_2": f("Yxs_2"),
            "Yps_2": f("Yps_2"),
            "Yas_2": f("Yas_2"),
            "m_2": f("m_2"),
            "pi0_s1": f("pi0_s1"),
            "pi1_s1": f("pi1_s1"),
            "pi0_s2": f("pi0_s2"),
            "pi1_s2": f("pi1_s2"),
            "delta": f("delta"),
            "sf1": f("sf1"),
            "sf_onestage": f("sf1"),
            "sf2_max": f("sf2_max"),
            "Ks": f("Ks"),
            "Ki": f("Ki") if is_substrate_inhibited else None,
            "x_max": f("x_max") if is_biomass_inhibited else None,
            "p_max": f("p_max") if is_product_inhibited else None,
            "V_total": f("V_total"),
            "growth_initial_state": [0.1, 0, 0],
            "prod_initial_state": [0, 0, 0],
            "growth_stage2": growth_stage2,
            "is_substrate_inhibited": is_substrate_inhibited,
            "is_biomass_inhibited": is_biomass_inhibited,
            "is_product_inhibited": is_product_inhibited,
            "t_span": np.linspace(0, 100, 201),
        }
        return params_dict

    @app.callback(
        Output("wait_modal", "is_open", allow_duplicate=True),
        Input("checked_inputs_store", "data"),
        State("wait_modal", "is_open"),
        prevent_initial_call=True,
    )
    def open_modal(checked, is_open):
        if not checked or not checked.get("ok"):
            raise PreventUpdate
        return True  # open modal immediately

    @app.callback(
        Output("wait_modal", "is_open", allow_duplicate=True),
        Input("optimal_params", "data"),
        State("wait_modal", "is_open"),
        prevent_initial_call=True,
    )
    def close_modal(_data, is_open):
        return False  # close modal

    @app.callback(
        [Output(i, "className") for i in app_helpers.INPUT_MAP.keys()],
        Input("checked_inputs_store", "data"),
        [State(i, "className") for i in app_helpers.INPUT_MAP.keys()],
        prevent_initial_call=True,
    )
    def highlight_fields(checked_inputs, *current_classes):
        # this is called when the checked_inputs_store is updated
        missing_inputs = checked_inputs["missing"] or []
        present_inputs = checked_inputs["present"] or []

        new_classes = []

        for key, cur_class in zip(app_helpers.INPUT_MAP.keys(), current_classes):
            # skip optional parameters
            if key.endswith("_inhibited") or key.endswith("growth_stage2"):
                new_classes.append(no_update)
            elif key in missing_inputs:
                new_classes.append("form-control-sm border-1 shadow-sm is-invalid")
            else:
                new_classes.append("form-control-sm border-1 shadow-sm")
        return new_classes

    @app.callback(
        Output("Ki_container", "style"), Input("is_substrate_inhibited", "value")
    )
    def toggle_Ki(is_enabled):
        return {"display": "block"} if is_enabled else {"display": "none"}

    @app.callback(
        Output("x_max_container", "style"), Input("is_biomass_inhibited", "value")
    )
    def toggle_x_max(is_enabled):
        return {"display": "block"} if is_enabled else {"display": "none"}

    @app.callback(
        Output("p_max_container", "style"), Input("is_product_inhibited", "value")
    )
    def toggle_p_max(is_enabled):
        return {"display": "block"} if is_enabled else {"display": "none"}
