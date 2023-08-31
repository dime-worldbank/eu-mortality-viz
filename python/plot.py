# Databricks notebook source
# MAGIC %md
# MAGIC # Excess Mortality in EU Pre, During, and Post-COVID
# MAGIC Map visualization in Python using public datasets on local mortality levels across the EU pre-, during, and post-COVID.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Environment and Data Preparation
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
# MAGIC Read the shapefile that contains EU country and subnational geometry data, identified by `NUTS_ID`

# COMMAND ----------

# Read NUTS shapefiles
SHAPE_FILE = os.path.join('..', 'data', 'NUTS_shapefile', 'NUTS_RG_03M_2021_3035.shp')
nuts_all = gpd.read_file(SHAPE_FILE)
nuts_all

# COMMAND ----------

# MAGIC %md
# MAGIC Read the mortality data file that contains location identifiers `nuts_id`

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

# MAGIC %md
# MAGIC ## Static Map Visualization
# MAGIC Pick a random period to visualize excess mortality measured using relative deaths on a map. Start with a basic `plot` command, specifying a color map and displaying legend.

# COMMAND ----------

sample_period = '2020_50'
mortality_2020_w50 = mortality_w_geo[mortality_w_geo.time_period == sample_period]
mortality_2020_w50.plot(column='deaths_rel_scaled', cmap='Spectral_r', legend=True)

# COMMAND ----------

# MAGIC %md
# MAGIC Zoom in and rid off the axis

# COMMAND ----------

# specify bounding box
fig, ax = plt.subplots(figsize = (6, 8))
ax.set_xlim([2511158,  6011158])
ax.set_ylim([1381228,  5395358])

# remove axis
ax.set_axis_off()

mortality_2020_w50.plot(column='deaths_rel_scaled', cmap='Spectral_r', legend=True, ax=ax)

# COMMAND ----------

# MAGIC %md
# MAGIC Surprising that during the height of the pandemic we don't see red. Maybe it's a value color coding issue. Quickly check the distribution of relative deaths.

# COMMAND ----------

# check distribution of relative deaths
plt.hist(mortality_2020_w50.deaths_rel_scaled)

# COMMAND ----------

# MAGIC %md
# MAGIC Cap the color coding at 200 max, which corresponds to 2x the baseline deaths. This covers a good % of data points and better shows variation and contrast (also because Robert says so). Then, overlay country boundaries for visual grouping of national trends.

# COMMAND ----------

fig, ax = plt.subplots(figsize = (6, 8))
ax.set_xlim([2511158,  6011158])
ax.set_ylim([1381228,  5395358])
ax.set_axis_off()

# cap max value used for plotting to visualize variation & contrast
mortality_2020_w50.plot(column='deaths_rel_scaled', cmap='Spectral_r', legend=True, ax=ax, vmin=0, vmax=200)

# overlay country boundaries
countries = nuts_all[nuts_all["LEVL_CODE"] == 0]
countries.geometry.boundary.plot(ax=ax, color=None, edgecolor='k', linewidth=0.7)

# COMMAND ----------

# MAGIC %md
# MAGIC Additional costmetic settings to make it look like Robert's map: reposition legend at the bottom, set a title and captions.

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

# MAGIC %md
# MAGIC ## Animated Map
# MAGIC Let's add the time dimension to the map visualization, starting with packaging the above visualization step as a function that takes the time_period as an argument.

# COMMAND ----------

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
from glob import glob

# # clear all jpg files
# for f in tqdm(glob(os.path.join('output', '*.jpg'))):
#     os.remove(f)

unique_time_periods = mortality_w_geo.time_period.unique()
for time_period in tqdm(unique_time_periods):
    fig = plot_map(time_period)
    year, week = time_period.split('_')
    # zero pad week so simple filename sort is chronological
    filename = os.path.join('output', 'week', f'{year}_{week.zfill(2)}.jpg')
    fig.savefig(filename, dpi=150)
    plt.close(fig) 

# COMMAND ----------

# MAGIC %md
# MAGIC Combine all the time periods' maps into a single gif

# COMMAND ----------

from PIL import Image

def combine_to_gif(input_filenames, output_filename, compress=True):
    images = []
    for filename in tqdm(input_filenames):
        img = Image.open(filename)
        if compress:
            img = img.resize((500, 750)) 
        images.append(img)

    images[0].save(
        output_filename,
        save_all=True, 
        append_images=images[1:], 
        duration=100, 
        loop=0 # 0 means loop forever
    )

gif_filename = os.path.join('output', "EU Excess Mortality 2020-2023.gif")
sorted_files = sorted(glob(os.path.join('output', 'week', '*.jpg')))
combine_to_gif(sorted_files, gif_filename)

# COMMAND ----------

# MAGIC %md
# MAGIC Only aminate all weeks of 2020, with higher resolution image for each frame

# COMMAND ----------

gif_filename = os.path.join('output', "EU Excess Mortality 2020.gif")
sorted_files = sorted(glob(os.path.join('output', 'week', '2020_*.jpg')))
combine_to_gif(sorted_files, gif_filename, compress=False)

# COMMAND ----------

# MAGIC %md
# MAGIC <img src="https://github.com/weilu/eu-mortality-viz/blob/main/python/output/EU%20Excess%20Mortality%202020.gif?raw=true" width=500/>

# COMMAND ----------

# MAGIC %md
# MAGIC ## Bonus: Interactive Map
# MAGIC Just because ;)

# COMMAND ----------

mortality_2020_w50.explore(
    column="deaths_rel_scaled",
    vmax=200,
    cmap="Spectral_r", 
    tooltip="deaths_rel_scaled",
    popup=True,  # show all values on click
)
