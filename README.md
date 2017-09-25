# Statistical-Districts
A program for creating an interactive map of Census data for select Congressional Districts

##  Required Python Libraries:
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

3. Set variables in settings files

4. TODO Build the stats for a given Congressional District:
  `python statbuilder.py --state tx --district 7`
   
   `statbuilder.py` currently only builds the stats for TX-07.

  Add a year:
   `statbuilder.py --state tx --district 7 --year 2014`

5. Run the webserver
  `python statserver.py`

6. View results in your web browser by going to [localhost:8000](http://localhost:8000)

This product uses the Census Bureau Data API but is not endorsed or certified by the Census Bureau.
