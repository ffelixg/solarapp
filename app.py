import dash
from dash import html, dcc, Input, Output, State
from db import execute
import datetime

app = dash.Dash(
    __name__,
    title='Solaranlage',
    update_title=None,
)

names_colors = (
    ("PV", "00ff00"),
    ("Akku", "00ffff"),
    ("Grid", "ff0000"),
    ("Load", "000000"),
)

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
                "height": "45vh",
            },
            id="fig_live"
        ),
        dcc.Slider(
            0, 2, 1,
            vertical=False, id="date_slicer",
        ),
        dcc.Graph(
            figure={
                'data': [],
                'layout': {
                    'xaxis': {},
                    'yaxis': {'title': 'Watt', 'range': [-11000, 11000]},
                    'hovermode': 'x unified',
                }
            },
            id="fig_aggregate",
            style={
                "width": "100%",
                "height": "45vh",
            },
        ),
    ]
)


def transpose(rows, i):
    return [row[i] for row in rows]


@dash.callback(
    Output("fig_aggregate", "figure"),
    Output("date_slicer", "value"),
    Output("date_slicer", "min"),
    Output("date_slicer", "max"),
    Output("date_slicer", "marks"),
    Input("date_slicer", "value"),
)
def initial_load(date_ord):
    if not date_ord:
        date_ord = datetime.date.today().toordinal()
    slicer_min = date_ord - 15
    slicer_max = date_ord + 15
    slicer_marks = {
        i: f"{datetime.date.fromordinal(i):%d.%m.%Y}"
        for i in range(slicer_min, slicer_max + 1)
    }
    data = execute("""
        select * from aggregated
        where time >= ? and time < ?
        order by time
    """, fetch="fetchall", parameters=[
        datetime.date.fromordinal(date_ord),
        datetime.date.fromordinal(date_ord + 1),
    ])
    fig = dash.Patch()
    names = {1: "PV", 4: "Akku", 7: "Grid", 10: "Load"}
    X = transpose(data, 0)
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
    fig['data'] = ([
        *gettraces(1, "00ff00"),
        *gettraces(4, "00ffff"),
        *gettraces(7, "ff0000"),
        *gettraces(10, "000000"),
    ])
    return (
        fig,
        date_ord,
        slicer_min,
        slicer_max,
        slicer_marks,
    )


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
        select
            time, pv, akku, grid, load
        from new
        where time > ?
        order by time
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
    app.run(
        debug=False,
        host='0.0.0.0',
    )