#!/usr/bin/env python
#
#   Processing Stage 1 - CSV to Rearranged JSON
#

import datetime
import glob
import json
import pandas as pd
from dateutil.parser import parse
import matplotlib.pyplot as plt

# Location of CSV file we wish to read in
CSV_FILES = "./csv_data/*.csv"

# Times we are interested in. 
START_TIME = "2024-10-03T12:16:00Z"
DURATION = 60*3


# Output data structure
OUTPUT_BLOB = {}

# Generate entries in the output blob
_start_time = parse(START_TIME)
for i in range(DURATION):
    _new_time = _start_time + datetime.timedelta(seconds=i)

    OUTPUT_BLOB[_new_time.isoformat()] = {}

print(f"Generated {len(list(OUTPUT_BLOB.keys()))} time slots for output data.")

def process_csv(filename):
    global OUTPUT_BLOB

    print(f"Reading in {filename}")
    _data = pd.read_csv(filename)

    # Iterating over a pandas DataFrame! I'm going to jail.
    for _entry in _data.iterrows():
        _data = _entry[1]

        # Extract the datetime, but round to the nearest second
        _datetime = parse(_data['datetime']+"Z")
        if _datetime.microsecond >= 500000:
            _datetime += datetime.timedelta(seconds=1)
        _datetime.replace(microsecond=0)

        # Correct for GPS vs UTC time
        # Newer versions of auto_rx and TTGO include a ref_datetime field
        if _data['ref_datetime'] == 'GPS':
            # GPS is 18 seconds in front of UTC
            _datetime += datetime.timedelta(seconds=-18)
        elif _data['ref_datetime'] == 'UTC':
            #print(_data)
            pass
        else:
            # No ref_datetime field
            # If it's auto_rx, and we're seeing a vaisala sonde, do the correction
            if _data['software_name'] == 'radiosonde_auto_rx':
                if 'manufacturer' == 'Vaisala':
                    _datetime += datetime.timedelta(seconds=-18)
            else:
                # Otherwise, print out the data so we can figure out what to do...
                print("NO REF DATETIME")
                print(_data)

        _datetime_str = _datetime.isoformat()

        if _datetime_str in OUTPUT_BLOB:
            #print(f"In range: {_datetime_str}")
            #print(_data)

            # Gather station and SNR information
            _station = _data['uploader_callsign']
            _snr = _data['snr']
            _station_loc = _data['uploader_position']

            # Sanity check data
            if type(_station_loc) == str:
                _loc_fields = _station_loc.split(',')
                if len(_loc_fields) == 2:
                    _station_lat = float(_loc_fields[0])
                    _station_lon = float(_loc_fields[1])
                else:
                    continue
            else:
                continue
            
            if _snr > 0 and _snr < 50:
                OUTPUT_BLOB[_datetime_str][_station] = {
                    'snr': _snr,
                    'lat': _station_lat,
                    'lon': _station_lon
                }
            else:
                continue


# Read in CSV files
_files = glob.glob(CSV_FILES)

for _file in _files:
    process_csv(_file)


# Write out JSON
_outdata = json.dumps(OUTPUT_BLOB)
_f = open("processed.json",'w')
_f.write(_outdata)
_f.close()

# Print some statistics on the results
_keys = list(OUTPUT_BLOB.keys())
_keys.sort()

_times = []
_stations = []

for _key in _keys:
    _times.append(parse(_key))
    _stations.append(len(list(OUTPUT_BLOB[_key].keys())))
    print(f"{_key}: {len(list(OUTPUT_BLOB[_key].keys()))}")

#... and plot number of stations vs time
plt.plot(_times, _stations)
plt.title("SondeHub RXers during 2024-10-03 12:17:40Z X9.1 Flare")
plt.xlabel("UTC Time")
plt.ylabel("Stations Reporting")
plt.grid()
plt.show()