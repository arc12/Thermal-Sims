from app.dash_apps import create_dash_app
from dash import html, dcc, ctx, no_update

from dash.dependencies import Output, Input, State

from config import get_building_default_options, get_tmp_options, get_ambient_hr_options
from data.solver import RoomTempSolver2

# endpoint of this page
URL_RULE = "/constant"
# dash internal route prefix, must be start and end with "/"
URL_BASE_PATHNAME = "/dash/constant/"


def create_dash(server):
    """Create a Dash view"""
    app = create_dash_app(server, URL_RULE, URL_BASE_PATHNAME)

    # dash app definitions goes here
    app.config.suppress_callback_exceptions = True
    app.title = "ASHP Room Temperature Simulation for Constant LWT"

    # Get the various parameter options
    building_default_options = get_building_default_options()
    building_default_option_keys = list(building_default_options)
    tmp_options = get_tmp_options()  # Thermal Mass Parameter name-value lookup
    ambient_hr_options = get_ambient_hr_options()
    ambient_hr_option_keys = list(ambient_hr_options)

    # layout "constants"
    # > for standard label + input/dropdown
    left_col_class = "col-md-4"
    right_col_class = "col-md-8"

    app.layout = html.Div([

        html.Div(
            [
                html.H1("Constant LWT Room Temperature Simulation", className="header-title"),
                html.P("What is the equilibrium temperature for constant LWT.", className="header-description")
            ],
            className="header"),

        html.Div(
            [
                # Building Model and Heating System Fixed Parameters
                html.Div(
                    [
                        html.Div([html.Label("Building Model")], className=left_col_class),
                        html.Div(
                            dcc.Dropdown(options=building_default_option_keys, value=building_default_option_keys[0],
                                         clearable=False, searchable=False, id="building_model"),
                            className=right_col_class)
                    ], className="row"
                ),
                html.Div(
                    [
                        html.Div([html.Label("Heat Loss Factor (W/K)")], className=left_col_class),
                        html.Div(dcc.Input(type="number", id="heat_loss_factor"), className=right_col_class)
                    ], className="row"
                ),
                html.Div(
                    [
                        html.Div([html.Label("Emitter Power (W @ dt50)")], className=left_col_class),
                        html.Div(dcc.Input(type="number", id="emitter_std_power"), className=right_col_class)
                    ], className="row"
                ),
                html.Div(
                    [
                        html.Div([html.Label("Thermal Mass Parameter")], className=left_col_class),
                        html.Div(
                            dcc.Dropdown(options={v: k for k, v in tmp_options.items()}, value=90,
                                         clearable=False, searchable=False, id="tmp"),
                            className=right_col_class)
                    ], className="row"
                ),
                html.Div(
                    [
                        html.Div([html.Label("Floor Area (m^2)")], className=left_col_class),
                        html.Div(dcc.Input(type="number", id="floor_area"), className=right_col_class)
                    ], className="row"
                ),

                html.Hr(),

                # Ambient Temperature Selection

                html.Div(
                    [
                        html.Div([html.Label("Ambient Temp Model")], className=left_col_class),
                        html.Div(
                            dcc.Dropdown(options=ambient_hr_option_keys, value=ambient_hr_option_keys[0],
                                         clearable=False, searchable=False, id="ambient_model"),
                            className=right_col_class)
                    ],
                    className="row"
                ),
                html.Div(
                    [
                        html.Div([html.Label("LWT (C), dT=5C")], className=left_col_class),
                        html.Div(dcc.Slider(min=30, max=50, value=35, step=1, id="lwt"), className=right_col_class)
                    ], className="row"
                ),

                html.Hr(),

            ],
            className="container-fluid"
        ),

        html.Div(
            [
                html.Div(
                    dcc.Loading(
                        dcc.Graph(
                            id="temp_chart",
                            config={"displayModeBar": True}
                        ),
                        id="temp_spinner",
                        type="circle"
                    ),
                    className="card"
                )
            ],
            className="wrapper"
        ),

        html.Div(
            [
                html.P(id="summary_results"),
                html.Div([
                    html.Div([html.Button("Compute", id="compute")], className="col-md-2"),
                    html.Div(id="compute_errors", className="col-md-10")
                ], className="row")
            ], className="container-fluid"
        ),
        html.Hr()

    ],
        className="wrapper"
    )

    @app.callback(
        [
            Output("heat_loss_factor", "value"),
            Output("emitter_std_power", "value"),
            Output("tmp", "value"),
            Output("floor_area", "value")
        ],
        Input("building_model", "value")
    )
    def select_building_model(building_model):
        building_data = building_default_options[building_model]
        outputs = [
            building_data["heat_loss_factor"],
            building_data["emitter_std_power"],
            tmp_options[building_data["tmp_category"]],
            building_data["floor_area"]
        ]
        return outputs

    @app.callback(
        [
            Output("temp_chart", "figure"),
            Output("summary_results", "children"),
            Output("compute_errors", "children")
        ],
        [
            Input("lwt", "value"),
            Input("ambient_model", "value"),
            Input("compute", "n_clicks")
        ],
        [
            State("heat_loss_factor", "value"),
            State("emitter_std_power", "value"),
            State("tmp", "value"),
            State("floor_area", "value")
        ]
    )
    def compute(lwt,
                ambient_model,
                compute_n_clicks,
                heat_loss_factor,
                emitter_std_power,
                tmp,
                floor_area):
        if ctx.triggered_id is None:  # no compute on initial load
            return [no_update, "", ""]

        error_msg = ""

        building_params = {
            "heat_loss_factor": float(heat_loss_factor),
            "emitter_std_power": float(emitter_std_power),
            "tmp": float(tmp),
            "floor_area": float(floor_area)
            # "fluid_volume": float(fluid_volume)
        }

        solver = RoomTempSolver2(building_params, ambient_model, lwt=lwt, initial_temp=16, steps_per_hour=12)

        MAX_ITERS = 20
        CONV_THRESHOLD = 0.05
        print("Iterations:")
        print("\tfull_day_loss \tfull_day_energy_delta \tmax_t_iter_delta \tmean_t_iter_delta")
        while (solver.full_day_loss_delta > CONV_THRESHOLD) and (solver.n_iterations < MAX_ITERS):
            solver.iterate()
            print(f"{solver.n_iterations}: \t{solver.full_day_loss:.3f} \t\t\t\t{solver.full_day_loss_delta:.4f} \t\t\t\t\t{solver.max_t_iter_delta:.4f} \t\t\t\t{solver.mean_t_iter_delta:.4f}")

        if (solver.full_day_loss_delta > CONV_THRESHOLD) and (solver.n_iterations == MAX_ITERS):
            error_msg = f"Failed to converge after {MAX_ITERS} solver iterations. Last loss delta={solver.full_day_loss_delta:.3f}kWh. Try increasing steps_per_hour."

        formatted_times = [f"{int(t):02d}:{int(t * 60 + 0.5) % 60:02d}" for t in solver.times]
        rt_diffs = [(solver.iter_room_temp[i + 1] - solver.iter_room_temp[i]) for i in range(len(solver.iter_room_temp) - 1)]
        rt_diffs.append(solver.iter_room_temp[0] - solver.iter_room_temp[-1])
        rt_rates = [r / solver.time_step_duration for r in rt_diffs]

        tc_data_chunks = [
            # temps
            {
                "x": formatted_times,
                "y": solver.iter_room_temp,
                "text": rt_rates,
                "mode": "lines",
                "hovertemplate": "Rm: %{y:.1f}C @ t=%{x}<br>Rate: %{text:.2f}C/hr<extra></extra>",
                "name": "Room"
            },
            {
                "x": formatted_times,
                "y": solver.ambient_temps,
                "mode": "lines",
                "hovertemplate": "Outside: %{y:.1f}C @ t=%{x}<extra></extra>",
                "name": "Ambient"
            },
            # Solver returns Watt.hours
            {
                "x": formatted_times,
                "y": [wh / solver.time_step_duration / 1000 for wh in solver.energy_lost],
                "mode": "lines",
                "hovertemplate": "Loss: %{y:.2f}kW @ t=%{x}<extra></extra>",
                "name": "Loss",
                "yaxis": "y2",
            },

            {
                "x": formatted_times,
                "y": [wh / solver.time_step_duration / 1000 for wh in solver.energy_emitted],
                "mode": "lines",
                "hovertemplate": "Emitted: %{y:.2f}kW @ t=%{x}<extra></extra>",
                "name": "Emitted",
                "yaxis": "y2",
            }
        ]

        tc_layout_chunk = {
            "title": {
                "text": f"Temperatures & Energy Balance",
                "x": 0.05,
                "xanchor": "left",
            },
            "legend": {"x": -0.07, "xanchor": "left", "y": 1.0, "yanchor": "bottom", "orientation": "h"},
            "xaxis": {"title": "Time", "fixedrange": False, "tickangle": 90},
            "yaxis": {"title": "Temperature", "ticksuffix": "C", "fixedrange": False},
            "yaxis2": {"title": "Power Input", "ticksuffix": "kW", "fixedrange": False, "overlaying": "y", "side": "right", "showgrid": False}
        }

        # summary

        summary = f"Total Heat Loss: {solver.full_day_loss:.2f}kWh"

        return [
            {"data": tc_data_chunks, "layout": tc_layout_chunk},
            summary,
            html.B(error_msg, style={"background": "yellow"})
        ]

    return app.server
