import h5py
import numpy as np
import plotly.graph_objects as go
import plotly.io as pio
import pandas as pd
pio.renderers.default = "browser"
# --- Read Home Assistant Data ---
ha_file = 'weather_ha.h5'
ha_dates = []
ha_high = []
ha_low = []
with h5py.File(ha_file, 'r') as f:
    for date in sorted(k for k in f.keys() if k.startswith('202')):

        ha_dates.append(date)
        subgrp = f[f"{date}/home_assistant"]
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
    for date in sorted(k for k in f.keys() if k.startswith('202')):
        weather_dates.append(date)
        for src in sources:
            path_high = f"{date}/{src}/high_temp"
            path_low = f"{date}/{src}/low_temp"
            weather_high[src].append(f[path_high][()] if path_high in f else np.nan)
            weather_low[src].append(f[path_low][()] if path_low in f else np.nan)

# compute mean absolute error of other sources relative to Home Assistant for each day
errors_high = []
errors_low = []
for i, date in enumerate(ha_dates):
    daily_errs_high = [
        weather_high[src][i] - ha_high[i]
        for src in sources
        if not np.isnan(weather_high[src][i]) and not np.isnan(ha_high[i])
    ]
    daily_errs_low = [
        weather_low[src][i] - ha_low[i]
        for src in sources
        if not np.isnan(weather_low[src][i]) and not np.isnan(ha_low[i])
    ]
    errors_high.append(np.nanmean(np.abs(daily_errs_high)) if daily_errs_high else np.nan)
    errors_low.append(np.nanmean(np.abs(daily_errs_low)) if daily_errs_low else np.nan)

# build upper and lower bounds for error bands
upper_high = [v + e for v, e in zip(ha_high, errors_high)]
lower_high = [v - e for v, e in zip(ha_high, errors_high)]
upper_low = [v + e for v, e in zip(ha_low, errors_low)]
lower_low = [v - e for v, e in zip(ha_low, errors_low)]

# plotly figure with continuous error bands
fig = go.Figure()

# Home Assistant high temp and its error band
fig.add_trace(go.Scatter(
    x=ha_dates,
    y=ha_high,
    mode='lines+markers',
    name='Home Assistant High',
    line=dict(color='red')
))
fig.add_trace(go.Scatter(
    x=ha_dates + ha_dates[::-1],
    y=upper_high + lower_high[::-1],
    fill='toself',
    fillcolor='rgba(255,0,0,0.2)',
    line=dict(color='rgba(255,0,0,0)'),
    hoverinfo='skip',
    name='High Error Band'
))

# Home Assistant low temp and its error band
fig.add_trace(go.Scatter(
    x=ha_dates,
    y=ha_low,
    mode='lines+markers',
    name='Home Assistant Low',
    line=dict(color='blue')
))
fig.add_trace(go.Scatter(
    x=ha_dates + ha_dates[::-1],
    y=upper_low + lower_low[::-1],
    fill='toself',
    fillcolor='rgba(0,0,255,0.2)',
    line=dict(color='rgba(0,0,255,0)'),
    hoverinfo='skip',
    name='Low Error Band'
))

fig.update_layout(
    title='Home Assistant Temperatures with Daily Mean Error Bands',
    xaxis_title='Date',
    yaxis_title='Temperature [°C]',
    hovermode='x unified'
)
fig.show()