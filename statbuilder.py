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
    _version=VERSION
    parser = argparse.ArgumentParser(description='Build stats for a particular Congressional District')
    parser.add_argument('-v','--version',action='version', version='%(prog)s %(version)s' % {"prog": parser.prog, "version": _version})
    parser.add_argument('-d','--debug',help='print debug messages',action="store_true")

    return parser.parse_args()

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
    # dynamic to state and district
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
    bgs_in_district[['BLKGRPCE','COUNTYFP', 'STATEFP', 'TRACTCE', 'GEOID']].to_csv('data/' + bgs_output +'.csv')


def get_census_fields(api, fields, year=2015,state='48',district='07'):
    """Query the census 
    Args:
        api: The state where the Congressional district is in
        year: Congressional district
        fields: 
        state: 
        district: 
    Returns:
        census_fields: 
    Raises:
        Nothing
    """
    # TODO make dynamic to state and district
    bgs_in_district = pd.read_csv('data/tx7-bgs.csv')
    
    # Setup Census query
    census_query = Census(api, year=year)
    print fields
    census_fields = []
    for bg_index, bg_row in bgs_in_district.iterrows():
        bg_stats = census_query.acs5.state_county_blockgroup(
                        fields=fields, 
                        state_fips=bg_row['STATEFP'], 
                        county_fips=bg_row['COUNTYFP'], 
                        blockgroup=bg_row['BLKGRPCE'],
                        tract=bg_row['TRACTCE']
                    )
        print bg_stats[0]
        census_fields.append(bg_stats)

    return census_fields


def main():
    """Builds stats and progressive scores for a Congressional District.
    """
    args = get_command_line_args()
    settings_dict = read_settings(args)
    census_api_key = settings_dict['census_api_key']
    
    # Table B01001, Sex by Age
    fields = (
                'B01001_001E', # Total
                'B01001_007E', # Male:!!18 and 19 years
                'B01001_008E', # Male:!!20 years
                'B01001_009E', # Male:!!21 years
                'B01001_010E', # Male:!!22 to 24 years
                'B01001_011E', # Male:!!25 to 29 years
                'B01001_012E', # Male:!!30 to 34 years
                'B01001_013E', # Male:!!35 to 39 years
                'B01001_014E', # Male:!!40 to 44 years
                'B01001_015E', # Male:!!45 to 49 years
                'B01001_016E', # Male:!!50 to 54 years
                'B01001_017E', # Male:!!55 to 59 years
                'B01001_018E', # Male:!!60 and 61 years
                'B01001_019E', # Male:!!62 to 64 years
                'B01001_020E', # Male:!!65 and 66 years
                'B01001_021E', # Male:!!67 to 69 years
                'B01001_022E', # Male:!!70 to 74 years
                'B01001_023E', # Male:!!75 to 79 years
                'B01001_024E', # Male:!!80 to 84 years
                'B01001_025E', # Male:!!85 years and over
                'B01001_031E', # Female:!!18 and 19 years
                'B01001_032E', # Female:!!20 years
                'B01001_033E', # Female:!!21 years
                'B01001_034E', # Female:!!22 to 24 years
                'B01001_035E', # Female:!!25 to 29 years
                'B01001_036E', # Female:!!30 to 34 years
                'B01001_037E', # Female:!!35 to 39 years
                'B01001_038E', # Female:!!40 to 44 years
                'B01001_039E', # Female:!!45 to 49 years
                'B01001_040E', # Female:!!50 to 54 years
                'B01001_041E', # Female:!!55 to 59 years
                'B01001_042E', # Female:!!60 and 61 years
                'B01001_043E', # Female:!!62 to 64 years
                'B01001_044E', # Female:!!65 and 66 years
                'B01001_045E', # Female:!!67 to 69 years
                'B01001_046E', # Female:!!70 to 74 years
                'B01001_047E', # Female:!!75 to 79 years
                'B01001_048E', # Female:!!80 to 84 years
                'B01001_049E'  # Female:!!85 years and over
            )

    census_fields = get_census_fields(api=census_api_key, fields=fields)

    print census_fields


if __name__ == "__main__":
    main()
