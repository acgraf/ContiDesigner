from ContiDesigner.core.model import ContiModel
from ContiDesigner.core.solver import Solver
from ContiDesigner.plot.plotter import Plotter
import app.app_helpers as app_helpers
from dash.exceptions import PreventUpdate
from .plot_highlights import add_highlight_marker
from .export_sbml import export_contimodel_to_sbml
from app.layout.summary_cards import summarize_process
import numpy as np
from dash import no_update

cache = None 

def cached_run_simulation(params):
    # return cached results if available
    key = app_helpers.make_cache_key(params)
    cached = cache.get(key)
    if cached is not None:
        return cached
    result = run_simulation(params)
    cache.set(key, result)
    return result



def get_optimum(params, solver, D_given=None):
    max_param = "STY_cascade"
    secondary_param = "X1"
    if D_given is None:
        grid_df, D_opt, STY= solver.optimize_phi_ny_across_D(max_param=max_param, secondary_param=secondary_param)
        with solver.model.temporary_params({"D_total": D_opt}):
            phi_opt, ny_opt, phi_ny_grid, improv = solver.find_optimum_phi_ny(
                max_D=D_opt, max_param=max_param, secondary_param=secondary_param
            )
        opt = {
            "D_opt": float(D_opt),
            "phi_opt": float(phi_opt),
            "ny_opt": float(ny_opt),
            "delta_STY_D": float(improv),
        }
        optimized_process = {
            "opt_params": opt,
            "D_grid_df": grid_df.to_json(orient="records"),
            "phi_ny_grid_df": phi_ny_grid.to_json(orient="records"),
        }
    # --- Case 2: Fixed D (selected by user) ---
    else:
        with solver.model.temporary_params({"D_total": D_given}):
            phi_opt, ny_opt, phi_ny_grid, delta_STY_D = (
                solver.find_optimum_phi_ny(max_D=D_given, max_param=max_param, secondary_param=secondary_param)
            )
        opt = {
            "D_opt": float(D_given),
            "phi_opt": float(phi_opt),
            "ny_opt": float(ny_opt),
            "delta_STY_D": float(delta_STY_D),
        }
        optimized_process = {
            "opt_params": opt,
            "D_grid_df": None,
            "phi_ny_grid_df": phi_ny_grid.to_json(orient="records"),
        }
    return optimized_process


def run_simulation(params):
    if not params:
        raise PreventUpdate

    base_model = ContiModel(params)
    base_solver = Solver(base_model)
    # Compute optimum and cache
    # opt contains D, phi, ny
    # optimal_cache is a dict that contains keys of input params the corresponding
    # D, phi, ny parameter values.
    optimal_process = get_optimum(params, base_solver)
    D_grid = optimal_process["D_grid_df"]
    phi_ny_grid = optimal_process["phi_ny_grid_df"]
    opt_values = optimal_process["opt_params"]
    # this updates the parameters globally
    params.update(
        {
            "D_total": opt_values["D_opt"],
            "phi": opt_values["phi_opt"],
            "ny": opt_values["ny_opt"],
        }
    )

    # setup optimal model
    opt_model = ContiModel(params)
    opt_solver = Solver(opt_model)
    opt_plotter = Plotter(opt_model, opt_solver)
    steady_states_cascade = opt_solver.calculate_steady_states()
    steady_states_cascade = opt_solver.calculate_steady_states()
    steady_states_OS = opt_solver.calculate_steady_states(cascade=False)

    STY_cascade_opt = opt_solver.calculate_STY(steady_states_cascade[-1], opt_values["D_opt"])
    # create the 4 figures
    onestage_fig_opt, cascade_fig_opt, D_range_fig, contour_fig = app_helpers.build_figures(
        opt_plotter, D_range=D_grid, contour=phi_ny_grid
    )
    # add optimal markers
    D_range_fig = add_highlight_marker(
        D_range_fig,
        opt_values["D_opt"],
        STY_cascade_opt,
        opt_values["D_opt"],
        is_optimal=True,
        secondary_y=True,
    )
    contour_fig = add_highlight_marker(
        contour_fig,
        opt_values["phi_opt"],
        opt_values["ny_opt"],
        opt_values["D_opt"],
        is_optimal=True,
        contour=True,
        z=opt_values["delta_STY_D"],
        D_value=opt_values["D_opt"],
    )
    opt_figures_dicts = {
        "onestage": app_helpers.fig_to_dict(onestage_fig_opt),
        "cascade": app_helpers.fig_to_dict(cascade_fig_opt),
        "D_range": app_helpers.fig_to_dict(D_range_fig),
        "contour": app_helpers.fig_to_dict(contour_fig),
    }

    sbml_model_opt_OS = export_contimodel_to_sbml(opt_model, n_stages=1)
    sbml_model_opt_cascade = export_contimodel_to_sbml(opt_model, n_stages=2)

    # the very first time we run the simulation, there is no selected figure
    # so the currently selected process is the optimal one
    shared_state = {
        "D_total": opt_values["D_opt"],
        "phi_sel": opt_values["phi_opt"],
        "ny_sel": opt_values["ny_opt"],
    }
    shared_state.update({"trigger_source": "initial_optimal"})

    opt_summary_card, opt_summary_data = summarize_process(
        steady_states_cascade,
        steady_states_OS,
        params,
        opt_model,
        opt_solver,
        is_optimal=True,
    )
    # add the optimal params to the params_store
    params.update(
        {
            "D_total_opt": opt_values["D_opt"],
            "phi_opt": opt_values["phi_opt"],
            "ny_opt": opt_values["ny_opt"],
        }
    )
    result = (
        opt_values,
        D_grid,
        phi_ny_grid,
        shared_state,
        opt_summary_card,
        opt_summary_data,
        sbml_model_opt_OS,
        sbml_model_opt_cascade,
        opt_figures_dicts,
        params,
    )
    return result

def handle_drange_click(
    shared_state,
    params_store,
    D_range_fig_store,
):
    if shared_state["trigger_source"] in ["initial_optimal", "contour_plot"]:
        # skip processing if this was triggered by initial optimal
        return no_update
    D_sel = shared_state.get("D_total")
    Y_sel = shared_state.get("Y_clicked")

    if D_sel is None or Y_sel is None:
        # nothing to plot yet
        raise PreventUpdate

    D_range_fig = app_helpers.from_store(D_range_fig_store)
    secondary_y = shared_state["yaxis_name"] == "y2"
    D_range_selected = add_highlight_marker(
        D_range_fig,
        D_sel,
        Y_sel,
        params_store["D_total_opt"],
        is_optimal=False,
        secondary_y=secondary_y,
    )
    # Recalculate process summary for selected D
    params = params_store
    params["D_total"] = D_sel
    model_sel = ContiModel(params)
    solver_sel = Solver(model_sel)
    optimal_process = get_optimum(params, solver_sel, D_given=D_sel)
    phi_ny_grid = optimal_process["phi_ny_grid_df"]
    selected_values = optimal_process["opt_params"]
    # build a new model with the optimal phi and ny at this D
    params.update(
        {
            "phi": selected_values["phi_opt"],
            "ny": selected_values["ny_opt"],
        }
    )
    model_sel = ContiModel(params)
    solver_sel = Solver(model_sel)
    steady_states_cascade = solver_sel.calculate_steady_states()
    steady_states_OS = solver_sel.calculate_steady_states(cascade=False)
    sel_summary_card, sel_summary_data = summarize_process(
        steady_states_cascade,
        steady_states_OS,
        params,
        model_sel,
        solver_sel,
        is_optimal=False,
        optimal_for_D=True,
    )
    plotter_sel = Plotter(model_sel, solver_sel)
    onestage_selected, cascade_selected, _, contour_fig = app_helpers.build_figures(
        plotter_sel, contour=phi_ny_grid
    )
    contour_selected = add_highlight_marker(
        contour_fig,
        selected_values["phi_opt"],
        selected_values["ny_opt"],
        params_store["D_total_opt"],
        is_optimal=True,
        contour=True,
        z=selected_values["delta_STY_D"],
        D_value=selected_values["D_opt"],
    )
    sbml_model_OS_sel = export_contimodel_to_sbml(model_sel, n_stages=1)
    sbml_model_cascade_sel = export_contimodel_to_sbml(model_sel, n_stages=2)

    figures_dicts = {
        "onestage": app_helpers.fig_to_dict(onestage_selected),
        "cascade": app_helpers.fig_to_dict(cascade_selected),
        "D_range": app_helpers.fig_to_dict(D_range_selected),
        "contour": app_helpers.fig_to_dict(contour_selected),
    }

    updated_shared_state = shared_state.copy()
    updated_shared_state.update(
        {
            "phi_sel": selected_values["phi_opt"],
            "ny_sel": selected_values["ny_opt"],
            "D_total": selected_values["D_opt"],
            "trigger_source": "D_range_plot",
        }
    )
    
    return (
        selected_values,
        phi_ny_grid,
        sel_summary_card,
        sel_summary_data,
        sbml_model_OS_sel,
        sbml_model_cascade_sel,
        figures_dicts,
        updated_shared_state,
    )



def handle_contour_click(
    shared_state, params_store, contour_fig_store, D_range_fig_store, selected_D_state
):
    if shared_state["trigger_source"] in ["initial_optimal", "D_range_plot"]:
        # skip processing if this was triggered by initial optimal
        return no_update
    phi_sel = shared_state["phi_sel"]
    ny_sel = shared_state["ny_sel"]
    D_sel = shared_state["D_total"]
    if None in (phi_sel, ny_sel, D_sel):
        raise PreventUpdate
    contour_fig = app_helpers.from_store(contour_fig_store)
    D_range_fig = app_helpers.from_store(D_range_fig_store)
    contour_selected = add_highlight_marker(
        contour_fig,
        phi_sel,
        ny_sel,
        params_store["D_total_opt"],
        is_optimal=False,
        contour=True,
        D_value=D_sel,
    )
    params = params_store
    # special case: if the chosen phi and ny are the optimal ones at this D
    if selected_D_state and (phi_sel, ny_sel) == (
        selected_D_state["phi_opt"],
        selected_D_state["ny_opt"],
    ):
        selected_is_opt = True
    else:
        selected_is_opt = False
    params["phi"] = phi_sel
    params["ny"] = ny_sel
    params["D_total"] = D_sel
    model_sel = ContiModel(params)
    if np.isnan(model_sel.D1):
        return no_update

    solver_sel = Solver(model_sel)

    steady_states_cascade = solver_sel.calculate_steady_states()
    steady_states_cascade = solver_sel.calculate_steady_states()
    plotter = Plotter(model_sel, solver_sel)
    (onestage_selected, cascade_selected, _, _) = app_helpers.build_figures(plotter)
    figures_dicts = {
        "onestage": app_helpers.fig_to_dict(onestage_selected),
        "cascade": app_helpers.fig_to_dict(cascade_selected),
        "D_range": app_helpers.fig_to_dict(D_range_fig),
        "contour": app_helpers.fig_to_dict(contour_selected),
    }

    steady_states_OS = solver_sel.calculate_steady_states(cascade=False)

    sel_summary_card, sel_summary_data = summarize_process(
        steady_states_cascade,
        steady_states_OS,
        params,
        model_sel,
        solver_sel,
        is_optimal=False,
        optimal_for_D=selected_is_opt,
    )
    sbml_model_OS_sel = export_contimodel_to_sbml(model_sel, n_stages=1)
    sbml_model_cascade_sel = export_contimodel_to_sbml(model_sel, n_stages=2)
    return (
        sel_summary_card,
        sel_summary_data,
        sbml_model_OS_sel,
        sbml_model_cascade_sel,
        figures_dicts,
    )
