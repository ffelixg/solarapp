import dash
from dash import html, dcc, Input, Output, State
from db import execute
import datetime

app = dash.Dash(__name__)

names_colors = (
    ("PV", "00ff00"),
    ("Akku", "00ffff"),
    ("Grid", "ff0000"),
    ("Load", "000000"),
)

def dates(startdate, direction):
    offsets = []
    display = []
    i = 0
    newdate = startdate
    while newdate.month == startdate.month:
        offsets.append(i)
        display.append(str(newdate))
        i += 1
        newdate += direction * datetime.timedelta(days=1)
    return offsets, display

_, dates = dates(datetime.date(2020, 5, 31), -1)

app.layout = html.Div(
    children=[
        html.Div(style={"hidden": "true"}, id="dummy"),
        dcc.Interval(
            id='interval',
            interval=1 * 1000,
            n_intervals=0
        ),
        dcc.Store(id="max_time", data="2000-05-20 19:16:54"),
        dcc.Graph(
            figure={
                'data': [
                    {
                        'x': [], 'y': [],
                        "type": 'scatter',
                        "mode": 'lines',
                        'line': {'color': f'#{color}ff', 'width': 3},
                        "name": name
                    }
                    for name, color in names_colors
                ],
                'layout': {
                    'xaxis': {'range': [0, 5]},
                    'yaxis': {'title': 'Watt'},
                    'hovermode': 'x unified',
                }
            },
            style={
                "width": "100%",
                "height": "48vh",
            },
            id="fig_live"
        ),
        dcc.Slider(
            0, len(dates), 1, value=0,
            marks={i: j for i, j in enumerate(dates)},
            vertical=False, id="date_slicer",
        ),
        html.Div([
            # html.Div([
            #     dcc.Slider(
            #         0, len(dates), 1, value=0,
            #         marks={i: j for i, j in enumerate(dates)},
            #         vertical=True, id="date_slicer",
            #         verticalHeight=500,
            #     ),
            # ], style={
            #     "display": "flex",
            #     "float": "left",
            #     "width": "25%",
            #     "height": "100%",
            #     # "border": "1rem",
            # }),
                dcc.Graph(
                    figure={
                        'data': [],
                        'layout': {
                            'xaxis': {},
                            'yaxis': {'title': 'Watt'},
                            'hovermode': 'x unified',
                        }
                    },
                    id="fig_aggregate",
                    style={"width": "100%", "height": "100%"},
                ),
            # ], style={"display": "flex", "float": "right", "width": "75%"}),
        ], style={
            "width": "100%",
            "height": "48vh",
        }),
    ]
)


def transpose(rows, i):
    return [row[i] for row in rows]


@dash.callback(
    Output("fig_aggregate", "figure"),
    Input("dummy", "children"),
)
def load_graph(dummy):
    data = execute("select * from aggregated where time is not null", fetch="fetchall")
    (min_date,), = execute("select min(time) from aggregated", fetch="fetchall")
    fig = dash.Patch()
    names = {1: "PV", 4: "Akku", 7: "Grid", 10: "Load"}
    def gettraces(i, color):
        return [
            {
                'x': X, 'y': transpose(data, i),
                'type': 'scatter',
                "fill": None,
                "fillgroup": 'one',
                "mode": 'lines',
                'line': {'color': '#000000', 'width': 0},
                "hoverinfo": "none",
                "showlegend": False,
            }, {
                'x': X, 'y': transpose(data, i+1),
                "type": 'scatter',
                "fill": 'tonexty',
                "fillgroup": 'one',
                "fillcolor": f"#{color}44",
                "mode": 'lines',
                'line': {'color': '#000000', 'width': 0},
                "hovertext": [f"{names[i]} {row[i]:.2f} | {row[i+2]:.2f} | {row[i+1]:.2f}" for row in data],
                "hoverinfo": "text",
                "name": names[i],
            }, {
                'x': X, 'y': transpose(data, i+2),
                "type": 'scatter',
                "mode": 'lines',
                'line': {'color': f'#{color}ff', 'width': 3},
                "hoverinfo": "none",
                "showlegend": False,
            },
        ]
    X = transpose(data, 0)
    fig['data'].extend([
        *gettraces(1, "00ff00"),
        *gettraces(4, "00ffff"),
        *gettraces(7, "ff0000"),
        *gettraces(10, "000000"),
    ])
    print("game")
    return fig


@dash.callback(
    Output("fig_live", "figure", allow_duplicate=True),
    Output("max_time", "data"),
    Input('interval', 'n_intervals'),
    Input("dummy", "children"),
    State("max_time", "data"),
    prevent_initial_call=True,
)
def update_graph(interval, _, max_time):
    new_data = execute("""
        SELECT
            time, pv, akku, grid, load
        FROM new
        where time > ?
    """, parameters=[max_time], fetch="fetchall")
    if not new_data:
        raise dash.exceptions.PreventUpdate
    fig = dash.Patch()
    times = transpose(new_data, 0)
    max_time_new = max(times)
    for i in range(4):
        fig["data"][i]["x"].extend(times)
        fig["data"][i]["y"].extend(transpose(new_data, i+1))

    fig["layout"]["xaxis"]["range"][0] = max_time_new - datetime.timedelta(seconds=300)
    fig["layout"]["xaxis"]["range"][1] = max_time_new
    return fig, max_time_new

# Run the app
if __name__ == '__main__':
    app.run_server(
        debug=True,
        host='0.0.0.0',
    )