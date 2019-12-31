#!/usr/bin/env python

# This file is part of Statistical Districts.
# 
# Copyright (c) 2019, James Sinton
# All rights reserved.
# 
# Released under the BSD 3-Clause License
# See https://github.com/jksinton/Statistical-Districts/blob/master/LICENSE

# standard libraries
import argparse
import os
from collections import OrderedDict
import configparser
import errno
from glob import glob
import gzip
import json
from urllib.request import urlopen
import re
import shutil
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
import numpy as np
import pandas as pd
from tqdm import tqdm
from us import states

class District(object):
    """
    """
    # Class constants
    US_REP = 'U.S. House'
    US_SEN = 'U.S. Senator'
    STATE_REP = 'State Representative'
    STATE_SEN = 'State Senator'

    OFFICES = {
                'US-REP' : US_REP,
                'US-SEN' : US_SEN,
                'STATE-REP' : STATE_REP,
                'STATE-SEN' : STATE_SEN

            }
    
    OFFICES_ABBR = {
                US_REP : 'US-REP',
                US_SEN : 'US-SEN',
                STATE_REP : 'STATE-REP',
                STATE_SEN : 'STATE-SEN'
            }

    # TODO program using pandas holidays,
    # see https://stackoverflow.com/questions/34708626/pandas-holiday-calendar-rule-for-us-election-day
    EDAYS = {
            2016 : '1108',
            2018 : '1106',
            2020 : '1103',
            2022 : '1108',
            2024 : '1105',
            2026 : '1103'
        }

    CRS = 4326

    def __init__(self, district, office, census_year="2018", election_year="2018", state=48, debug_is_on=False):
        self.state = int(state)
        self.district = int(district)
        self.office = self.OFFICES[office]
        self.census_year = str(census_year)
        self.election_year = str(election_year)
        self.election_day = self.EDAYS[int(election_year)]
        self.debug_is_on = debug_is_on
        
        district_name = "{0:0>2}".format(district)
        state_fips = "{0:0>2}".format(state) 
        state_name = states.mapping('abbr', 'name')[states.mapping('fips', 'abbr')[state_fips]]
        
        self.title = state_name + " " + self.office + " District "  + district_name
        
        # default path structure
        self.data_path = 'static/data/'
        self.geojson_path = 'static/geojson/'
        data_path = self.data_path
        geojson_path = self.geojson_path
        
        # make path structure
        paths = [self.geojson_path, self.data_path]
        for path in paths:
            if os.path.isdir(path) == False:
                print( "Making path {path}".format(path=path) )
                Utilities.mkdir_p(path)

        # geojson files
        self.district_geojson_fn = self.get_filename(path=geojson_path, ext='.geojson')
        self.district_vps_geojson_fn = self.get_filename(path=geojson_path, ext='-voting-precincts.geojson')
        self.district_bgs_geojson_fn = self.get_filename(path=geojson_path, ext='-blockgroups.geojson')
        self.district_counties_geojson_fn = self.get_filename(path=geojson_path, ext='-counties.geojson')
        self.state_vps_geojson_fn = self.get_filename(path=geojson_path, ext='-voting-precincts.geojson', isState=True)
        self.state_bgs_geojson_fn = self.get_filename(path=geojson_path, ext='-blockgroups.geojson', isState=True)
        self.state_counties_geojson_fn = self.get_filename(path=geojson_path, ext='-counties.geojson', isState=True)
        
        # district data files
        self.district_config_fn = self.get_filename(path=data_path, ext='-config.json')
        self.district_bgs_fn = self.get_filename(path=data_path, ext='-blockgroups.json')
        self.district_data_fn = self.get_filename(path=data_path, ext='-data.json')
        self.district_categories_fn = self.get_filename(path=data_path, ext='-categories.json')
        self.district_census_data_fn = self.get_filename(path=data_path, ext='-census-data.json')
        self.district_counties_fn = self.get_filename(path=data_path, ext='-counties.json')
        self.state_counties_fn = self.get_filename(path=data_path, ext='-counties.json', isState=True)
        
        # web-based files
        self.web_district_config_fn = data_path + 'district.json'
        self.web_district_categories_fn = data_path + 'categories.json'
        self.web_district_data_fn = data_path + 'district-data.json'
        
        # excel file
        self.district_excel_fn = self.get_filename(path=data_path, ext='-{}-census-data.xlsx'.format(census_year))
       
        # election results file
        state_abbr = states.mapping('fips', 'abbr')[state_fips]
        self.state_election_results = data_path + '{year}{eday}__{state}__general__precinct.csv'.format(
                    year=self.election_year,
                    eday=self.election_day,
                    state=state_abbr.lower()
                )
        
        self.district_election_results = data_path + '{year}{eday}__{state}-{office}-{district}__general__precinct.csv'.format(
                    year=self.election_year,
                    eday=self.election_day,
                    state=state_abbr.lower(),
                    office=self.OFFICES_ABBR[self.office].lower(),
                    district=district
                )
        
        # tx district boundary files
        tx_hou_url = 'ftp://ftpgis1.tlc.state.tx.us/DistrictViewer/House/PlanH358.zip'
        tx_sen_url = 'ftp://ftpgis1.tlc.state.tx.us/DistrictViewer/Senate/PlanS172.zip'


    def get_filename(self, path, ext, isState=False):
        """Return the path and file name for a file
        Args:
            path
            ext
            isState
        Returns:
            filename
        """
        state = "{0:0>2}".format(self.state)
        district = "{0:0>2}".format(self.district)
        office = self.OFFICES_ABBR[self.office]
        
        state_abbr = str(states.mapping('fips', 'abbr')[state])

        if isState:
            abbr = state_abbr
        else:
            abbr = office + '-' + state_abbr + district
        
        filename = path +  abbr + ext
        
        return filename


    def fetch_cb_boundary_files(self):
        """
        """
        # fetch district file
        self.get_district_file()

        # fetch county files
        self.get_county_file()

        # fetch voting precincts file
        self.get_state_voting_precincts()

        # fetch state blockgroups
        self.get_state_blockgroups_file()


    def get_district_file(self):
        """Download the shape file for the district
        Args:
            class attributes
        """
        district_file = self.district_geojson_fn
        geojson_path = self.geojson_path
        state = "{0:0>2}".format(self.state)
        district = "{0:0>2}".format(self.district)
        office = self.office
        census_year = self.census_year

        if not os.path.isfile(district_file):
            print( "Downloading district file" )
            if office == self.US_REP:
                congress = int(115 + ((census_year - 2016)  - (census_year - 2016)%2)/2)
                district_url = 'ftp://ftp2.census.gov/geo/tiger/GENZ{y}/shp/cb_{y}_us_cd{c}_500k.zip'.format(y=census_year, c=congress)
            if office == self.STATE_REP:
                district_url = self.tx_hou_url
            if office == self.STATE_SEN:
                district_url = self.tx_sen_url
            
            district_dl_file = geojson_path + 'district.zip'
            Utilities.download_file(district_url, district_dl_file)
            Utilities.extract_all(district_dl_file, geojson_path)
            
            districts_shapefile = self._get_shapefile(path=geojson_path)
            
            print( "Converting district file to GEOJSON" )
            districts = gpd.read_file(districts_shapefile)
            
            if office == self.US_REP:
                d_index = districts[districts.GEOID == (state + district) ].index
            if office == self.STATE_REP or office == self.STATE_SEN:
                d_index = districts[districts.District == int(district) ].index

            district_shape = districts.loc[d_index]
            # TODO resolve the init warning
            #district_shape = district_shape.to_crs(epsg=4326)
            district_shape = district_shape.to_crs(epsg=self.CRS)
            district_shape.to_file(district_file, driver='GeoJSON')

            # cleanup geojson dir
            self._cleanup_geojson_dir(download_file=district_dl_file, path=geojson_path)


    def get_state_voting_precincts(self):
        """Download the shape file with the statewide voting precincts
        """
        vps_file = self.state_vps_geojson_fn
        geojson_path = self.geojson_path
        state = "{0:0>2}".format(self.state)
        state_fips = self.state
        
        if not os.path.isfile(vps_file):
            print( "Downloading statewide voting precincts file")
            # TODO download the most recent precincts file
            # currently it downloads the 2016 TX precincts
            # 'https://github.com/nvkelso/election-geodata/raw/master/data/48-texas/statewide/2016/Precincts.zip'
            # TODO add support for other states
            if state_fips == 48:
                vps_url = 'https://github.com/nvkelso/election-geodata/raw/master/data/48-texas/statewide/2016/Precincts.zip'
            else:
                pass
            
            vps_dl_file = geojson_path + 'vps.zip'
            Utilities.download_file(vps_url, vps_dl_file)
            Utilities.extract_all(vps_dl_file, geojson_path)
            
            vps_shapefile = self._get_shapefile(path=geojson_path)
            
            print( "Converting statewide voting precincts file to GEOJSON")
            vps = gpd.read_file(vps_shapefile)
            
            vps = vps.to_crs(epsg=self.CRS)
            vps.to_file(vps_file, driver='GeoJSON')

            # cleanup geojson dir
            self._cleanup_geojson_dir(download_file=vps_dl_file, path=geojson_path)


    def get_county_file(self):
        """Download the shape file for the counties
        Args:
            class attributes
        """
        counties_file = self.state_counties_geojson_fn
        geojson_path = self.geojson_path
        state = "{0:0>2}".format(self.state)
        district = "{0:0>2}".format(self.district)
        office = self.office
        census_year = self.census_year

        if not os.path.isfile(counties_file):
            print( "Downloading counties file" )
            url = 'ftp://ftp2.census.gov/geo/tiger/GENZ{y}/shp/cb_{y}_us_county_20m.zip'.format(y=census_year)
            counties_dl_file = geojson_path + 'counties.zip'
            Utilities.download_file(url, counties_dl_file)
            Utilities.extract_all(counties_dl_file, geojson_path)
            counties_shapefile = self._get_shapefile(path=geojson_path)
            
            print( "Converting counties file to GEOJSON" )
            counties = gpd.read_file(counties_shapefile)
            
            c_index = counties[counties.STATEFP == state ].index
            
            state_counties = counties.loc[c_index]
            state_counties = state_counties.to_crs(epsg=self.CRS)
            state_counties.to_file(counties_file, driver='GeoJSON')
            state_counties[['STATEFP', 'COUNTYFP', 'NAME']].to_json(self.state_counties_fn)

            # cleanup geojson dir
            self._cleanup_geojson_dir(download_file=counties_dl_file, path=geojson_path)


    def get_state_blockgroups_file(self):
        """Download the file, from the Census Bureau, containing the blockgroups for an entire state
        Args:
            class attributes
        """
        blockgroups_file = self.state_bgs_geojson_fn
                
        state = "{0:0>2}".format(self.state)
        district = "{0:0>2}".format(self.district)
        year = self.census_year
        geojson_path = self.geojson_path
        
        if not os.path.isfile(blockgroups_file):
            print( "Downloading blockgroups" )
            bgs_url = 'ftp://ftp2.census.gov/geo/tiger/TIGER{year}/BG/tl_{year}_{state}_bg.zip'.format(year=year, state=state)
            bgs_dl_file = geojson_path + 'bgs.zip'
            Utilities.download_file(bgs_url, bgs_dl_file)
            Utilities.extract_all(bgs_dl_file, geojson_path)
            bgs_shapefile = self._get_shapefile(path=geojson_path)

            print( "Converting blockgroups file to GEOJSON")
            bgs = gpd.read_file(bgs_shapefile)
            bgs = bgs.to_crs(epsg=self.CRS)
            bgs.to_file(blockgroups_file, driver='GeoJSON')

            self._cleanup_geojson_dir(download_file=bgs_dl_file, path=geojson_path)


    def _get_shapefile(self, path):
        """
        Args:
            path
        Return:
            shapefile
        """
        if len(glob(path + '*shp')) > 0:
            shapefile = glob(path + '*shp')[0]
            return shapefile
        else:
            for p in glob(path + '*'):
                if os.path.isdir(p):
                    shapefile_path = p
                    shapefile = glob(p + '/*shp')[0]
                    return shapefile

    def _cleanup_geojson_dir(self, download_file, path):
        """
        Args:
            download_file
            path
        """
        # cleanup geojson dir
        if len(glob(path + '*shp')) > 0:
            shapefile_prefix = glob(path + '*shp')[0].split(path)[1].split('.')[0]
            shapefiles = glob(path + shapefile_prefix + '*')
            for f in shapefiles:
                os.remove(f)
        # shapefiles are nested in a directory
        else:
            for p in glob(path + '*'):
                if os.path.isdir(p):
                    shapefile_path = p
            shapefile_prefix = glob(shapefile_path + '/*shp')[0].split(shapefile_path)[1].split('.')[0]
            shapefiles = glob(shapefile_path + shapefile_prefix + '*')
            for f in shapefiles:
                os.remove(f)
            os.rmdir(shapefile_path)
        os.remove(download_file)

    # TODO
    # def find_tracts_in_district(state='48', district='07'):


    def find_blockgroups_in_district(self):
        """Find the blockgroups that intersect with a legislative district, e.g., US Congressional District.
        Args:
            class attributes
        """
        debug_is_on = self.debug_is_on
        bgs_in_district_GeoJSON = self.district_bgs_geojson_fn
        bgs_in_district_JSON = self.district_bgs_fn
        district_file = self.district_geojson_fn
        blockgroups_file = self.state_bgs_geojson_fn
        
        if (not os.path.isfile(bgs_in_district_JSON)) or (not os.path.isfile(bgs_in_district_GeoJSON) ):
            self.get_district_file()
            self.get_state_blockgroups_file()
            
            print( "\nFinding blockgroups in district" )
            district = gpd.read_file(district_file)
            block_groups = gpd.read_file(blockgroups_file)
            
            print( "Finding blockgroups that touch the district boundary" )
            bgs_touching_district_bool = block_groups.touches(district.geometry[0])
            
            print( "Finding blockgroups that intersect the district boundary")
            bgs_intersecting_district_bool = block_groups.intersects(district.geometry[0])
            
            print( "Filtering the blockgroups" )
            for index in bgs_touching_district_bool[bgs_touching_district_bool==True].index:
                bgs_intersecting_district_bool.loc[index] = False

            bgs_in_district = block_groups[bgs_intersecting_district_bool]
            print( "Finding blockgroups to filter based on threshold" )
            intersections = bgs_in_district.intersection(district.geometry[0])

            areas_of_intersections = intersections.area
            indx_out = []
            for bg_index, bg in bgs_in_district.iterrows():
                area_of_intersection = areas_of_intersections[bg_index]
                bg_area = GeoSeries(bg.geometry).area[0]

                share_of_intersection = area_of_intersection / bg_area
                
                if share_of_intersection < 0.10:
                    indx_out.append(bg_index)

                #print( "\nBlock Group: ", bg.GEOID )
                #print( "Area: ", str(bg_area) )
                #print( "Share of Intersection: ", str(share_of_intersection) )
            
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
   

    def find_counties_intersecting_district(self):
        """Find the counties that intersect a district
        """
        pass
        debug_is_on = self.debug_is_on
        state_counties_GEOJSON = self.state_counties_geojson_fn
        district_counties_GeoJSON = self.district_counties_geojson_fn
        district_file = self.district_geojson_fn
        district_counties_JSON = self.district_counties_fn
        
        if (not os.path.isfile(district_counties_JSON)) or (not os.path.isfile(district_counties_GeoJSON)):
            self.get_county_file()
            self.get_district_file()

            district = gpd.read_file(district_file)
            state_counties = gpd.read_file(state_counties_GEOJSON)
            
            print( "Finding counties that touch the district boundary" )
            cnts_touching_district_bool = state_counties.touches(district.geometry[0])
            
            print( "Finding counties that intersect the district boundary")
            cnts_intersecting_district_bool = state_counties.intersects(district.geometry[0])
            
            print( "Filtering the counties that touch the district" )
            for index in cnts_touching_district_bool[cnts_touching_district_bool==True].index:
                bgs_intersecting_district_bool.loc[index] = False

            district_counties = state_counties[cnts_intersecting_district_bool]
     
            print( "Finding counties to filter based on threshold" )
            intersections = district_counties.intersection(district.geometry[0])

            areas_of_intersections = intersections.area
            indx_out = []
            for cnt_index, cnt in district_counties.iterrows():
                area_of_intersection = areas_of_intersections[cnt_index]
                district_area = GeoSeries(district.geometry[0]).area[0]

                share_of_intersection = area_of_intersection / district_area
                
                if share_of_intersection < 0.01:
                    indx_out.append(cnt_index)

                #print( "\nCounty: ", cnt.GEOID )
                #print( "Area: ", str(district_area) )
                #print( "Share of Intersection: ", str(share_of_intersection) )
            
            cnts_to_remove_bool = pd.Series([False]*len(state_counties))

            for index in indx_out:
                cnts_to_remove_bool.loc[index] = True

            cnts_to_remove = state_counties[cnts_to_remove_bool]

            for index in cnts_to_remove_bool[cnts_to_remove_bool==True].index:
                cnts_intersecting_district_bool.loc[index] = False

            district_counties = state_counties[cnts_intersecting_district_bool]

            # See issue #367 https://github.com/geopandas/geopandas/issues/367
            try: 
                os.remove(district_counties_GeoJSON)
            except OSError:
                pass
            district_counties.to_file(district_counties_GeoJSON, driver='GeoJSON')
            
            # Create json file of geo units
            district_counties[['STATEFP', 'COUNTYFP','NAME']].to_json(district_counties_JSON)
            
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

    
    def fetch_election_results(self):
        """
        """
        state_fips = "{0:0>2}".format(self.state) 
        state_abbr = states.mapping('fips', 'abbr')[state_fips]
        state_abbr = state_abbr.lower()
        year = self.election_year
        eday = self.election_day
        state_election_results = self.state_election_results
        district_election_results = self.district_election_results
        state_counties_fn = self.state_counties_fn
        office = self.office
        district = self.district

        url = 'https://github.com/openelections/openelections-data-{state}/raw/master/{year}/{year}{eday}__{state}__general__precinct.csv'.format(
                state=state_abbr,
                year=year,
                eday=eday
            )

        if not os.path.isfile(state_election_results):
            Utilities.download_file(url, state_election_results)
        
        if not os.path.isfile(district_election_results):
            # filter the election results for only the rows associated with the district
            # TODO add support for offices without a district
            state_counties = pd.read_json(state_counties_fn)
            
            vr_state = pd.read_csv(state_election_results, index_col=False)
            vr = vr_state[ (vr_state['office'] == office) & (vr_state['district'] == str(district)) ]
            counties = list(set([ p['county'] for i, p in vr.iterrows() ]))
            vr = pd.DataFrame()
            for county in counties:
                vr = vr.append(vr_state[ vr_state['county'] == county])
            
            vr['district'] = pd.to_numeric(vr['district'])
            
            # standardize voting_results_data, e.g., 2016 format differs from 2018 format
            # convert party column to DEM or REP
            # TODO add for loop through dictionary
            if len(vr[ vr['party'] == 'Republican' ]) > 0:
                vr.loc[ vr[ vr['party'] == 'Republican' ].index, 'party' ] = 'REP'
            if len(vr[ vr['party'] == 'Democratic' ]) > 0:
                vr.loc[ vr[ vr['party'] == 'Democratic' ].index, 'party' ] = 'DEM'
                
            # convert precinct column to int
            vr.drop( vr[ vr['precinct'] == 'TOTAL' ].index, inplace=True)
            vr['precinct'] = pd.to_numeric(vr['precinct'])

            vr.to_csv(district_election_results, index=False)


    def find_voting_precincts_in_district(self):
        """Find the voting precincts that are in a district
        """
        vps_in_district_GeoJSON  = self.district_vps_geojson_fn
        district_counties_JSON = self.district_counties_fn
        state_counties_fn = self.state_counties_fn
        district_election_results = self.district_election_results
        office = self.office
        district = self.district

        if not os.path.isfile(vps_in_district_GeoJSON):
            voting_precincts_file = self.state_vps_geojson_fn
            self.fetch_election_results()
            
            self.get_state_voting_precincts()
            
            vr = pd.read_csv(district_election_results)
            state_counties = pd.read_json(state_counties_fn)
            
            # TODO support county specific VP files, as this source is out of date for most counties
            print( "\nLoading voting precincts" )
            vps = gpd.read_file(voting_precincts_file)
            
            # find the parties in the office
            vr_district = vr[ (vr['office'] == office) & (vr['district'] == district) ] 
            parties = list(set([ p['party'] for i, p in vr_district.iterrows() ]))
            # remove instances of nan
            parties = [p for p in parties if p == p]
            # find the voting precincts from the election results
            if len(parties) > 0:
                party = parties[0]
                vps_indexes = vr_district[ vr_district['party'] == party ]['precinct'].index
            
            counties = list(set([ p['county'] for i, p in vr_district.iterrows() ]))
            vps_in_district_bool = pd.Series([False]*len(vps))
            if len(counties) > 0:
                for county in counties:
                    county_fip = int( state_counties[state_counties['NAME'] == county]['COUNTYFP'] )
                    for precinct_index in vps_indexes:
                        precinct = "{0:0>4}".format(str(vr_district.loc[precinct_index]['precinct']))
                        state_index = vps[ (vps['CNTY'] == county_fip) & (vps['PREC'] == precinct) ].index
                        vps_in_district_bool.loc[ state_index ] = True
            
            vps_in_district = vps[vps_in_district_bool]
            if 'PREC' in list(vps_in_district.columns.values):
                vps_in_district = vps_in_district.rename(columns={'PREC':'PRECINCT'})

            # See issue #367 https://github.com/geopandas/geopandas/issues/367
            try: 
                os.remove(vps_in_district_GeoJSON)
            except OSError:
                pass
            vps_in_district.to_file(vps_in_district_GeoJSON, driver='GeoJSON')
            
            if self.debug_is_on:
                vps_in_district.sort_values(by=['PRECINCT'])[['PRECINCT', 'CNTY']].to_csv("vps.csv", index=False)


    def get_district_centroid(self):
        """Return the centroid of a district
        Returns:
            longitude: longitudinal coordinate of the centroid
            latitude: latitudinal coordinate of the centroid
        """
        self.get_district_file()
        district_filename = self.district_geojson_fn
        
        district = gpd.read_file(district_filename)

        longitude = district.geometry.centroid[0].x
        latitude = district.geometry.centroid[0].y

        return (longitude, latitude)


    def get_blockgroup_census_data(self, fields, census_data = {}):
        """Retrieve the census data for the block groups in a District
        Args:
            fields: the fields to query from api.census.gov; 
                See e.g., https://api.census.gov/data/2015/acs5/variables.html
            census_data
        Returns:
            census_data: a list of dictionaries storing the blockgroup results
        """
        state=self.state
        api = self.api
        year = self.census_year

        blockgroup_key = 'bg'
        
        if year not in census_data.keys():
            census_data[year] = { blockgroup_key: {} }
        else:
            if blockgroup_key not in census_data[year].keys():
                census_data[year][blockgroup_key] = { }

        bgs_in_district_JSON = self.district_bgs_fn
        bgs_in_district = pd.read_json(bgs_in_district_JSON)
        
        # Setup Census query
        census_query = Census(api, year=int(year))
        num_of_bgs = len(bgs_in_district)
        i = 0.0
        pbar = tqdm(
                total=num_of_bgs, initial=0, 
                unit_scale=True, desc='Processing Blockgroups'
            )
        # find the FIPS codes for the counties
        counties = list(set([ bg['COUNTYFP'] for i, bg in bgs_in_district.iterrows() ]))
        # for each county get the census data and search through the list of dictionaries
        for county in counties:
            county_stats = census_query.acs5.state_county_blockgroup(
                        fields=fields,
                        state_fips=state,
                        county_fips=county,
                        blockgroup=Census.ALL
                    )
            # only search for the bgs in the county
            bgs_in_county = [ bg for i, bg in bgs_in_district.iterrows() if bg['COUNTYFP'] == county ]
            
            for bg in bgs_in_county:
                bg_stats = [stats for stats in county_stats if ( (stats['tract'] == str(bg['TRACTCE'])) & (stats['block group'] == str(bg['BLKGRPCE'])))]
                bg_stats = bg_stats[0]
                geoid = str(bg['GEOID'])
                if geoid in census_data[year][blockgroup_key].keys():
                    census_data[year][blockgroup_key][geoid].update(bg_stats)
                else:
                    census_data[year][blockgroup_key][geoid] = bg_stats
                # print percent complete
                pbar.update(1)
        pbar.close()
        return census_data


    def get_district_census_data(self, fields, census_data = {}):
        """Retrieve the census data for the entire district
        Args:
            api: Census api key
            fields: the fields to query from api.census.gov; 
                See e.g., https://api.census.gov/data/2015/acs/acs5/variables.html
            state: the state of the district
            district: district number
            office: legislative body, e.g., State Representative, State Senate, 
                      or US Representative
            year: year associated with disctrict data
        Returns:
            census_data: a list of dictionaries storing the census data
        """
        api = self.api
        state = self.state
        district = self.district
        office = self.office
        year = self.census_year
        
        district_key = 'district'
        if year not in census_data.keys():
            census_data[year] = { district_key: {} }
        else:
            if district_key not in census_data[year].keys():
                census_data[year][district_key] = { }

        if office == self.US_REP:
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
        # TODO populate statewide census data 
        if office == self.US_SEN:
            pass
        
        return census_data


    def get_census_fields_by_table(self, table):
        """Return the fields in a census table
        Args: 
            table: the table name  
        Returns: 
            fields: 
            labels: 
        """
        data_path = self.data_path
        year = str(self.census_year)
        variables_file = data_path + 'variables_' + year + '.json'
        if not os.path.isfile(variables_file):
            url = 'https://api.census.gov/data/' + year + '/acs/acs5/variables.json'
            Utilities.download_file(url, variables_file)

        fields = []
        labels = {}

        with open(variables_file) as variables:
            data = json.load(variables)
            for key in data['variables']:
                if re.match(table+'_[0-9]*E', key):
                    fields.append(key)
                    labels[key]=data['variables'][key]['label']
        
        return fields, labels

    # TODO load districts file

    def load_district_data(self):
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
        district_data_filename = self.district_data_fn

        district_data={}
        if os.path.isfile(district_data_filename):
            with open(district_data_filename) as district_json:
                district_data = json.load(district_json)

        return district_data


    def make_class_data(self, census_data_in_district, census_classes, 
            district_data={}, geo_key='bg' ):
        """Populate Census classes
        Args:
            census_data_in_district:
            census_class:
        Returns: 
            district_data:
        """
        year = self.census_year
        office = self.office

        if year not in district_data.keys():
            district_data[year] = { geo_key: {} }
        if year in district_data.keys():
            if geo_key not in district_data[year].keys():
                district_data[year][geo_key] = {}
        
        #TODO add support for a tract
        if geo_key is not 'district':    
            for geoid, census_data in census_data_in_district[year][geo_key].items():
                if geoid not in district_data[year][geo_key].keys():
                    district_data[year][geo_key][geoid] = {}

                # Census classes
                for census_class, census_class_row in census_classes.items():
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
            if office == self.US_REP:
                # Census classes
                for census_class, census_class_row in census_classes.items():
                    # Add up the total of this census_class, e.g., (18-29) or 30s
                    census_class_total = 0

                    for census_subclass in census_class_row['fields']:
                        census_subclass_value = int(census_data_in_district[year][geo_key][census_subclass])
                        census_class_total =  census_class_total + census_subclass_value

                    # Census Class
                    district_data[year][geo_key][census_class] = census_class_total

        return district_data


    def make_district_data_for_local_office(self, categories={}, district_data={}):
        """Calculate the district data for a State legistlative district
        Args:
            categories:
            district_data:
        Returns: 
            district_data:
        """
        year = self.census_year
        bg_key = 'bg'
        district_key = 'district'
        office = self.office

        blockgroups_file = self.district_bgs_geojson_fn
        district_file = self.district_geojson_fn
        
        if office == self.US_REP:
            pass
        else:
            print( "\nEstimating districtwide statistics")
            blockgroups = gpd.read_file(blockgroups_file)
            district_boundary = gpd.read_file(district_file)
            
            if district_key not in district_data[year].keys():
                district_data[year][district_key] = {}
            
            # set all district fields to zero
            for cat_index, category in categories.items(): 
                for field in category['fields']:
                    if field not in 'median_income':
                        district_data[year][district_key][field] = 0.0

            intersections = blockgroups.geometry.intersection(district_boundary.geometry[0])
            areas = intersections.area
            for bg_index, bg in blockgroups.iterrows():
                interArea = areas[bg_index]
                bgArea = GeoSeries(bg.geometry).area[0]

                share = (interArea/bgArea)
                for field, value in district_data[year][bg_key][str(bg.GEOID)].items():
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


    def get_census_data(self, category, fields):
        """Store the raw census data in a json file and return the census data
        Args:
            category
            fields
        Returns: 
            census_data: 
        """
        state = self.state
        office = self.office
        district = self.district
        year = str(self.census_year)
        district_config_file = self.district_config_fn
        census_data_file = self.district_census_data_fn

        # If district config file exists, only get the census data that's not there
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
                census_data = self.get_blockgroup_census_data(
                        census_data=census_data,
                        fields=fields 
                    )
                # get the data for the entire district
                census_data = self.get_district_census_data(
                        census_data=census_data,
                        fields=fields 
                    )

                # TODO add get_tract_census_data()

                if year not in district_config.keys():
                    district_config[year] = [category]
                    district_config['census_years'].append(year)
                else:
                    district_config[year].append(category)
                # save census data to file
                Utilities.to_json(census_data, census_data_file)
                Utilities.to_json(district_config, district_config_file)
                
                return census_data

        # if there is no previous data for this district, then build from scratch
        census_data = self.get_blockgroup_census_data(fields=fields)
        
        census_data = self.get_district_census_data(census_data=census_data, fields=fields)

        # TODO add get_tract_census_data()

        # create district config file
        # add state, district, years, and categories
        district_config = {}
        district_config['state'] = state
        district_config['district'] = district
        district_config['office'] = office
        district_config[year] = [category]
        district_config['census_years'] = [year]
        
        # add centroid
        longitude, latitude = self.get_district_centroid()
        district_config['lat']=latitude
        district_config['lng']=longitude   
        
        # add file locations
        district_GeoJSON = self.district_geojson_fn
        bgs_in_district_GeoJSON = self.district_bgs_geojson_fn
        vps_in_district_GeoJSON  = self.district_vps_geojson_fn
        district_config['district_geojson'] = '/' + district_GeoJSON
        district_config['bg_geojson'] = '/' + bgs_in_district_GeoJSON
        district_config['precinct_geojson'] = '/' + vps_in_district_GeoJSON
        
        # add title
        district_config['title']=self.title

        # save census data to file
        Utilities.to_json(census_data, census_data_file)
        Utilities.to_json(district_config, district_config_file)
        
        return census_data

    
    def make_age_data(self, district_data = {}, categories = {'Age': {} }):
        """Make the census data on age for a district
        Args:
            district_data:
            categrories:
        Returns: 
            categories:
            district_data:
        """
        year = self.census_year
        office = self.office

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
        
        age_classes = CensusFields.get_age_fields()
        
        under_18_classes = CensusFields.get_under_18_fields()
        
        # Load the census data
        print( "\n" )
        print( "Getting Census Data for Sex by Age" )
        census_fields, census_labels = self.get_census_fields_by_table(table=age_table)
        census_data = self.get_census_data(category=category, fields=census_fields)
        
        # create fields and labels for census classes
        # used in web-based dashboard
        fields = []
        labels = {}
        
        fields.append(over_18_field)
        labels[over_18_field] = over_18_label
        
        fields.append(total_field)
        labels[total_field] = total_label
        
        for age_field, age_row in age_classes.items():
            fields.append(age_field)
            labels[age_field] = age_row['label']
        
        categories[category] = {'fields': fields, 'labels': labels}

        print( "Building Age Data" )
       
        # make the party identification data and data for the census classes
        # for the blockgroups
        district_data = self.make_class_data( 
                census_data_in_district=census_data, 
                census_classes=age_classes,
                district_data=district_data,
                geo_key=blockgroup_key
            )
        # make the party identification data and data for the census classes
        # for the district
        district_data = self.make_class_data( 
                census_data_in_district=census_data, 
                census_classes=age_classes,
                district_data=district_data,
                geo_key=district_key
            )

        # Calculate persons 18 and over in each block group and 
        # get the total population in each block group
        geo_key = blockgroup_key
        for geoid, census_data_row in census_data[year][geo_key].items():
            # Persons 18 and over
            under_18 = 0
            for census_field in under_18_classes['fields']:
                under_18 = under_18 + int(census_data_row[census_field])
            # (over 18) = total - (under 18)
            over_18 = int(census_data_row[total_census_field]) - under_18
            district_data[year][geo_key][geoid][over_18_field] = over_18
                
            # Total Population
            district_data[year][geo_key][geoid][total_field] = int(census_data_row[total_census_field])
        
        if office == self.US_REP:
            # calculate the district stats
            geo_key = district_key
            for census_field in under_18_classes['fields']:
                under_18 = under_18 + int(census_data[year][geo_key][census_field])
            # (over 18) = total - (under 18)
            over_18 = int(census_data[year][geo_key][total_census_field]) - under_18
            district_data[year][geo_key][over_18_field] = over_18
                
            # Total Population
            district_data[year][geo_key][total_field] = int(census_data[year][geo_key][total_census_field])

        return categories, district_data


    def make_income_data(self, district_data = {}, categories = {'Income': { }} ):
        """Make the income data for a district
        Args: 
            categories:
            district_data:
        Returns: 
            categories:
            district_data:
        """
        year = self.census_year
        office = self.office

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
        
        over_100k_field = 'over_100k'
        over_100k_label = '> $100,000'

        under_100k_field = 'under_100k'
        under_100k_label = '< $100,000'
        
        median_field = 'median_income'
        median_label = 'Median Household Income'
        
        income_classes = CensusFields.get_income_fields()

        # Load the census data
        print( "\n" )
        print( "Getting Census Data for Household Income" )
        census_fields, census_labels = self.get_census_fields_by_table(table=income_table) 
        census_fields.append(median_household_inc_field)
        census_data = self.get_census_data(category=category, fields=census_fields)

        if category not in categories.keys():
            categories[category] = {}

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

        for income_field, income_row in income_classes.items():
            fields.append(income_field)
            labels[income_field] = income_row['label']
        
        fields.append(median_field)
        labels[median_field] = median_label
        
        categories[category] = {'fields': fields, 'labels': labels}
        
        # add over/under fields
        # this is to customize their position in the drop down menu
        income_classes[over_100k_field] = CensusFields.get_over_100k_income_fields()
        income_classes[under_100k_field] = CensusFields.get_under_100k_income_fields()

        print( "Building Income data" )
       
        # make the blockgroup census data
        district_data = self.make_class_data(
                census_data_in_district=census_data, 
                census_classes=income_classes,
                district_data=district_data,
                geo_key=blockgroup_key
            )

        # make district-wide census data
        district_data = self.make_class_data( 
                census_data_in_district=census_data, 
                census_classes=income_classes,
                district_data=district_data,
                geo_key=district_key
            )

        # get the total households and the median household income
        geo_key = blockgroup_key
        for geoid, census_data_row in census_data[year][geo_key].items():
            # Median Household Income
            district_data[year][geo_key][geoid][median_field] = census_data_row[median_household_inc_field]
                
            # Total Households
            district_data[year][geo_key][geoid][total_field] = census_data_row[total_household_inc_field]
        
        # calculate the district stats
        if office == self.US_REP: 
            geo_key = district_key
            # Median Household Income
            district_data[year][geo_key][median_field] = census_data[year][geo_key][median_household_inc_field]
                
            # Total Households
            district_data[year][geo_key][total_field] = census_data[year][geo_key][total_household_inc_field]

        return categories, district_data


    def make_race_data(self,  district_data = {}, categories = {'Race': { }}): 
        """Make the race data for a district
        Args: 
            api: 
            state: 
            district: 
            year: 
        Returns: 
            categories:
            district_data:
        """
        year = self.census_year
        office = self.office
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
        
        race_classes = CensusFields.get_race_fields()

        # Load the census data
        census_fields = []
        print( "\n" )
        print( "Getting Census Data for Race" )
        race_fields, census_labels = self.get_census_fields_by_table(table=race_table) 
        census_fields.extend(race_fields)
        
        hispanic_fields, census_labels = self.get_census_fields_by_table(table=hispanic_table) 
        census_fields.extend(hispanic_fields)

        census_data = self.get_census_data(category=category, fields=census_fields)

        if category not in categories.keys():
            categories[category] = {}
        
        # create fields and labels for census classes
        # used in web-based dashboard
        fields = []
        labels = {}
        
        fields.append(total_field)
        labels[total_field] = total_label
        
        for race_field, race_row in race_classes.items():
            fields.append(race_field)
            labels[race_field] = race_row['label']
        
        categories[category] = {'fields': fields, 'labels': labels}
        
        print( "Building Race data" )
       
        # make blockgroup census data
        district_data = self.make_class_data(
                census_data_in_district=census_data, 
                census_classes=race_classes,
                district_data=district_data,
                geo_key=blockgroup_key
            )
        
        # make district-wide data for the census classes
        district_data = self.make_class_data( 
                census_data_in_district=census_data, 
                census_classes=race_classes,
                district_data=district_data,
                geo_key=district_key
            )

        # get the total population from the race table
        geo_key=blockgroup_key
        for geoid, census_data_row in census_data[year][geo_key].items():
            district_data[year][geo_key][geoid][total_field] = census_data_row[race_total_field]

        if office == self.US_REP: 
            geo_key=district_key
            district_data[year][geo_key][total_field] = census_data[year][geo_key][race_total_field]

        return categories, district_data


    def make_edu_data(self,  district_data = {}, categories = {'Education': { }}): 
        """Make the education data for a district
        Args: 
            api: 
            state: 
            district: 
            year: 
        Returns: 
            categories:
            district_data:
        """
        year = self.census_year
        office = self.office
        category='Education'

        district_key='district'
        blockgroup_key='bg'
        precinct_key='precinct'
        tract_key='tract'

        edu_table = 'B15002'
        edu_total_field = 'B15002_001E'
        
        total_field = 'total_edu'
        total_label = 'Total Population over 25'
        
        edu_classes = CensusFields.get_edu_fields()

        # Load the census data
        census_fields = []
        print( "\n" )
        print( "Getting Census Data for Education" )
        edu_fields, census_labels = self.get_census_fields_by_table(table=edu_table) 
        census_fields.extend(edu_fields)
        
        census_data = self.get_census_data(category=category, fields=census_fields)

        if category not in categories.keys():
            categories[category] = {}

        # create fields and labels for census classes
        # used in web-based dashboard
        fields = []
        labels = {}
        
        fields.append(total_field)
        labels[total_field] = total_label
        
        for field, edu_class in edu_classes.items():
            fields.append(field)
            labels[field] = edu_class['label']
        
        categories[category] = {'fields': fields, 'labels': labels}
        
        # make census data
        district_data = self.make_class_data(
                census_data_in_district=census_data, 
                census_classes=edu_classes,
                district_data=district_data,
                geo_key=blockgroup_key
            )

        # make the district-wide data for the census classes
        district_data = self.make_class_data( 
                census_data_in_district=census_data, 
                census_classes=edu_classes,
                district_data=district_data,
                geo_key=district_key
            )

        # get the total population from the edu table
        geo_key=blockgroup_key
        for geoid, census_data_row in census_data[year][geo_key].items():
            # Total Population
            district_data[year][geo_key][geoid][total_field] = census_data_row[edu_total_field]
        
        if office == self.US_REP: 
            geo_key=district_key
            district_data[year][geo_key][total_field] = census_data[year][geo_key][edu_total_field]

        return categories, district_data


    def make_voting_precinct_data(self, categories, district_data = {}, voting_precincts_file=None):
        """
        Args: 
            district_data:
            blockgroups:
            voting_precincts_file:
        Returns: 
            categories:
            district_data:
        """
        year = self.census_year
        precinct_key = 'precinct'
        
        # TODO account for multiple counties and geojson files for each county
        if voting_precincts_file is None:
            self.find_voting_precincts_in_district()
            voting_precincts_file  = self.district_vps_geojson_fn

        blockgroups_file = self.district_bgs_geojson_fn

        print( "\nCalculating statistics for voting precincts" )
        blockgroups = gpd.read_file(blockgroups_file)
        voting_precincts = gpd.read_file(voting_precincts_file)
        
        if precinct_key not in district_data[year].keys():
            district_data[year][precinct_key] = {}
        for precIndex, precinct in voting_precincts.iterrows():
            geoid = precinct.PRECINCT
            if geoid not in district_data[year][precinct_key].keys():
                district_data[year][precinct_key][geoid] = {}
            for cat_index, category in categories.items():
                for field in category['fields']:
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
                for field, value in district_data[year]['bg'][str(bg.GEOID)].items():
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
        
        # generate dictionary for each excel worksheet
        excel_sheets = {}
        for cat_key, category in categories.items():
            excel_sheets[cat_key] = {}
            excel_sheets[cat_key]['Precinct'] = []
            labels = category['labels']
            for field in category['fields']:
                if field not in 'median_income':
                    excel_sheets[cat_key][labels[field]] = []

        for cat_key, category in categories.items():
            labels = category['labels']
            for precIndex, precinct in voting_precincts.iterrows():
                geoid = precinct.PRECINCT
                excel_sheets[cat_key]['Precinct'].append( int(geoid) )
                for field in category['fields']:
                    if field not in 'median_income':
                        excel_sheets[cat_key][labels[field]].append(district_data[year][precinct_key][geoid][field])

        return district_data, excel_sheets


    def query_voting_results(self, vr_data, precinct, queries):
        """Return the value in the voting results for a given precinct based on various conditions
        Args: 
            vr_data: DataFrame of voting results
            precinct: int of precinct
            queries: a list queries, where each query is a list of the column and value,
            e.g., [['office', 'U.S. Senate'], ['party', 'DEM']]
        Returns: 
            query_result: an int of query result
        """
        query_result = 0
        # Get the voting results for the precinct
        vr_data = vr_data[ vr_data['precinct'] == precinct ]
        
        # for each of the queries return the remaining that match the conditions
        for col, row in queries:
            if  (len(vr_data) > 0) & (col in vr_data.columns.values) & (len( vr_data[ vr_data[col] == row ] ) > 0):
                vr_data = vr_data[ vr_data[col] == row ]
            else:
                return query_result
        
        if len(vr_data) > 0:
            query_result = int(vr_data.iloc[0]['votes'])

        return query_result


    def make_voting_results_data(self, categories, district_data = {}, voting_results_file=None):
        """Build voting results data per precinct and district from Open Elections file
        Args: 
            district_data:
            blockgroups:
            voting_precincts_file:
        Returns: 
            categories:
            district_data:
        """
        election_year = self.election_year
        census_year = self.census_year
        
        print( "\nGetting election results per precinct" )
        
        precinct_key = 'precinct'
        district_key = 'district'
        category = 'Voting Results'
        fields = []
        labels = {}
        
        # TODO if office == 'STATE-REP' or office == 'STATE-SEN':
        
        # TODO set presidential year versus congressional year
        election_result_fields = []
        election_result_fields = [
                    'us_pres_dem',
                    'us_pres_rep',
                    'us_sen_rep',
                    'us_sen_dem',
                    'registered_voters',
                    'us_hou_rep',
                    'us_hou_dem',
                    'total_votes'
                ] 
       
        # fields
        fields = []
        fields.extend(election_result_fields)
        fields.extend(['reg_per', 'dem_diff', 'hou_dem_per', 'over_18', 'us_hou_dem_pot'])

        labels = {
                'us_hou_dem_pot' : 'Democratic Potential',
                'registered_voters' : 'Registered Voters',
                'us_pres_rep' : 'US President Republican',
                'us_pres_dem' : 'US President Democratic',
                'us_sen_rep' : 'US Senate Republican',
                'us_sen_dem' : 'US Senate Democratic',
                'us_hou_rep' : 'US House Republican',
                'us_hou_dem' : 'US House Democratic',
                'total_votes' : 'Total Ballots Cast',
                'dem_diff' : 'US House Democratic Difference',
                'reg_per' : 'Registered Voters:18 Years+ %',
                'hou_dem_per' : 'US House Democratic Votes:18 Years+ %',
                'us_sen_per' : 'US Senate Democratic Votes:18 Years+ %',
                'over_18' : '18 Years and Over'
            }
        
        over_18 = float(district_data[census_year][district_key]['over_18'])

        # read voting precincts 
        self.find_voting_precincts_in_district()
        voting_precincts_file  = self.district_vps_geojson_fn
        voting_precincts = gpd.read_file(voting_precincts_file)
        
        # read voting results
        if voting_results_file is None:
            self.fetch_election_results()
            voting_results_file = self.district_election_results
        voting_results_data = pd.read_csv(voting_results_file)
       
        # add election results info (election years) to district_config file
        district_config_file = self.district_config_fn
        with open(district_config_file) as district_json:
            district_config = json.load(district_json)
        
        if 'election_years' not in district_config.keys():
            district_config['election_years'] = [election_year]
        else:
            if election_year not in district_config['election_years']:
                district_config['election_years'].append(election_year)
        
        if election_year not in district_config.keys():
            district_config[election_year] = [category]
        
        if category not in district_config[election_year]:
            district_config[election_year].append(category)
        
        # add election result categories
        if category not in categories.keys():
            categories[category] = {'fields': fields, 'labels': labels}
        
        # add voting results to district data
        if election_year not in district_data.keys():
            district_data[election_year] = { precinct_key: {} }
        if election_year in district_data.keys():
            if precinct_key not in district_data[election_year].keys():
                district_data[election_year][precinct_key] = {}

        # prepare the district data for disctrict-wide voting results
        if district_key not in district_data[election_year].keys():
            district_data[election_year][district_key] = {}
        
        # set all voting results for the disctrict to zero
        for field in fields:
            if field != 'over_18':
                district_data[election_year][district_key][field] = 0.0
        
        peak_no_vote = 0
        
        # initialize a progress bar for processing the precincts
        total_precincts = len(voting_precincts)
        pbar = tqdm(
                total=total_precincts, initial=0, 
                unit_scale=True, desc='Voting Precincts'
            )
        
        field_queries = {
                'us_pres_rep' : [['office', 'President'], ['party', 'REP']],
                'us_pres_dem' : [['office', 'President'], ['party', 'DEM']],
                'us_sen_rep' : [['office', 'U.S. Senate'], ['party', 'REP']],
                'us_sen_dem' : [['office', 'U.S. Senate'], ['party', 'DEM']],
                'us_hou_rep' : [['office', 'U.S. House'], ['party', 'REP']],
                'us_hou_dem' : [['office', 'U.S. House'], ['party', 'DEM']],
                'registered_voters' : [['office', 'Registered Voters']],
                'total_votes' : [['office', 'Ballots Cast']]
            }
        # dict for dataframe and excel file
        election_results_excel = {}
        election_results_excel['Precinct'] = []
        for field in fields:
            election_results_excel[labels[field]] = []

        # TODO for loop through counties
        # get the voting results for each precinct
        for precIndex, precinct in voting_precincts.iterrows():
            geoid = precinct.PRECINCT
            election_results_excel['Precinct'].append(int(geoid))
            if geoid not in district_data[election_year][precinct_key].keys():
                district_data[election_year][precinct_key][geoid] = {} 
            
            for field in election_result_fields:
                # get the number of pres-rep votes in each precinct
                query_result = self.query_voting_results( voting_results_data, int(geoid), field_queries[ field ] )
                district_data[election_year][precinct_key][geoid][field] = query_result
                election_results_excel[labels[field]].append( query_result )
                # get the total number of ballots cast
                if field == 'total_votes':
                    total_votes = query_result
                 
                # calculate the district wide total for field
                total = district_data[election_year][district_key][field]
                total = total + float(district_data[election_year][precinct_key][geoid][field])
                district_data[election_year][district_key][field] = total

            # calculate the democrat / republican difference
            field = 'dem_diff'
            dem = district_data[election_year][precinct_key][geoid]['us_hou_dem']
            rep = district_data[election_year][precinct_key][geoid]['us_hou_rep']
            district_data[election_year][precinct_key][geoid][field] = dem - rep
            election_results_excel[labels[field]].append( dem - rep )

            # calculate the democrat percent turnout relative to the 18+ age population
            field = 'hou_dem_per'
            over_18 = float(district_data[census_year][precinct_key][geoid]['over_18'])
            election_results_excel[labels['over_18']].append( int(over_18) )
            if over_18 > 0.0: 
                district_data[election_year][precinct_key][geoid][field] = int((float(dem) / over_18) * 100.0)
                election_results_excel[labels[field]].append( int((float(dem) / over_18) * 100.0) )
            else:
                district_data[election_year][precinct_key][geoid][field] = 0
                election_results_excel[labels[field]].append( 0 )

            # calculate the registred voter percent relative to the 18+ age population
            field = 'reg_per'
            reg = district_data[election_year][precinct_key][geoid]['registered_voters']
            if over_18 > 0.0:
                district_data[election_year][precinct_key][geoid][field] = int((float(reg) / over_18) * 100.0)
                election_results_excel[labels[field]].append( int((float(reg) / over_18) * 100.0) )
            else:
                district_data[election_year][precinct_key][geoid][field] = 0
                election_results_excel[labels[field]].append( 0 )
                
            no_vote = over_18 - total_votes
            if no_vote > peak_no_vote:
                peak_no_vote = no_vote
            pbar.update(1) 

        pbar.close()

        # calculate democratic potential factor = normalized non-voters plus dem percentage
        for precIndex, precinct in voting_precincts.iterrows():
            geoid = precinct.PRECINCT
            
            dem = float(district_data[election_year][precinct_key][geoid]['us_hou_dem'])
            over_18 = float(district_data[census_year][precinct_key][geoid]['over_18'])
            # temporary format
            # if election_year == '2018':
            #    total_votes = int(voting_results_data[ 
            #                    (voting_results_data['PRECINCT'] == geoid) 
            #                ].iloc[0]['TOTAL'])
            # else:
            # openelections format here
            total_votes = self.query_voting_results( voting_results_data, int(geoid), field_queries[ 'total_votes' ] )
           
            no_vote = over_18 - total_votes
            rel_no_vote = float(no_vote) / float(peak_no_vote)
            field = 'us_hou_dem_pot'
            if over_18 > 0.0:
                dem_pot = ( (rel_no_vote + (dem / over_18) ) / 2.0 ) * 100.0
            else:
                dem_pot = ( rel_no_vote / 2.0 ) * 100.0
            district_data[election_year][precinct_key][geoid][field] = int(dem_pot)
            election_results_excel[labels[field]].append( int(dem_pot) )

        # calculate district wide difference
        field = 'dem_diff'
        dem = int(district_data[election_year][district_key]['us_hou_dem'])
        rep = int(district_data[election_year][district_key]['us_hou_rep'])
        district_data[election_year][district_key][field] = int(dem - rep)

        # calculate district wide percentages
        field = 'hou_dem_per'
        dem = float(district_data[election_year][district_key]['us_hou_dem'])
        over_18 = float(district_data[census_year][district_key]['over_18'])
        district_data[election_year][district_key][field] = int((dem / over_18) * 100.0)
        
        field = 'reg_per'
        reg = float(district_data[election_year][district_key]['registered_voters'])
        district_data[election_year][district_key][field] = int((reg / over_18) * 100.0)
        

        # write the disctrict config to a file
        Utilities.to_json(district_config, district_config_file)

        return categories, district_data, election_results_excel

    
    def make_district_data(self, api, voting_precincts_file=None, voting_results_file=None):
        self.api = api
        office = self.office
        
        self.fetch_cb_boundary_files()
        self.fetch_election_results()

        self.find_blockgroups_in_district()
        self.find_voting_precincts_in_district()

        district_data=self.load_district_data()
        
        # Make the age categories and data for the district file
        categories, district_data = self.make_age_data(
                district_data=district_data
            )
        
        # Add income categories and data to the district file
        categories, district_data = self.make_income_data(
                district_data=district_data,
                categories=categories
            )
        
        # Add race categories and data to the district file
        categories, district_data = self.make_race_data(
                district_data=district_data,
                categories=categories
            )

        # Add educational categories and data to the district file
        categories, district_data = self.make_edu_data(
                district_data=district_data,
                categories=categories
            )
        
        # Calculate local office statistics
        district_data = self.make_district_data_for_local_office(
            district_data=district_data,
            categories=categories
        )
	
        # Estimate voting precinct data based on block group data
        district_data, excel_sheets = self.make_voting_precinct_data(
		district_data=district_data, 
		categories=categories
	    )
        
        # Determine election results per precinct and district
        categories, district_data, election_results_excel = self.make_voting_results_data(
		categories=categories, 
		district_data=district_data 
	    )
        
        # save district data to json
        district_data_file = self.district_data_fn
        Utilities.to_json(district_data, district_data_file)

        # save district categories to json
        categories_file = self.district_categories_fn
        Utilities.to_json(categories, categories_file)
        
        # copy district config, categories, and data to web-based files
        shutil.copyfile(self.district_config_fn, self.web_district_config_fn)
        shutil.copyfile(categories_file, self.web_district_categories_fn)
        shutil.copyfile(district_data_file, self.web_district_data_fn)
        
        # generate an excel file with different sheets for 
        # Age, Income, Race, Education, and Election Results
        excel_file = self.district_excel_fn
        with pd.ExcelWriter(excel_file) as x_writer:
            for sheet_name, sheet in excel_sheets.items():
                sheet = pd.DataFrame(sheet)
                sheet.to_excel(x_writer, sheet_name=sheet_name)
            election_results_excel = pd.DataFrame(election_results_excel)
            election_results_excel.to_excel(x_writer, sheet_name="{} Election Results".format(self.election_year))

        return categories, district_data 


class Utilities:
    @staticmethod
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


    @staticmethod
    def download_file(url, dl_filename):
        """Download a file given the url and filename
        Args:
            url: url to the file
            dl_filename: save the downloaded file using this filename
        See https://stackoverflow.com/questions/22676/how-do-i-download-a-file-over-http-using-python/22776#22776
        See https://gist.github.com/wy193777/0e2a4932e81afc6aa4c8f7a2984f34e2
        """
        print( url )
        url_object=urlopen(url)
        dl_file_object=open(dl_filename,'wb')
        meta = url_object.info()
        file_size = 0
        if int(meta.get("Content-Length", -1)) > 0:
            file_size = int(meta.get("Content-Length", -1))
        if file_size == 0:
            print( "Downloading: %s" % (dl_filename.split('/')[-1]) )
        else:
            print( "Downloading: %s Bytes: %s" % (dl_filename.split('/')[-1], file_size) )

        current_file_size = 0
        block_size = 8192
        pbar = tqdm(
                total=file_size, initial=0, 
                unit='B', unit_scale=True, desc=dl_filename.split('/')[-1] 
            )
        while True:
            buffer = url_object.read(block_size)
            if not buffer:
                break
            current_file_size += len(buffer)
            dl_file_object.write(buffer)
            pbar.update(block_size)
        pbar.close()
        dl_file_object.close()


    @staticmethod
    def extract_all(fn,dst="."):
        """extracts archive to dst
        Args:
            fn: filename
            dst: destiation
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
            print( "Please provide a tar archive file or zip file" )
    
    @staticmethod
    def to_json(data, out_filename):
        """Convert data to json
        Args: 
            data: a python data structure
            out_filename: the filename of the saved json file 
        """
        with open(out_filename, 'w') as outfile:  
            json.dump(data, outfile)


class CensusFields:
    """Static methods that return the fields for various census data classes
    Methods:
        get_under_18_fields()
        get_age_fields()
        get_income_fields()
        get_under_100k_income_fields()
        get_over_100k_income_fields()
        get_race_fields()
        get_race_fields()
    Attributes:
        None
    """
    @staticmethod
    def get_under_18_fields():
        """TODO fill in description
        Args: 
            Maybe year:  
        Returns:
            under_18_fields:
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
        
        under_18_fields = { 'label': 'Over 18', 'fields': under_18_fields }

        return under_18_fields

    @staticmethod
    def get_age_fields():
        """Return the fields for calculating population by age groups
        Args:
            Nothing
        Returns: 
            age_fields
        """
        under_18_fields = CensusFields.get_under_18_fields()

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
        
        age_fields = OrderedDict()
        age_fields[ 'age_18_to_29' ] = { 'label': '18-29', 'fields': age_18_to_29_fields }
        age_fields[ 'age_30_to_39' ] = { 'label': '30s', 'fields': age_30_to_39_fields }
        age_fields[ 'age_40_to_49' ] = { 'label': '40s', 'fields': age_40_to_49_fields }
        age_fields[ 'age_50_to_59' ] = { 'label': '50s', 'fields': age_50_to_59_fields }
        age_fields[ 'age_60_to_69' ] = { 'label': '60s', 'fields': age_60_to_69_fields } 
        age_fields[ 'age_70_to_79' ] = { 'label': '70s', 'fields': age_70_to_79_fields }
        age_fields[ 'age_81_plus' ]  = { 'label': '80+', 'fields': age_81_plus_fields }

        return age_fields

    @staticmethod
    def get_income_fields():
        """Return the fields for calculating income by households
        Args:
            Nothing
        Returns: 
            income_fields
        See Table B19001
        """
        less_than_30k_fields = [
                'B19001_002E', #	Less than $10,000	
                'B19001_003E', #	$10,000 to $14,999	
                'B19001_004E', #	$15,000 to $19,999	
                'B19001_005E', #	$20,000 to $24,999	
                'B19001_006E', #	$25,000 to $29,999	
            ]
        inc_30k_to_39k_fields = [
                'B19001_007E', #	$30,000 to $34,999	
                'B19001_008E', #	$35,000 to $39,999
            ]
        inc_40k_to_49k_fields = [
                'B19001_009E', #	$40,000 to $44,999	
                'B19001_010E', #	$45,000 to $49,999  
            ]
        inc_50k_to_74k_fields = [
                'B19001_011E', #	$50,000 to $59,999	
                'B19001_012E', #	$60,000 to $74,999
            ]
        inc_75k_to_99k_fields = [
                'B19001_013E' #	$75,000 to $99,999
            ]
        inc_100k_to_149k_fields = [
                'B19001_014E', #	$100,000 to $124,999	
                'B19001_015E', #	$125,000 to $149,999	
            ]
        inc_150k_plus_fields = [
                'B19001_016E', #	$150,000 to $199,999	
                'B19001_017E', #	$200,000 or more
            ]

        income_fields = OrderedDict()
        income_fields[ 'less_than_30k' ] = { 'label': '<$30,000', 'fields': less_than_30k_fields }
        income_fields[ 'inc_30k_to_39k' ] = { 'label': '$30,000 to $39,999', 'fields': inc_30k_to_39k_fields }
        income_fields[ 'inc_40k_to_49k' ] = { 'label': '$40,000 to $49,999', 'fields': inc_40k_to_49k_fields }
        income_fields[ 'inc_50k_to_74k' ] = { 'label': '$50,000 to $74,999', 'fields': inc_50k_to_74k_fields }
        income_fields[ 'inc_75k_to_99k' ] = { 'label': '$75,000 to $99,999', 'fields': inc_75k_to_99k_fields }
        income_fields[ 'inc_100k_to_149k' ] = { 'label': '$100,000 to $149,999', 'fields': inc_100k_to_149k_fields }
        income_fields[ 'inc_150k_plus' ] = { 'label': '$150,000+', 'fields': inc_150k_plus_fields }

        return income_fields


    @staticmethod
    def get_under_100k_income_fields():
        """Return the fields for calculating income under $100,000
        Args:
            Nothing
        Returns: 
            income_fields
        See Table B19001
        """
        inc_under_100k_fields = [
                'B19001_002E', #	Less than $10,000	
                'B19001_003E', #	$10,000 to $14,999	
                'B19001_004E', #	$15,000 to $19,999	
                'B19001_005E', #	$20,000 to $24,999	
                'B19001_006E', #	$25,000 to $29,999	
                'B19001_007E', #	$30,000 to $34,999	
                'B19001_008E', #	$35,000 to $39,999
                'B19001_009E', #	$40,000 to $44,999	
                'B19001_010E', #	$45,000 to $49,999  
                'B19001_011E', #	$50,000 to $59,999	
                'B19001_012E', #	$60,000 to $74,999
                'B19001_013E', #	$75,000 to $99,999
            ]

        return { 'label': '<$100,000', 'fields': inc_under_100k_fields }


    @staticmethod
    def get_over_100k_income_fields():
        """Return the fields for calculating income over $100,000
        Args:
            Nothing
        Returns: 
            income_fields
        See Table B19001
        """
        inc_over_100k_fields = [
                'B19001_014E', #	$100,000 to $124,999	
                'B19001_015E', #	$125,000 to $149,999	
                'B19001_016E', #	$150,000 to $199,999	
                'B19001_017E', #	$200,000 or more
            ]

        return { 'label': '$100,000+', 'fields': inc_over_100k_fields }

    @staticmethod
    def get_race_fields():
        """Return the census fields for race
        Args:
            Nothing
        Returns: 
            race_fields
        """
        race_fields = OrderedDict()
        race_fields['white_alone'] = { 
                    'label' : 'White alone', 
                    'fields': ['B02001_002E'] 
                }
        race_fields['black_alone'] = {
                    'label': 'Black or African American alone', 
                    'fields': ['B02001_003E'] 
                }
        race_fields['american_indian_alone'] = {
                    'label': 'American Indian and Alaska Native alone', 
                    'fields': ['B02001_004E'] 
                }
        race_fields['asian_alone'] = { 
                    'label': 'Asian alone', 
                    'fields': [ 'B02001_005E'] 
                }
        race_fields['pacific_alone'] = { 
                    'label': 'Native Hawaiian and Other Pacific Islander alone', 
                    'fields': [ 'B02001_006E'] 
                }
        race_fields['other_race_alone'] = { 
                'label': 'Some other race alone', 
                'fields': [ 'B02001_007E'] 
                }
        race_fields['not_hispanic'] = { 
                'label': 'Not Hispanic or Latino', 
                'fields': ['B03003_002E'] 
                }
        race_fields['hispanic'] =  { 
                'label': 'Hispanic or Latino', 
                'fields': ['B03003_003E']
                }

        return race_fields

    @staticmethod
    def get_edu_fields():
        """Return the census fields for educational attainment
        Args:
            Nothing
        Returns: 
            edu_fields
        """
        edu_hs_men_fields = [
                'B15002_003E', #	Male:!!No schooling completed	
                'B15002_004E', #	Male:!!Nursery to 4th grade	
                'B15002_005E', #	Male:!!5th and 6th grade	
                'B15002_006E', #	Male:!!7th and 8th grade	
                'B15002_007E', #	Male:!!9th grade	
                'B15002_008E', #	Male:!!10th grade	
                'B15002_009E', #	Male:!!11th grade	
                'B15002_010E', #	Male:!!12th grade, no diploma	
                'B15002_011E', #	Male:!!High school graduate (includes equivalency)
            ]
        edu_hs_women_fields = [
                'B15002_020E', #	Female:!!No schooling completed	
                'B15002_021E', #	Female:!!Nursery to 4th grade	
                'B15002_022E', #	Female:!!5th and 6th grade	
                'B15002_023E', #	Female:!!7th and 8th grade	
                'B15002_024E', #	Female:!!9th grade	
                'B15002_025E', #	Female:!!10th grade	
                'B15002_026E', #	Female:!!11th grade	
                'B15002_027E', #	Female:!!12th grade, no diploma	
                'B15002_028E', #	Female:!!High school graduate (includes equivalency)	
            ]
        edu_some_college_men_fields = [
                'B15002_012E', #	Male:!!Some college, less than 1 year	
                'B15002_013E', #	Male:!!Some college, 1 or more years, no degree	
                'B15002_014E', #	Male:!!Associate's degree	
            ]
        edu_some_college_women_fields = [
                'B15002_029E', #	Female:!!Some college, less than 1 year	
                'B15002_030E', #	Female:!!Some college, 1 or more years, no degree	
                'B15002_031E', #	Female:!!Associate's degree
            ]
        edu_college_men_fields = [
                'B15002_015E', #	Male:!!Bachelor's degree
            ]
        edu_college_women_fields = [
                'B15002_032E', #	Female:!!Bachelor's degree
            ]
        edu_postgrad_men_fields = [
                'B15002_016E', #	Male:!!Master's degree
                'B15002_018E', #	Male:!!Doctorate degree
            ]
        edu_postgrad_women_fields = [
                'B15002_033E', #	Female:!!Master's degree
                'B15002_035E', #	Female:!!Doctorate degree	
            ]

        edu_fields = OrderedDict()

        edu_fields['postgrad_men'] = { 'label' : 'Postgrad men', 'fields': edu_postgrad_men_fields }
        edu_fields['postgrad_women'] = {'label': 'Postgrad women', 'fields': edu_postgrad_women_fields }
        edu_fields['college_men'] = { 'label': 'College men', 'fields':  edu_college_men_fields }
        edu_fields['college_women'] =  { 'label': 'College women', 'fields': edu_college_women_fields }
        edu_fields['some_college_men'] =  { 'label': 'Some college men', 'fields': edu_some_college_men_fields }
        edu_fields['some_college_women'] =  { 'label': 'Some college women', 'fields': edu_some_college_women_fields }
        edu_fields['hs_men'] =  { 'label': 'HS or less men', 'fields': edu_hs_men_fields }
        edu_fields['hs_women'] =  { 'label': 'HS or less women', 'fields': edu_hs_women_fields }

        return edu_fields
