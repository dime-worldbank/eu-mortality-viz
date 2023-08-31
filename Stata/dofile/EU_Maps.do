	********************************************************************************
	*Analysis of COVID-19 mortality rates across the EU
	*Analyst: Ayesha Khurshid
	*Data: 18/08/2023
	********************************************************************************

	***************************************************
	*Setting up globals
	***************************************************
	global eu_map "C:\Users\wb581100\OneDrive - WBG\Desktop\Maps"
	cd "$eu_map"

	global raw "$eu_map\raw"
	global clean "$eu_map/\clean"
	global output "$eu_map/output"

	***----------------------------------------------------------
	*** Preparation for map creation
	***----------------------------------------------------------

	**Using shapefile for Europe
	spshape2dta "$raw\NUTS_RG_03M_2021_3035", replace 
	
	**Creating polygon shape file at the country level only for later
	use NUTS_RG_03M_2021_3035_shp.dta, clear
	keep if _X > -20 & _Y >20								//Removing far out islands
	keep if inrange(_ID, 1, 35) | inlist(_ID, 41, 42)		//Keeping countries with available data
	save country_lvl.dta, replace
	
	**Loading original data coordinates file to prepare for merging with mortality data
	use NUTS_RG_03M_2021_3035.dta, clear
	
	**Restricting to data available on mortality for merging
	keep if LEVL_CODE == 3 | (LEVL_CODE == 1 & inlist(CNTR_CODE, "DE", "IE", "SI"))
	tempfile db
	save `db'

	**Specifying data for EU mortality
	import delimited "$raw\mortality_europe_19_23.csv", clear
	
	**Restricting to data available on mortality and merging
	keep if levl_code == 3 | (levl_code == 1 & inlist(cntr_code, "DE", "IE", "SI"))
	rename nuts_id NUTS_ID									//rename for merging
	merge m:1 NUTS_ID using `db', keep(3) nogen				//merging with coordinates data
	keep if _CX > -20 & _CY >20								//restricting to remove far out islands
	
	**Cleaning indicator to map
	replace deaths_rel = deaths_rel*100
	replace deaths_rel = 225 if deaths_rel > 200

	**Creating year-week identifier for maps 
	egen year_week = group (year week)
	
	***----------------------------------------------------------
	*** Map creation
	***----------------------------------------------------------
	
	**Start loop
	forvalues x = 99/99 {					//530-105 for 2020
	    
	    preserve
		
			keep if year_week == `x'
			
			local year = year[_n] 			//For year label in title
			local week = week[_n] 			//For week label in title
			
			*Setting coordinates system
			spset, modify coordsys(latlong, kilometers)
			
			*Setting color palette
			colorpalette Spectral, n(9) nograph reverse
			local colors `r(p)'
			
			*Plot map
			grmap deaths_rel,  clm(custom) clbreaks(0(25)225)				///
			fcolor("`colors'") legstyle(2) ocolor(gray ..)					/// 
			osize(0.05 ..) polygon(data(country_lvl.dta)   					///
			ocolor(gray*1.6) osize(0.1 ..)) legend(pos(11) 					///
			size(1.5) symx(2.5) symy(1.5) order(1 "NA" 2 "0-25" 			///
			3 "26-50" 4 "51-75" 5 "76-100" 6 "101-125" 7 					///
			"126-150" 8 "151-175" 9 "176-200" 10 ">200") 					///
			title("{bf:Relative mortality} {it:(2015-18 average = 100)}",	///
			size(1.5))) title("{bf: Mortality across Europe}", 				///
			size(5)) subtitle(`year' (Week `week')) 						///
			note("{bf:Notes: } Values calculated relative to 2015-2018 average (=100) and shown at NUTS3 level" "of, if unavailable, the closest more disaggregated level." "{bf:Data sources: } European Commission, Eurostat, 'Deaths by week, sex and NUTS 3 region'" "(mortality data); European Commission - Eurostat/GISCO (NUTS-3 shapefiles)", size(1.7))
		
			graph export "$output/eumap_`x'.png", replace

		restore
	}
