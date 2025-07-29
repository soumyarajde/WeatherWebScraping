#!/bin/bash
cd /home/spec/pydatasci/WeatherWebScraping/
export HA_URL="url"
export HA_USER="user"
export HA_PASS="pass"
/usr/bin/python scrape_ha.py
