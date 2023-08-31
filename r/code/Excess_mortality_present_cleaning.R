
#
# SET-UP ----
#

# rm(list=ls())

### Copy of the file
file.copy(rstudioapi::getSourceEditorContext()$path,
          gsub('\\.R', ' - copy.R', rstudioapi::getSourceEditorContext()$path),
          overwrite = T, copy.date = T)



### Packages 
if( !is.element("pacman", installed.packages() )){
  install.packages("pacman", dep= T)
}

pacman::p_load(tidyverse, haven,
               janitor, data.table, ggplot2, dplyr,
               sf, lubridate, xlsx,
               patchwork, ggtext, ggthemes, extrafont,
               tidylog, gganimate, transformr, magick,
               update = F)


### Load fonts
loadfonts(quiet = T)
fonts()


### Custom functions
mean_miss   <- function(x){mean(x, na.rm = TRUE)}
median_miss <- function(x){median(x, na.rm = TRUE)}
sf          <- function(x){return(summary(factor(x)))}
pr          <- function(x){return(prop.table(table(x, useNA = "no"))*100)}


### Directory
main_dir = '~/Moje/Maps/Europe mortality (weekly, NUTS3)'


#
# MORTALITY DATA ----
#


### Read data

mortality =  fread(file.path(main_dir, 'Data','demo_r_mwk3_t.csv')) 

mortality = mortality %>%
              clean_names() %>% 
              dplyr::select(-c(dataflow,last_update, freq, obs_flag)) %>%
              mutate(obs_value = as.numeric(obs_value))
         


### Clean dates
mortality = mortality %>% 
                  # Separate week and year
                  separate('time_period', into = c('year', 'week'), '-W', remove = F) %>%
                  mutate(year = as.numeric(year),
                         week = as.numeric(gsub('^0', '', week)),
                         time_period = gsub('-W', '-', gsub('-W0', '-W', time_period))) %>%
                  # Ensure only correct and necessary dates are kept
                  filter(week >= 1 & week <= 53 & year >= 2015 & year <= 2023)


### Calculate 2015-2018 average
temp = mortality %>% 
          filter(year %in% c(2015:2018)) %>% 
          group_by(geo, week) %>% 
          mutate(av_15_18 = mean_miss(obs_value)) %>%
          dplyr::select(c(unit, geo, week, av_15_18)) %>% 
          distinct()

# Re-join to the main dataset
mortality = left_join(mortality, temp)


# Remove those with non-positive values
mortality = mortality %>% filter(av_15_18 >= 0)


### Calculate relative values
mortality$obs_rel = mortality$obs_value / mortality$av_15_18

### Now leave only 2019 onwards
mortality = mortality %>%  filter(year >= 2019) 



#
# SHAPEFILE ----
#

### Read NUTS shapefiles
nuts_all = read_sf(file.path(main_dir, 'Data', 'NUTS_shapefile', 'NUTS_RG_03M_2021_3035.shp'))


### Extract
nuts0 = nuts_all[nuts_all$LEVL_CODE == 0, ] # Countries
nuts1 = nuts_all[nuts_all$LEVL_CODE == 1, ] # NUTS1 only
nuts2 = nuts_all[nuts_all$LEVL_CODE == 2, ] # NUTS2 only
nuts3 = nuts_all[nuts_all$LEVL_CODE == 3, ] # NUTS3 only



# Remove countries we don't have data for
nuts0 = nuts0 %>% filter(!grepl('TR', CNTR_CODE))
nuts3 = nuts3 %>% filter(!grepl('TR', CNTR_CODE))



### Plot empty map to test
ggplot() +
  geom_sf(data = nuts3, linewidth = 0.2, col = 'grey80', fill = NA) +
  geom_sf(data = nuts0, linewidth = 0.6, col = 'black', fill = NA) +
  scale_x_continuous(limits = c(2511158,
                                6011158))+
  scale_y_continuous(limits = c(1381228,
                                5395358 )) +
  theme_void()





### Merge mortatlity data with shapefiles ----
mortality = left_join(mortality %>% rename('NUTS_ID' = 'geo'),
                  nuts_all) %>%
          filter(!is.na(CNTR_CODE))

tapply(mortality$LEVL_CODE, mortality$CNTR_CODE, sf)


# Some countries don't have data at NUTS-3 level. Select NUTS-3 level
# for all countries, apart from those. 

temp = data.frame(CNTR_CODE = unique(mortality$CNTR_CODE), LEVL_CODE = 3)
temp$LEVL_CODE[temp$CNTR_CODE %in% c('SI', 'IE', 'DE')] = 1
temp$LEVL_CODE[temp$CNTR_CODE %in% c('MT')] = 2

mortality = inner_join(mortality, temp)

### Treat as spatial object
mortality$geometry = st_geometry(mortality$geometry)
mortality = st_as_sf(mortality)


### Final clean
mortality$time_period = gsub('-', '_', mortality$time_period) 


mortality = mortality %>%
              clean_names() %>%
              dplyr::select(c(unit, cntr_code, nuts_id, levl_code, nuts_name,
                                                        time_period, year, week,
                                                        obs_value, obs_rel, av_15_18,
                                                        geometry)) %>%
              rename('deaths_abs' = 'obs_value',
                     'deaths_rel' = 'obs_rel',
                     'deaths_15_18' = 'av_15_18')



### Save

# As shapefile
write_sf(mortality, file.path(main_dir, 'Data', 'mortality_europe_19_23.shp'))

# As .csv
fwrite(as.data.frame(mortality %>% st_drop_geometry()), file.path(main_dir, 'Data', 'mortality_europe_19_23.csv'), na=NA, row.names = F)


### Plot empty map to test
# ggplot() +
#   geom_sf(data = mortality %>% filter(time_period == '2020_10'),
#           linewidth = .3, col = 'grey40', fill = NA) +
#   geom_sf(data = nuts0, linewidth = .85, col = 'black', fill = NA) +
#   scale_x_continuous(limits = c(2511158,
#                                 6011158))+
#   scale_y_continuous(limits = c(1381228,
#                                 5395358  )) +
#   theme_void()

#
# END OF CODE ----
# 