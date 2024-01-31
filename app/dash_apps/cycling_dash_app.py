import plotly.graph_objs

from app.dash_apps import create_dash_app
from dash import html, dcc, ctx, no_update

from dash.dependencies import Output, Input, State

from config import get_building_default_options, get_tmp_options, get_cop_point_options
from data.solver import CyclingSolver

# endpoint of this page
URL_RULE = "/cycling"
# dash internal route prefix, must be start and end with "/"
URL_BASE_PATHNAME = "/dash/cycling/"


def create_dash(server):
    """Create a Dash view"""
    app = create_dash_app(server, URL_RULE, URL_BASE_PATHNAME)

    # dash app definitions goes here
    app.config.suppress_callback_exceptions = True
    app.title = "ASHP Cycling Simulation"

    # Get the various parameter options
    building_default_options = get_building_default_options()
    building_default_option_keys = list(building_default_options)
    tmp_options = get_tmp_options()  # Thermal Mass Parameter name-value lookup
    cop_point_options = get_cop_point_options("lwt")
    cop_point_option_keys = list(cop_point_options)

    # layout "constants"
    # > for standard label + input/dropdown
    left_col_class = "col-md-4"
    right_col_class = "col-md-8"

    app.layout = html.Div([

        html.Div(
            [
                html.H1("ASHP Cycling Simulation", className="header-title"),
                html.P("Simulation against a steady state environment. 'Thermostat period' is the duration it is 'calling', given net warming from one HP cycle.", className="header-description"),
                html.P(html.B("This makes some quite unrealistic assumptions! Definitely do not trust the COP."))
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
                        html.Div([html.Label("Heating Fluid Volume (l)")], className=left_col_class),
                        html.Div(dcc.Input(type="number", id="fluid_volume"), className=right_col_class)
                    ], className="row"
                ),
                html.Div(
                    [
                        html.Div(dcc.Checklist(["Volumiser"], id="with_volumiser"), className=left_col_class),
                        html.Div(dcc.Input(type="number", value=35, id="volumiser_volume"), className=right_col_class)
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

                # Heat Pump Settings and Ambient Temperature Selection
                html.Div(
                    [
                        html.Div([html.Label("COP Model")], className=left_col_class),
                        html.Div(
                            dcc.Dropdown(options=cop_point_option_keys, value=cop_point_option_keys[0],
                                         clearable=False, searchable=False, id="cop_model"),
                            className=right_col_class)
                    ],
                    className="row"
                ),
                html.Div(
                    [
                        html.Div([html.Label("LWT & overshoot (C)")], className=left_col_class),
                        html.Div([dcc.Input(type="number", value=35, id="lwt"), dcc.Input(type="number", value=4, id="lwt_overshoot")], className=right_col_class)
                    ], className="row"
                ),
                html.Div(
                    [
                        html.Div([html.Label("HP Capacity (kW)")], className=left_col_class),
                        html.Div(dcc.Input(type="number", id="hp_capacity"), className=right_col_class)
                    ], className="row"
                ),
                html.Div(
                    [
                        html.Div([html.Label("Setpoint Temp (C)")], className=left_col_class),
                        html.Div(dcc.Input(type="number", value=18, id="setpoint_temp"), className=right_col_class)
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
                html.Div(id="summary_results"),
                html.Div([
                    html.Div([html.Button("Compute", id="compute")], className="col-md-2"),
                    html.Div(id="compute_errors", className="col-md-10")
                ], className="row")
            ], className="container-fluid"
        )
    ],
        className="wrapper"
    )

    @app.callback(
        [
            Output("heat_loss_factor", "value"),
            Output("emitter_std_power", "value"),
            Output("fluid_volume", "value"),
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
            building_data["fluid_volume"],
            tmp_options[building_data["tmp_category"]],
            building_data["floor_area"]
        ]
        return outputs

    @app.callback(
        Output("volumiser_volume", "disabled"),
        Input("with_volumiser", "value")
    )
    def select_volumiser(with_volumiser):
        return not with_volumiser


    @app.callback(
        [
            Output("hp_capacity", "value")
        ],
        Input("cop_model", "value")
    )
    def select_cop_model(cop_model_key):
        cop_model = get_cop_point_options("lwt")[cop_model_key]
        return [cop_model["capacity"]]

    @app.callback(
        [
            Output("temp_chart", "figure"),
            Output("summary_results", "children"),
            Output("compute_errors", "children")
        ],
        Input("compute", "n_clicks"),
        [
            State("heat_loss_factor", "value"),
            State("emitter_std_power", "value"),
            State("fluid_volume", "value"),
            State("with_volumiser", "value"),
            State("volumiser_volume", "value"),
            State("tmp", "value"),
            State("floor_area", "value"),
            State("cop_model", "value"),
            State("lwt", "value"),
            State("lwt_overshoot", "value"),
            State("hp_capacity", "value"),
            State("setpoint_temp", "value")
        ]
    )
    def compute(n_clicks,
                heat_loss_factor,
                emitter_std_power,
                fluid_volume, with_volumiser, volumiser_volume,
                tmp,
                floor_area,
                cop_model,
                lwt, lwt_overshoot,
                hp_capacity,
                setpoint_temp):
        if ctx.triggered_id is None:  # no compute on initial load
            return [no_update, "", ""]

        error_msg = ""

        building_params = {
            "heat_loss_factor": float(heat_loss_factor),
            "emitter_std_power": float(emitter_std_power),
            "tmp": float(tmp),
            "floor_area": float(floor_area),
            "fluid_volume": float(fluid_volume) + (float(volumiser_volume) if with_volumiser else 0)
        }

        solver = CyclingSolver(building_params, cop_model, lwt=lwt, lwt_overshoot=lwt_overshoot, hp_capacity=hp_capacity, initial_temp=setpoint_temp,
                               steps_per_minute=10)

        solver.iterate()

        if solver.on_duration is None or solver.off_duration is None:
            return [
                {"data": [], "layout": {"title": {"text": "No Cycle"}}},
                "",
                html.B(f"Cycle period exceeds simulation limit of {int(round(solver.max_steps * solver.time_step_secs / 60, 0))} minutes.", style={"background": "orange"})]

        power = [e / solver.time_step_secs * 3600 for e in solver.cycle_elec_used]  # Wh to W

        tc_data_chunks = [
            {
                "x": solver.times_mins,
                "y": solver.mean_water_temp,
                "mode": "lines",
                "hovertemplate": "Mean Water: %{y:.1f}C @ t=%{x}<extra></extra>",
                "name": "Mean Water Temp"
            },
            # {
            #     "x": solver.times_mins,
            #     "y": solver.cycle_room_temp,
            #     "mode": "lines",
            #     "hovertemplate": "Room: %{y:.1f}C @ t=%{x}<extra></extra>",
            #     "name": "Room Temp"
            # },
            {
                "x": solver.times_mins,
                "y": power,
                "text": solver.cycle_cop,
                "mode": "lines",
                "hovertemplate": "In: %{y:.1f}kW @ t=%{x}<br>COP = %{text:.2f}<extra></extra>",
                "name": "In",
                "yaxis": "y2",
            },
            {
                "x": solver.times_mins,
                "y": solver.cycle_emitter_output,
                "mode": "lines",
                "hovertemplate": "Emitter: %{y:.1f}W @ t=%{x}<extra></extra>",
                "name": "Emitter",
                "yaxis": "y2",
            }
        ]

        tc_layout_chunk = {
            "title": {
                "text": f"One Cycle Pattern",
                "x": 0.05,
                "xanchor": "left",
            },
            "legend": {"x": -0.07, "xanchor": "left", "y": 1.0, "yanchor": "bottom", "orientation": "h"},
            "xaxis": {"title": "Time (minutes)", "fixedrange": False},
            "yaxis": {"title": "Temperature", "ticksuffix": "C", "fixedrange": False},
            "yaxis2": {"title": "Power", "ticksuffix": "W", "fixedrange": False, "overlaying": "y", "side": "right", "showgrid": False}
        }

        # summary
        duty = round(100 * solver.on_duration / (solver.on_duration + solver.off_duration), 0)
        cycle_duration_hrs = (solver.on_duration + solver.off_duration) / 60
        starts_per_hour = 1 / cycle_duration_hrs
        from math import fabs
        thermostat_period = cycle_duration_hrs * 1 / fabs(solver.iter_room_temp_delta)  # estimate period for a 1C thermostat hysteresis around target temp
        mean_input_power = sum(solver.cycle_elec_used) / cycle_duration_hrs / 1000
        clean_cops = [c for c in solver.cycle_cop if c is not None]
        mean_cop = sum(clean_cops) / len(clean_cops)
        summary = [
            html.P(f"Starts/hr: {starts_per_hour:.1f}, Duty: {duty}%, Room Temp Change: {solver.iter_room_temp_delta:.1f}C, "
                   f"Thermostatic Period: {thermostat_period:.1f}h"),
            html.P(f"Mean Power: {mean_input_power:.2f}kW, Mean COP: {mean_cop:.2f}")
        ]
        return [
            {"data": tc_data_chunks, "layout": tc_layout_chunk},
            summary,
            html.B(error_msg, style={"background": "yellow"})
        ]

    return app.server
