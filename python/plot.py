# Databricks notebook source
# MAGIC %md
# MAGIC Install additional dependencies and import libraries

# COMMAND ----------

# MAGIC %pip install geopandas folium mapclassify tqdm

# COMMAND ----------

import os
import pandas as pd
import geopandas as gpd
import numpy as np
import matplotlib.pyplot as plt

# COMMAND ----------

# MAGIC %md
# MAGIC Read shapefile that contains EU country and subnational geometry data, identified by `NUTS_ID`

# COMMAND ----------

# Read NUTS shapefiles
SHAPE_FILE = os.path.join('..', 'data', 'NUTS_shapefile', 'NUTS_RG_03M_2021_3035.shp')
nuts_all = gpd.read_file(SHAPE_FILE)
nuts_all

# COMMAND ----------

# MAGIC %md
# MAGIC Read mortality data file that contains location identifiers `nuts_id`

# COMMAND ----------

MORTALITY_FILE = os.path.join('..', 'data', 'mortality_europe_19_23.csv')
mortality = pd.read_csv(MORTALITY_FILE)
mortality

# COMMAND ----------

# MAGIC %md
# MAGIC Minor mortality data cleaning: only keep 2020 onwards and scale relative deaths by 100x

# COMMAND ----------

mortality_2020on = mortality[mortality.year > 2019]
mortality_2020on['deaths_rel_scaled'] = (mortality_2020on['deaths_rel'] * 100).round()
mortality_2020on

# COMMAND ----------

# mortality_2020on.info()
assert mortality_2020on.nuts_id.isna().sum() == 0, "Expect no missing nuts_id, but found some"

# COMMAND ----------

# mortality_2020on.describe(include='all')
mortality_2020on.levl_code.describe()

# COMMAND ----------

nuts_all.keys()

# COMMAND ----------

# the geopandas df needs to be on the left for the resulting df to be a geo df
mortality_w_geo = pd.merge(nuts_all, mortality_2020on, how="right", left_on="NUTS_ID", right_on="nuts_id")
mortality_w_geo

# COMMAND ----------

sample_period = '2020_50'
mortality_2020_w50 = mortality_w_geo[mortality_w_geo.time_period == sample_period]
mortality_2020_w50.plot(column='deaths_rel_scaled', cmap='Spectral_r', legend=True)

# COMMAND ----------

# specify bounding box
fig, ax = plt.subplots(figsize = (6, 8))
ax.set_xlim([2511158,  6011158])
ax.set_ylim([1381228,  5395358])

# remove axis
ax.set_axis_off()

mortality_2020_w50.plot(column='deaths_rel_scaled', cmap='Spectral_r', legend=True, ax=ax)

# COMMAND ----------

# check distribution of relative deaths
plt.hist(mortality_2020_w50.deaths_rel_scaled)

# COMMAND ----------

fig, ax = plt.subplots(figsize = (6, 8))
ax.set_xlim([2511158,  6011158])
ax.set_ylim([1381228,  5395358])
ax.set_axis_off()

# cap max value used for plotting to visualize variation & contract
mortality_2020_w50.plot(column='deaths_rel_scaled', cmap='Spectral_r', legend=True, ax=ax, vmin=0, vmax=200)

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
cax = divider.append_axes("bottom", size="5%", pad=0.3)
cax.annotate("Relative mortality (2015-18 average = 100)", 
             xy=(0.5, 1.25), 
             xycoords="axes fraction", 
             ha="center")
legend_kwds = {"orientation": "horizontal", }
mortality_2020_w50.plot(column='deaths_rel_scaled', cmap='Spectral_r', ax=ax, vmin=0, vmax=200, legend=True, legend_kwds=legend_kwds, cax=cax)

countries.geometry.boundary.plot(ax=ax, color=None, edgecolor='k', linewidth=0.7)

# set title
year, week = sample_period.split('_')
ax.set(title=f'Mortality across Europe\n{year} (Week {week})')

# set caption
caption = '''Notes: Values calculated relative to 2015-2018 average (=100) and shown at NUTS3 level or, if unavailable, the closest most disaggregated level.\n\nData sources: European Commission, Eurostat, 'Deaths by week, sex and NUTS 3 region' (mortality data); European Commission – Eurostat/GISCO (NUTS-3 shapefiles)'''
txt = fig.text(.05, .02, caption, ha='left', wrap=True)
txt._get_wrap_line_width = lambda : 400 # hack only necessary for displaying the graph in notebook

# COMMAND ----------

# Bonus: interactive map!
mortality_2020_w50.explore(
    column="deaths_rel_scaled",
    vmax=200,
    cmap="Spectral_r", 
    tooltip="deaths_rel_scaled",
    popup=True,  # show all values on click
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Animated Map
# MAGIC Let's add the time dimension to the map visualization

# COMMAND ----------

# Package the above viz steps into a function

caption = '''Notes: Values calculated relative to 2015-2018 average (=100) and shown at NUTS3 level or, if unavailable, the closest most disaggregated level.\n\nData sources: European Commission, Eurostat, 'Deaths by week, sex and NUTS 3 region' (mortality data); European Commission – Eurostat/GISCO (NUTS-3 shapefiles)'''

def plot_map(time_period):
    fig, ax = plt.subplots(figsize = (6, 9))
    fig.text(.05, .02, caption, wrap=True)

    ax.set_xlim([2511158,  6011158])
    ax.set_ylim([1381228,  5395358])
    ax.set_axis_off()

    year, week = time_period.split('_')
    ax.set(title=f'Mortality across Europe\n{year} (Week {week})')

    # plot relative mortality as colors
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("bottom", size="5%", pad=0.3)
    cax.annotate("Relative mortality (2015-18 average = 100)", 
                xy=(0.5, 1.25), 
                xycoords="axes fraction", 
                ha="center")
    mortality_w_geo[mortality_w_geo.time_period == time_period].plot(
        column='deaths_rel_scaled',
        cmap='Spectral_r',
        ax=ax, 
        vmin=0, 
        vmax=200, 
        legend=True, 
        legend_kwds={"orientation": "horizontal"}, 
        cax=cax
    )

    # plot country boundaries
    countries.geometry.boundary.plot(ax=ax, color=None, edgecolor='k', linewidth=0.7)
    
    return fig

# COMMAND ----------

# MAGIC %md
# MAGIC Check that the function works

# COMMAND ----------

fig = plot_map('2020_50')
fig.show()

# COMMAND ----------

# MAGIC %md
# MAGIC Create and save map viz for all time periods. Zero pad the week number in the output filename, e.g. 2023_3 becomes 2023_03. This way when the files are sorted by name they are sorted chronologically, otherwise 2023_21 will sort before 2023_3 due to alphanumerical order.

# COMMAND ----------

from tqdm import tqdm # for displaying progress

# clear all jpg files
# for f in glob(os.path.join('output', '*.jpg')):
#     os.remove(f)

unique_time_periods = mortality_w_geo.time_period.unique()
for time_period in tqdm(unique_time_periods):
    fig = plot_map(time_period)
    year, week = time_period.split('_')
    # zero pad week so simple filename sort is chronological
    filename = os.path.join('output', f'{year}_{week.zfill(2)}.jpg')
    fig.savefig(filename, dpi=150)
    plt.close(fig) 

# COMMAND ----------

# MAGIC %md
# MAGIC Combine all the time periods' maps into a single gif

# COMMAND ----------

from PIL import Image
from glob import glob

GIF_FILENAME = os.path.join('output', "0 EU Excess Mortality 2020-2023.gif")

sorted_files = sorted(glob(os.path.join('output', '*.jpg')))
images = []
for filename in tqdm(sorted_files):
    img = Image.open(filename)
    resized = img.resize((500, 750)) 
    images.append(resized)

images[0].save(
    GIF_FILENAME,
    save_all=True, 
    append_images=images[1:], 
    duration=600, 
    loop=1
)
