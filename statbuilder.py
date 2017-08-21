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
import urllib2
import gzip
import tarfile
import zipfile

import pandas as pd
import geopandas as gpd
from geopandas import GeoSeries, GeoDataFrame

from collections import OrderedDict
from census import Census
from us import states

# GLOBAL CONSTANTS

VERSION = '0.1.1'

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
    # provide state, district, and year as options
    _version=VERSION
    parser = argparse.ArgumentParser(description='Build stats for a particular Congressional District')
    parser.add_argument('-v','--version',action='version', version='%(prog)s %(version)s' % {"prog": parser.prog, "version": _version})
    parser.add_argument('-d','--debug',help='print debug messages',action="store_true")

    return parser.parse_args()

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
    url_object=urllib2.urlopen(url)
    dl_file_Ooject=open(dl_filename,'wb')
    meta = url_object.info()
    fileSize = int(meta.getheaders("Content-Length")[0])
    print "Downloading: %s Bytes: %s" % (dlFileName.split('/')[-1], fileSize)
    
    current_file_size = 0
    block_size = 8192
    while True:
        buffer = url_object.read(block_size)
        if not buffer:
            break

        current_file_size += len(buffer)
        dl_file_object.write(buffer)
        status = r"%10d  [%3.2f%%]" % (current_file_size, current_file_size * 100. / file_size)
        status = status + chr(8)*(len(status)+1)
        print status,
    dl_file_object.close()


def extractall(fn,dst="."):
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


# TODO
# def find_tracts_in_district(state='48', district='07'):


def find_blockgroups_in_district(state=48, district=7, year=2015):
    """Find the geographical units that intersect with a Congressional District.
    Args:
        state: The state where the Congressional district is in
        district: Congressional district
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
    bgs_outputGeoJSON = 'static/geojson/' + bgs_output + '.geojson'

    # TODO 
    # see if geojson files is available for district
    #   if not generate geojson file for district
    district_geojson = 'static/geojson/district.geojson'

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


def get_blockgroup_census_data(api, fields, state=48, district=7, year=2015):
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
    bgs_in_district = pd.read_csv('static/data/tx7-blockgroups.csv')
    
    # Setup Census query
    census_query = Census(api, year=year)
    census_fields = {}
    
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
        census_fields[ bg_row['GEOID'] ] = bg_stats
        i = i + 1

    return census_fields


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


def get_census_fields_by_table(table, year=2015):
    """Return the fields in a census table
    Args: 
        table: 
        year:  
    Returns: 
        TODO document structure of fields and labels
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


def get_under_18_classes():
    """
    Args: 
        Maybe year:  
    Returns:
        under_18_classes:
    Raises:
        Nothing (yet)
    """
    under_18_fields = [
                'B01001_003E', # Male:!!Under 5 years
                'B01001_004E', # Male:!!5 to 9 years
                'B01001_005E', # Male:!!10 to 14 years
                'B01001_006E', # Male:!!15 to 17 years
                'B01001_027E', # Female:!!Under 5 years
                'B01001_028E', # Female:!!5 to 9 years
                'B01001_029E', # Female:!!10 to 14 years
                'B01001_030E'  # Female:!!15 to 17 years
            ]
    
    under_18_classes = { 'label': 'Over 18', 'fields': under_18_fields }

    return under_18_classes


def get_age_pid_classes():
    """
    Args: 
    Returns: 
        age_pid_classes
    Raises:
        Nothing (yet)
    """
    pid_18_to_25_fields = [ 
                'B01001_007E', # Male:!!18 and 19 years
                'B01001_008E', # Male:!!20 years
                'B01001_009E', # Male:!!21 years
                'B01001_010E', # Male:!!22 to 24 years
                'B01001_031E', # Female:!!18 and 19 years
                'B01001_032E', # Female:!!20 years
                'B01001_033E', # Female:!!21 years
                'B01001_034E'  # Female:!!22 to 24 years
            ]
    pid_26_to_35_fields = [
                'B01001_011E', # Male:!!25 to 29 years
                'B01001_012E', # Male:!!30 to 34 years
                'B01001_035E', # Female:!!25 to 29 years
                'B01001_036E'  # Female:!!30 to 34 years
            ]
    pid_36_to_43_fields = [
                'B01001_013E', # Male:!!35 to 39 years
                'B01001_014E', # Male:!!40 to 44 years
                'B01001_037E', # Female:!!35 to 39 years
                'B01001_038E'  # Female:!!40 to 44 years
            ]
    pid_44_to_51_fields = [
                'B01001_015E', # Male:!!45 to 49 years
                'B01001_039E'  # Female:!!45 to 49 years
            ]
    pid_52_to_60_fields = [
                'B01001_016E', # Male:!!50 to 54 years
                'B01001_017E', # Male:!!55 to 59 years
                'B01001_040E', # Female:!!50 to 54 years
                'B01001_041E', # Female:!!55 to 59 years
            ]
    pid_61_to_70_fields = [
                'B01001_018E', # Male:!!60 and 61 years
                'B01001_019E', # Male:!!62 to 64 years
                'B01001_020E', # Male:!!65 and 66 years
                'B01001_021E', # Male:!!67 to 69 years
                'B01001_042E', # Female:!!60 and 61 years
                'B01001_043E', # Female:!!62 to 64 years
                'B01001_044E', # Female:!!65 and 66 years
                'B01001_045E', # Female:!!67 to 69 years
            ]
    pid_71_to_80_fields = [
                'B01001_022E', # Male:!!70 to 74 years
                'B01001_023E', # Male:!!75 to 79 years
                'B01001_046E', # Female:!!70 to 74 years
                'B01001_047E', # Female:!!75 to 79 years
            ]
    pid_81_plus_fields = [
                'B01001_024E', # Male:!!80 to 84 years
                'B01001_025E', # Male:!!85 years and over
                'B01001_048E', # Female:!!80 to 84 years
                'B01001_049E', # Female:!!85 years and over
            ]
    
    age_pid_classes = OrderedDict()
    age_pid_classes[ 'pid_18_to_25' ] = { 'label': 'PID Age 18-25', 'fields': pid_18_to_25_fields, 'pid': 0.58}
    age_pid_classes[ 'pid_26_to_35' ] = { 'label': 'PID Age 26-35', 'fields': pid_26_to_35_fields, 'pid': 0.56} 
    age_pid_classes[ 'pid_36_to_43' ] = { 'label': 'PID Age 36-43', 'fields': pid_36_to_43_fields, 'pid': 0.51} 
    age_pid_classes[ 'pid_44_to_51' ] = { 'label': 'PID Age 44-51', 'fields': pid_44_to_51_fields, 'pid': 0.46}
    age_pid_classes[ 'pid_52_to_60' ] = { 'label': 'PID Age 52-60', 'fields': pid_52_to_60_fields, 'pid': 0.46}
    age_pid_classes[ 'pid_61_to_70' ] = { 'label': 'PID Age 61-70', 'fields': pid_61_to_70_fields, 'pid': 0.44}
    age_pid_classes[ 'pid_71_to_80' ] = { 'label': 'PID Age 71-80', 'fields': pid_71_to_80_fields, 'pid': 0.41}
    age_pid_classes[ 'pid_81_plus' ] =  { 'label': 'PID Age 81+', 'fields': pid_81_plus_fields, 'pid': 0.39}

    return age_pid_classes


def get_age_classes():
    """
    Args: 
    Returns: 
        age_pid_classes
    Raises:
        Nothing (yet)
    """
    under_18_classes = get_under_18_classes

    age_18_to_29_fields = [ 
                'B01001_007E', # Male:!!18 and 19 years
                'B01001_008E', # Male:!!20 years
                'B01001_009E', # Male:!!21 years
                'B01001_010E', # Male:!!22 to 24 years
                'B01001_011E', # Male:!!25 to 29 years
                'B01001_031E', # Female:!!18 and 19 years
                'B01001_032E', # Female:!!20 years
                'B01001_033E', # Female:!!21 years
                'B01001_034E', # Female:!!22 to 24 years
                'B01001_035E', # Female:!!25 to 29 years
            ]
    age_30_to_39_fields = [
                'B01001_012E', # Male:!!30 to 34 years
                'B01001_013E', # Male:!!35 to 39 years
                'B01001_036E', # Female:!!30 to 34 years
                'B01001_037E', # Female:!!35 to 39 years
            ]
    age_40_to_49_fields = [
                'B01001_014E', # Male:!!40 to 44 years
                'B01001_038E', # Female:!!40 to 44 years
                'B01001_015E', # Male:!!45 to 49 years
                'B01001_039E', # Female:!!45 to 49 years

            ]
    age_50_to_59_fields = [
                'B01001_016E', # Male:!!50 to 54 years
                'B01001_017E', # Male:!!55 to 59 years
                'B01001_040E', # Female:!!50 to 54 years
                'B01001_041E', # Female:!!55 to 59 years

            ]
    age_60_to_69_fields = [
                'B01001_018E', # Male:!!60 and 61 years
                'B01001_019E', # Male:!!62 to 64 years
                'B01001_020E', # Male:!!65 and 66 years
                'B01001_021E', # Male:!!67 to 69 years
                'B01001_042E', # Female:!!60 and 61 years
                'B01001_043E', # Female:!!62 to 64 years
                'B01001_044E', # Female:!!65 and 66 years
                'B01001_045E', # Female:!!67 to 69 years
            ]
    age_70_to_79_fields = [
                'B01001_022E', # Male:!!70 to 74 years
                'B01001_023E', # Male:!!75 to 79 years
                'B01001_046E', # Female:!!70 to 74 years
                'B01001_047E', # Female:!!75 to 79 years
            ]
    age_81_plus_fields = [
                'B01001_024E', # Male:!!80 to 84 years
                'B01001_025E', # Male:!!85 years and over
                'B01001_048E', # Female:!!80 to 84 years
                'B01001_049E', # Female:!!85 years and over
            ]
    
    age_classes = OrderedDict()
    age_classes[ 'age_18_to_29' ] = { 'label': '18-29', 'fields': age_18_to_29_fields }
    age_classes[ 'age_30_to_39' ] = { 'label': '30s', 'fields': age_30_to_39_fields }
    age_classes[ 'age_40_to_49' ] = { 'label': '40s', 'fields': age_40_to_49_fields }
    age_classes[ 'age_50_to_59' ] = { 'label': '50s', 'fields': age_50_to_59_fields }
    age_classes[ 'age_60_to_69' ] = { 'label': '60s', 'fields': age_60_to_69_fields } 
    age_classes[ 'age_70_to_79' ] = { 'label': '70s', 'fields': age_70_to_79_fields }
    age_classes[ 'age_81_plus' ]  = { 'label': '81+', 'fields': age_81_plus_fields }

    return age_classes


def make_age_data(api, state=48, district=7, year=2015, make_blockgroup=True, 
        make_tract=False, make_voting_precinct=False):
    """
    Args: 
        api: 
        state: 
        district: 
        year: 
        data_file:
        make_blockgroup: dtype(bool)
        make_tract: dtype(bool)
        make_voting_precinct: dtype(bool)
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
    
    total_census_field = 'B01001_001E'
    
    total_field = 'total'
    total_label = 'Total'
    
    over_18_field = 'over_18'
    over_18_label = '18 and over'
    
    pid_total_field = 'pid_age_total'
    pid_total_label = 'PID Age Total'
    
    data_path = 'static/data/'

    census_data_file = data_path + 'bg-age-data.json'

    age_pid_classes = get_age_pid_classes()
    age_classes = get_age_classes()
    
    under_18_classes = get_under_18_classes()
    
    if os.path.isfile(census_data_file):
        with open(census_data_file) as census_json:
            census_data_in_bgs = json.load(census_json)
    else:
        print "Getting Census Data for Sex by Age"
        census_fields, census_labels = get_census_fields_by_table("B01001")
        census_data_in_bgs = get_blockgroup_census_data(api=api, fields=census_fields, year=year)
        to_json(census_data_in_bgs, census_data_file)
    
    categories = {'Age': {} }
    fields = []
    labels = {}

    fields.append(total_field)
    labels[total_field] = total_label

    fields.append(pid_total_field)
    labels[pid_total_field] = pid_total_label
    
    fields.append(over_18_field)
    labels[over_18_field] = over_18_label

    for age_field, age_row in age_pid_classes.iteritems():
        fields.append(age_field)
        labels[age_field] = age_row['label']
    
    categories['Age']['PID'] = {'fields': fields, 'labels': labels}
    
    fields = []
    labels = {}
    
    fields.append(total_field)
    labels[total_field] = total_label

    fields.append(over_18_field)
    labels[over_18_field] = over_18_label
    
    for age_field, age_row in age_classes.iteritems():
        fields.append(age_field)
        labels[age_field] = age_row['label']
    
    categories['Age']['Census'] = {'fields': fields, 'labels': labels}

    print "\nCalculating PID by Age"
    
    # TODO convert this to a function
    # data_in_bgs = get_pid_class_data(census_data_in_bgs, age_pid_classes, age_classes)
    # data_in_bgs = get_over_18_data(census_data_in_bgs, data_in_bgs, under_18_classes)
    data_in_bgs = {}
    for geoid, census_data in census_data_in_bgs.iteritems():
        pid_total = 0.0
        data_in_bgs[geoid] = {}

        # PID Total and classes
        for pid_class, census_classes in age_pid_classes.iteritems():
            pid_class_total = 0.0
            for census_field in census_classes['fields']:
                # Add up the total PID for this class, e.g., Younger Millennial (18-25) 
                pid_class_value = float(census_data[census_field]) * float(census_classes['pid'])
                pid_class_total =  pid_class_total + pid_class_value

                # Add up the total PID by age
                pid_total = pid_total + pid_class_value
            # PID Class
            data_in_bgs[geoid][pid_class] = int(pid_class_total)
        # PID Total
        data_in_bgs[geoid][pid_total_field] = int(pid_total)
        
        # Census classes
        for census_class, census_classes in age_classes.iteritems():
            # Add up the total of this census_class, e.g., (18-29) or 30s
            census_class_total = 0
            for census_subclass in census_classes['fields']:
                census_subclass_value = int(census_data[census_subclass])
                census_class_total =  census_class_total + census_subclass_value

            # Census Class
            data_in_bgs[geoid][census_class] = census_class_total

        # Persons 18 and over
        under_18 = 0
        for census_field in under_18_classes['fields']:
            under_18 = under_18 + int(census_data[census_field])
        # (over 18) = total - (under 18)
        data_in_bgs[geoid][over_18_field] = int(census_data[total_census_field]) - under_18
            
        # Total Population
        data_in_bgs[geoid][total_field] = census_data[total_census_field]
    
    return categories, data_in_bgs


def main():
    """Builds stats and progressive scores for a Congressional District.
    """
    args = get_command_line_args()
    settings_dict = read_settings(args)
    census_api_key = settings_dict['census_api_key']
    # TODO
    # make it modular to state, district, and year
    state = 48
    district = 7
    year = 2015
    
    categories, data_in_bgs = make_age_data(census_api_key)
    
    to_json(data_in_bgs, "static/data/district-age.json")
    to_json(categories, "static/data/categories.json")


if __name__ == "__main__":
    main()
