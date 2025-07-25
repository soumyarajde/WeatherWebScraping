import h5py
import matplotlib.pyplot as plt
import numpy as np

# --- Read Home Assistant Data ---
ha_file = 'weather_ha.h5'
ha_dates = []
ha_high = []
ha_low = []

with h5py.File(ha_file, 'r') as f:
    for date in sorted([k for k in f.keys() if k.startswith('202')]):
        ha_dates.append(date)
        subgrp = f[f"{date}/home_assistant"]
        # Try/except in case there are missing datasets
        try:
            ha_high.append(subgrp['high_temp'][()])
        except KeyError:
            ha_high.append(np.nan)
        try:
            ha_low.append(subgrp['low_temp'][()])
        except KeyError:
            ha_low.append(np.nan)

# --- Read Weather Sources Data ---
weather_file = 'weather.h5'
sources = ['stadt_reutlingen', 'wetter_com', 'wetter_net']
weather_dates = []
weather_high = {s: [] for s in sources}
weather_low = {s: [] for s in sources}

with h5py.File(weather_file, 'r') as f:
    for date in sorted([k for k in f.keys() if k.startswith('202')]):
        weather_dates.append(date)
        for src in sources:
            path_high = f"{date}/{src}/high_temp"
            path_low  = f"{date}/{src}/low_temp"
            if path_high in f:
                weather_high[src].append(f[path_high][()])
            else:
                weather_high[src].append(np.nan)
            if path_low in f:
                weather_low[src].append(f[path_low][()])
            else:
                weather_low[src].append(np.nan)

# compute mean and median of high and low across Home Assistant and other sources
common_dates   = sorted(set(ha_dates) & set(weather_dates))
mean_high      = []
median_high    = []
mean_low       = []
median_low     = []

for date in common_dates:
    ha_idx = ha_dates.index(date)
    w_idx  = weather_dates.index(date)
    highs = [ha_high[ha_idx]] + [weather_high[src][w_idx] for src in sources]
    lows  = [ha_low[ha_idx]]  + [weather_low[src][w_idx]  for src in sources]
    mean_high.append(np.nanmean(highs))
    median_high.append(np.nanmedian(highs))
    mean_low.append(np.nanmean(lows))
    median_low.append(np.nanmedian(lows))

plt.figure(figsize=(12,6))

# Assign colors for each source (using tab10 colormap)
from matplotlib import cm
colormap = plt.get_cmap('tab10')

# Home Assistant in its own color
ha_color = 'tab:red'
plt.plot(ha_dates, ha_high, 'o-',  label='Home Assistant High', c=ha_color)
plt.plot(ha_dates, ha_low,  'o--', label='Home Assistant Low',  c=ha_color)

# Assign each weather source a color
for i, src in enumerate(sources):
    color = colormap(i % 10)
    plt.plot(weather_dates, weather_high[src], '.-',  label=f'{src} High', c=color)
    plt.plot(weather_dates, weather_low[src],  '.--', label=f'{src} Low',  c=color)

# plot mean and median
plt.plot(common_dates, mean_high,   '-',  label='Mean High',   c='black')
#plt.plot(common_dates, median_high, '--', label='Median High', c='black')
plt.plot(common_dates, mean_low,    '--',  label='Mean Low',    c='black')
#plt.plot(common_dates, median_low,  '--', label='Median Low',  c='gray')

plt.xlabel('Date')
plt.ylabel('Temperature [°C]')
plt.title('High and Low Temperatures: Home Assistant vs Other Sources')
plt.xticks(rotation=45)
plt.tight_layout(rect=[0,0,0.8,1])  # Leave space for legend on the right

# Place the legend outside
plt.legend(bbox_to_anchor=(1.02, 1), loc='upper left', borderaxespad=0)
plt.show()