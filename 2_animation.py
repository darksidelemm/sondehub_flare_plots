#!/usr/bin/env python
#
#   Processing Stage 2 - JSON to animation
#

import datetime
import glob
import json
import pandas as pd
import numpy as np
from dateutil.parser import parse
import cartopy
import cartopy.feature as cpf
from matplotlib import animation, cm, pyplot as plt

from datetime import timedelta


SNR_MIN = 10
SNR_MAX = 25

MAP_EXTENT = (-20.0, 60.0, 26.0, 71.0)

INPUT_JSON = "processed.json"

# Load in JSON data
_f = open(INPUT_JSON,'r')
data = json.loads(_f.read())
_f.close()

print("Loaded data")

# Get list of times
_times = list(data.keys())
_times.sort()

# Clip times to just around event
_times = _times[90:120]



axis = plt.axes(projection=cartopy.crs.PlateCarree())
axis.clear()
axis.add_feature(cpf.COASTLINE.with_scale("10m"))
axis.add_feature(cpf.BORDERS.with_scale("10m"), edgecolor="gray", linewidth=0.3)

scatter = axis.scatter([], [])
title = plt.title("Date")
axis.set_extent(MAP_EXTENT)

def animate(i):
    title.set_text(f"{_times[i]}")

    print(_times[i])

    lons = []
    lats = []
    vals = []

    for _station in data[_times[i]]:
        lat  = data[_times[i]][_station]['lat']
        lon  = data[_times[i]][_station]['lon']
        lon = lon % 360  # make sure it's positive, cartopy needs that
        snr  = data[_times[i]][_station]['snr']

        lons.append(lon)
        lats.append(lat)
        vals.append(snr)

    scatter.set_offsets(np.array((lons, lats)).T)
    scale = (SNR_MIN, SNR_MAX)
    nvals = np.array(vals)
    if len(nvals) > 0:
        # re-center about 0 and clip
        nvals = np.clip(nvals - scale[0], 0, scale[1] - scale[0])
        # normalize data from 0 to 1
        nvals /= scale[1] - scale[0]
        scatter.set_color(cm.plasma(nvals))

def init():
    return scatter

ani = animation.FuncAnimation(
    plt.gcf(),
    animate,
    init_func=init,
    frames=len(_times),
    repeat=True,
    interval=200,
)
axis.figure.tight_layout(pad=0.0, w_pad=0.0, h_pad=0.0)
axis.figure.subplots_adjust(
    left=0, bottom=0, right=1, top=1, wspace=None, hspace=None
)

#print("Saving animation.")
#ani.save("output.gif", writer="imagemagick", fps=5)

plt.show()