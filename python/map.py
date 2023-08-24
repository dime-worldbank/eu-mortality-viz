import os
import pandas as pd
import geopandas as gpd
import numpy as np
from plotnine import ggplot, geom_sf, scale_x_continuous, scale_y_continuous, \
    labs, theme_void, theme, guides, element_blank, element_rect, element_markdown, \
    element_text, unit, ggsave
from PIL import Image


# Read NUTS shapefiles
nuts_all = gpd.read_file(os.path.join('..', 'data', 'NUTS_shapefile', 'NUTS_RG_03M_2021_3035.shp'))

# Extract
nuts0 = nuts_all[nuts_all["LEVL_CODE"] == 0]  # Countries
nuts3 = nuts_all[nuts_all["LEVL_CODE"] == 3]  # NUTS3 only

# Remove countries we don't have data for
nuts0 = nuts0[~nuts0["CNTR_CODE"].str.contains('TR')]
nuts3 = nuts3[~nuts3["CNTR_CODE"].str.contains('TR|UK')]


