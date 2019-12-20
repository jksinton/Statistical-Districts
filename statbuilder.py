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
import configparser

# local libaries
from statlib import CensusFields
from statlib import District
from statlib import Utilities

# GLOBAL CONSTANTS

VERSION = '0.5.0'

def read_settings(args):
    """Read the settings stored in settings.ini
    Args: 
        args: argparse.ArgumentParser object that stores command line arguments
    Returns: 
        settings_dict: A dictionary holding the argument(s)
    """
    # Default values
    state = 48
    district = 7
    leg_body = 'US-REP'
    census_year = '2017'
    election_year = '2018'
    voting_precincts = None
    voting_results = None
    
    # Set values in settings.ini
    settings = configparser.ConfigParser()
    settings.read('settings.ini') # change example.settings.ini to settings.ini

    # Census API Key
    census_api_key = settings.get( 'census', 'CENSUS_API_KEY' )

    if args.census_year:
        census_year=args.census_year
    if args.election_year:
        election_year=args.election_year
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
                "census_year": census_year,
                "election_year": election_year,
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
    """
    _version=VERSION
    parser = argparse.ArgumentParser(description='Build stats for a given Congressional District')
    parser.add_argument('-s','--state', help='State of District, e.g., TX')
    parser.add_argument('-d','--district', help='District No., e.g., 7')
    parser.add_argument('-l','--leg-body', help='Legislative Body, e.g., US-REP, US-SEN, STATE-REP, or STATE-SEN')
    parser.add_argument('-y','--census-year', help='Year of Census data to build')
    parser.add_argument('-p','--voting-precincts', help='Estimate stats for voting precincts using geospatial vector file, e.g., shapefile or GEOJSON')
    parser.add_argument('-q','--election-year', help='Year of voting results')
    parser.add_argument('-r','--voting-results', help='Build voting results from Open Elections csv file')
    parser.add_argument('-v','--version',action='version', 
            version='%(prog)s %(version)s' % {"prog": parser.prog, "version": _version})
    parser.add_argument('--debug',help='print debug messages',action="store_true")

    return parser.parse_args()


def main():
    """Builds stats for a legislative district, e.g., a US Congressional District
    """
    args = get_command_line_args()
    settings = read_settings(args)
    
    census_api_key = settings['census_api_key']
    state = settings['state']
    district = settings['district']
    leg_body = settings['leg_body']
    census_year = settings['census_year']
    election_year = settings['election_year']
    voting_precincts_file = settings['voting_precincts']
    voting_results_file = settings['voting_results']
    
    my_district = District( 
                state=state, 
                district=district, 
                leg_body=leg_body,
                census_year=census_year,
                election_year=election_year
            )

    categories, district_data = my_district.make_district_data(
            api=census_api_key,
            voting_precincts_file=voting_precincts_file,
            voting_results_file=voting_results_file
        )


if __name__ == "__main__":
    main()
