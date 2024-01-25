import json
import logging
from os import rename, remove

from app.dash_apps import create_dash_app
from dash import html, dcc, ctx, no_update

from dash.dependencies import Output, Input, State

import plotly.express as px

from config import get_building_default_options, get_tmp_options, get_ambient_hr_options, get_cop_point_options, get_target_temp_options
from data.solver import RoomTempSolver

# endpoint of this page
URL_RULE = "/room_temp"
# dash internal route prefix, must be start and end with "/"
URL_BASE_PATHNAME = "/dash/room_temp/"


def create_dash(server):
    """Create a Dash view"""
    app = create_dash_app(server, URL_RULE, URL_BASE_PATHNAME)

    # dash app definitions goes here
    app.config.suppress_callback_exceptions = True
    app.title = "ASHP Room Temperature Simulation"

    # Get the various parameter options
    building_default_options = get_building_default_options()
    building_default_option_keys = list(building_default_options)
    tmp_options = get_tmp_options()  # Thermal Mass Parameter name-value lookup
    ambient_hr_options = get_ambient_hr_options()
    ambient_hr_option_keys = list(ambient_hr_options)
    cop_point_options = get_cop_point_options()
    cop_point_option_keys = list(cop_point_options)
    target_temp_options = get_target_temp_options()
    target_temp_option_keys = list(target_temp_options)

    # Prep target temp sliders
    marks = {v: str(v) for v in range(5, 21)}
    slider_inputs = [
        html.Div(
            [
                html.Div([html.Label(f"{hour:02d}")], className="col-md-1"),
                html.Div([dcc.Slider(min=5, max=20, step=0.5, marks=marks, value=5, id=f"target_{hour:02d}")], className="col-md-8")
            ], className="row") for hour in range(24)
    ]

    # layout "constants"
    # > for standard label + input/dropdown
    left_col_class = "col-md-4"
    right_col_class = "col-md-8"

    app.layout = html.Div([

        html.Div(
            [
                html.H1("Room Temperature Simulation", className="header-title"),
                html.P("Space for notes.", className="header-description")
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
                        html.Div([html.Label("Ambient Temp Model")], className=left_col_class),
                        html.Div(
                            dcc.Dropdown(options=ambient_hr_option_keys, value=ambient_hr_option_keys[0],
                                         clearable=False, searchable=False, id="ambient_model"),
                            className=right_col_class)
                    ],
                    className="row"
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
                ),
                html.Div(
                    dcc.Loading(
                        dcc.Graph(
                            id="power_chart",
                            config={"displayModeBar": True}
                        ),
                        id="pwr_spinner",
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
        html.Hr(),

        html.Div(
            [
                # Target Temperature
                html.Div(
                    [
                        html.Div([html.Label("Target Temp Profile")], className=left_col_class),
                        html.Div(
                            [
                                dcc.Dropdown(options=target_temp_option_keys,
                                             value=target_temp_option_keys[0],
                                             clearable=False,
                                             searchable=False,
                                             id="target_temp_profile")
                            ], className=right_col_class)
                    ],
                    className="row"
                ),
                html.Div([html.Label("Hour")])
            ] +
            slider_inputs,
            className="container-fluid"
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
        [Output(f"target_{hour:02d}", "value") for hour in range(24)],
        Input("target_temp_profile", "value")
    )
    def select_profile(target_temp_profile):
        return target_temp_options[target_temp_profile]  # should just be a list of target temps for each hour of a day

    @app.callback(
        [
            Output("temp_chart", "figure"),
            Output("power_chart", "figure"),
            Output("summary_results", "children"),
            Output("compute_errors", "children")
        ],
        Input("compute", "n_clicks"),
        [
            State("heat_loss_factor", "value"),
            State("emitter_std_power", "value"),
            State("fluid_volume", "value"),
            State("tmp", "value"),
            State("floor_area", "value"),
            State("cop_model", "value"),
            State("ambient_model", "value"),
        ] + [State(f"target_{hour:02d}", "value") for hour in range(24)]
    )
    def compute(n_clicks, heat_loss_factor, emitter_std_power, fluid_volume, tmp, floor_area, cop_model, ambient_model, *target_temps):
        if ctx.triggered_id is None:  # no compute on initial load
            return [no_update, no_update, "", ""]

        error_msg = ""

        building_params = {
            "heat_loss_factor": float(heat_loss_factor),
            "emitter_std_power": float(emitter_std_power),
            "tmp": float(tmp),
            "floor_area": float(floor_area),
            "fluid_volume": float(fluid_volume)
        }

        solver = RoomTempSolver(building_params, cop_model, ambient_model, target_temps_hourly=target_temps, initial_temp=16, steps_per_hour=6)

        MAX_ITERS = 10
        while (solver.mean_t_iter_delta > 0.1) and (solver.n_iterations < MAX_ITERS):
            solver.iterate()
            print(solver.max_t_iter_delta, solver.mean_t_iter_delta)

        if solver.n_iterations == MAX_ITERS:
            error_msg = f"Failed to converge after {MAX_ITERS} solver iterations."

        formatted_times = [f"{int(t):02d}:{int(t * 60 + 0.5) % 60:02d}" for t in solver.times]

        tc_data_chunks = [
            # temps
            {
                "x": formatted_times,
                "y": solver.iter_room_temp,
                "mode": "lines",
                "hovertemplate": "Rm: %{y:.1f}C @ %{x}<extra></extra>",
                "name": "Room"
            },
            {
                "x": formatted_times,
                "y": solver.ambient_temps,
                "mode": "lines",
                "hovertemplate": "Outside: %{y:.1f}C @ %{x}<extra></extra>",
                "name": "Ambient"
            },
            # power in. Solver returns Watt.hours
            {
                "x": formatted_times,
                "y": [wh / solver.time_step_duration / 1000 for wh in solver.iter_elec_used],
                "mode": "lines",
                "hovertemplate": "Power: %{y:.1f}kW @ %{x}<extra></extra>",
                "name": "Power",
                "yaxis": "y2",
            }
        ]

        # add the target temps as a stepped coloured background.
        y0 = min(int(min(solver.ambient_temps)), int(min(solver.iter_room_temp)))
        shapes = list()
        shape_template = {
            "fillcolor": "red",
            "line": {"width": 0},
            "opacity": 0.2,
            "type": "rect",
            "x0": None,
            "x1": None,
            "y0": y0,
            "y1": None
            }
        for hr, target_temp in enumerate(solver.target_temps):
            if target_temp > y0:  # see above
                # x0 = f"{hr:02d}:00"
                # x1 = f"{hr+1:02d}:59"
                x0, x1 = hr, hr+1
                shape_template.update({"x0": x0, "x1": x1, "y1": target_temp})
                shapes.append(shape_template.copy())

        tc_layout_chunk = {
            "title": {
                "text": f"Temperatures & Energy In",
                "x": 0.05,
                "xanchor": "left",
            },
            "legend": {"x": -0.07, "xanchor": "left", "y": 1.0, "yanchor": "bottom", "orientation": "h"},
            "xaxis": {"title": "Time", "fixedrange": False, "tickangle": 90},
            "yaxis": {"title": "Temperature", "ticksuffix": "C", "fixedrange": False},
            "yaxis2": {"title": "Power Input", "ticksuffix": "kW", "fixedrange": False, "overlaying": "y", "side": "right", "showgrid": False},
            "shapes": shapes
        }

        pwr_data_chunks = [
            # power in. Solver returns Watt.hours
            {
                "x": formatted_times,
                "y": [wh / solver.time_step_duration / 1000 for wh in solver.iter_elec_used],
                "mode": "lines",
                "hovertemplate": "In: %{y:.1f}kW @ %{x}<extra></extra>",
                "name": "Power In"
            },
            {
                "x": formatted_times,
                "y": [None if cop is None else cop * wh / solver.time_step_duration / 1000 for wh, cop in zip(solver.iter_elec_used, solver.cops)],
                "mode": "lines",
                "hovertemplate": "Out: %{y:.1f}kW @ %{x}<extra></extra>",
                "name": "Power Out"
            },
            # COP
            {
                "x": formatted_times,
                "y": solver.cops,
                "mode": "lines",
                "hovertemplate": "COP: %{y:.2f} @ %{x}<extra></extra>",
                "name": "COP",
                "yaxis": "y2",
            }
        ]

        pwr_layout_chunk = {
            "title": {
                "text": f"Power and COP",
                "x": 0.05,
                "xanchor": "left",
            },
            "legend": {"x": -0.07, "xanchor": "left", "y": 1.0, "yanchor": "bottom", "orientation": "h"},
            "xaxis": {"title": "Time", "fixedrange": False, "tickangle": 90},
            "yaxis": {"title": "Power", "ticksuffix": "kW", "fixedrange": False},
            "yaxis2": {"title": "COP", "fixedrange": False, "overlaying": "y", "side": "right", "showgrid": False},
        }

        # summary
        total_energy = sum(solver.iter_elec_used) / 1000  # kWh
        clean_cops = [c for c in solver.cops if c is not None]
        mean_cop = sum(clean_cops) / len(clean_cops)
        summary = f"Total Energy: {total_energy:.2f}kWh, Mean COP: {mean_cop:.2f}"

        return [
            {"data": tc_data_chunks, "layout": tc_layout_chunk},
            {"data": pwr_data_chunks, "layout": pwr_layout_chunk},
            summary,
            html.B(error_msg, style={"background": "yellow"})
        ]

    return app.server
