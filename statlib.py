#!/usr/bin/env python

# This file is part of Statistical Districts.
# 
# Copyright (c) 2017, James Sinton
# All rights reserved.
# 
# Released under the BSD 3-Clause License
# See https://github.com/jksinton/Statistical-Districts/blob/master/LICENSE

from collections import OrderedDict

def get_under_18_classes():
    """TODO fill in description
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
    """TODO fill in description
    Args: 
    Returns: 
        age_pid_classes
    Raises:
        Nothing (yet)
    """
    # TODO prepare PID age classes that align with census data, e.g.,
    # 18 to 29, 30s, 40s, 50s, 60s, 70s, 80+
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
    """Return the classes for calculating population by age groups
    Args:
        Nothing
    Returns: 
        age_classes
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
    age_classes[ 'age_81_plus' ]  = { 'label': '80+', 'fields': age_81_plus_fields }

    return age_classes


def get_income_classes():
    """Return the classes for calculating income by households
    Args:
        Nothing
    Returns: 
        income_classes
    Raises:
        Nothing (yet)
    
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

    income_classes = OrderedDict()
    income_classes[ 'less_than_30k' ] = { 'label': '<$30,000', 'fields': less_than_30k_fields }
    income_classes[ 'inc_30k_to_39k' ] = { 'label': '$40,000 to $49,999', 'fields': inc_30k_to_39k_fields }
    income_classes[ 'inc_40k_to_49k' ] = { 'label': '$40,000 to $49,999', 'fields': inc_40k_to_49k_fields }
    income_classes[ 'inc_50k_to_74k' ] = { 'label': '$50,000 to $74,999', 'fields': inc_50k_to_74k_fields }
    income_classes[ 'inc_75k_to_99k' ] = { 'label': '$75,000 to $99,999', 'fields': inc_75k_to_99k_fields }
    income_classes[ 'inc_100k_to_149k' ] = { 'label': '$100,000 to $149,999', 'fields': inc_100k_to_149k_fields }
    income_classes[ 'inc_150k_plus' ] = { 'label': '$150,000+', 'fields': inc_150k_plus_fields }

    return income_classes


def get_under_100k_income_classes(under_100k_field):
    """Return the classes for calculating income under $100,000
    Args:
        Nothing
    Returns: 
        income_classes
    Raises:
        Nothing (yet)
    
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


def get_over_100k_income_classes(over_100k_field):
    """Return the classes for calculating income over $100,000
    Args:
        Nothing
    Returns: 
        income_classes
    Raises:
        Nothing (yet)
    
    See Table B19001
    """
    inc_over_100k_fields = [
            'B19001_014E', #	$100,000 to $124,999	
            'B19001_015E', #	$125,000 to $149,999	
            'B19001_016E', #	$150,000 to $199,999	
            'B19001_017E', #	$200,000 or more
        ]

    return { 'label': '$100,000+', 'fields': inc_over_100k_fields }


def get_income_pid_classes():
    """Return the classes for calculating income party identification by households
    Args:
        Nothing
    Returns: 
        income_classes
    Raises:
        Nothing (yet)
    """

    income_classes = get_income_classes()

    income_pid_classes = OrderedDict()

    for key, row in income_classes.iteritems():
        income_pid_classes[ 'pid_' + key ] = row

    income_pid_classes[ 'pid_less_than_30k' ]['pid'] = 0.60
    income_pid_classes[ 'pid_less_than_30k' ]['label'] = 'PID: ' + income_classes[ 'less_than_30k' ]['label']
    
    income_pid_classes[ 'pid_inc_30k_to_39k' ]['pid'] = 0.46
    income_pid_classes[ 'pid_inc_30k_to_39k' ]['label'] = 'PID: ' + income_classes[ 'inc_30k_to_39k' ]['label']
    
    income_pid_classes[ 'pid_inc_40k_to_49k' ]['pid'] = 0.46
    income_pid_classes[ 'pid_inc_40k_to_49k' ]['label'] = 'PID: ' + income_classes[ 'inc_40k_to_49k' ]['label']
    
    income_pid_classes[ 'pid_inc_50k_to_74k' ]['pid'] = 0.44
    income_pid_classes[ 'pid_inc_50k_to_74k' ]['label'] = 'PID: ' + income_classes[ 'inc_50k_to_74k' ]['label']
    
    income_pid_classes[ 'pid_inc_75k_to_99k' ]['pid'] = 0.44
    income_pid_classes[ 'pid_inc_75k_to_99k' ]['label'] = 'PID: ' + income_classes[ 'inc_75k_to_99k' ]['label']
    
    income_pid_classes[ 'pid_inc_100k_to_149k' ]['pid'] = 0.45
    income_pid_classes[ 'pid_inc_100k_to_149k' ]['label'] = 'PID: ' + income_classes[ 'inc_100k_to_149k' ]['label']
    
    income_pid_classes[ 'pid_inc_150k_plus' ]['pid'] = 0.48
    income_pid_classes[ 'pid_inc_150k_plus' ]['label'] = 'PID: ' + income_classes[ 'inc_150k_plus' ]['label']

    return income_pid_classes


def get_race_classes():
    """Return the census classes for race
    Args:
        Nothing
    Returns: 
        race_classes
    Raises:
        Nothing (yet)
    """
    race_classes = OrderedDict()
    race_classes['white_alone'] = { 'label' : 'White alone', 'fields': ['B02001_002E'] }
    race_classes['black_alone'] = {'label': 'Black or African American alone', 'fields': ['B02001_003E'] }
    race_classes['american_indian_alone'] = {'label': 'American Indian and Alaska Native alone', 'fields': ['B02001_004E'] }
    race_classes['asian_alone'] = { 'label': 'Asian alone', 'fields': [ 'B02001_005E'] }
    race_classes['pacific_alone'] = { 'label': 'Native Hawaiian and Other Pacific Islander alone', 'fields': [ 'B02001_006E'] }
    race_classes['other_race_alone'] = { 'label': 'Some other race alone', 'fields': [ 'B02001_007E'] }
    race_classes['not_hispanic'] = { 'label': 'Not Hispanic or Latino', 'fields': ['B03003_002E'] }
    race_classes['hispanic'] =  { 'label': 'Hispanic or Latino', 'fields': ['B03003_003E']}

    return race_classes


def get_race_pid_classes():
    """Return the census classes for race
    Args:
        Nothing
    Returns: 
        race_classes
    Raises:
        Nothing (yet)
    """
    race_classes = OrderedDict()
    race_classes['pid_white_alone'] = { 'label' : 'PID White alone', 'fields': ['B02001_002E'], 'pid': 0.39 }
    race_classes['pid_black_alone'] = {'label': 'PID Black or African American alone', 'fields': ['B02001_003E'], 'pid': 0.87 }
    race_classes['pid_asian_alone'] = { 'label': 'PID Asian alone', 'fields': [ 'B02001_005E'] , 'pid': 0.63 }
    race_classes['pid_hispanic'] =  { 'label': 'PID Hispanic or Latino', 'fields': ['B03003_003E'], 'pid': 0.66 }

    return race_classes


def get_edu_classes():
    """Return the census classes for educational attainment
    Args:
        Nothing
    Returns: 
        edu_classes
    Raises:
        Nothing (yet)
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

    edu_classes = OrderedDict()
    edu_classes['pid_postgrad_men'] = { 'label' : 'Postgrad men', 'fields': edu_postgrad_men_fields }
    edu_classes['pid_postgrad_women'] = {'label': 'Postgrad women', 'fields': edu_postgrad_women_fields }
    edu_classes['pid_college_men'] = { 'label': 'College men', 'fields':  edu_college_men_fields }
    edu_classes['pid_college_women'] =  { 'label': 'College women', 'fields': edu_college_women_fields }
    edu_classes['pid_some_college_men'] =  { 'label': 'Some college men', 'fields': edu_some_college_men_fields }
    edu_classes['pid_some_college_women'] =  { 'label': 'Some college women', 'fields': edu_some_college_women_fields }
    edu_classes['pid_hs_men'] =  { 'label': 'HS or less men', 'fields': edu_hs_men_fields }
    edu_classes['pid_hs_women'] =  { 'label': 'HS or less women', 'fields': edu_hs_women_fields }

    return edu_classes

def get_edu_pid_classes():
    """Return the PID classes for educational attainment
    Args:
        Nothing
    Returns: 
        edu_classes
    Raises:
        Nothing (yet)
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

    edu_classes = OrderedDict()
    edu_classes['pid_postgrad_men'] = { 'label' : 'PID Postgrad men', 'fields': edu_postgrad_men_fields, 'pid': 0.49 }
    edu_classes['pid_postgrad_women'] = {'label': 'PID Postgrad women', 'fields': edu_postgrad_women_fields, 'pid': 0.69 }
    edu_classes['pid_college_men'] = { 'label': 'PID College men', 'fields':  edu_college_men_fields, 'pid': 0.43 }
    edu_classes['pid_college_women'] =  { 'label': 'PID College women', 'fields': edu_college_women_fields, 'pid': 0.56 }
    edu_classes['pid_some_college_men'] =  { 'label': 'PID Some college men', 'fields': edu_some_college_men_fields, 'pid': 0.37 }
    edu_classes['pid_some_college_women'] =  { 'label': 'PID Some college women', 'fields': edu_some_college_women_fields, 'pid': 0.52 }
    edu_classes['pid_hs_men'] =  { 'label': 'PID HS or less men', 'fields': edu_hs_men_fields, 'pid': 0.42 }
    edu_classes['pid_hs_women'] =  { 'label': 'PID HS or less women', 'fields': edu_hs_women_fields, 'pid': 0.50 }

    return edu_classes
