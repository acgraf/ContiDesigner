from dash import dcc, Input, Output, State, callback_context, no_update
from dash.exceptions import PreventUpdate
import io, csv
import pandas as pd
import app.app_helpers as app_helpers

def register_callbacks_results(app):
    @app.callback(
        Output("download_summary_file_optimal", "data"),
        Input("download_summary_btn_optimal", "n_clicks"),
        State("optimal_summary_data_store", "data"),
        prevent_initial_call=True,
    )
    def download_summary_optimal(n_clicks, summary_data):
        if not n_clicks:  # guard
            raise PreventUpdate
        if not summary_data:
            raise PreventUpdate

        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(["Parameter", "Value"])
        for k, v in summary_data.items():
            writer.writerow([k, v])

        return dict(
            content=buffer.getvalue(), filename="optimal_summary.csv", type="text/csv"
        )

    @app.callback(
        Output("download_summary_file_selected", "data"),
        Input("download_summary_btn_selected", "n_clicks"),
        State("selected_summary_data_store", "data"),
        prevent_initial_call=True,
    )
    def download_summary_selected(n_clicks, selected_data):
        if not n_clicks:  # guard
            raise PreventUpdate
        if not selected_data:
            raise PreventUpdate

        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(["Parameter", "Value"])
        for k, v in selected_data.items():
            writer.writerow([k, v])

        return dict(
            content=buffer.getvalue(), filename="selected_summary.csv", type="text/csv"
        )


    @app.callback(
        Output("download_D_range_grid_file", "data"),
        Input("download_D_range_grid_btn", "n_clicks"),
        State("D_grid_store", "data"),
        prevent_initial_call=True,
    )
    def download_D_range_grid(n_clicks, grid_json):
        if not n_clicks:  # guard
            raise PreventUpdate
        if not grid_json:
            raise PreventUpdate

        df = pd.read_json(io.StringIO(grid_json), orient="records")
        return dcc.send_data_frame(df.to_csv, "D_range_grid.csv", index=False)


    @app.callback(
        Output("download_contour_grid_file", "data"),
        Input("download_contour_grid_btn", "n_clicks"),
        State("phi_ny_grid_store", "data"),
        State("phi_ny_grid_store_selected", "data"),
        prevent_initial_call=True,
    )
    def download_contour_grid(n_clicks, grid_json, grid_json_selected):
        if not n_clicks:  # guard
            raise PreventUpdate
        if grid_json_selected:
            grid_json = grid_json_selected
        if not grid_json:
            raise PreventUpdate
        df = pd.read_json(io.StringIO(grid_json), orient="records")
        return dcc.send_data_frame(df.to_csv, "phi_ny_grid.csv", index=False)


    @app.callback(
        Output("download_sbml_file_optimal_OS", "data"),
        Input("download_sbml_OS_btn_optimal", "n_clicks"),
        State("optimal_OS_model_sbml_store", "data"),
        prevent_initial_call=True,
    )
    def download_sbml_optimal_OS(n_clicks, optimodel_OS_sbml):
        if not n_clicks:  # guard
            raise PreventUpdate
        if not optimodel_OS_sbml:
            raise PreventUpdate

        return dict(
            content=optimodel_OS_sbml,
            filename="optimal_model_onestage.sbml",
            type="text/xml",
        )


    @app.callback(
        Output("download_sbml_file_selected_OS", "data"),
        Input("download_sbml_OS_btn_selected", "n_clicks"),
        State("selected_OS_model_sbml_store", "data"),
        prevent_initial_call=True,
    )
    def download_sbml_selected_OS(n_clicks, selected_model_OS_sbml):
        if not n_clicks:
            raise PreventUpdate
        if not selected_model_OS_sbml:
            raise PreventUpdate
        return dict(
            content=selected_model_OS_sbml,
            filename="selected_model_onestage.sbml",
            type="text/xml",
        )


    @app.callback(
        Output("download_sbml_file_optimal_cascade", "data"),
        Input("download_sbml_cascade_btn_optimal", "n_clicks"),
        State("optimal_cascade_model_sbml_store", "data"),
        prevent_initial_call=True,
    )
    def download_sbml_optimal_cascade(n_clicks, optimodel_cascade_sbml):
        if not n_clicks:
            raise PreventUpdate
        if not optimodel_cascade_sbml:
            raise PreventUpdate

        return dict(
            content=optimodel_cascade_sbml,
            filename="optimal_model_cascade.sbml",
            type="text/xml",
        )


    @app.callback(
        Output("download_sbml_file_selected_cascade", "data"),
        Input("download_sbml_cascade_btn_selected", "n_clicks"),
        State("selected_cascade_model_sbml_store", "data"),
        prevent_initial_call=True,
    )
    def download_sbml_selected_cascade(n_clicks, selected_model_cascade_sbml):
        if not n_clicks:
            raise PreventUpdate
        if not selected_model_cascade_sbml:
            raise PreventUpdate
        return dict(
            content=selected_model_cascade_sbml,
            filename="selected_model_cascade.sbml",
            type="text/xml",
        )

    @app.callback(
        Output("selected_summary_data_store", "data"),
        Input("selected_summary_data_store_D_range", "data"),
        Input("selected_summary_data_store_contour", "data"),
        prevent_initial_call=True,
    )
    def selected_summary_data(selected_summary_drange, selected_summary_contour):
        triggered = callback_context.triggered[0]["prop_id"].split(".")[0]
        if triggered in ["selected_summary_data_store_D_range"]:
            selected_summary = selected_summary_drange
        elif triggered in ["selected_summary_data_store_contour"]:
            selected_summary = selected_summary_contour
        else:
            selected_summary = None

        return selected_summary


    # one callback for  whether selected sbml is from drange or contour
    @app.callback(
        [
            Output("selected_OS_model_sbml_store", "data"),
            Output("selected_cascade_model_sbml_store", "data"),
        ],
        [
            Input("selected_OS_model_sbml_store_D_range", "data"),
            Input("selected_cascade_model_sbml_store_D_range", "data"),
            Input("selected_OS_model_sbml_store_contour", "data"),
            Input("selected_cascade_model_sbml_store_contour", "data"),
        ],
        prevent_initial_call=True,
    )
    def update_selected_sbml(os_drange, cas_drange, os_contour, cas_contour):
        # if the trigger is D-range, return those
        # and if its contour, return those
        triggered = callback_context.triggered[0]["prop_id"].split(".")[0]
        if triggered in [
            "selected_OS_model_sbml_store_D_range",
            "selected_cascade_model_sbml_store_D_range",
        ]:
            return os_drange, cas_drange

        if triggered in [
            "selected_OS_model_sbml_store_contour",
            "selected_cascade_model_sbml_store_contour",
        ]:
            return os_contour, cas_contour

        # failsafe
        return no_update, no_update


    @app.callback(
        [
            Output("onestage_fig_store", "data"),
            Output("cascade_fig_store", "data"),
            Output("D_range_plot", "figure"),
            Output("contour_plot", "figure"),
        ],
        [
            Input("all4figures_run", "data"),
            Input("all4figures_D_range", "data"),
            Input("all4figures_contour", "data"),
        ],
        prevent_initial_call=True,
    )
    def unpack_and_plot(run_data, drange_data, contour_data):
        def safe_load_or_no_update(fig_data):
            if fig_data is None:
                return no_update
            return app_helpers.safe_load_fig(fig_data)

        trigger = callback_context.triggered[0]["prop_id"].split(".")[0]
        if "contour" in trigger:
            # contour click
            onestage_fig = safe_load_or_no_update(contour_data.get("onestage"))
            cascade_fig = safe_load_or_no_update(contour_data.get("cascade"))
            D_range_fig = safe_load_or_no_update(contour_data.get("D_range"))
            contour_fig = safe_load_or_no_update(contour_data.get("contour"))
            return onestage_fig, cascade_fig, D_range_fig, contour_fig
        elif "D_range" in trigger:
            # D range click
            onestage_fig = safe_load_or_no_update(drange_data.get("onestage"))
            cascade_fig = safe_load_or_no_update(drange_data.get("cascade"))
            D_range_fig = safe_load_or_no_update(drange_data.get("D_range"))
            contour_fig = safe_load_or_no_update(drange_data.get("contour"))
            return onestage_fig, cascade_fig, D_range_fig, contour_fig
        else:
            onestage_fig = safe_load_or_no_update(run_data.get("onestage"))
            cascade_fig = safe_load_or_no_update(run_data.get("cascade"))
            D_range_fig = safe_load_or_no_update(run_data.get("D_range"))
            contour_fig = safe_load_or_no_update(run_data.get("contour"))

            return onestage_fig, cascade_fig, D_range_fig, contour_fig


    @app.callback(
        Output("summary_card_container", "children"),
        Input("optimal_summary_card_store", "data"),
        Input("selected_summary_card_store_D_range", "data"),
        Input("selected_summary_card_store_contour", "data"),
        prevent_initial_call=True,
    )
    def render_summary_card(opt_card, selected_card_drange, selected_card_contour):
        triggered = callback_context.triggered[0]["prop_id"].split(".")[0]
        if triggered in ["selected_summary_card_store_D_range"]:
            selected_card = selected_card_drange
        elif triggered in ["selected_summary_card_store_contour"]:
            selected_card = selected_card_contour
        else:
            selected_card = None
        cards_to_show = []
        if opt_card:
            cards_to_show.append(opt_card)
        if selected_card:
            cards_to_show.append(selected_card)
        return cards_to_show


    @app.callback(
        Output("onestage_fig", "figure"),
        Output("cascade_fig", "figure"),
        # Input("time_evolution_selector", "value"),
        Input("onestage_fig_store", "data"),
        Input("cascade_fig_store", "data"),
        Input("onestage_fig_selected_store", "data"),
        Input("cascade_fig_selected_store", "data"),
    )
    def update_time_evolution(
        onestage_fig, cascade_fig, onestage_selected_fig, cascade_selected_fig
    ):
        fig_onestage = onestage_selected_fig or onestage_fig
        fig_cascade = cascade_selected_fig or cascade_fig
        return fig_onestage, fig_cascade






