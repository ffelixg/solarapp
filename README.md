Collect and log data of my Fronius inverter using duckdb. New data comes in every second. Historic data (5min+) is only kept in aggregated form - one line per minute with min/avg/max. The data is visualized using Plotly inside a dash app.

The data provided by the inverter includes current usage of the solar panels, battery, energy provider and home appliances as well as battery state and total power generated. The top visual shows a live ticker of the current data and the bottom one shows historic data for the selected day, aggregated per minute as well as the two metrics providing totals.

![GIF name](./preview.gif)
