
#
# SET-UP ----
#

start1 = Sys.time()

### Copy of the file
file.copy(rstudioapi::getSourceEditorContext()$path,
          gsub('\\.R', ' - copy.R', rstudioapi::getSourceEditorContext()$path),
          overwrite = T, copy.date = T)



### Packages 
if( !is.element("pacman", installed.packages() )){
  install.packages("pacman", dep= T)
}

pacman::p_load(tidyverse, haven, stringr, paletteer,
               janitor, data.table, ggplot2, stringi, dplyr,
               sf, paletteer, data.table, beepr, lubridate, xlsx,
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
# PLOT ----
#


### Read the data

# NUTS shapefiles
nuts_all = read_sf(file.path(main_dir, 'Data', 'NUTS_shapefile', 'NUTS_RG_03M_2021_3035.shp')) %>% clean_names()
nuts0 = nuts_all[nuts_all$levl_code == 0, ] # Countries

# Mortality (pre-cleaned)
mortality = fread( file.path(main_dir, 'Data', 'mortality_europe_19_23.csv'))

mortality = left_join(mortality,
                      nuts_all) %>% filter(!is.na(cntr_code))


### Treat as spatial object
mortality$geometry = st_geometry(mortality$geometry)
mortality = st_as_sf(mortality)

### Order
mortality = mortality[order(mortality$year, mortality$week),]

### Plot

# var1 = '2020-12'


count = 1000
for(var1 in unique(mortality$time_period)){

  
  # Skip any periods as needed
  if(unique(mortality$year[mortality$time_period == var1]) != 2020){next}

  # Control the loop
  print(var1)
  count = count+1
  
  # Leave only the week in question
  dta_plot = mortality %>% filter(time_period == var1)

  
  ### Plot
  
  # General command ggplot()
  g1=ggplot() +  
    
    # Plot spatial (sf) object
    geom_sf(data = dta_plot, 
            aes(fill = deaths_rel * 100),
            linewidth = .1, col = 'grey60')+
    
    # Define color bar
    scale_fill_distiller(na.value = "darkred",
                         name = '<b>Relative mortality</b> (<i>2015-18 average = 100</i>)',
                         palette='Spectral',
                         guide="colorbar",
                         breaks = seq(0,200, 50),
                         limits = c(0,200))+
    
    # Plot another spatial (sf) object (country borders)
    geom_sf(data = nuts0, linewidth = .7, col = 'black',
            fill = NA)+
    
    # Define x- and y-axis limits
    scale_x_continuous(limits = c(2511158,
                                  6011158))+
    scale_y_continuous(limits = c(1381228,
                                  5395358  )) +
    
    # Control the color bar
    guides(fill = guide_colorbar(title.position = 'top', title.hjust = .5,
                                 ticks.colour = "black",
                                 label.position = 'bottom'))+
    
    # Control plot (and axes) titles
    labs(
      title = '<b>Mortality across Europe</b>',
      subtitle = paste0('<b>', 
                        gsub('_.*', '', var1),
                        ' (Week ',
                        gsub('.*_', '', var1),
                        ')',
                        '</b><br>'),
      caption = '<br><br><b>Notes:</b> Values calculated relative to 2015-2018 average (=100) and 
                shown at NUTS3 level or, if unavailable, the closest most disaggregated level.<br>
                <b>Data sources:</b> European Commission, Eurostat, ‘Deaths by week, sex and NUTS 3 region’ (<i>mortality data</i>); 
                European Commission – Eurostat/GISCO (<i>NUTS-3 shapefiles</i>) <br>'
    )+
    
    # Add pre-prepared theme
    theme_void()+
    
    # Customize theme
    theme(
      panel.border = element_blank(),
      plot.background = element_rect(fill = 'white', color = NA),
      panel.background = element_rect(fill = 'white', color = NA),
      legend.background = element_rect(fill = 'white', color = NA),
      legend.position = 'bottom',
      legend.direction = 'horizontal',
      legend.title = element_markdown(size = 20, family = 'Calibiri'),
      legend.text = element_text(size = 21, family = 'Calibiri'),
      legend.key.height = unit(.7, 'cm'),
      legend.key.width = unit(3, 'cm'),
      plot.title = element_markdown(size = 40, hjust = .5, family = 'Calibiri'),
      plot.subtitle = element_markdown(size = 39, hjust = .5, color = 'grey20', family = 'Calibiri'),
      plot.caption = element_textbox_simple(size = 13, family = 'Calibiri')
    )
  
  
  ggsave(file.path(main_dir, 'Figures (present)', 'Individual',  paste0(count,'_excess_mortality_', var1,'.png')),
         plot = g1, width = 29, height = 39, unit = 'cm')
  
}


#
# GIF ----
#

img <- image_blank(width = 800, height = 800)

files1 = list.files(file.path(main_dir, 'Figures (present)', 'Individual'), pattern = '.*.png')

for(file1 in files1){
  print(file1)
  img = c(img, image_read(file.path(main_dir, 'Figures (present)', 'Individual', file1)))
}


my.animation<-image_animate(image_scale(img, "800x800"), fps = 10, dispose = "previous")
image_write(path  = file.path(main_dir, 'Figures (present)',  paste0('Excess_mortality (2020) [1_10sec)','.gif')),
            image = my.animation)

beep()




end1 = Sys.time()
end1-start1

#
# END OF CODE ----
# 