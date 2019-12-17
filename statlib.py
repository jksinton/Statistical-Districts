#!/usr/bin/env python

# This file is part of Statistical Districts.
# 
# Copyright (c) 2019, James Sinton
# All rights reserved.
# 
# Released under the BSD 3-Clause License
# See https://github.com/jksinton/Statistical-Districts/blob/master/LICENSE

from collections import OrderedDict

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
        income_fields[ 'inc_30k_to_39k' ] = { 'label': '$40,000 to $49,999', 'fields': inc_30k_to_39k_fields }
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

        return edu_fields
