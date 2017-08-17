#!/usr/bin/env python

# This file is part of Statistical Districts.
# 
# Copyright (c) 2017, James Sinton
# All rights reserved.
# 
# Released under the BSD 3-Clause License
# See https://github.com/jksinton/Statistical-Districts/blob/master/LICENSE

import os
import argparse
import ConfigParser
import json
import re

import pandas as pd
import geopandas as gpd
from geopandas import GeoSeries, GeoDataFrame

from census import Census
from us import states

#GLOBAL CONSTANTS

VERSION = '0.1.0'

def read_settings(args):
    """Read the settings stored in settings.ini
    Args: 
        args: argparse.ArgumentParser object that stores command line arguments
    Returns: 
        settingsDict: A dictionary holding the argument(s)
    Raises:
        Nothing (yet)
    """
    # Set values in settings.ini
    settings = ConfigParser.ConfigParser()
    settings.read('settings.ini') # change example.settings.ini to settings.ini

    # Census API Key
    census_api_key = settings.get( 'census', 'CENSUS_API_KEY' )

    settings_dict = { "census_api_key": census_api_key }

    return settings_dict


def get_command_line_args():
    """Define command line arguments using argparse
    Args:
        None
    Return: 
        argparse.ArgumentParser object that stores command line arguments
    Raises:
        Nothing (yet)
    """
    # TODO
    # take state and district
    _version=VERSION
    parser = argparse.ArgumentParser(description='Build stats for a particular Congressional District')
    parser.add_argument('-v','--version',action='version', version='%(prog)s %(version)s' % {"prog": parser.prog, "version": _version})
    parser.add_argument('-d','--debug',help='print debug messages',action="store_true")

    return parser.parse_args()

# TODO
# thoughts on creating an object?
# class CongDistrict(object):
#    
#    def __init__(self, state, district):
#        self.state = state
#        self.district = district

# TODO
# def find_tracts_in_district(state='48', district='07'):


def find_blockgroups_in_district(state='48', district='07'):
    """Find the geographical units that intersect with a Congressional District.
    Args:
        state: The state where the Congressional district is in
        district: Congressional district
        blockgroup: Boolean
        tract: Boolean
        plot: Boolean
    Returns:
        Nothing
    Raises:
        Nothing
    """
    # TODO
    # process based on state and district args
    # set based on args: state, distric
    bgs_output = 'district-blockgroups'
    bgs_outputGeoJSON = 'geojson/' + bgs_output + '.geojson'

    # TODO 
    # see if geojson files is available for district
    #   if not generate geojson file for district
    district_geojson = 'geojson/district.geojson'

    # TODO download blockgroup shapefile for state, unzip, and read *.shp file
    census_block_groups_file = '2015_community_survey/tl_2015_48_bg/tl_2015_48_bg.shp' # Public domain ftp://ftp2.census.gov/geo/tiger/TIGER2015/BG/tl_2015_48_bg.zip

    district = gpd.read_file(district_geojson)
    block_groups = gpd.read_file(census_block_groups_file)
    
    block_groups=block_groups.to_crs({'init': u'epsg:4326'})

    bgs_in_district_bool = block_groups.intersects(district.geometry[0])
    bgs_in_district = block_groups[bgs_in_district]
    
    # TODO mkdir plots if not there
    plt.figure(figsize=(400, 400))
    district_plot=district.plot(color='blue')
    bgs_in_district.plot(ax=district_plot, color='green')
    plt.savefig('plots/' + bgs_output,dpi=600)
    plt.close()

    # See issue #367 https://github.com/geopandas/geopandas/issues/367
    try: 
        os.remove(bgs_outputGeoJSON)
    except OSError:
        pass
    bgs_in_district.to_file(bgs_outputGeoJSON, driver='GeoJSON')

    # Create csv file of geo units
    bgs_in_district[['BLKGRPCE','COUNTYFP', 'STATEFP', 'TRACTCE', 'GEOID']].to_csv('static/data/' + bgs_output +'.csv')


def get_blockgroup_data(api, fields, year=2015, state='48', district='07'):
    """Retrieve the census data for the block groups in a Congressional District
    Args:
        api: Census api key
        fields: the fields to query from api.census.gov; 
            See e.g., https://api.census.gov/data/2015/acs5/variables.html
        year: The year the census data was collected
        state: The state where the Congressional district is in
        district: The Congressional district
    Returns:
        census_fields: a list of dictionaries storing the blockgroup results
    Raises:
        Nothing
    """
    # TODO make dynamic to state and district
    bgs_in_district = pd.read_csv('static/data/tx7-bgs.csv')
    
    # Setup Census query
    census_query = Census(api, year=year)
    census_fields = []
    
    num_of_bgs = len(bgs_in_district)
    i = 0.0
    for bg_index, bg_row in bgs_in_district.iterrows():
        # TODO
        # print percent complete
        status = r"%10d  [%3.2f%%]" % (i, i * 100. / num_of_bgs)
        status = status + chr(8)*(len(status)+1)
        print status,
        bg_stats = census_query.acs5.state_county_blockgroup(
                        fields=fields, 
                        state_fips=bg_row['STATEFP'], 
                        county_fips=bg_row['COUNTYFP'], 
                        blockgroup=bg_row['BLKGRPCE'],
                        tract=bg_row['TRACTCE']
                    )[0]
        bg_stats['GEOID'] = bg_row['GEOID']
        census_fields.append(bg_stats)
        i = i + 1

    return census_fields

# TODO
# def dem_lean_by_age():



def to_json(data, out_filename='static/data/out.json'):
    """Convert data to json
    Args: 
        data: a python data structure
        out_filename: the file the data is saved to 
    Returns: 
        Nothing
    Raises:
        Nothing (yet)
    """
    with open(out_filename, 'w') as outfile:  
        json.dump(data, outfile)


def get_census_fields(table, year=2015):
    """Return the fields in a census table
    Args: 
        table: 
        year:  
    Returns: 
        fields: 
        labels: 
    Raises:
        Nothing (yet)
    """
    # TODO 
    # check:
    #   if variables_<year>.json does not exist
    #       download variables for the given year
    #           example url: https://api.census.gov/data/2015/acs5/variables.json
    #       save the file to variables_<>.json
    variables_file = 'static/data/variables_' + str(year) + '.json'
    fields = []
    labels = {}

    with open(variables_file) as variables:
        data = json.load(variables)
        for key in data['variables']:
            if re.match(table+'_[0-9]*E', key):
                fields.append(key)
                labels[key]=data['variables'][key]['label']
    
    return fields, labels


def main():
    """Builds stats and progressive scores for a Congressional District.
    """
    args = get_command_line_args()
    settings_dict = read_settings(args)
    census_api_key = settings_dict['census_api_key']
    year = 2015
    
    fields, labels = get_census_fields("B01001")

    print "Getting Sex by Age stats for TX-07"
    data_in_bgs = get_blockgroup_data(api=census_api_key, fields=fields, year=year)
    
    to_json(data_in_bgs, "static/data/sex_by_age_in_tx7.json")

    to_json([fields, labels], "static/data/labels.json")


if __name__ == "__main__":
    main()
