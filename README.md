# Automated Weather Data Collection via Web Scraping

Python scripts which automatically collect the daily high and low temperature forecast for city of Reutlingen from various weather sources using webscraping and compare it with scraped data from local home assistant. 

## weather_sources.csv

CSV file containing the url of the webpages, selcted for scraping.

## webscrape.py

Scrape high and low temperature forecast from sources reutlingen.de, wetter.com and wetter.net and save the data into an HDF5 file in tabular format.

## scrape_ha.py

Scrape high and low temperature readings for previous day from local home assistant dashboard.

## weather_combined_sort_v2.h5

HDF5 file containing the scraped data in tabular format.

## line_plot_updated.py

Visualize time series plot of high and low temperature along with mean.



