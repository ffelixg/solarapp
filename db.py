from duckdb import connect as _connect
from time import time


def connect():
    now = time()
    while time() - now < 5:
        try:
            return _connect("db.duckdb")
        except Exception:
            pass
    raise Exception("Duckdb connection unsuccessful after 5 seconds.")

def execute(*args, fetch=None, **kwargs):
    with connect() as con:
        if fetch:
            return getattr(con.execute(*args, **kwargs), fetch)()
        else:
            return con.execute(*args, **kwargs)