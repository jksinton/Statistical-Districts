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
import statlib

import pandas as pd
import geopandas as gpd
from geopandas import GeoSeries, GeoDataFrame

from collections import OrderedDict
from census import Census
from us import states

from statlib import *

# GLOBAL CONSTANTS

VERSION = '0.2.0'

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
    year = '2015'
    
    # Set values in settings.ini
    settings = ConfigParser.ConfigParser()
    settings.read('settings.ini') # change example.settings.ini to settings.ini

    # Census API Key
    census_api_key = settings.get( 'census', 'CENSUS_API_KEY' )

    if args.year:
        year=args.year

    settings_dict = { 
                "census_api_key": census_api_key,
                "state": state,
                "district": district,
                "year": year
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
    # TODO
    # provide state, district, and year as options
    _version=VERSION
    parser = argparse.ArgumentParser(description='Build stats for a particular Congressional District')
    parser.add_argument('-y','--year',help='Year of Census data to build')
    parser.add_argument('-v','--version',action='version', 
            version='%(prog)s %(version)s' % {"prog": parser.prog, "version": _version})
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
    print url
    url_object=urllib2.urlopen(url)
    dl_file_object=open(dl_filename,'wb')
    meta = url_object.info()
    file_size = int(meta.getheaders("Content-Length")[0])
    print "Downloading: %s Bytes: %s" % (dl_filename.split('/')[-1], file_size)
    
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


# TODO
# def find_tracts_in_district(state='48', district='07'):


def find_blockgroups_in_district(state=48, district=7, year='2015'):
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

    bgs_touching_district_bool = block_groups.touches(district.geometry[0])
    
    bgs_intersecting_district_bool = block_groups.intersects(district.geometry[0])

    for index in bgs_touching_district_bool[bgs_touching_district_bool==True].index:
        bgs_intersecting_district_bool.loc[index] = False

    bgs_in_district = block_groups[bgs_intersecting_district_bool]
    
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


def get_blockgroup_census_data(api, fields, census_data = {}, state=48, district=7, year='2015'):
    """Retrieve the census data for the block groups in a Congressional District
    Args:
        api: Census api key
        fields: the fields to query from api.census.gov; 
            See e.g., https://api.census.gov/data/2015/acs5/variables.html
        year: The year the census data was collected
        state: The state where the Congressional district is in
        district: The Congressional district
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
    # also read a json file
    bgs_in_district = pd.read_csv('static/data/tx7-blockgroups.csv')
    
    # Setup Census query
    census_query = Census(api, year=year)
    num_of_bgs = len(bgs_in_district)
    i = 0.0
    for bg_index, bg_row in bgs_in_district.iterrows():
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
        geoid = str(bg_row['GEOID'])
        if geoid in census_data[year][blockgroup_key].keys():
            census_data[year][blockgroup_key][geoid].update(bg_stats)
        else:
            census_data[year][blockgroup_key][geoid] = bg_stats
        i = i + 1

    return census_data

def get_district_census_data(api, fields, census_data = {}, state=48, district=7, year='2015'):
    """Retrieve the census data for the block groups in a Congressional District
    Args:
        api: Census api key
        fields: the fields to query from api.census.gov; 
            See e.g., https://api.census.gov/data/2015/acs5/variables.html
        year: The year the census data was collected
        state: The state where the Congressional district is in
        district: The Congressional district
    Returns:
        census_data: a list of dictionaries storing the blockgroup results
    Raises
        Nothing
    """
    district_key = 'district'
    if year not in census_data.keys():
        census_data[year] = { district_key: {} }
    else:
        if district_key not in census_data[year].keys():
            census_data[year][district_key] = { }
    
    # Setup Census query
    census_query = Census(api, year=year)
    district_stats = census_query.acs5.get(
                    fields,
                    {   'for': 'congressional district:' + str(district),
                        'in': 'state:' + str(state)
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
        table: 
        year:  
    Returns: 
        TODO document structure of fields and labels
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
        census_classes, pid_total_field, district_data={}, year='2015', geo_key='bg' ):
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
    else:
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


def get_census_data(api, category, fields,
        district_config_file = 'static/data/district.json',
        census_data_file='static/data/district-census-data.json', 
        state=48, district=7, year='2015'):
    """Store the raw census data in a json file and return the census data
    Args:
        
    Returns: 
        census_data: 
    Raises:
        Nothing (yet)
    """
    # TODO document
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
                    year=year
                )
            # get the data for the entire district
            census_data = get_district_census_data(
                    api=api, 
                    census_data=census_data,
                    fields=fields, 
                    state=state, 
                    district=district, 
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
            year=year)
    
    census_data = get_district_census_data(
            api=api, 
            census_data=census_data,
            fields=fields, 
            state=state, 
            district=district, 
            year=year
        )

    # TODO add get_tract_census_data()
    district_config = {}
    district_config['state'] = state
    district_config['district'] = district
    district_config[year] = [category]
    district_config['years'] = [year]
    
    # save census data to file
    to_json(census_data, census_data_file)
    to_json(district_config, district_config_file)
    
    return census_data


def make_age_data(api, district_data = {}, categories = {'Age': {} },
        state=48, district=7, year='2015', make_voting_precinct=False):
    """Make the age Party Identification (PID) data and census data for a district
    Args: 
        api: 
        state: 
        district: 
        year: 
        data_file:
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
    category='Age'
    district_key='district'
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
        state=state, district=district, year=year)
    
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
            year=year,
            geo_key=district_key
        )

    # Calculate persons 18 and over in each block group and 
    # get the total population in each block group
    geo_key = 'bg'
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
        state=48, district=7, year='2015', 
        make_voting_precinct=False):
    """Make the income data for a district
    Args: 
        api: 
        state: 
        district: 
        year: 
        make_voting_precinct: dtype(bool)
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
        state=state, district=district, year=year)

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
            year=year,
            geo_key=district_key
        )

    # get the total households and the median household income
    geo_key = 'bg'
    for geoid, census_data_row in census_data[year][geo_key].iteritems():
        # Median Household Income
        district_data[year][geo_key][geoid][median_field] = census_data_row[median_household_inc_field]
            
        # Total Households
        district_data[year][geo_key][geoid][total_field] = census_data_row[total_household_inc_field]
    
    # calculate the district stats
    geo_key = district_key
    # Median Household Income
    district_data[year][geo_key][median_field] = census_data[year][geo_key][median_household_inc_field]
        
    # Total Households
    district_data[year][geo_key][total_field] = census_data[year][geo_key][total_household_inc_field]

    return categories, district_data
    

def make_race_data( api,  district_data = {}, categories = {'Race': { }}, 
        state=48, district=7, year='2015', make_voting_precinct=False):
    """Make the race data for a district
    Args: 
        api: 
        state: 
        district: 
        year: 
        make_voting_precinct: dtype(bool)
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
        state=state, district=district, year=year)

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
            year=year,
            geo_key=district_key
        )

    # get the total population from the race table
    geo_key='bg'
    for geoid, census_data_row in census_data[year][geo_key].iteritems():
        # 
        district_data[year][geo_key][geoid][total_field] = census_data_row[race_total_field]
    
    geo_key=district_key
    district_data[year][geo_key][total_field] = census_data[year][geo_key][race_total_field]

    return categories, district_data


def make_edu_data( api,  district_data = {}, categories = {'Education': { }}, 
        state=48, district=7, year='2015', make_voting_precinct=False):
    """Make the education data for a district
    Args: 
        api: 
        state: 
        district: 
        year: 
        make_voting_precinct: dtype(bool)
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
        state=state, district=district, year=year)

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
            year=year,
            geo_key=district_key
        )

    # get the total population from the edu table
    geo_key='bg'
    for geoid, census_data_row in census_data[year][geo_key].iteritems():
        # Total Population
        district_data[year][geo_key][geoid][total_field] = census_data_row[edu_total_field]
    
    geo_key=district_key
    district_data[year][geo_key][total_field] = census_data[year][geo_key][edu_total_field]

    return categories, district_data


def main():
    """Builds stats and progressive scores for a Congressional District.
    """
    args = get_command_line_args()
    settings_dict = read_settings(args)
    census_api_key = settings_dict['census_api_key']
    # TODO
    # make it modular to state, district, and year
    state = settings_dict['state']
    district = settings_dict['district']
    year = settings_dict['year']
    
    district_data=load_district_data()

    # Make the age categories and data for the district file
    categories, district_data = make_age_data(
            api=census_api_key, 
            district_data=district_data,
            year=year)
    
    # Add income categories and data to the district file
    categories, district_data = make_income_data(
            api=census_api_key,
            district_data=district_data,
            categories=categories,
            year=year
        )
    
    # Add race categories and data to the district file
    categories, district_data = make_race_data(
            api=census_api_key,
            district_data=district_data,
            categories=categories,
            year=year
        )
    # Add educational categories and data to the district file
    categories, district_data = make_edu_data(
            api=census_api_key,
            district_data=district_data,
            categories=categories,
            year=year
        )

    to_json(district_data, "static/data/district-data.json")
    to_json(categories, "static/data/categories.json")


if __name__ == "__main__":
    main()
