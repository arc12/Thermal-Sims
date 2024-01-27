from app.dash_apps import create_dash_app
from dash import html, dcc, ctx, no_update

from dash.dependencies import Output, Input, State

from config import get_cop_point_options
from utilities import COP

# endpoint of this page
URL_RULE = "/cop_curves"
# dash internal route prefix, must be start and end with "/"
URL_BASE_PATHNAME = "/dash/cop_curves/"


def create_dash(server):
    """Create a Dash view"""
    app = create_dash_app(server, URL_RULE, URL_BASE_PATHNAME)

    # dash app definitions goes here
    app.config.suppress_callback_exceptions = True
    app.title = "ASHP COP Curves"

    # layout "constants"
    # > for standard label + input/dropdown
    left_col_class = "col-md-4"
    right_col_class = "col-md-8"

    app.layout = html.Div([

        html.Div(
            [
                html.H1("ASHP COP Curves", className="header-title"),
                html.P("Splines built from datasheet points.", className="header-description")
            ],
            className="header"),

        html.Div(
            [
                html.Div(
                    [
                        html.Div([html.Label("COP vs")], className=left_col_class),
                        html.Div(
                            dcc.Dropdown(options={"ambient": "Ambient", "lwt": "LWT"}, value="amb",
                                         clearable=False, searchable=False, id="cop_vs"),
                            className=right_col_class)
                    ], className="row"
                ),
                html.Div(
                    [
                        html.Div([html.Label("COP Model")], className=left_col_class),
                        html.Div(
                            dcc.Dropdown(clearable=False, searchable=False, multi=True, id="cop_model"),
                            className=right_col_class)
                    ],
                    className="row"
                )
            ],
            className="container-fluid"
        ),

        html.Div(
            [
                html.Div(
                    dcc.Loading(
                        dcc.Graph(
                            id="cop_chart",
                            config={"displayModeBar": True}
                        ),
                        id="temp_spinner",
                        type="circle"
                    ),
                    className="card"
                )
            ],
            className="wrapper"
        )
    ],
        className="wrapper"
    )

    @app.callback(
        Output("cop_model", "options"),
        Input("cop_vs", "value")
    )
    def change_cop_vs(cop_vs):
        return list(get_cop_point_options(vs=cop_vs))

    @app.callback(
        [
            Output("cop_chart", "figure")
            # Output("summary_results", "children")
        ],
        Input("cop_model", "value"),
        State("cop_vs", "value")
    )
    def compute(cop_model_options, cop_vs):
        if ctx.triggered_id is None:  # no compute on initial load
            return [no_update]

        cop_defs = get_cop_point_options(cop_vs)

        data_chunks = []
        if cop_vs == "ambient":
            temps = list(range(-10, 13))
            t_key = "T_amb"
            x_title = "Ambient Temperature"
        else:
            temps = list(range(30, 56))
            t_key = "LWT"
            x_title = "LWT"

        for option in cop_model_options:
            cop_def = cop_defs[option]

            # points
            t_points, cop_points = cop_def[t_key], cop_def["COP"]
            # skip this for now as it makes the legend messy (if points in legend) or the use of the legend to show/hide curves silly (cant hide points if not in legend!)
            # TODO add a checkbox to control point plotting
            # data_chunks.append(
            #     {
            #         "x": t_points,
            #         "y": cop_points,
            #         "mode": "markers",
            #         "hovertemplate": option + ": %{y:.2f} @ T=%{x}C<extra></extra>",
            #         "name": option
            #     }
            # )

            # spline
            cop_model = COP(t_points, cop_points)
            data_chunks.append(
                {
                    "x": temps,
                    "y": [cop_model.cop(t) for t in temps],
                    "mode": "lines",
                    "hovertemplate": option + ": %{y:.2f} @ T=%{x}<extra></extra>",
                    "name": option
                }
            )

        layout_chunk = {
            # "title": {
            #     "text": f"Power and COP",
            #     "x": 0.05,
            #     "xanchor": "left",
            # },
            "legend": {"x": -0.07, "xanchor": "left", "y": 1.0, "yanchor": "bottom", "orientation": "h"},
            "xaxis": {"title": x_title, "ticksuffix": "C", "range": (min(temps), max(temps)), "tickangle": 90},
            "yaxis": {"title": "COP", "fixedrange": False}
        }

        return [{"data": data_chunks, "layout": layout_chunk}]

    return app.server
