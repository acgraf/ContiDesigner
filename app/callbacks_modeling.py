from dash import Input, Output, State, callback_context
from dash.exceptions import PreventUpdate
import app.app_helpers as app_helpers
from app.modeling import cached_run_simulation, run_simulation, handle_drange_click, handle_contour_click

def register_callbacks_modeling(app):
    # validation callback
    @app.callback(
        Output("checked_inputs_store", "data"),
        Input("run", "n_clicks"),
        State("params_store", "data"),
        prevent_initial_call=True,
    )
    def validate_inputs(n_clicks, params_store):
        # called when the run simulation button is clicked
        # it checks if all required inputs are present
        # and updates the checked_inputs_store accordingly
        if not params_store:
            raise PreventUpdate
        checked_inputs = app_helpers.check_input_params(params_store)
        if checked_inputs["missing"]:
            return {
                "ok": False,
                "missing": checked_inputs["missing"],
                "present": checked_inputs["present"],
            }
        return {
            "ok": True,
            "missing": [],
            "present": checked_inputs["present"],
            "params": params_store,
        }




    @app.callback(
        Output("shared_state", "data", allow_duplicate=True),
        Input("D_range_plot", "clickData"),
        Input("contour_plot", "clickData"),
        State("shared_state", "data"),
        State("D_range_plot", "figure"),
        prevent_initial_call=True,
    )
    def update_shared_state(drange_click, contour_click, stored, D_range_fig):
        # called when either contour plot or D range plot is clicked
        # it updates the shared state store with the clicked values
        # needs the current state to update it
        # and the D range figure to get the yaxis name
        # shared state contains D_one_stage, Y_clicked, yaxis_name, phi, ny
        stored = stored or {}
        triggered_id = callback_context.triggered[0]["prop_id"].split(".")[0]

        if triggered_id == "D_range_plot" and drange_click:
            D = drange_click["points"][0]["x"]
            y = drange_click["points"][0]["y"]
            curve_num = drange_click["points"][0]["curveNumber"]
            clicked_trace = D_range_fig["data"][curve_num]
            yaxis_name = clicked_trace.get("yaxis", "y")
            stored.update(
                {
                    "D_total": D,
                    "Y_clicked": y,
                    "curve_num": curve_num,
                    "yaxis_name": yaxis_name,
                    "trigger_source": "D_range_plot",
                }
            )

        elif triggered_id == "contour_plot" and contour_click:
            x = contour_click["points"][0]["x"]
            y = contour_click["points"][0]["y"]
            stored.update(
                {"phi_sel": float(x), "ny_sel": float(y), "trigger_source": "contour_plot"}
            )

        return stored


    @app.callback(
        [
            Output("optimal_params", "data"),
            Output("D_grid_store", "data"),
            Output("phi_ny_grid_store", "data"),
            Output("shared_state", "data"),
            Output("optimal_summary_card_store", "data"),
            Output("optimal_summary_data_store", "data"),
            Output("optimal_OS_model_sbml_store", "data"),
            Output("optimal_cascade_model_sbml_store", "data"),
            Output("all4figures_run", "data"),
            Output("params_store", "data", allow_duplicate=True),
        ],
        [Input("checked_inputs_store", "data")],
        prevent_initial_call=True,
        allow_duplicate=True,
    )
    def run_callback(checked):
        if not checked or not checked.get("ok"):
            raise PreventUpdate
        params = checked["params"]

        return cached_run_simulation(params)


    @app.callback(
        [
            Output("selected_D_state", "data"),
            Output("phi_ny_grid_store_selected", "data"),
            Output("selected_summary_card_store_D_range", "data"),
            Output("selected_summary_data_store_D_range", "data"),
            Output("selected_OS_model_sbml_store_D_range", "data"),
            Output("selected_cascade_model_sbml_store_D_range", "data"),
            Output("all4figures_D_range", "data"),
            Output("shared_state", "data", allow_duplicate=True),
        ],
        [
            Input("shared_state", "data"),
        ],
        [
            State("params_store", "data"),
            State("D_range_plot", "figure"),
        ],
        prevent_initial_call=True,
    )
    def click_drange_callback(shared_state, params_store, D_range_fig):
        return handle_drange_click(shared_state, params_store, D_range_fig)


    @app.callback(
        [
            Output("selected_summary_card_store_contour", "data"),
            Output("selected_summary_data_store_contour", "data"),
            Output("selected_OS_model_sbml_store_contour", "data"),
            Output("selected_cascade_model_sbml_store_contour", "data"),
            Output("all4figures_contour", "data"),
        ],
        [
            Input("shared_state", "data"),
        ],
        [
            State("params_store", "data"),
            State("contour_plot", "figure"),
            State("D_range_plot", "figure"),
            State("selected_D_state", "data"),
        ],
        prevent_initial_call=True,
    )
    def click_contour_callback(
        shared_state, params_store, contour_fig_store, D_range_fig_store, selected_D_state
    ):
        return handle_contour_click(
            shared_state,
            params_store,
            contour_fig_store,
            D_range_fig_store,
            selected_D_state,
        )

