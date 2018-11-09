#!/usr/bin/env python

# This file is part of Statistical Districts.
# 
# Copyright (c) 2018, James Sinton
# All rights reserved.
# 
# Released under the BSD 3-Clause License
# See https://github.com/jksinton/Statistical-Districts/blob/master/LICENSE

# standard libraries
import argparse
import os
from collections import OrderedDict
import ConfigParser
import errno
from glob import glob
import gzip
import json
import urllib2
import re
import tarfile
import zipfile

# third-party libraries
from census import Census
import geopandas as gpd
from geopandas import GeoSeries
from geopandas import GeoDataFrame
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
from us import states

# local libaries
from statlib import *

# GLOBAL CONSTANTS

VERSION = '0.4.6'

def read_settings(args):
    """Read the settings stored in settings.ini
    Args: 
        args: argparse.ArgumentParser object that stores command line arguments
    Returns: 
        settings_dict: A dictionary holding the argument(s)
    Raises:
        Nothing (yet)
    """
    # Default values
    state = 48
    district = 7
    leg_body = 'US-REP'
    year = '2016'
    voting_year = '2018'
    voting_precincts = None
    voting_results = None
    
    # Set values in settings.ini
    settings = ConfigParser.ConfigParser()
    settings.read('settings.ini') # change example.settings.ini to settings.ini

    # Census API Key
    census_api_key = settings.get( 'census', 'CENSUS_API_KEY' )

    if args.year:
        year=args.year
    if args.voting_year:
        voting_year=args.voting_year
    if args.state:
        state = args.state
    if args.district:
        district = args.district
    if args.leg_body:
        leg_body = args.leg_body
    if args.voting_precincts:
        voting_precincts = args.voting_precincts
    if args.voting_results:
        voting_results = args.voting_results

    settings_dict = { 
                "census_api_key": census_api_key,
                "state": state,
                "district": district,
                "leg_body": leg_body,
                "year": year,
                "voting_year": voting_year,
                "voting_precincts": voting_precincts,
                "voting_results": voting_results
            }

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
    parser = argparse.ArgumentParser(description='Build stats for a given Congressional District')
    parser.add_argument('-s','--state', help='State of District, e.g., TX')
    parser.add_argument('-d','--district', help='District No., e.g., 7')
    parser.add_argument('-l','--leg-body', help='Legislative Body, e.g., US-REP, US-SEN, STATE-REP, or STATE-SEN')
    parser.add_argument('-y','--year', help='Year of Census data to build')
    parser.add_argument('-p','--voting-precincts', help='Estimate stats for voting precincts using geospatial vector file, e.g., shapefile or GEOJSON')
    parser.add_argument('-q','--voting-year', help='Year of voting results')
    parser.add_argument('-r','--voting-results', help='Build voting results from Open Elections csv file')
    parser.add_argument('-v','--version',action='version', 
            version='%(prog)s %(version)s' % {"prog": parser.prog, "version": _version})
    parser.add_argument('--debug',help='print debug messages',action="store_true")

    return parser.parse_args()


def mkdir_p(path):
    """create a directory with mkdir -p functionality
    Args:
        path: path to create
    Returns:
        Nothing
    Raises:
        OSError

    See https://stackoverflow.com/questions/600268/mkdir-p-functionality-in-python
    """
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def download_file(url, dl_filename):
    """Download a file given the url and filename
    Args:
        url: url to the file
        dl_filename: save the downloaded file using this filename
    Returns:
        Nothing
    Raises:
        Nothing

    See https://stackoverflow.com/questions/22676/how-do-i-download-a-file-over-http-using-python/22776#22776
    """
    print url
    url_object=urllib2.urlopen(url)
    dl_file_object=open(dl_filename,'wb')
    meta = url_object.info()
    file_size = None
    if len(meta.getheaders("Content-Length")) > 0:
        file_size = int(meta.getheaders("Content-Length")[0])
    if file_size is None:
        print "Downloading: %s" % (dl_filename.split('/')[-1])
    else:
        print "Downloading: %s Bytes: %s" % (dl_filename.split('/')[-1], file_size)
    
    current_file_size = 0
    block_size = 8192
    while True:
        buffer = url_object.read(block_size)
        if not buffer:
            break
        current_file_size += len(buffer)
        dl_file_object.write(buffer)
        if file_size is None:
            status = r"%10d " % (current_file_size)
        else:
            status = r"%10d  [%3.2f%%]" % (current_file_size, current_file_size * 100. / file_size)
        status = status + chr(8)*(len(status)+1)
        print status,
    dl_file_object.close()
    print "\n"


def extract_all(fn,dst="."):
    """extracts archive to dst
    Args:
        fn: filename
        dst: destiation
    Returns:
        Nothing
    Raises:
        Nothing
    """
    if tarfile.is_tarfile(fn): 
        with tarfile.open(fn,'r') as tf:
            tf.extractall(dst)
            tf.close()
    elif zipfile.is_zipfile(fn):
        with zipfile.ZipFile(fn, 'r') as zf:
            zf.extractall(dst)
            zf.close()
    else:
        print "Please provide a tar archive file or zip file"


# TODO Convert to a class

class District(object):

    def __init__(self, state, district, leg_body):
        self.state = state
        self.district = district
        self.leg_body = leg_body


def get_district_geojson_filename(state=48, district=7, leg_body='US-REP'):
    """Return the path and file name for the district file
    Args:
        state: state of district
        district: district number
        leg_body: legislative body, e.g., State Representative, State Senate, 
                  or US Representative
    Returns:
        district_file: filename of geojson file containing the boundary of the district
    Raises:
        Nothing
    """
    state = "{0:0>2}".format(state)
    district = "{0:0>2}".format(district)
    
    state_abbr = str(states.mapping('fips', 'abbr')[state])
    district_abbr = leg_body + '-' + state_abbr + district
    geojson_path = 'static/geojson/'

    district_file = geojson_path +  district_abbr + '.geojson'

    return district_file


def get_voting_precincts_geojson_filename(state=48, district=7, leg_body='US-REP'):
    """ Return the path and filename for the voting precincts file
    Args:
        state: state of district
        district: district number
        leg_body: legislative body, e.g., State Representative, State Senate, 
                  or US Representative
    Returns:
        vps_file: filename of the geijson file containing the voting precincts of the district
    Raises:
        Nothing
    """
    state = "{0:0>2}".format(state)
    district = "{0:0>2}".format(district)
    
    state_abbr = str(states.mapping('fips', 'abbr')[state])
    vps_abbr = leg_body + '-' + state_abbr + district + '-voting-precincts'
    geojson_path = 'static/geojson/'

    vps_file = geojson_path +  vps_abbr + '.geojson'

    return vps_file


def get_statewide_voting_precincts_geojson_filename(state=48):
    """Return the path and filename containing all the voting precincts for a state
    Args:
        state: state of district
    Returns:
        vps_file: filename of the geojson file containing the voting precincts of the state
    Raises:
        Nothing
    """
    state = "{0:0>2}".format(state)
    
    state_abbr = str(states.mapping('fips', 'abbr')[state])
    vps_abbr = state_abbr + '-voting-precincts'
    geojson_path = 'static/geojson/'

    vps_file = geojson_path +  vps_abbr + '.geojson'

    return vps_file


def get_state_blockgroups_geojson_filename(state=48):
    """Return the path and filename to the block groups for a state
    Args:
        state: state of the disctrict
    Returns:
        blockgroups_file: filename of the geojson file containing the blockgroups of the state
    Raises:
        Nothing
    """
    state = "{0:0>2}".format(state)
    
    state_abbr = str(states.mapping('fips', 'abbr')[state])
    geojson_path = 'static/geojson/'

    blockgroups_file = geojson_path + state_abbr + '-blockgroups.geojson'

    return blockgroups_file


def get_bgs_in_district_geojson_filename(state=48, district=7, leg_body='US-REP'):
    """Return the path and filename of the geojson file containing the blockgroups that overlap with the disctrict
    Args:
        state: state of district
        district: district number
        leg_body: legislative body, e.g., State Representative, State Senate, 
                  or US Representative
    Returns:
        bgs_in_district_GeoJSON: filename of the geojson file containing the blockgroups that overlap with the disctrict
    Raises:
        Nothing
    """
    state = "{0:0>2}".format(state)
    district = "{0:0>2}".format(district)
    
    state_abbr = str(states.mapping('fips', 'abbr')[state])
    district_abbr = leg_body + '-' + state_abbr + district
    geojson_path = 'static/geojson/'
    data_path = 'static/data/'
    shapfile_path = None
    bgs_in_district_fn = district_abbr + '-blockgroups'
    bgs_in_district_GeoJSON = geojson_path + bgs_in_district_fn + '.geojson'

    return bgs_in_district_GeoJSON


def get_bgs_in_district_json_filename(state=48, district=7, leg_body='US-REP'):
    """Return the path and filename of the json file containing the blockgroups that overlap with the disctrict
    Args:
        state: state of district
        district: district number
        leg_body: legislative body, e.g., State Representative, State Senate, 
                  or US Representative
    Returns:
        bgs_in_district_JSON: filename of json file containing the blockgroups that overlap with the disctrict
    Raises:
        Nothing
    """
    state = "{0:0>2}".format(state)
    district = "{0:0>2}".format(district)
    state_abbr = str(states.mapping('fips', 'abbr')[state])
    district_abbr = leg_body + '-' + state_abbr + district
    data_path = 'static/data/'
    bgs_in_district_fn = district_abbr + '-blockgroups'
   
    bgs_in_district_JSON = data_path + bgs_in_district_fn + '.json'

    return bgs_in_district_JSON
   

def get_district_file(state=48, district=7, leg_body='US-REP'):
    """Download the shape file for the disctrict
    Args:
        state: state of district
        district: district number
        leg_body: legislative body, e.g., State Representative, State Senate, 
                  or US Representative
    Returns:
        Nothing
    Raises:
        Nothing
    """

    district_file = get_district_geojson_filename(
            state=state, district=district, leg_body=leg_body)
    geojson_path = 'static/geojson/' 
    state = "{0:0>2}".format(state)
    district = "{0:0>2}".format(district)
    
    if not os.path.isfile(district_file):
        print "Downloading district file"
        # TODO download the most recent districts file
        # currently it downloads the 2016 district
        # 'http://www2.census.gov/geo/tiger/GENZ2016/shp/cb_2016_us_cd115_500k.zip'
        
        if leg_body == 'US-REP':
            district_url = 'http://www2.census.gov/geo/tiger/GENZ2016/shp/cb_2016_us_cd115_500k.zip'
        if leg_body == 'STATE-REP':
            district_url = 'ftp://ftpgis1.tlc.state.tx.us/DistrictViewer/House/PlanH358.zip'
        if leg_body == 'STATE-SEN':
            district_url = 'ftp://ftpgis1.tlc.state.tx.us/DistrictViewer/Senate/PlanS172.zip'
        
        district_dl_file = geojson_path + 'district.zip'
        download_file(district_url, district_dl_file)
        extract_all(district_dl_file, geojson_path)
        
        if len(glob(geojson_path + '*shp')) > 0:
            districts_shapefile = glob(geojson_path + '*shp')[0]
        else:
            for p in glob(geojson_path + '*'):
                if os.path.isdir(p):
                    shapefile_path = p
                    districts_shapefile = glob(p + '/*shp')[0]
        
        print "Converting district file to GEOJSON"
        districts = gpd.read_file(districts_shapefile)
        
        if leg_body == 'US-REP':
            d_index = districts[districts.GEOID == (state + district) ].index
        if leg_body == 'STATE-REP' or leg_body == 'STATE-SEN':
            d_index = districts[districts.District == int(district) ].index

        district_shape = districts.loc[d_index]
        district_shape = district_shape.to_crs({'init': u'epsg:4326'})
        district_shape.to_file(district_file, driver='GeoJSON')

        # cleanup geojson dir
        if len(glob(geojson_path + '*shp')) > 0:
            shapefile_prefix = glob(geojson_path + '*shp')[0].split(
                    geojson_path)[1].split('.')[0]
            shapefiles = glob(geojson_path + shapefile_prefix + '*')
            for f in shapefiles:
                os.remove(f)
        else:
            shapefile_prefix = glob(shapefile_path + '/*shp')[0].split(
                    shapefile_path)[1].split('.')[0]
            shapefiles = glob(shapefile_path + shapefile_prefix + '*')
            for f in shapefiles:
                os.remove(f)
            os.rmdir(shapefile_path)
        os.remove(district_dl_file)


def get_statewide_voting_precincts(state=48):
    """Download the shape file with the statewide voting precincts
    Args:
        state: state of the disctrict
    Returns:
        Nothing
    Raises:
        Nothing
    """
    vps_file = get_statewide_voting_precincts_geojson_filename(state)
    geojson_path = 'static/geojson/' 
    state = "{0:0>2}".format(state)
    
    if not os.path.isfile(vps_file):
        print "Downloading statewide voting precincts file"
        # TODO download the most recent precincts file
        # currently it downloads the 2016 TX precincts
        # 'https://github.com/nvkelso/election-geodata/raw/master/data/48-texas/statewide/2016/Precincts.zip'
        # TODO add support for other states
        
        vps_url = 'https://github.com/nvkelso/election-geodata/raw/master/data/48-texas/statewide/2016/Precincts.zip'
        
        vps_dl_file = geojson_path + 'vps.zip'
        download_file(vps_url, vps_dl_file)
        extract_all(vps_dl_file, geojson_path)
        
        if len(glob(geojson_path + '*shp')) > 0:
            vps_shapefile = glob(geojson_path + '*shp')[0]
        else:
            for p in glob(geojson_path + '*'):
                if os.path.isdir(p):
                    shapefile_path = p
                    vps_shapefile = glob(p + '/*shp')[0]
        
        print "Converting statewide voting precincts file to GEOJSON"
        vps = gpd.read_file(vps_shapefile)
        
        vps = vps.to_crs({'init': u'epsg:4326'})
        vps.to_file(vps_file, driver='GeoJSON')

        # cleanup geojson dir
        if len(glob(geojson_path + '*shp')) > 0:
            shapefile_prefix = glob(geojson_path + '*shp')[0].split(
                    geojson_path)[1].split('.')[0]
            shapefiles = glob(geojson_path + shapefile_prefix + '*')
            for f in shapefiles:
                os.remove(f)
        else:
            shapefile_prefix = glob(shapefile_path + '/*shp')[0].split(
                    shapefile_path)[1].split('.')[0]
            shapefiles = glob(shapefile_path + shapefile_prefix + '*')
            for f in shapefiles:
                os.remove(f)
            os.rmdir(shapefile_path)
        os.remove(vps_dl_file)


def get_state_blockgroups_file(state=48, district=7, leg_body='US-REP', year='2015'):
    """Download the file, from the Census Bureau, containing the blockgroups for an entire state
    Args:
        state: state of the disctrict
        district: district number
        leg_body: legislative body, e.g., State Representative, State Senate, 
                  or US Representative
        year: year for the district data
    Returns:
        Nothing
    Raises:
        Nothing
    """

    blockgroups_file = get_state_blockgroups_geojson_filename(state=state)
            
    state = "{0:0>2}".format(state)
    district = "{0:0>2}".format(district)
    
    print blockgroups_file

    if not os.path.isfile(blockgroups_file):
        print "Downloading blockgroups"
        bgs_url = 'ftp://ftp2.census.gov/geo/tiger/TIGER{year}/BG/tl_{year}_{state}_bg.zip'.format(year=year, state=state)
        bgs_dl_file = geojson_path + 'bgs.zip'
        download_file(bgs_url, bgs_dl_file)
        extract_all(bgs_dl_file, geojson_path)
        bgs_shapefile = glob(geojson_path + '*shp')[0]

        print "Converting blockgroups file to GEOJSON"
        bgs = gpd.read_file(bgs_shapefile)
        bgs = bgs.to_crs({'init': u'epsg:4326'})
        bgs.to_file(blockgroups_file, driver='GeoJSON')

        # cleanup geojson dir
        shapefile_prefix = glob(geojson_path + '*shp')[0].split(
                geojson_path)[1].split('.')[0]
        shapefiles = glob(geojson_path + shapefile_prefix + '*')
        for f in shapefiles:
            os.remove(f)
        os.remove(bgs_dl_file)

# TODO
# def find_tracts_in_district(state='48', district='07'):


def find_blockgroups_in_district(state=48, district=7, leg_body='US-REP', year='2015', debug_is_on=False):
    """Find the blockgroups that intersect with a legislative district, e.g., US Congressional District.
    Args:
        state: The state of the district
        district: district number
        leg_body: legislative body, e.g., State Representative, State Senate, 
                  or US Representative
        year: year associated with the district data
        debug_is_on: boolean providing whether to print debug output
    Returns:
        Nothing
    Raises:
        Nothing
    """
    shapfile_path = None
    bgs_in_district_GeoJSON = get_bgs_in_district_geojson_filename(state=state, district=district, leg_body=leg_body)
    bgs_in_district_JSON = get_bgs_in_district_json_filename(state=state, district=district, leg_body=leg_body)
    district_file = get_district_geojson_filename(state=state, district=district, leg_body=leg_body)
    blockgroups_file = get_state_blockgroups_geojson_filename(state=state)
    
    if not os.path.isfile(bgs_in_district_GeoJSON):
        get_district_file(state=state, district=district, leg_body=leg_body)
    
        get_state_blockgroups_file(
            state=state, district=district, leg_body=leg_body, year=year)
        
        print "Finding blockgroups in district"
        district = gpd.read_file(district_file)
        block_groups = gpd.read_file(blockgroups_file)
        
        print "Finding blockgroups that touch the district boundary"
        bgs_touching_district_bool = block_groups.touches(district.geometry[0])
        
        print "Finding blockgroups that intersect the district boundary"
        bgs_intersecting_district_bool = block_groups.intersects(district.geometry[0])
        
        print "Filtering the blockgroups"
        for index in bgs_touching_district_bool[bgs_touching_district_bool==True].index:
            bgs_intersecting_district_bool.loc[index] = False

        bgs_in_district = block_groups[bgs_intersecting_district_bool]
 
        print "Finding blockgroups to filter based on threshold"
        intersections = bgs_in_district.intersection(district.geometry[0])

        areas_of_intersections = intersections.area
        indx_out = []
        for bg_index, bg in bgs_in_district.iterrows():
            area_of_intersection = areas_of_intersections[bg_index]
            bg_area = GeoSeries(bg.geometry).area[0]

            share_of_intersection = area_of_intersection / bg_area
            
            if share_of_intersection < 0.10:
                indx_out.append(bg_index)

            #print "\nBlock Group: ", bg.GEOID
            #print "Area: ", str(bg_area)
            #print "Share of Intersection: ", str(share_of_intersection)
        
        bgs_to_remove_bool = pd.Series([False]*len(block_groups))

        for index in indx_out:
            bgs_to_remove_bool.loc[index] = True

        bgs_to_remove = block_groups[bgs_to_remove_bool]

        for index in bgs_to_remove_bool[bgs_to_remove_bool==True].index:
            bgs_intersecting_district_bool.loc[index] = False

        bgs_in_district = block_groups[bgs_intersecting_district_bool]

        # See issue #367 https://github.com/geopandas/geopandas/issues/367
        try: 
            os.remove(bgs_in_district_GeoJSON)
        except OSError:
            pass
        bgs_in_district.to_file(bgs_in_district_GeoJSON, driver='GeoJSON')
        
        # Create json file of geo units
        bgs_in_district[['BLKGRPCE','COUNTYFP', 'STATEFP', 'TRACTCE', 'GEOID']].to_json(bgs_in_district_JSON)
        
        if debug_is_on:
            plt.figure(figsize=(400, 400))
            district_plot=district.plot(color='blue', alpha=0.5)
            bgs_in_district.plot(ax=district_plot, color='green',alpha=0.5)
            plt.savefig(bgs_in_district_fn,dpi=600)
            plt.close()

            plt.figure(figsize=(400, 400))
            district_plot=district.plot(color='blue', alpha=0.5)
            block_groups[bgs_touching_district_bool].plot(ax=district_plot, color='green',alpha=0.5)
            plt.savefig(bgs_in_district_fn + '-touching',dpi=600)
            plt.close()

            plt.figure(figsize=(400, 400))
            district_plot=district.plot(color='blue', alpha=0.5)
            bgs_to_remove.plot(ax=district_plot, color='green',alpha=0.5)
            plt.savefig(bgs_in_district_fn + '-threshold-filter',dpi=600)
            plt.close()
        

def find_voting_precincts_in_district(state=48, district=7, leg_body='US-REP'):
    """Find the voting precincts that are in a district
    Args:
        state: state of the disctrict
        district: district number
        leg_body: legislative body, e.g., State Representative, State Senate, 
                  or US Representative
    Returns:
        Nothing
    Raises:
        Nothing
    """
    vps_in_district_GeoJSON  = get_voting_precincts_geojson_filename(
            state=state, district=district, leg_body=leg_body)
    
    if not os.path.isfile(vps_in_district_GeoJSON):
        voting_precincts_file = get_statewide_voting_precincts_geojson_filename(state)
    
        district_file = get_district_geojson_filename(
            state=state, district=district, leg_body=leg_body)
    
        get_district_file(state=state, district=district, leg_body=leg_body)

        get_statewide_voting_precincts(state=state)
        
        print "Finding voting precincts in district"
        district_boundary = gpd.read_file(district_file)
        voting_precincts = gpd.read_file(voting_precincts_file)
        
        print "Finding voting precincts that touch the district boundary"
        vps_touching_district_bool = voting_precincts.touches(district_boundary.geometry[0])
            
        print "Finding voting precincts that intersect the district boundary"
        vps_intersecting_district_bool = voting_precincts.intersects(district_boundary.geometry[0])
            
        print "Filtering the voting precincts"
        for index in vps_touching_district_bool[vps_touching_district_bool==True].index:
            vps_intersecting_district_bool.loc[index] = False

        vps_in_district = voting_precincts[vps_intersecting_district_bool]
     
        print "Finding blockgroups to filter based on threshold"
        intersections = vps_in_district.intersection(district_boundary.geometry[0])

        areas_of_intersections = intersections.area
        indx_out = []
        for vp_index, vp in vps_in_district.iterrows():
            area_of_intersection = areas_of_intersections[vp_index]
            vp_area = GeoSeries(vp.geometry).area[0]

            share_of_intersection = area_of_intersection / vp_area
                
            if share_of_intersection < 0.10:
                indx_out.append(vp_index)

            #print "\nBlock Group: ", bg.GEOID
            #print "Area: ", str(bg_area)
            #print "Share of Intersection: ", str(share_of_intersection)
            
        vps_to_remove_bool = pd.Series([False]*len(voting_precincts))

        for index in indx_out:
            vps_to_remove_bool.loc[index] = True

        vps_to_remove = voting_precincts[vps_to_remove_bool]

        for index in vps_to_remove_bool[vps_to_remove_bool==True].index:
            vps_intersecting_district_bool.loc[index] = False

        vps_in_district = voting_precincts[vps_intersecting_district_bool]
        if 'PREC' in list(vps_in_district.columns.values):
            vps_in_district = vps_in_district.rename(columns={'PREC':'PRECINCT'})

        # See issue #367 https://github.com/geopandas/geopandas/issues/367
        try: 
            os.remove(vps_in_district_GeoJSON)
        except OSError:
            pass
        vps_in_district.to_file(vps_in_district_GeoJSON, driver='GeoJSON')
        
        vps_in_district.sort_values(by=['PRECINCT'])[['PRECINCT']].to_csv("vps.csv", index=False)


def get_district_centroid(state=48, district=7, leg_body='US-REP', year='2015'):
    """Return the centroid of a district
    Args:
        state: state of the disctrict
        district: district number
        leg_body: legislative body, e.g., State Representative, State Senate, 
                  or US Representative
    Returns:
        longitude: longitudinal coordinate of the centroid
        latitude: latitudinal coordinate of the centroid
    Raises:
        Nothing
    """
    district_file = get_district_geojson_filename(
            state=state, district=district, leg_body=leg_body)
    
    get_district_file(state=state, district=district, leg_body=leg_body)

    district = gpd.read_file(district_file)

    longitude = district.geometry.centroid[0].x
    latitude = district.geometry.centroid[0].y

    return (longitude, latitude)


def get_blockgroup_census_data(api, fields, census_data = {}, state=48, district=7, leg_body='US-REP', year='2015'):
    """Retrieve the census data for the block groups in a District
    Args:
        api: Census api key
        fields: the fields to query from api.census.gov; 
            See e.g., https://api.census.gov/data/2015/acs5/variables.html
        year: The year the census data was collected
        state: state of the district
        district: district number
        leg_body: legislative body, e.g., State Representative, State Senate, 
                  or US Representative
        year: year associated with district data
    Returns:
        census_data: a list of dictionaries storing the blockgroup results
    Raises
        Nothing
    """
    blockgroup_key = 'bg'
    if year not in census_data.keys():
        census_data[year] = { blockgroup_key: {} }
    else:
        if blockgroup_key not in census_data[year].keys():
            census_data[year][blockgroup_key] = { }
    # TODO make dynamic to state and district

    state = "{0:0>2}".format(state)
    district = "{0:0>2}".format(district)
    
    state_abbr = str(states.mapping('fips', 'abbr')[state])
    district_abbr = leg_body + '-' + state_abbr + district
    data_path = 'static/data/'
    bgs_in_district_JSON = data_path + district_abbr + '-blockgroups.json'

    bgs_in_district = pd.read_json(bgs_in_district_JSON)
    
    # Setup Census query
    census_query = Census(api, year=int(year))
    num_of_bgs = len(bgs_in_district)
    i = 0.0
    for bg_index, bg in bgs_in_district.iterrows():
        # print percent complete
        status = r"%10d  [%3.2f%%]" % (i, i * 100. / num_of_bgs)
        status = status + chr(8)*(len(status)+1)
        print status,
        bg_stats = census_query.acs5.state_county_blockgroup(
                        fields=fields, 
                        state_fips=bg['STATEFP'], 
                        county_fips=bg['COUNTYFP'], 
                        blockgroup=bg['BLKGRPCE'],
                        tract=bg['TRACTCE']
                    )[0]
        geoid = str(bg['GEOID'])
        if geoid in census_data[year][blockgroup_key].keys():
            census_data[year][blockgroup_key][geoid].update(bg_stats)
        else:
            census_data[year][blockgroup_key][geoid] = bg_stats
        i = i + 1

    return census_data


def get_district_census_data(api, fields, census_data = {}, state=48, district=7, leg_body='US-REP', year='2015'):
    """Retrieve the census data for the entire district
    Args:
        api: Census api key
        fields: the fields to query from api.census.gov; 
            See e.g., https://api.census.gov/data/2015/acs/acs5/variables.html
        state: the state of the district
        district: district number
        leg_body: legislative body, e.g., State Representative, State Senate, 
                  or US Representative
        year: year associated with disctrict data
    Returns:
        census_data: a list of dictionaries storing the census data
    Raises
        Nothing
    """
    district_key = 'district'
    if year not in census_data.keys():
        census_data[year] = { district_key: {} }
    else:
        if district_key not in census_data[year].keys():
            census_data[year][district_key] = { }

    if leg_body == 'US-REP':
        state = "{0:0>2}".format(state)
        district = "{0:0>2}".format(district)
        # Setup Census query
        census_query = Census(api, year=int(year))
        district_stats = census_query.acs5.get(
                        fields,
                        {   'for': 'congressional district:' + district,
                            'in': 'state:' + state
                        }
                    )[0]
        census_data[year][district_key].update(district_stats)
    
    return census_data


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


def get_census_fields_by_table(table, year='2015'):
    """Return the fields in a census table
    Args: 
        table: the table name  
        year: year of census data 
    Returns: 
        fields: 
        labels: 
    Raises:
        Nothing (yet)
    """
    variables_file = 'static/data/variables_' + year + '.json'
    if not os.path.isfile(variables_file):
        url = 'https://api.census.gov/data/' + year + '/acs5/variables.json'
        download_file(url, variables_file)

    fields = []
    labels = {}

    with open(variables_file) as variables:
        data = json.load(variables)
        for key in data['variables']:
            if re.match(table+'_[0-9]*E', key):
                fields.append(key)
                labels[key]=data['variables'][key]['label']
    
    return fields, labels


def load_district_data(district_data_file='static/data/district-data.json', 
        state=48, district=7, year='2015'):
    """
    Args:
        district_data_file:
        state:
        district:
        year:
    Returns: 
        district_data:
    Raises:
        Nothing (yet)
    """
    district_data={}
    if os.path.isfile(district_data_file):
        with open(district_data_file) as district_json:
            district_data = json.load(district_json)

    return district_data


def make_pid_and_class_data(census_data_in_district, pid_classes, 
        census_classes, pid_total_field, category= {}, district_data={}, 
        state=48, district=7, leg_body='US-REP', year='2015', geo_key='bg' ):
    """Calculate the PID classes and populate Census classes
    Args:
        census_data_in_district:
        pid_class:
        census_class:
    Returns: 
        district_data:
    Raises:
        Nothing (yet)
    """
    if year not in district_data.keys():
        district_data[year] = { geo_key: {} }
    if year in district_data.keys():
        if geo_key not in district_data[year].keys():
            district_data[year][geo_key] = {}
    
    if geo_key is not 'district':    
        for geoid, census_data in census_data_in_district[year][geo_key].iteritems():
            pid_total = 0.0
            if geoid not in district_data[year][geo_key].keys():
                district_data[year][geo_key][geoid] = {}

            # PID Total and classes
            for pid_class, pid_census_classes in pid_classes.iteritems():
                pid_class_total = 0.0
                for pid_census_field in pid_census_classes['fields']:
                    # Add up the total PID for this class, e.g., Younger Millennial (18-25) 
                    pid_class_value = float(census_data[pid_census_field]) * float(pid_census_classes['pid'])
                    pid_class_total =  pid_class_total + pid_class_value

                    # Add up the total PID by Category, e.g., Age
                    pid_total = pid_total + pid_class_value
                # PID Class
                district_data[year][geo_key][geoid][pid_class] = int(pid_class_total)
            # PID Total
            district_data[year][geo_key][geoid][pid_total_field] = int(pid_total)
            
            # Census classes
            for census_class, census_class_row in census_classes.iteritems():
                # Add up the total of this census_class, e.g., (18-29) or 30s
                census_class_total = 0

                for census_subclass in census_class_row['fields']:
                    census_subclass_value = int(census_data[census_subclass])
                    census_class_total =  census_class_total + census_subclass_value

                # Census Class
                district_data[year][geo_key][geoid][census_class] = census_class_total

    # geokey is 'district'
    if geo_key == 'district':
        # TODO add support for non-congressional districts
        if leg_body == 'US-REP':
            pid_total = 0.0
            # PID Total and classes
            for pid_class, pid_census_classes in pid_classes.iteritems():
                pid_class_total = 0.0
                for pid_census_field in pid_census_classes['fields']:
                    # Add up the total PID for this class, e.g., Younger Millennial (18-25) 
                    pid_class_value = float(census_data_in_district[year][geo_key][pid_census_field]) * float(pid_census_classes['pid'])
                    pid_class_total =  pid_class_total + pid_class_value

                    # Add up the total PID by Category, e.g., Age
                    pid_total = pid_total + pid_class_value
                # PID Class
                district_data[year][geo_key][pid_class] = int(pid_class_total)
            # PID Total
            district_data[year][geo_key][pid_total_field] = int(pid_total)
        
            # Census classes
            for census_class, census_class_row in census_classes.iteritems():
                # Add up the total of this census_class, e.g., (18-29) or 30s
                census_class_total = 0

                for census_subclass in census_class_row['fields']:
                    census_subclass_value = int(census_data_in_district[year][geo_key][census_subclass])
                    census_class_total =  census_class_total + census_subclass_value

                # Census Class
                district_data[year][geo_key][census_class] = census_class_total

    return district_data


def make_district_data_for_state_leg(categories={}, district_data={}, 
        state=48, district=7, leg_body='US-REP', year='2015'):
    """
    Args:
        ________
    Returns: 
        district_data:
    Raises:
        Nothing (yet)
    """

    bg_key = 'bg'
    district_key = 'district'
    
    state = "{0:0>2}".format(state)
    district = "{0:0>2}".format(district)
    
    state_abbr = str(states.mapping('fips', 'abbr')[state])
    district_abbr = leg_body + '-' + state_abbr + district
    geojson_path = 'static/geojson/'
    
    if os.path.isdir(geojson_path) == False:
        print "Making path {path}".format(path=geojson_path)
        mkdir_p(geojson_path)

    blockgroups_file = geojson_path + district_abbr + '-blockgroups.geojson' 
    district_file = geojson_path +  district_abbr + '.geojson'
    
    print "Estimating districtwide statistics for the district"
    blockgroups = gpd.read_file(blockgroups_file)
    district_boundary = gpd.read_file(district_file)
    
    if district_key not in district_data[year].keys():
        district_data[year][district_key] = {}

    for cat_index, category in categories.iteritems(): 
        for cat_typ_index, cat_type in category.iteritems():
            for field in cat_type['fields']:
                if field not in 'median_income':
                    district_data[year][district_key][field] = 0.0

    intersections = blockgroups.geometry.intersection(district_boundary.geometry[0])
    areas = intersections.area
    for bg_index, bg in blockgroups.iterrows():
        interArea = areas[bg_index]
        bgArea = GeoSeries(bg.geometry).area[0]

        share = (interArea/bgArea)
        for field, value in district_data[year][bg_key][bg.GEOID].iteritems():
            if 'median_income' not in field:
                if value is None:
                    value = 0.0
                total = district_data[year][district_key][field]
                total = total + float(value) * share
                district_data[year][district_key][field] = total

    # convert all the district values to int
    for field in district_data[year][district_key].keys():
        field_to_int = int(district_data[year][district_key][field])
        district_data[year][district_key][field] = field_to_int
        # TODO add support for state legislative bodies

    return district_data


def get_census_data(api, category, fields,
        district_config_file = 'static/data/district.json',
        census_data_file='static/data/district-census-data.json', 
        state=48, district=7, leg_body='US-REP', year='2015'):
    """Store the raw census data in a json file and return the census data
    Args:
        api
        category
        fields
        district_config_file
        census_data_file
        state
        district
        leg_body
        year
    Returns: 
        census_data: 
    Raises:
        Nothing (yet)
    """
    # If district config file is there, only get the census data that's not there
    if os.path.isfile(district_config_file):
        with open(district_config_file) as district_json:
            district_config = json.load(district_json)

            if os.path.isfile(census_data_file):
                with open(census_data_file) as census_json:
                    census_data = json.load(census_json)

            census_data_is_for_my_district = (district_config['state'] == state) and ( 
                    district_config['district'] == district)

            census_data_is_for_my_year = year in district_config
            
            # if everything is there, load from file
            if census_data_is_for_my_district and census_data_is_for_my_year:
                census_data_has_my_category = category in district_config[year]
                if census_data_has_my_category:
                    return census_data

            # if not, get data via census api and save to file
            # get the data for the blockgroups in the district
            census_data = get_blockgroup_census_data(
                    api=api, 
                    census_data=census_data,
                    fields=fields, 
                    state=state, 
                    district=district, 
                    leg_body=leg_body, 
                    year=year
                )
            # get the data for the entire district
            census_data = get_district_census_data(
                    api=api, 
                    census_data=census_data,
                    fields=fields, 
                    state=state, 
                    district=district, 
                    leg_body=leg_body, 
                    year=year
                )

            # TODO add get_tract_census_data()

            if year not in district_config.keys():
                district_config[year] = [category]
                district_config['years'].append(year)
            else:
                district_config[year].append(category)
            # save census data to file
            to_json(census_data, census_data_file)
            to_json(district_config, district_config_file)
            
            return census_data

    # if there is no previous data for this district, then build from scratch
    census_data = get_blockgroup_census_data(
            api=api, 
            fields=fields, 
            state=state, 
            district=district, 
            leg_body=leg_body, 
            year=year)
    
    census_data = get_district_census_data(
            api=api, 
            census_data=census_data,
            fields=fields, 
            state=state, 
            district=district, 
            leg_body=leg_body, 
            year=year
        )

    # TODO add get_tract_census_data()

    # create district config file
    # add state, district, years, and categories
    district_config = {}
    district_config['state'] = state
    district_config['district'] = district
    district_config[year] = [category]
    district_config['years'] = [year]
    
    # add centroid
    longitude, latitude = get_district_centroid(
            state=state, district=district, leg_body=leg_body, year=year)
    district_config['lat']=latitude
    district_config['lng']=longitude   
    
    # add file locations
    district_GeoJSON = get_district_geojson_filename(
            state=state, district=district, leg_body=leg_body)
    bgs_in_district_GeoJSON = get_bgs_in_district_geojson_filename(
            state=state, district=district, leg_body=leg_body)
    vps_in_district_GeoJSON  = get_voting_precincts_geojson_filename(
            state=state, district=district, leg_body=leg_body)
    district_config['district_geojson'] = '/' + district_GeoJSON
    district_config['bg_geojson'] = '/' + bgs_in_district_GeoJSON
    district_config['precinct_geojson'] = '/' + vps_in_district_GeoJSON
    
    # add title
    state_fips = "{0:0>2}".format(state) 
    district_name = "{0:0>2}".format(district)
    state_name = states.mapping('abbr', 'name')[states.mapping('fips', 'abbr')[state_fips]]
    if leg_body == 'US-REP':
        leg_name = "Congressional"
    if leg_body == 'STATE-REP':
        leg_name = "House"
    if leg_body == 'STATE-SEN':
        leg_name = "Senate"
    title = state_name + " " + leg_body + " District "  + district_name
    district_config['title']=title

    # save census data to file
    to_json(census_data, census_data_file)
    to_json(district_config, district_config_file)
    
    return census_data


def make_age_data(api, district_data = {}, categories = {'Age': {} },
        state=48, district=7, leg_body='US-REP', year='2015'):
    """Make the age Party Identification (PID) data and census data for a district
    Args: 
        api: 
        state: 
        district: 
        year: 
        data_file:
    Returns: 
        categories:
    Raises:
        Nothing (yet)

    PID by Age Class:
                                R       D       I       O       LR      LD      NL      UN*
                                %	%	%	%	%	%	%	
    DETAILED GENERATION
    Younger Millennial (18-25)	22	33	43	2	36	58	6	613
    Older Millennial (26-35)	22	35	39	4	36	56	8	982
    Younger Gen Xer (36-43)	24	34	37	4	38	51	11	809
    Older Gen Xer (44-51)	30	32	35	3	46	46	8	1,055
    Younger Boomer (52-60)	32	33	32	3	48	46	6	1,602
    Older Boomer (61-70)	33	34	28	4	49	44	7	1,711
    Younger Silent (71-80)	39	33	24	4	53	41	7	928
    Older Silent (81-88)	43	31	19	8	53	39	8	248
      * R = Rep
        D = Dem
        I = Ind
        O = Other
        LR = Lean Rep
        LD = Lean Dem
        NL = No leaning
        UN = Unweighted N
    
    See http://www.people-press.org/2016/09/13/2016-party-identification-detailed-tables/

    """
    category='Age'
    
    district_key='district'
    blockgroup_key='bg'
    precinct_key='precinct'
    tract_key='tract'

    total_census_field = 'B01001_001E'
    age_table = 'B01001'
    
    total_field = 'total'
    total_label = 'Total'
    
    over_18_field = 'over_18'
    over_18_label = '18 and over'
    
    pid_total_field = 'pid_age_total'
    pid_total_label = 'PID Age Total'
    
    data_path = 'static/data/'

    age_pid_classes = get_age_pid_classes()
    age_classes = get_age_classes()
    
    under_18_classes = get_under_18_classes()
    
    # Load the census data
    print "Getting Census Data for Sex by Age"
    census_fields, census_labels = get_census_fields_by_table(table=age_table, 
            year=year)
    census_data = get_census_data(api=api, category=category, fields=census_fields, 
        state=state, district=district, leg_body=leg_body, year=year)
    
    # create fields and labels for Party Identification classes
    # used in web-based dashboard
    fields = []
    labels = {}
    
    fields.append(pid_total_field)
    labels[pid_total_field] = pid_total_label
    
    fields.append(total_field)
    labels[total_field] = total_label
    
    fields.append(over_18_field)
    labels[over_18_field] = over_18_label

    for age_field, age_row in age_pid_classes.iteritems():
        fields.append(age_field)
        labels[age_field] = age_row['label']
    
    categories[category]['PID'] = {'fields': fields, 'labels': labels}
    
    # create fields and labels for census classes
    # used in web-based dashboard
    fields = []
    labels = {}
    
    fields.append(over_18_field)
    labels[over_18_field] = over_18_label
    
    fields.append(total_field)
    labels[total_field] = total_label
    
    for age_field, age_row in age_classes.iteritems():
        fields.append(age_field)
        labels[age_field] = age_row['label']
    
    categories[category]['Census'] = {'fields': fields, 'labels': labels}

    print "\nCalculating PID by Age"
   
    # make the party identification data and data for the census classes
    # for the blockgroups
    district_data = make_pid_and_class_data( 
            census_data_in_district=census_data, 
            pid_classes=age_pid_classes,
            census_classes=age_classes,
            pid_total_field=pid_total_field,
            district_data=district_data,
            district=district,
            leg_body=leg_body,
            year=year
        )
    # make the party identification data and data for the census classes
    # for the district
    district_data = make_pid_and_class_data( 
            census_data_in_district=census_data, 
            pid_classes=age_pid_classes,
            census_classes=age_classes,
            pid_total_field=pid_total_field,
            district_data=district_data,
            category=categories[category],
            district=district,
            leg_body=leg_body,
            year=year,
            geo_key=district_key
        )

    # Calculate persons 18 and over in each block group and 
    # get the total population in each block group
    geo_key = blockgroup_key
    for geoid, census_data_row in census_data[year][geo_key].iteritems():
        # Persons 18 and over
        under_18 = 0
        for census_field in under_18_classes['fields']:
            under_18 = under_18 + int(census_data_row[census_field])
        # (over 18) = total - (under 18)
        over_18 = int(census_data_row[total_census_field]) - under_18
        district_data[year][geo_key][geoid][over_18_field] = over_18
            
        # Total Population
        district_data[year][geo_key][geoid][total_field] = census_data_row[total_census_field]
    
    if leg_body == 'US-REP':
        # calculate the district stats
        geo_key = district_key
        for census_field in under_18_classes['fields']:
            under_18 = under_18 + int(census_data[year][geo_key][census_field])
        # (over 18) = total - (under 18)
        over_18 = int(census_data[year][geo_key][total_census_field]) - under_18
        district_data[year][geo_key][over_18_field] = over_18
            
        # Total Population
        district_data[year][geo_key][total_field] = census_data[year][geo_key][total_census_field]

    return categories, district_data


def make_income_data(api, district_data = {}, categories = {'Income': { }}, 
        state=48, district=7, leg_body='US-REP', year='2015'):
    """Make the income data for a district
    Args: 
        api: 
        state: 
        district: 
        year: 
    Returns: 
        categories:
        district_data:
    Raises:
        Nothing (yet)

    PID by Income:
                                R       D       I       O       LR      LD      NL      UN*
                                %	%	%	%	%	%	%	
    $150,000+                   33      32      32      3       46      48      6       1,069
    $100,000 to $149,999        34      30      33      3       51      45      4       1,188
    $75,000 to $99,999          31      30      35      4       48      44      8       1,084
    $50,000 to $74,999          32      30      35      4       49      44      6       1,275
    $40,000 to $49,999          31      31      35      3       47      46      7       638
    $30,000 to $39,999          31      33      33      3       47      46      7       671
    <$30,000                    20      43      34      3       32      60      8       1,464
      * R = Rep
        D = Dem
        I = Ind
        O = Other
        LR = Lean Rep
        LD = Lean Dem
        NL = No leaning
        UN = Unweighted N
    
    See http://www.people-press.org/2016/09/13/2016-party-identification-detailed-tables/

    """
    category='Income'

    district_key='district'
    blockgroup_key='bg'
    precinct_key='precinct'
    tract_key='tract'

    income_table = 'B19001'
    total_household_inc_field = 'B19001_001E'
    median_household_inc_field = 'B19013_001E'
    
    total_field = 'total_income'
    total_label = 'Total Households'
    
    pid_total_field = 'pid_total_income'
    pid_total_label = 'PID by Total Household Income'
    
    over_100k_field = 'over_100k'
    over_100k_label = '> $100,000'

    under_100k_field = 'under_100k'
    under_100k_label = '< $100,000'
    
    median_field = 'median_income'
    median_label = 'Median Household Income'
    
    income_pid_classes = get_income_pid_classes()
    income_classes = get_income_classes()
    

    # Load the census data
    print "Getting Census Data for Household Income"
    census_fields, census_labels = get_census_fields_by_table(table=income_table, 
            year=year)
    census_fields.append(median_household_inc_field)
    census_data = get_census_data(api=api, category=category, fields=census_fields,
        state=state, district=district, leg_body=leg_body, year=year)

    # create fields and labels for Party Identification classes
    # used in web-based dashboard
    fields = []
    labels = {}
    
    fields.append(pid_total_field)
    labels[pid_total_field] = pid_total_label
    
    fields.append(total_field)
    labels[total_field] = total_label
    
    for income_field, income_row in income_pid_classes.iteritems():
        fields.append(income_field)
        labels[income_field] = income_row['label']
    
    if category not in categories.keys():
        categories[category] = {}

    categories[category]['PID'] = {'fields': fields, 'labels': labels}
    
    # create fields and labels for census classes
    # used in web-based dashboard
    fields = []
    labels = {}
    
    fields.append(total_field)
    labels[total_field] = total_label
    
    fields.append(under_100k_field)
    labels[under_100k_field] = under_100k_label
    
    fields.append(over_100k_field)
    labels[over_100k_field] = over_100k_label

    for income_field, income_row in income_classes.iteritems():
        fields.append(income_field)
        labels[income_field] = income_row['label']
    
    fields.append(median_field)
    labels[median_field] = median_label
    
    categories[category]['Census'] = {'fields': fields, 'labels': labels}
    
    # add over/under fields
    # this is to customize their position in the drop down menu
    income_classes[over_100k_field] = get_over_100k_income_classes(over_100k_field)
    income_classes[under_100k_field] = get_under_100k_income_classes(under_100k_field)

    print "\nCalculating PID by Income"
   
    # make the party identification data and census data
    district_data = make_pid_and_class_data(
            census_data_in_district=census_data, 
            pid_classes=income_pid_classes,
            census_classes=income_classes,
            pid_total_field=pid_total_field,
            district_data=district_data,
            district=district,
            leg_body=leg_body,
            year=year
            # TODO
            # add a list of singles (eg, total or median) to retrieve
        )

    # make the party identification data and data for the census classes
    # for the district
    district_data = make_pid_and_class_data( 
            census_data_in_district=census_data, 
            pid_classes=income_pid_classes,
            census_classes=income_classes,
            pid_total_field=pid_total_field,
            district_data=district_data,
            district=district,
            leg_body=leg_body,
            year=year,
            geo_key=district_key
        )

    # get the total households and the median household income
    geo_key = blockgroup_key
    for geoid, census_data_row in census_data[year][geo_key].iteritems():
        # Median Household Income
        district_data[year][geo_key][geoid][median_field] = census_data_row[median_household_inc_field]
            
        # Total Households
        district_data[year][geo_key][geoid][total_field] = census_data_row[total_household_inc_field]
    
    # calculate the district stats
    if leg_body == 'US-REP': 
        geo_key = district_key
        # Median Household Income
        district_data[year][geo_key][median_field] = census_data[year][geo_key][median_household_inc_field]
            
        # Total Households
        district_data[year][geo_key][total_field] = census_data[year][geo_key][total_household_inc_field]

    return categories, district_data
    

def make_race_data( api,  district_data = {}, categories = {'Race': { }}, 
        state=48, district=7, leg_body='US-REP', year='2015' ):
    """Make the race data for a district
    Args: 
        api: 
        state: 
        district: 
        year: 
    Returns: 
        categories:
        district_data:
    Raises:
        Nothing (yet)

    PID by Race:
                                R       D       I       O       LR      LD      NL      UN*
                                %	%	%	%	%	%	%	
    White, non-Hispanic	        36	26	35	3	54	39	7	5,895
    Black, non-Hispanic	        3	70	23	4	7	87	6	782
    Hispanic	                16	47	32	5	27	63	10	810
    Asian, non-Hispanic         18	44	32	6	27	66	7	164
    (English-speaking
    only)	
      * R = Rep
        D = Dem
        I = Ind
        O = Other
        LR = Lean Rep
        LD = Lean Dem
        NL = No leaning
        UN = Unweighted N
    
    See http://www.people-press.org/2016/09/13/2016-party-identification-detailed-tables/

    """
    category='Race'

    district_key='district'
    blockgroup_key='bg'
    precinct_key='precinct'
    tract_key='tract'

    race_table = 'B02001'
    hispanic_table = 'B03003'
    race_total_field = 'B02001_001E'
    
    total_field = 'total_race'
    total_label = 'Total Population'
    
    pid_total_field = 'pid_total_race'
    pid_total_label = 'PID by Race'
    
    race_pid_classes = get_race_pid_classes()
    race_classes = get_race_classes()

    # Load the census data
    census_fields = []
    print "Getting Census Data for Race"
    race_fields, census_labels = get_census_fields_by_table(table=race_table, 
            year=year)
    census_fields.extend(race_fields)
    
    hispanic_fields, census_labels = get_census_fields_by_table(table=hispanic_table, 
            year=year)
    census_fields.extend(hispanic_fields)

    census_data = get_census_data(api=api, category=category, fields=census_fields,
        state=state, district=district, leg_body=leg_body, year=year)

    # create fields and labels for Party Identification classes
    # used in web-based dashboard
    fields = []
    labels = {}
    
    fields.append(pid_total_field)
    labels[pid_total_field] = pid_total_label
    
    fields.append(total_field)
    labels[total_field] = total_label
    
    for race_field, race_row in race_pid_classes.iteritems():
        fields.append(race_field)
        labels[race_field] = race_row['label']
    
    if category not in categories.keys():
        categories[category] = {}

    categories[category]['PID'] = {'fields': fields, 'labels': labels}
    
    # create fields and labels for census classes
    # used in web-based dashboard
    fields = []
    labels = {}
    
    fields.append(total_field)
    labels[total_field] = total_label
    
    for race_field, race_row in race_classes.iteritems():
        fields.append(race_field)
        labels[race_field] = race_row['label']
    
    categories[category]['Census'] = {'fields': fields, 'labels': labels}
    
    print "\nCalculating PID by Race"
   
    # make the party identification data and census data
    district_data = make_pid_and_class_data(
            census_data_in_district=census_data, 
            pid_classes=race_pid_classes,
            census_classes=race_classes,
            pid_total_field=pid_total_field,
            district_data=district_data,
            district=district,
            leg_body=leg_body,
            year=year
            # TODO
            # add a list of singles (eg, total or median) to retrieve
        )
    
    # make the party identification data and data for the census classes
    # for the district
    district_data = make_pid_and_class_data( 
            census_data_in_district=census_data, 
            pid_classes=race_pid_classes,
            census_classes=race_classes,
            pid_total_field=pid_total_field,
            district_data=district_data,
            district=district,
            leg_body=leg_body,
            year=year,
            geo_key=district_key
        )

    # get the total population from the race table
    geo_key=blockgroup_key
    for geoid, census_data_row in census_data[year][geo_key].iteritems():
        district_data[year][geo_key][geoid][total_field] = census_data_row[race_total_field]

    if leg_body == 'US-REP': 
        geo_key=district_key
        district_data[year][geo_key][total_field] = census_data[year][geo_key][race_total_field]

    return categories, district_data


def make_edu_data( api,  district_data = {}, categories = {'Education': { }}, 
        state=48, district=7, leg_body='US-REP', year='2015' ):
    """Make the education data for a district
    Args: 
        api: 
        state: 
        district: 
        year: 
    Returns: 
        categories:
        district_data:
    Raises:
        Nothing (yet)

    PID by Educational Attainment:
                                R       D       I       O       LR      LD      NL      UN*
                                %	%	%	%	%	%	%	
    Postgrad men	        28	31	38	3	45	49	6	668
    Postgrad women	        20	52	26	2	27	69	4	621
    College men	                31	25	40	3	50	43	7	1,474
    College women	        27	41	29	3	38	56	6	1,193
    Some college men	        33	22	40	5	53	37	10	1,153
    Some college women	        27	38	32	4	40	52	7	1,105
    HS or less men	        33	29	34	4	51	42	7	1,024
    HS or less women	        29	38	29	4	40	50	10	835
      * R = Rep
        D = Dem
        I = Ind
        O = Other
        LR = Lean Rep
        LD = Lean Dem
        NL = No leaning
        UN = Unweighted N
    
    See http://www.people-press.org/2016/09/13/2016-party-identification-detailed-tables/

    """
    category='Education'

    district_key='district'
    blockgroup_key='bg'
    precinct_key='precinct'
    tract_key='tract'

    edu_table = 'B15002'
    edu_total_field = 'B15002_001E'
    
    total_field = 'total_edu'
    total_label = 'Total Population over 25'
    
    pid_total_field = 'pid_total_edu'
    pid_total_label = 'PID by Educational Attainment'
    
    edu_pid_classes = get_edu_pid_classes()
    edu_classes = get_edu_classes()

    # Load the census data
    census_fields = []
    print "Getting Census Data for Education"
    edu_fields, census_labels = get_census_fields_by_table(table=edu_table, 
            year=year)
    census_fields.extend(edu_fields)
    
    census_data = get_census_data(api=api, category=category, fields=census_fields,
        state=state, district=district, leg_body=leg_body, year=year)

    # create fields and labels for Party Identification classes
    # used in web-based dashboard
    fields = []
    labels = {}
    
    fields.append(pid_total_field)
    labels[pid_total_field] = pid_total_label
    
    fields.append(total_field)
    labels[total_field] = total_label
    
    for field, row in edu_pid_classes.iteritems():
        fields.append(field)
        labels[field] = row['label']
    
    if category not in categories.keys():
        categories[category] = {}

    categories[category]['PID'] = {'fields': fields, 'labels': labels}
    
    # create fields and labels for census classes
    # used in web-based dashboard
    fields = []
    labels = {}
    
    fields.append(total_field)
    labels[total_field] = total_label
    
    for field, row in edu_classes.iteritems():
        fields.append(field)
        labels[field] = row['label']
    
    categories[category]['Census'] = {'fields': fields, 'labels': labels}
    
    print "\nCalculating PID by Educational Attainment"
   
    # make the party identification data and census data
    district_data = make_pid_and_class_data(
            census_data_in_district=census_data, 
            pid_classes=edu_pid_classes,
            census_classes=edu_classes,
            pid_total_field=pid_total_field,
            district_data=district_data,
            district=district,
            leg_body=leg_body,
            year=year
            # TODO
            # add a list of singles (eg, total or median) to retrieve
        )

    # make the party identification data and data for the census classes
    # for the district
    district_data = make_pid_and_class_data( 
            census_data_in_district=census_data, 
            pid_classes=edu_pid_classes,
            census_classes=edu_classes,
            pid_total_field=pid_total_field,
            district_data=district_data,
            district=district,
            leg_body=leg_body,
            year=year,
            geo_key=district_key
        )

    # get the total population from the edu table
    geo_key=blockgroup_key
    for geoid, census_data_row in census_data[year][geo_key].iteritems():
        # Total Population
        district_data[year][geo_key][geoid][total_field] = census_data_row[edu_total_field]
    
    if leg_body == 'US-REP': 
        geo_key=district_key
        district_data[year][geo_key][total_field] = census_data[year][geo_key][edu_total_field]

    return categories, district_data


def make_voting_precinct_data(categories, district_data = {}, state=48, district=7, leg_body='US-REP', year='2015',
        voting_precincts_file=None):
    """
    Args: 
        district_data:
        blockgroups:
        voting_precincts_file:
    Returns: 
        categories:
        district_data:
    Raises:
        Nothing (yet)
    """
    precinct_key = 'precinct'
    
    state = "{0:0>2}".format(state)
    district = "{0:0>2}".format(district)
    
    state_abbr = str(states.mapping('fips', 'abbr')[state])
    district_abbr = leg_body + '-' + state_abbr + district
    geojson_path = 'static/geojson/'
    
    if voting_precincts_file is None:
        find_voting_precincts_in_district(state=state, district=district, leg_body=leg_body)
        voting_precincts_file  = get_voting_precincts_geojson_filename(
                state=state, district=district, leg_body=leg_body)

    blockgroups_file = geojson_path + district_abbr + '-blockgroups.geojson' 

    print "Calculating statistics for voting precincts"
    blockgroups = gpd.read_file(blockgroups_file)
    voting_precincts = gpd.read_file(voting_precincts_file)
    
    if precinct_key not in district_data[year].keys():
        district_data[year][precinct_key] = {}
    for precIndex, precinct in voting_precincts.iterrows():
        geoid = precinct.PRECINCT
        if geoid not in district_data[year][precinct_key].keys():
            district_data[year][precinct_key][geoid] = {}
        for cat_index, category in categories.iteritems():
            for cat_type_index, cat_type in category.iteritems():
                for field in cat_type['fields']:
                    if field not in 'median_income':
                        district_data[year][precinct_key][geoid][field] = 0.0

        precincts_bool = blockgroups.geometry.intersects(precinct.geometry)
        bg_prec_intersects = blockgroups[precincts_bool]
        
        intersections = bg_prec_intersects.intersection(precinct.geometry)
        areas = intersections.area
        for bg_index, bg in bg_prec_intersects.iterrows():
            interArea = areas[bg_index]
            bgArea = GeoSeries(bg.geometry).area[0]

            share = (interArea/bgArea)
            for field, value in district_data[year]['bg'][bg.GEOID].iteritems():
                if 'median_income' not in field:
                    if value is None:
                        value = 0.0
                    total = district_data[year][precinct_key][geoid][field]
                    total = total + float(value) * share
                    district_data[year][precinct_key][geoid][field] = total
    
    # convert all the precinct values to int
    for geoid in district_data[year][precinct_key].keys():
        for field in district_data[year][precinct_key][geoid].keys():
            field_to_int = int(district_data[year][precinct_key][geoid][field])
            district_data[year][precinct_key][geoid][field] = field_to_int

    return district_data


def make_voting_results_data(categories, district_data = {}, state=48, district=7, leg_body='US-REP', year='2015',
        voting_precincts_file=None, voting_results_file=None):
    """
    Args: 
        district_data:
        blockgroups:
        voting_precincts_file:
    Returns: 
        categories:
        district_data:
    Raises:
        Nothing (yet)
    """
    precinct_key = 'precinct'
    category = 'Voting Results'
    fields = ['regisered_voters']
    labels = {'registered_voters' : 'Registered Voters'}
    
    state = "{0:0>2}".format(state)
    district = "{0:0>2}".format(district)
    
    state_abbr = str(states.mapping('fips', 'abbr')[state])
    district_abbr = leg_body + '-' + state_abbr + district
    geojson_path = 'static/geojson/'
    
    if voting_precincts_file is None:
        find_voting_precincts_in_district(state=state, district=district, leg_body=leg_body)
        voting_precincts_file  = get_voting_precincts_geojson_filename(
                state=state, district=district, leg_body=leg_body)
    
    if voting_results_file is None:
        # TODO download voting results from Open Elections, e.g., https://github.com/openelections/openelections-data-tx
        voting_results_file = 'static/data/harris-county-2018-primary-results.csv'

    if category not in categories.keys():
        categories[category] = {'fields': fields, 'labels': labels}
    
    voting_results_data = pd.read_csv(voting_results_file)

    voting_precincts = gpd.read_file(voting_precincts_file)

    if year not in district_data.keys():
        district_data[year] = { precinct_key: {} }
    if year in district_data.keys():
        if precinct_key not in district_data[year].keys():
            district_data[year][precinct_key] = {}
    
    for precIndex, precinct in voting_precincts.iterrows():
        geoid = precinct.PRECINCT
        if geoid not in district_data[year][precinct_key].keys():
            district_data[year][precinct_key][geoid] = {} 
        
        district_data[year][precinct_key][geoid] = {}
        field = 'registered_voters'

        district_data[year][precinct_key][geoid][field] = int(
                voting_results_data[ 
                    (voting_results_data['precinct'] == int(geoid)) & 
                    (voting_results_data['office'] == 'Registered Voters') 
                ].iloc[0]['votes']
            )
    
    # TODO add up district-wide data

    return categories, district_data


def make_district_data(api, state, district, leg_body, year):
    district_data=load_district_data()

    # Make the age categories and data for the district file
    categories, district_data = make_age_data(
            state=state,
            district=district,
            leg_body=leg_body,
            api=api, 
            district_data=district_data,
            year=year)
    
    # Add income categories and data to the district file
    categories, district_data = make_income_data(
            state=state,
            district=district,
            leg_body=leg_body,
            api=api,
            district_data=district_data,
            categories=categories,
            year=year
        )
    
    # Add race categories and data to the district file
    categories, district_data = make_race_data(
            state=state,
            district=district,
            leg_body=leg_body,
            api=api,
            district_data=district_data,
            categories=categories,
            year=year
        )
    # Add educational categories and data to the district file
    categories, district_data = make_edu_data(
            state=state,
            district=district,
            leg_body=leg_body,
            api=api,
            district_data=district_data,
            categories=categories,
            year=year
        )
    
    if leg_body == 'STATE-REP' or leg_body == 'STATE-SEN':
        district_data = make_district_data_for_state_leg(
            state=state,
            district=district,
            leg_body=leg_body,
            district_data=district_data,
            categories=categories,
            year=year
        )

    return categories, district_data


def main():
    """Builds stats for a legislative district, e.g., a US Congressional District
    """
    args = get_command_line_args()
    settings = read_settings(args)
    
    census_api_key = settings['census_api_key']
    state = settings['state']
    district = settings['district']
    leg_body = settings['leg_body']
    year = settings['year']
    voting_year = settings['voting_year']
    voting_precincts_file = settings['voting_precincts']
    voting_results_file = settings['voting_results']
    
    find_blockgroups_in_district(
            state=state,
            district=district,
            leg_body=leg_body,
            year=year
        )

    categories, district_data = make_district_data(
            api=census_api_key,
            state=state,
            district=district,
            leg_body=leg_body,
            year=year
        )

    # Estimate voting precinct data based on block group data
    district_data = make_voting_precinct_data(
            district_data=district_data, 
            categories=categories,
            state=state,
            district=district,
            leg_body=leg_body,
            year=year,
            voting_precincts_file=voting_precincts_file
        )


    categories, district_data = make_voting_results_data(
            categories=categories, 
            district_data = district_data, 
            state=state, 
            district=district, 
            leg_body=leg_body, 
            year=voting_year,
            voting_precincts_file=voting_precincts_file, 
            voting_results_file=voting_results_file
        )

    to_json(district_data, "static/data/district-data.json")
    to_json(categories, "static/data/categories.json")


if __name__ == "__main__":
    main()
