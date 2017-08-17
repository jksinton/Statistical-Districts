# Statistical-Districts
A program for creating an interactive map of Census data for select Congressional Districts

##  Required Python Libraries:
* geopandas
* tornado
* census
* us

## Installation
1. Install Python libraries:
  * pip install geopandas
  * pip install tornado
  * pip install census
  * pip install us

2. Get API keys
  * US Census
  * Google Maps

3. Set variables in settings files

4. Build the stats for a Congressional District:
  `python statbuilder.py --state tx --district 7`

5. Run the webserver
  `python statserver.py`

6. View results in a webbrowser go to [localhost:8000](http://localhost:800)

This product uses the Census Bureau Data API but is not endorsed or certified by the Census Bureau.
