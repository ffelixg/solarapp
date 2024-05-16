import dash
from dash import html, dcc, Input, Output, State
from duckdb import query

app = dash.Dash(__name__)

app.layout = html.Div(
    children=[
        html.Div(style={"hidden": "true"}, id="dummy"),
        dcc.Interval(
            id='interval',
            interval=2 * 1000,
            n_intervals=0
        ),
        dcc.Graph(
            figure={
                'data': [
                    # {'x': [1,2,3], 'y': [5,3,4], 'type': 'line', 'name': 'Line Chart'}
                ],
                'layout': {
                    # 'title': 'Line Chart',
                    # 'xaxis': {
                    #     'title': 'Zeit',
                    #     'tickformat': '%b %Y',  # this controls the format of the x-value in the hover box
                    #     'tickmode': 'array',
                    #     # 'ticktext': xticktext,
                    #     # 'tickvals': xtickvals
                    # },
                    # 'yaxis': {'title': 'kW'},
                    # 'showlegend': False,
                    # 'hovertemplate': '%{hovertext}<br>',
                    # 'hoverlabel': {"bgcolor": "white"},
                    # 'xaxis': {'gridcolor': 'transparent', 'title': {'text': 'Datum'}},
                    # 'yaxis': {'gridcolor': 'transparent', 'title': {'text': 'Rechnungszeit'}},
                    # 'title': 'Line Chart',
                    'xaxis': {
                        # 'title': 'Zeit'
                    },
                    'yaxis': {'title': 'Watt'},
                    'hovermode': 'x unified',
                }
            },
            style={
                "width": "100%",
                "height": "100vh",
            },
            id="graph"
        )
    ]
)

@dash.callback(
    Output("graph", "figure"),
    Input("dummy", "children"),
)
def load_graph(dummy):
    q = query("""
        SELECT
            strptime(Head.Timestamp, '%Y-%m-%dT%H:%M:%S%z'),
            Body.Data.Site.P_PV PhotoVoltaik,
            Body.Data.Site.P_Akku Akku,
            Body.Data.Site.P_Grid Netz,
            Body.Data.Site.P_Load Verbraucher
        FROM read_json_auto('log.json', format = 'newline_delimited');
    """)
    names = q.columns
    data = q.fetchall()
    fig = dash.Patch()
    fig['data'].extend([
        {'x': [row[0] for row in data], 'y': [row[1] for row in data], 'type': 'line', 'name': names[1], 'line': {'color': '#00ff00', 'width': 4}},
        {'x': [row[0] for row in data], 'y': [row[2] for row in data], 'type': 'line', 'name': names[2], 'line': {'color': '#00ffff', 'width': 4}},
        {'x': [row[0] for row in data], 'y': [row[3] for row in data], 'type': 'line', 'name': names[3], 'line': {'color': '#ff0000', 'width': 4}},
        {'x': [row[0] for row in data], 'y': [row[4] for row in data], 'type': 'line', 'name': names[4], 'line': {'color': '#000000', 'width': 4}},
        # {'x': [row[0] for row in data], 'y': [[*row[1:]] for row in data], 'type': 'line', 'name': names[4]},
    ])
    # fig['layout'] = {
    #     'title': 'Line Chart',
    #     'xaxis': {'title': 'Zeit'},
    #     'yaxis': {'title': 'kW'},
    #     'hovermode': 'x unified',
    # }
    # df = q.df()
    # fig = px.line(df, x=names[0], y=names[1:])
    # fig.update_traces(hovertemplate="%{x|%d/%m} %{y}")
    # fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgray',
    #     # range=xl,
    #     # range=(df[names[0]].values.min(), df[names[0]].values.max()),
    #     dtick="M1", tickformat="%b\n%Y")
    # fig.update_layout(
    #     hovermode='x unified',
    # )
    return fig

@dash.callback(
    Output("graph", "figure", allow_duplicate=True),
    Input('interval', 'n_intervals'),
    prevent_initial_call=True,
)
def update_graph(interval):
    (time, *entries), = query("""
        SELECT
            strptime(Head.Timestamp, '%Y-%m-%dT%H:%M:%S%z'),
            Body.Data.Site.P_PV,
            Body.Data.Site.P_Akku,
            Body.Data.Site.P_Grid,
            Body.Data.Site.P_Load
        FROM read_json_auto('most_recent.json');
    """).fetchall()
    fig = dash.Patch()
    for i, entry in enumerate(entries):
        fig["data"][i]["x"].append(time)
        fig["data"][i]["y"].append(entry)
    return fig

# Run the app
if __name__ == '__main__':
    app.run_server(
        debug=True,
        host='0.0.0.0',
    )