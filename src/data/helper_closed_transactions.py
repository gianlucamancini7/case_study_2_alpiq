import pandas as pd
import numpy as np
import time


def format_delta(instrument_type_duration, delivery_instrument):
    """
    This function takes the delivery instrument and reformat it to with the starting time
    being first

    """

    if instrument_type_duration == 'Hour':
        return delivery_instrument-pd.Timedelta(1, unit='hours')
    elif instrument_type_duration == 'Half Hour':
        return delivery_instrument-pd.Timedelta(0.5, unit='hours')
    else:
        return delivery_instrument-pd.Timedelta(0.25, unit='hours')


def read_epex_file(path, fast_load=False, new_data_type=False):
    """
    This function takes the path of the old data frame type, reads it and loads it as a dataframe

    Args:
        path: file location path (string)
        new_data_type: defining whether the input is a new or old data file (bool)
        fast_load: deciding whether to load a minor section of the dataset [100000 rows] (bool)
    Returns:
        df: read dataframe (Pandas DataFrame)

    """

    # read first row only to get the columns name and avoid reading 'Unnamed: 17'
    cols = list(pd.read_csv(path, nrows=1, sep=';'))

    df = pd.read_csv(path,
                     sep=';',
                     decimal=",",
                     usecols=[i for i in cols if i !=
                              'Unnamed: 17'],
                     parse_dates=['Start Validity Date',
                                  'End Validity Date', 'Cancelling Date'],
                     date_parser=lambda col: pd.to_datetime(col,
                                                            utc=True,
                                                            format='%d/%m/%Y %H:%M:%S.%f',
                                                            ),
                     nrows=None if not fast_load else 100000
                     )

    # change time data type
    df['Delivery Instrument'] = pd.to_timedelta(
        df['Delivery Instrument'].apply(lambda x: x + ':00'))

    del_instument = df.apply(lambda x: format_delta(
        x['Instrument Type'], x['Delivery Instrument']), axis=1)

    df['Delivery Instrument'] = del_instument

    df['Delivery Date'] = pd.to_datetime(
        df['Delivery Date'], utc=True, format='%d/%m/%Y')

    # add column combination of execution volume, time and price which allows to combine the sell and buy transaction univocally
    df['Executed Price & Volume'] = list(
        zip(df['Execution Price'], df['Executed Volume']))

    # create delivery start column
    df['Delivery Start'] = df['Delivery Date'] + df['Delivery Instrument']

    # create the lead time column
    df['lead_time'] = df['Delivery Start']-df['End Validity Date']

    # rest index to have an index which univocously identify daily transactions
    df.reset_index(inplace=True)

    return df


def filter_lead_time(df):
    """

    This function filters the LOB dataframe for the orders with a lead time which is relevant for the investigation

    Args:
        df: LOB dataframe (Pandas DataFrame)
    Return:
        df_filtered: dataframe with filtered LOB (Pandas DataFrame)

    """

    # define logical statement to filter rows based on lead time
    logical_statement_lead_time = (df['lead_time'].dt.total_seconds(
    )/60 >= 30) & (df['lead_time'].dt.total_seconds()/60 <= 60)

    # filter the dataframe based on logical statement
    df_filtered = df[logical_statement_lead_time]

    # define logical statement to filter rows based on execution
    logical_statement_execution = df_filtered['Is Executed'] != 0

    # filter the dataframe based on logical statement
    df_filtered = df_filtered[logical_statement_execution]

    # check for presence of unbound contracts

    if df_filtered[df_filtered['Side'] == 'B']['Executed Volume'].sum() == df_filtered[df_filtered['Side'] == 'S']['Executed Volume'].sum():
        unbounded_contract = False

    else:
        unbounded_contract = True

    return df_filtered, unbounded_contract


def extract_transactions(df_filtered, unbounded_contract=False):
    """

    This function filters extract the completed transactions from the filtered LOB dataframe

    Args:
        df_filtered: filtered LOB dataframe (Pandas DataFrame)
    Return:
        pivoted: pivoted table showing transactions for confy visualization (Pandas DataFrame)
        pivoted_levels: pivoted table showing transactions for further analysis (Pandas DataFrame)
    """

    # table view with transactions buy and sell side showing row wise
    pivoted = pd.pivot_table(df_filtered,
                             values=['Price', 'Volume', 'Initial ID', 'Order ID', 'Parent ID', 'Is block',
                                     'Is Executed', 'Execution Price', 'Executed Volume', 'lead_time', 'Instrument Type', 'index'],
                             index=['End Validity Date',
                                    'Executed Price & Volume', 'Delivery Start', 'Side'],
                             aggfunc=list,
                             ).apply(pd.Series.explode).sort_index()
    if unbounded_contract:

        problematic = []
        for ind, v in pivoted.groupby(level=0):
            d = dict(v.reset_index()['Side'].value_counts())
            s = set(v.reset_index()['Side'].values)

            if s != set(['B', 'S']):
                problematic.append(ind)
            elif d['B']-d['S'] != 0:
                problematic.append(ind)
        pivoted = pivoted[~pivoted.index.get_level_values(
            'End Validity Date').isin(problematic)]

    # table view with transactions indexed only for datetime and execution price adn volumes
    pivoted_levels = pd.merge(pivoted.query('Side == "B"').reset_index(level=3, drop=True).reset_index(),
                              pivoted.query('Side == "S"').reset_index(
        level=3, drop=True).reset_index(),
        left_index=True,
        right_index=True,
        suffixes=('_B', '_S'))

    return pivoted, pivoted_levels


def prepare_new_transactions(path):
    """

    This function filters and prepare the contracts for the months of November and December to be analysed

    Args:
        path: ALPIQ transactions dataframe path (Pandas DataFrame)
    Return:
        df_list: list of daily dataframes with transactions to be saved and fed to the optimizer (list)

    """

    cols = list(pd.read_csv(path, nrows=1))
    df = pd.read_csv(path,
                     usecols=[i for i in cols if 'Unnamed' not in i])

    # format time presenting hour as well
    df['problem_from_time'] = df['FROM_TIME'].apply(lambda x: isTimeFormat(x))
    df['problem_to_time'] = df['TO_TIME'].apply(lambda x: isTimeFormat(x))
    df['problem_timestamp'] = df['TIMESTAMP'].apply(lambda x: isTimeFormat(x))
    df['FROM_TIME'] = df['FROM_TIME'].apply(
        lambda x: x if isTimeFormat(x) else str(x)+' 0:0')
    df['TO_TIME'] = df['TO_TIME'].apply(
        lambda x: x if isTimeFormat(x) else str(x)+' 0:0')
    df['TIMESTAMP'] = df['TIMESTAMP'].apply(
        lambda x: x if isTimeFormat(x) else str(x)+' 0:0')

    # convert to datetime
    df['FROM_TIME'] = pd.to_datetime(
        df['FROM_TIME'], utc=True, format='%m/%d/%y %H:%M')
    df['TO_TIME'] = pd.to_datetime(
        df['TO_TIME'], utc=True, format='%m/%d/%y %H:%M')
    df['TIMESTAMP'] = pd.to_datetime(
        df['TIMESTAMP'], utc=True, format='%m/%d/%y %H:%M')

    # remove unusable columns
    df = df[df['problem_timestamp']]

    # modify dates mistakes
    df['FROM_TIME'] = df.apply(lambda x: correct_from_time(
        x['problem_from_time'], x['TO_TIME'], x['FROM_TIME'], x['DURATION']), axis=1)
    df['TO_TIME'] = df.apply(lambda x: correct_to_time(
        x['problem_to_time'], x['TO_TIME'], x['FROM_TIME'], x['DURATION']), axis=1)

    # define lead time
    df['lead_time'] = df['FROM_TIME']-df['TIMESTAMP']

    # define logical statement to filter rows based on lead time
    logical_statement_lead_time = (df['lead_time'].dt.total_seconds(
    )/60 >= 30) & (df['lead_time'].dt.total_seconds()/60 <= 60)

    # filter the dataframe based on logical statement
    df_filtered = df[logical_statement_lead_time]

    # add columns for pipeline compatibility
    df_filtered['End Validity Date'] = df_filtered['TIMESTAMP']
    df_filtered['Execution Price'] = df_filtered['PRICE']
    df_filtered['Executed Volume'] = df_filtered['VOLUME']
    df_filtered['Delivery Start'] = df_filtered['FROM_TIME']
    df_filtered['Instrument Type'] = df_filtered['DURATION'].apply(
        lambda x: map_duration(x))

    df_list, file_names = split_daily_transactions(df_filtered)

    return df_list, file_names


def split_daily_transactions(df):

    min_date_day = df['FROM_TIME'].dt.day.min()
    max_date_day = df['FROM_TIME'].dt.day.max()
    month = str(df['FROM_TIME'].dt.month.iloc[0])

    df_list = []
    file_names = []
    for day in range(min_date_day, max_date_day+1):

        df_day = df[df['FROM_TIME'].dt.day == day]
        df_list.append(df_day)

        day_string = str(day) if len(str(day)) == 2 else '0'+str(day)
        name = 'DE_2019'+month+day_string+'.csv'
        file_names.append(name)

    return df_list, file_names


def map_duration(duration):

    d = {0.25: 'Quarter Hour', 0.5: 'Half Hour', 1: 'Hour'}

    return d[duration]


def correct_to_time(problem, to_time, from_time, duration):

    if not problem:
        return from_time + pd.Timedelta(duration, unit='hours')
    else:
        return to_time


def correct_from_time(problem, to_time, from_time, duration):

    if not problem:
        return to_time - pd.Timedelta(duration, unit='hours')
    else:
        return from_time


def isTimeFormat(input):
    try:
        time.strptime(input, '%m/%d/%y %H:%M')
        return True
    except ValueError:
        return False
