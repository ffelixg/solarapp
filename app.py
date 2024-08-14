import dash
from dash import html, dcc, Input, Output, State
from db import execute
import datetime
import pytz

app = dash.Dash(
    __name__,
    title='Solaranlage',
    update_title=None,
)

names_colors = (
    ("PV", "00ff00"),
    ("Akku", "00ffff"),
    ("Netz", "ff0000"),
    ("Haus", "000000"),
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
        html.Div([
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
                        'yaxis': {'title': '', 'side': 'right'},
                        'margin': {'b': 40, 'l': 0, 'r': 40, 't': 0},
                        'showlegend': False,
                        'hovermode': 'x unified',
                    }
                },
                style={
                    "width": "90%",
                    "height": "100%",
                    "float": "left",
                },
                id="fig_live"
            ),
            html.Div(
                [
                    html.Div(
                        f"{name}: 69W",
                        style={
                            "background-color": f"#{color}44",
                            "padding": "10%",
                            "margin": "auto",
                            "border-radius": "1rem",
                        },
                        id=name,
                    )
                    for name, color in names_colors
                ], style={
                    "width": "10%",
                    "height": "100%",
                    "float": "right",
                    "display": "flex",
                    "flex-direction": "column",
                    "justify-content": "center",
                }
            ),
        ], style={
            "width": "100%",
            "height": "42vh",
        }),
        html.Div(
            dcc.Slider(
                0, 2, 1,
                vertical=False, id="date_slicer",
            ),
            style={"margin": "0rem 4rem 1em 0rem"},
        ),
        dcc.Graph(
            figure={
                'data': [],
                'layout': {
                    'xaxis': {'range': [0, 1]},
                    'yaxis': {'title': '', 'range': [-11000, 11000], 'side': 'right'},
                    'margin': {'b': 40, 'l': 0, 'r': 40, 't': 0},
                    'showlegend': False,
                    'hovermode': 'x unified',
                }
            },
            id="fig_aggregate",
            style={
                "width": "100%",
                "height": "42vh",
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
def update_aggregate(date_ord):
    today_ord = datetime.datetime.now(pytz.timezone("Europe/Berlin")).date().toordinal()
    if not date_ord:
        date_ord = today_ord
    date = datetime.date.fromordinal(date_ord)
    slicer_min = date_ord - 7
    slicer_max = date_ord + 7
    slicer_marks = {
        i: {
            "label": f"{datetime.date.fromordinal(i):%d.%m.%Y %A}",
            "style": {
                "width": "1px",
                "color": "red" if i == today_ord else "black" if i == date_ord else "gray"
            },
        }
        for i in range(slicer_min, slicer_max + 1)
    }
    data = execute("""
        select
            time at time zone 'Europe/Berlin',
            round(pv_min)::int, round(pv_max)::int, round(pv_avg)::int,
            round(akku_min)::int, round(akku_max)::int, round(akku_avg)::int,
            round(grid_min)::int, round(grid_max)::int, round(grid_avg)::int,
            round(load_min)::int, round(load_max)::int, round(load_avg)::int,
        from aggregated
        join (
            select dt as start, dt + interval '1 day' as end
            from (select ? at time zone 'Europe/Berlin' as dt)_
        ) as filter
        on filter.start <= time and time < filter.end
        order by time
    """, fetch="fetchall", parameters=[date])

    fig = dash.Patch()
    fig["layout"]["xaxis"]["range"] = [date, date + datetime.timedelta(days=1)]

    names = {k: name for k, (name, _) in zip([1, 4, 7, 10], names_colors)}
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
                "hoverinfo": "none",
            }, {
                'x': X, 'y': transpose(data, i+2),
                "type": 'scatter',
                "mode": 'lines',
                'line': {'color': f'#{color}ff', 'width': 3},
                "hovertext": [f"{names[i]} {row[i]} < {row[i+2]} < {row[i+1]}" for row in data],
                "hoverinfo": "x+text",
                "name": names[i],
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
    Output("fig_live", "figure"),
    Output("max_time", "data"),
    *[Output(name, "children") for name, _ in names_colors],
    Input('interval', 'n_intervals'),
    Input("dummy", "children"),
    State("max_time", "data"),
)
def update_ticker(interval, _, max_time):
    print(max_time)
    new_data = execute("""
        select
            time at time zone 'Europe/Berlin',
            round(pv)::int, round(akku)::int, round(grid)::int, round(load)::int,
        from new
        where time > cast(? as TIMESTAMP) at time zone 'Europe/Berlin'
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

    return (
        fig, max_time_new,
        *[
            f"{name}: {int(val)}W"
            for (name, _), val in zip(names_colors, new_data[-1][1:])
        ]
    )

# Run the app
if __name__ == '__main__':
    app.run(
        debug=False,
        host='0.0.0.0',
    )