# Databricks notebook source
# MAGIC %pip install geopandas folium mapclassify

# COMMAND ----------

import os
import pandas as pd
import geopandas as gpd
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image


# Read NUTS shapefiles
SHAPE_FILE = os.path.join('..', 'data', 'NUTS_shapefile', 'NUTS_RG_03M_2021_3035.shp')
nuts_all = gpd.read_file(SHAPE_FILE)
nuts_all

# COMMAND ----------

MORTALITY_FILE = os.path.join('..', 'data', 'mortality_europe_19_23.csv')
mortality = pd.read_csv(MORTALITY_FILE)
mortality

# COMMAND ----------

# mortality.info()
assert mortality.nuts_id.isna().sum() == 0, "Expect no missing nuts_id, but found some"

# COMMAND ----------

# mortality.describe(include='all')
mortality.levl_code.describe()

# COMMAND ----------

nuts_all.keys()

# COMMAND ----------

# the geopandas df needs to be on the left for the resulting df to be a geo df
mortality_w_geo = pd.merge(nuts_all, mortality, how="right", left_on="NUTS_ID", right_on="nuts_id")
mortality_w_geo

# COMMAND ----------

sample_period = '2020_50'
mortality_2020_w50 = mortality_w_geo[mortality_w_geo.time_period == sample_period]
mortality_2020_w50.plot(column='deaths_rel', cmap='Spectral_r', legend=True)

# COMMAND ----------

# specify bounding box
fig, ax = plt.subplots(figsize = (6, 8))
ax.set_xlim([2511158,  6011158])
ax.set_ylim([1381228,  5395358])

# remove axis
ax.set_axis_off()

mortality_2020_w50.plot(column='deaths_rel', cmap='Spectral_r', legend=True, ax=ax)

# COMMAND ----------

# check distribution of relative deaths
plt.hist(mortality_2020_w50.deaths_rel)

# COMMAND ----------

fig, ax = plt.subplots(figsize = (6, 8))
ax.set_xlim([2511158,  6011158])
ax.set_ylim([1381228,  5395358])
ax.set_axis_off()

# cap max value used for plotting to visualize variation & contract
mortality_2020_w50.plot(column='deaths_rel', cmap='Spectral_r', legend=True, ax=ax, vmax=2)

# overlay country boundaries
countries = nuts_all[nuts_all["LEVL_CODE"] == 0]
countries.geometry.boundary.plot(ax=ax, color=None, edgecolor='k', linewidth=0.7)

# COMMAND ----------

from mpl_toolkits.axes_grid1 import make_axes_locatable

fig, ax = plt.subplots(figsize = (6, 9))
ax.set_xlim([2511158,  6011158])
ax.set_ylim([1381228,  5395358])
ax.set_axis_off()

# place legend at bottom
divider = make_axes_locatable(ax)
cax = divider.append_axes("bottom", size="5%", pad=0.4)
cax.annotate("Relative mortality (2015-18 average = 100)", 
             xy=(0.5, 1.25), 
             xycoords="axes fraction", 
             ha="center")
legend_kwds = {"orientation": "horizontal", }
mortality_2020_w50.plot(column='deaths_rel', cmap='Spectral_r', ax=ax, vmax=2, legend=True, legend_kwds=legend_kwds, cax=cax)

countries.geometry.boundary.plot(ax=ax, color=None, edgecolor='k', linewidth=0.7)

# set title
year, week = sample_period.split('_')
ax.set(title=f'Mortality across Europe\n{year} (Week {week})')

# set caption
caption = '''Notes: Values calculated relative to 2015-2018 average (=100) and shown at NUTS3 level or, if unavailable, the closest most disaggregated level.\n\nData sources: European Commission, Eurostat, 'Deaths by week, sex and NUTS 3 region' (mortality data); European Commission – Eurostat/GISCO (NUTS-3 shapefiles)'''
fig.text(.05, 0, caption, wrap=True)

# COMMAND ----------

# Bonus: interactive map!
mortality_2020_w50.explore(
    column="deaths_rel",
    vmax=2,
    cmap="Spectral_r", 
    tooltip="deaths_rel",
    popup=True,  # show all values on click
)

# COMMAND ----------


