import dash
from dash import html, dcc, Input, Output, State
from duckdb import query
import threading
# from log import do_logging, duckdisk, duckmem
import logging

# threading.Thread(target=do_logging).start()
from duckdb import connect
duckdisk = connect("db.duckdb", config={"threads": 2}, read_only=True)
curdisk = duckdisk.cursor()
# curmem = duckmem.cursor()
disklock = threading.Lock()
memlock = threading.Lock()

app = dash.Dash(__name__)

app.layout = html.Div(
    children=[
        html.Div(style={"hidden": "true"}, id="dummy"),
        dcc.Interval(
            id='interval',
            interval=5 * 1000,
            n_intervals=0
        ),
        dcc.Graph(
            figure={
                'data': [],
                'layout': {
                    'xaxis': {},
                    'yaxis': {'title': 'Watt'},
                    'hovermode': 'x unified',
                }
            },
            style={
                "width": "100%",
                "height": "50vh",
            },
            id="fig_live"
        ),
        dcc.Graph(
            figure={
                'data': [],
                'layout': {
                    'xaxis': {},
                    'yaxis': {'title': 'Watt'},
                    'hovermode': 'x unified',
                }
            },
            style={
                "width": "100%",
                "height": "50vh",
            },
            id="fig_aggregate"
        ),
    ]
)

@dash.callback(
    Output("fig_aggregate", "figure"),
    Input("dummy", "children"),
)
def load_graph(dummy):
    try:
        with disklock:
            data = curdisk.execute("select * from aggregated where time is not null").fetchall()
        fig = dash.Patch()
        def getcol(i):
            return [row[i] for row in data]
        names = {1: "PV", 4: "Akku", 7: "Grid", 10: "Load"}
        def gettraces(i, color):
            return [
                {'x': X, 'y': getcol(i),
                    'type': 'scatter',
                    "fill": None,
                    "fillgroup": 'one',
                    "mode": 'lines',
                    'line': {'color': '#000000', 'width': 0},
                    "hoverinfo": "none",
                    "showlegend": False,
                },
                {'x': X, 'y': getcol(i+1),
                    "type": 'scatter',
                    "fill": 'tonexty',
                    "fillgroup": 'one',
                    "fillcolor": f"#{color}44",
                    "mode": 'lines',
                    'line': {'color': '#000000', 'width': 0},
                    "hovertext": [f"{names[i]} {row[i]:.2f} | {row[i+2]:.2f} | {row[i+1]:.2f}" for row in data],
                    "hoverinfo": "text",
                    "name": names[i],
                },
                {'x': X, 'y': getcol(i+2),
                    "type": 'scatter',
                    "mode": 'lines',
                    'line': {'color': f'#{color}ff', 'width': 3},
                    "hoverinfo": "none",
                    "showlegend": False,
                },
            ]
        X = getcol(0)
        fig['data'].extend([
            *gettraces(1, "00ff00"),
            *gettraces(4, "00ffff"),
            *gettraces(7, "ff0000"),
            *gettraces(10, "000000"),
        ])
        print("game")
        return fig
    except Exception as e:
        logging.exception("Error in load_graph")
        raise

# @dash.callback(
#     Output("graph", "figure", allow_duplicate=True),
#     Input('interval', 'n_intervals'),
#     prevent_initial_call=True,
# )
# def update_graph(interval):
#     (time, *entries), = query("""
#         SELECT
#             strptime(Head.Timestamp, '%Y-%m-%dT%H:%M:%S%z'),
#             Body.Data.Site.P_PV,
#             Body.Data.Site.P_Akku,
#             Body.Data.Site.P_Grid,
#             Body.Data.Site.P_Load
#         FROM read_json_auto('most_recent.json');
#     """).fetchall()
#     fig = dash.Patch()
#     for i, entry in enumerate(entries):
#         fig["data"][i]["x"].append(time)
#         fig["data"][i]["y"].append(entry)
#     return fig

# Run the app
if __name__ == '__main__':
    app.run_server(
        debug=True,
        host='0.0.0.0',
    )