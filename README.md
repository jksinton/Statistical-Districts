# Statistical Districts
A program for creating an interactive map of Census data for select Congressional Districts, Texas House Districts, and Texas Senate Districts.

##  Required Python Libraries
* [geopandas](https://github.com/geopandas/geopandas)
* [tornado](https://github.com/tornadoweb/tornado)
* [census](https://github.com/datamade/census)
* [us](https://github.com/unitedstates/python-us)
* [matplotlib](https://github.com/matplotlib/matplotlib) (Used to debug GIS operations)

## Installation
1. Install Python libraries:
  * pip install geopandas
  * pip install tornado
  * pip install census
  * pip install us
  * pip install matplotlib

2. Get API keys
  * [US Census](https://api.census.gov/data/key_signup.html)
  * [Google Maps](https://developers.google.com/maps/)

3. Set variables in settings files:
  * Rename `example.settings.ini` to `settings.ini`; and put your Census API in this file
  * Rename `static/js/example.settings.js` to `static/js/settings.js`; and put your Google Maps API key in in this file

## Usage
1. Build the stats from the Census Bureau with `python statbuilder.py`
  * Build the stats for a particular year: 
    * `statbuilder.py --year 2014`
  * Build the stats for a given Congressional District: 
    * `python statbuilder.py --state 48 --district 7`
  * Build the stats for a given Texas House District:  
    * `python statbuilder.py --state 48 --district 134 --leg-body "STATE-REP"`
  * Build the stats for a given Texas Senate District
    * `python statbuilder.py --state 48 --district 17 --leg-body "STATE-SEN"`

2. Run the webserver
  `python statserver.py`

3. View results in your web browser by going to [localhost:8000](http://localhost:8000)

## Open Source Licenses
  * Bootstrap by [Twitter](https://github.com/twbs/bootstrap/blob/master/LICENSE)
  * census by [DataMade](https://github.com/datamade/census/blob/master/LICENSE)
  * Chart.js by [Nick Downie](https://github.com/chartjs/Chart.js/blob/master/LICENSE.md)
  * code excerpts by [Google](http://www.apache.org/licenses/LICENSE-2.0)
    * E.g. [Combining and Visualizing Multiple Data Sources](https://developers.google.com/maps/documentation/javascript/combining-data)
  * geopandas by [GeoPandas developers](https://github.com/geopandas/geopandas/blob/master/LICENSE.txt)
  * hamburgers by [Jonathan Suh](https://github.com/jonsuh/hamburgers/blob/master/LICENSE)
  * matplotlib by [Matplot Lib Development Team et al.](https://github.com/matplotlib/matplotlib/tree/master/LICENSE)
  * slideout.js by [Mango](https://github.com/Mango/slideout/blob/master/LICENSE)
  * tornado by [The Tornado Authors](https://github.com/tornadoweb/tornado/blob/master/LICENSE)
  * us by [Sunlight Labs](https://github.com/unitedstates/python-us/blob/master/LICENSE)

## Disclaimer

This product uses the Census Bureau Data API but is not endorsed or certified by the Census Bureau.
