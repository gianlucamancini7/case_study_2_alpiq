import json
import xmltodict
import pandas as pd
from config import DICTIONARY_NATIONS
import sys
sys.path.append('..')

# xml conversion


def store_geographical_time_variables(start_date, end_date, country_1, country_2):
    """
    Function to return the key variables to download the relevant
    ENTSO-E data from the platform

    Args:
        start_date: start date to download the data (Eg. '20191003', 10th October 2019) (string)
        end_date: end date to download the data (string)
        country_1:  main country (Eg. CSwitzerland,  Germany) (string)
        country_2:  secondary country (Eg.  Switzerland, Germany) (string)
    Return:
        start: start date to download the data (pd.Timestamp)
        end: end date to download the data (pd.Timestamp)
        country_code_1: alphabetical code of the main country (Eg. CH--> Switzerland, DE --> Germany) (string)
        country_code_2: alphabetical code of the secondary country (Eg. CH--> Switzerland, DE --> Germany) (string)

    """

    # transform into pd.Timestamp
    start = pd.Timestamp(start_date, tz='Europe/Brussels')
    end = pd.Timestamp(end_date, tz='Europe/Brussels')

    if country_1 and country_2 in DICTIONARY_NATIONS.keys():
        country_code_1, country_code_2 = DICTIONARY_NATIONS[country_1], DICTIONARY_NATIONS[country_2]
    else:
        print('Invalid country name, check your spelling ')
        country_code_1, country_code_2 = None, None

    return start, end, country_code_1, country_code_2


def store_data(entsoe_pandas_object, name='default'):
    """

    This function takes as input the ENTSO-E client function which return time dependent data 
    and return a table

    Args:
        entsoe_pandas_object: entso_e client function returning pandas object
        name: name of the quanitity calculated (string)
    Return:
        df: pandas dataframe (pd.DataFame)

    """
    entsoe_pandas_object_ = entsoe_pandas_object

    # check if object is dataframe or
    if type(entsoe_pandas_object) == pd.core.series.Series:
        df = pd.DataFrame({name: entsoe_pandas_object_})
    else:
        df = entsoe_pandas_object_

    # add a column called time
    df['time'] = pd.to_datetime(df.index)

    # drop the intial index
    df.reset_index(drop=True, inplace=True)

    return df


def process_xml_net_capacity(entsoe_pandas_object, start, end, name='default'):
    """Function to transfor the net capacity xml string into a table format

    Args:
        entsoe_pandas_object: entso_e client function returning pandas object
        name: name of the quanitity calculated (string)
        start: start date to download the data (pd.Timestamp)
        end: end date to download the data (pd.Timestamp)
    Return:
        df: pandas dataframe (pd.DataFame)

    """

    entsoe_pandas_object_ = entsoe_pandas_object

    # convert xml to json
    o = xmltodict.parse(entsoe_pandas_object_)
    json_string = json.dumps(o)

    # conver json to readable pandas
    df_converted = pd.read_json(json_string, orient='index', typ='frame')

    # initiate time period
    time_period = pd.period_range(start, end, freq='H')[:-1]

    # initiate list of values
    values = []

    # loop over the time series hidden in the xml file
    for el in df_converted['TimeSeries'][0]:
        for d in el['Period']['Point']:
            values.append(d['quantity'])

    df = pd.DataFrame(data={'time': time_period, name: values})

    return df


def save_data(df):
    """Function to save files to csv"""

    return df
