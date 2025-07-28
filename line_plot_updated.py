import pandas as pd
import matplotlib.pyplot as plt

# read back the combined data
combined_hdf5_file_path = 'weather_combined_sort_v2.h5'
df = pd.read_hdf(combined_hdf5_file_path, key='weather')

# make sure 'date' is a datetime
df['date'] = pd.to_datetime(df['date'])

# sort and reset the integer index
df = df.sort_values("date").reset_index(drop=True)

key_cols = ['date', 'source']          # the columns that together must be unique
# find duplicate rows (same col1+col2) – keep=False marks every occurrence
dupes_mask = df.duplicated(subset=key_cols, keep=False)

# remove all but the last occurrence of each duplicated pair
df = df.drop_duplicates(subset=key_cols, keep='last').reset_index(drop=True)

#print(df.info())


# prepare the plot
fig, ax = plt.subplots(figsize=(14, 8))

# choose one color per source
sources = df['source'].unique()
colors = plt.cm.tab10.colors  # up to 10 distinct colors
for idx, source in enumerate(sources):
    color = colors[idx % len(colors)]
    df_src = df[df['source'] == source]
    # plot high_temp (solid) and low_temp (dashed) in same color
    ax.plot(df_src['date'],
            df_src['high_temp'],
            marker='o',
            color=color,
            label=f"{source} high")
    ax.plot(df_src['date'],
            df_src['low_temp'],
            marker='x',
            linestyle='--',
            color=color,
            label=f"{source} low")
# keep only those dates that have data from *all* sources
num_sources = len(sources)
date_counts = df.groupby('date')['source'].nunique()
complete_dates = date_counts[date_counts == num_sources].index
df_complete = df[df['date'].isin(complete_dates)]

df_mean = (
    df_complete
        .groupby('date')[['high_temp', 'low_temp']]
        .mean()
        .reset_index()
)



# plot mean high (thick solid) and mean low (thick dashed)
ax.plot(df_mean['date'],
        df_mean['high_temp'],
        color='grey',
        linewidth=2.5,
        label='mean high')
ax.plot(df_mean['date'],
        df_mean['low_temp'],
        color='grey',
        linewidth=2.5,
        linestyle='--',
        label='mean low')

ax.set_xlabel('Date')
ax.set_ylabel('Temperature')
ax.set_title('High/Low Temperatures by Source')
ax.legend(loc='best')
fig.autofmt_xdate()
plt.tight_layout()
plt.show()