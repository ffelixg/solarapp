import requests
import json
from pprint import pprint
from time import sleep

while True:
    try:
        data = requests.get("http://192.168.188.37/solar_api/v1/GetPowerFlowRealtimeData.fcgi").json()
        pprint(data, compact=True)
        with (
            open("log.json", "a") as log,
            open("most_recent.json", "w") as rec
        ):
            dump = json.dumps(data)
            log.write(dump)
            log.write("\n")
            rec.write(dump)
    except Exception as e:
        print(e)
    sleep(10)