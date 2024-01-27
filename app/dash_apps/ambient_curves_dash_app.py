from app.dash_apps import create_dash_app
from dash import html, dcc

from config import get_ambient_hr_options
from utilities import AmbientTemps

# endpoint of this page
URL_RULE = "/ambient"
# dash internal route prefix, must be start and end with "/"
URL_BASE_PATHNAME = "/dash/ambient/"


def make_ambient_curves(drop_constant=True):
    data_chunks = []
    hrs = list(range(0, 24))
    for option, t_points in get_ambient_hr_options().items():
        if drop_constant and option.lower().startswith("constant"):
            continue
        amb_spline = AmbientTemps(t_points)
        data_chunks.append(
            {
                "x": hrs,
                "y": [amb_spline.temp(hr) for hr in hrs],
                "mode": "lines",
                "hovertemplate": option + ": %{y:.1f}C @ t=%{x}<extra></extra>",
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
        "xaxis": {"title": "Hour", "fixedrange": False, "tickangle": 90},
        "yaxis": {"title": "Temperature", "ticksuffix": "C", "fixedrange": False}
    }

    return {"data": data_chunks, "layout": layout_chunk}


def create_dash(server):
    """Create a Dash view"""
    app = create_dash_app(server, URL_RULE, URL_BASE_PATHNAME)

    # dash app definitions goes here
    app.config.suppress_callback_exceptions = True
    app.title = "Ambient Options"

    app.layout = html.Div([

        html.Div(
            [
                html.H1("Ambient Temperature Curve Options", className="header-title")
            ],
            className="header"),

        html.Div(
            [
                html.Div(
                    dcc.Loading(
                        dcc.Graph(
                            id="temp_chart",
                            config={"displayModeBar": True},
                            figure=make_ambient_curves()
                        ),
                        id="temp_spinner",
                        type="circle"
                    ),
                    className="card"
                )
            ],
            className="wrapper"
        )
        ]
    )

    return app.server
