from db import execute

execute("""
drop index idx_time_agg;
alter table aggregated rename to aggregated_old;
create table aggregated as select *, 0::double battery_pct from aggregated_old;
drop table aggregated_old;
create index if not exists idx_time_agg on aggregated(time);
""")

execute("""
drop index idx_time_new;
alter table new rename to new_old;
create table new as select *, 0::double battery_pct from new_old;
drop table new_old;
create index if not exists idx_time_new on new(time);
""")
