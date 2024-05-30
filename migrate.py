from db import execute

execute("""
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
    cnt integer,
);
create index if not exists idx_time_agg on aggregated(time);
""")

execute("""
create table if not exists new (
    time timestamp,
    pv double,
    akku double,
    grid double,
    load double,
    total double,
);
create index if not exists idx_time_new on new(time);
""")

execute("""
insert into aggregated
select
    min(tstmp) + (max(tstmp) - min(tstmp)) / 2,
    min(PhotoVoltaik),
    max(PhotoVoltaik),
    avg(PhotoVoltaik),
    min(Akku),
    max(Akku),
    avg(Akku),
    min(Netz),
    max(Netz),
    avg(Netz),
    min(Verbraucher),
    max(Verbraucher),
    avg(Verbraucher),
    avg(Total),
    count(*),
from (
    SELECT *, date_trunc('minute', tstmp) tstmp_min
    FROM (
        SELECT
            strptime(Head.Timestamp, '%Y-%m-%dT%H:%M:%S%z') tstmp,
            Body.Data.Site.P_PV PhotoVoltaik,
            Body.Data.Site.P_Akku Akku,
            Body.Data.Site.P_Grid Netz,
            Body.Data.Site.P_Load Verbraucher,
            Body.Data.Site.E_Total Total,
        FROM read_json_auto('../solaranlage_v1/log.json', format = 'newline_delimited')
    )_
)__
group by tstmp_min
""")