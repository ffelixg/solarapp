import requests
from time import sleep, time
from db import execute

execute("""
create table if not exists aggregated (
    time timestamptz,
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
    cnt integer,
);
create index if not exists idx_time_agg on aggregated(time);
""")

execute("""
create table if not exists new (
    time timestamptz,
    pv double,
    akku double,
    grid double,
    load double,
    total double,
);
create index if not exists idx_time_new on new(time);
""")

def dump():
    execute("""
        insert into aggregated
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
            avg(total),
            count(*),
        from (
            select * from new
            where datediff('second', time, (select max(time) from new)) <= 60
        )_
    """)

dump_minute = time() // 60
try:
    while True:
        try:
            current_minute = time() // 60
            if dump_minute != current_minute:
                dump_minute = current_minute
                dump()
                execute("""
                    delete from new
                    where datediff('second', time, (select max(time) from new)) > 300
                """)

            data_req = requests.get("http://192.168.188.37/solar_api/v1/GetPowerFlowRealtimeData.fcgi", timeout=120).json()
            execute("insert into new values (strptime(?, '%Y-%m-%dT%H:%M:%S%z'), ?, ?, ?, ?, ?)", (
                data_req["Head"]["Timestamp"],
                data_req["Body"]["Data"]["Site"]["P_PV"],
                data_req["Body"]["Data"]["Site"]["P_Akku"],
                data_req["Body"]["Data"]["Site"]["P_Grid"],
                data_req["Body"]["Data"]["Site"]["P_Load"],
                data_req["Body"]["Data"]["Site"]["E_Total"],
            ))

            print("logged", time())
            # sleep((-time()) % 0.5) # max 2 requests per second
            sleep(1)

        except Exception as e:
            print(e)

finally:
    dump()
