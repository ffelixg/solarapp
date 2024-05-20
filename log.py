import requests
import json
from pprint import pprint
from time import sleep, time
from duckdb import connect

duckdisk = connect("db.duckdb", config={"threads": 2})
duckmem = connect(config={"threads": 2})

duckdisk.execute("""
create table if not exists aggregated (
    time timestamp,
    pv_min double,
    pv_max double,
    pv_avg double,
    akku_min double,
    akku_max double,
    akku_avg double,
    grid_min double,
    grid_max double,
    grid_avg double,
    load_min double,
    load_max double,
    load_avg double,
    total double,
);
create index if not exists idx_time on aggregated(time);
""")
# duckdisk.execute("select * from aggregated").df()
# duckdisk.execute("truncate aggregated")

duckmem.execute("""
create table if not exists new (
    time timestamp,
    pv double,
    akku double,
    grid double,
    load double,
    total double,
);
create index if not exists idx_time on new(time);
""")
# duckmem.execute("select * from new").df()
# duckmem.execute("truncate new")

def do_logging():
    curdisk = duckdisk.cursor()
    curmem = duckmem.cursor()

    def to_disk():
        data_store = duckmem.execute("""
            select
                min(time) + (max(time) - min(time)) / 2,
                min(pv),
                max(pv),
                avg(pv),
                min(akku),
                max(akku),
                avg(akku),
                min(grid),
                max(grid),
                avg(grid),
                min(load),
                max(load),
                avg(load),
                avg(total)
            from new
        """).arrow()
        curdisk.execute("insert into aggregated select * from data_store")

    dump_minute = time() // 60
    while True:
        try:
            current_minute = time() // 60
            if dump_minute != current_minute:
                dump_minute = current_minute
                to_disk()
                curmem.execute("truncate new")

            data_req = requests.get("http://192.168.188.37/solar_api/v1/GetPowerFlowRealtimeData.fcgi").json()
            curmem.execute("insert into new values (strptime(?, '%Y-%m-%dT%H:%M:%S%z'), ?, ?, ?, ?, ?)", (
                data_req["Head"]["Timestamp"],
                data_req["Body"]["Data"]["Site"]["P_PV"],
                data_req["Body"]["Data"]["Site"]["P_Akku"],
                data_req["Body"]["Data"]["Site"]["P_Grid"],
                data_req["Body"]["Data"]["Site"]["P_Load"],
                data_req["Body"]["Data"]["Site"]["E_Total"],
            ))

            print("logged", time())
            sleep((-time()) % 0.5) # max 2 requests per second

        except Exception as e:
            print(e)

        finally:
            to_disk()