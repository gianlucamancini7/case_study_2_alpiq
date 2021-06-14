import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.dates as mdates


def assign_to_time_window(df_liquidity, sta, end, hours_s, hours_e, updated=False):
    """
    This function takes the limit order book, the start and end time of a window and the starting and
    ending times and days of the limit order transactions and assign it to the the window calculating the average
    bid ask spread

    Args:
        df_liquidity: read dataframe (Pandas DataFrame)
        sta: starting time (pandas._libs.tslibs.timestamps.Timestamp)
        end: ending time (pandas._libs.tslibs.timestamps.Timestamp)
        hours_s: starting date hours of validity of limit order  (pandas.core.series.Series)
        hours_e: ending date hours of validity of limit order  (pandas.core.series.Series)
    Returns:
        liquidity value (float)

    """

    if updated:
        price_name_tag = 'Price Updated'
    else:
        price_name_tag = 'Price'

    df_liquidity_sel = df_liquidity[(hours_s >= sta)
                                    & (hours_e <= end)
                                    ]

    # filter for ice-berg order indication
    df_liquidity_sel_ = df_liquidity_sel[df_liquidity_sel['Volume'] != 0]

    # check if df_liquidity_sel_ is not empty and return average in the rare case that now orders are submitted in a specific time frame
    if df_liquidity_sel_.shape[0] > 0:
        return np.average(df_liquidity_sel_[price_name_tag][df_liquidity_sel_['Side'] == 'S'], weights=df_liquidity_sel_['Volume'][df_liquidity_sel_['Side'] == 'S'],)
        -np.average(df_liquidity_sel_[price_name_tag][df_liquidity_sel_['Side'] == 'B'],
                    weights=df_liquidity_sel_['Volume'][df_liquidity_sel_['Side'] == 'B'])

    else:
        return None


def update_prices_closed_transactions(df_liquidity, pivoted_levels_sort):
    """
    This function takes the processed limit order book of one day and its start time and update the orders with the new transaction order prices

    Args:
        df_liquidity: read dataframe (Pandas DataFrame)
        starttime: date and time of the opening of the intraday market (Eg. "30/09/2019 15:00") (string)
        pivoted_levels_sort: read dataframe (Pandas DataFrame)
    Returns:
        df_liquidity_updated: pandas dataframe with new updated price for those orders matched (Pandas DataFrame)

    """

    # select only interesting columns
    pivoted_levels_sort_ = pivoted_levels_sort[[
        'A posteriori Execution Price', 'match_binary_outcome', 'index_S']]

    # merge dataframes for CH-DE effect (merging based on ORDERED ID IN LOB)
    df_liquidity_updated = pd.merge(df_liquidity,
                                    pivoted_levels_sort_,
                                    left_on='index',
                                    right_on='index_S',
                                    how='left')

    # create a new column with the updated price/s
    df_liquidity_updated['Price Updated'] = df_liquidity_updated.apply(
        lambda x: x['A posteriori Execution Price'] if x['match_binary_outcome'] == 1 else x['Price'], axis=1)

    return df_liquidity_updated


def update_prices_closed_transactions_complete(df_liquidity, pivoted_levels_sort):
    """
    This function takes the processed limit order book of one day and its start time and update the orders with the new transaction order prices

    Args:
        df_liquidity: read dataframe (Pandas DataFrame)
        starttime: date and time of the opening of the intraday market (Eg. "30/09/2019 15:00") (string)
        pivoted_levels_sort: read dataframe (Pandas DataFrame)
    Returns:
        df_liquidity_updated: pandas dataframe with new updated price for those orders matched (Pandas DataFrame)

    """

    # select only interesting columns
    pivoted_levels_sort_ = pivoted_levels_sort[[
        'A posteriori Execution Price', 'match_binary_outcome_selling', 'match_binary_outcome_pumping', 'index_S']]

    # merge dataframes for CH-DE effect (merging based on ORDERED ID IN LOB)
    df_liquidity_updated = pd.merge(df_liquidity,
                                    pivoted_levels_sort_,
                                    left_on='index',
                                    right_on='index_S',
                                    how='left')

    # create a new column with the updated price/s
    df_liquidity_updated['Price Updated'] = df_liquidity_updated.apply(
        lambda x: x['A posteriori Execution Price'] if (x['match_binary_outcome_selling'] == 1) or (x['match_binary_outcome_pumping'] == 1) else x['Price'], axis=1)

    return df_liquidity_updated


def assign_to_time_window_depth(df_liquidity, sta, end, hours_s, hours_e):
    """
    This function takes the limit order book, the start and end time of a window and the starting and
    ending times and days of the limit order transactions and assign it to the the window calculating the average
    bid ask spread

    Args:
        df_liquidity: read dataframe (Pandas DataFrame)
        sta: starting time (pandas._libs.tslibs.timestamps.Timestamp)
        end: ending time (pandas._libs.tslibs.timestamps.Timestamp)
        hours_s: starting date hours of validity of limit order  (pandas.core.series.Series)
        hours_e: ending date hours of validity of limit order  (pandas.core.series.Series)
    Returns:
        list: volumes and prices for bid and ask curve (list of lists)

    """

    df_liquidity_sel = df_liquidity[(hours_s >= sta)
                                    & (hours_e <= end)
                                    ]

    # filter for ice-berg order indication
    df_liquidity_sel_ = df_liquidity_sel[df_liquidity_sel['Volume'] != 0]

    # check if df_liquidity_sel_ is not empty and return average in the rare case that now orders are submitted in a specific time frame
    if df_liquidity_sel_.shape[0] > 0:
        return [df_liquidity_sel_['Price'][df_liquidity_sel_['Side'] == 'S'].values.tolist(),
                df_liquidity_sel_['Volume'][df_liquidity_sel_[
                    'Side'] == 'S'].values.tolist(),
                df_liquidity_sel_['Price'][df_liquidity_sel_[
                    'Side'] == 'B'].values.tolist(),
                df_liquidity_sel_['Volume'][df_liquidity_sel_['Side'] == 'B'].values.tolist()]

    else:
        return None


def hourly_bid_ask_spread(df_liquidity, starttime, comparison=False):
    """
    This function takes the processed limit order book of one day and its start time and compute the
    hourly bid ask spread

    Args:
        df_liquidity: read dataframe (Pandas DataFrame)
        starttime: date and time of the opening of the intraday market (Eg. "30/09/2019 15:00") (string)
    Returns:
        df_validity: pandas dataframe with hours of the intraday market and the corresponding
        bid-ask spread (Pandas DataFrame)

    """

    # convert string like input in timestamp
    start_time = pd.Timestamp(starttime)

    # obtain end times for hourly like sequence
    end_time1 = start_time+pd.Timedelta(1+17/48, unit='days')
    end_time2 = start_time+pd.Timedelta(1.375, unit='days')

    # create a dataframe which defines the validity of the different time stamps in the timeseries
    df_validity = pd.DataFrame()
    df_validity['Start'] = pd.date_range(
        start_time, end_time1, freq="30min", tz='UTC')
    df_validity['End'] = pd.date_range(
        start_time+pd.Timedelta(0.5, unit='hours'), end_time2, freq="30min", tz='UTC')
    df_validity.reset_index(inplace=True)

    if not comparison:
        df_validity['Hourly Bid-Ask Spread'] = df_validity.apply(lambda x: assign_to_time_window(df_liquidity,
                                                                                                 x['Start'],
                                                                                                 x['End'],
                                                                                                 df_liquidity['Start Validity Date'],
                                                                                                 df_liquidity['End Validity Date']
                                                                                                 ), axis=1)
    else:
        # update df_liquidity prices with the new marginal prices

        df_validity['Hourly Bid-Ask Spread'] = df_validity.apply(lambda x: assign_to_time_window(df_liquidity,
                                                                                                 x['Start'],
                                                                                                 x['End'],
                                                                                                 df_liquidity['Start Validity Date'],
                                                                                                 df_liquidity['End Validity Date'],
                                                                                                 updated=comparison
                                                                                                 ), axis=1)

    return df_validity


def hourly_bid_ask_spread_depth(df_liquidity, starttime, start_time_depth="30/09/2019 15:00", minute_depth=30):
    """
    This function takes the processed limit order book of one day and its start time and compute the
    hourly bid ask spread

    Args:
        df_liquidity: read dataframe (Pandas DataFrame)
        starttime: date and time of the opening of the intraday market (Eg. "30/09/2019 15:00") (string)
        start_time_depth: starting hour to calculat depth (string)
        minute_depth: number of minutes over which plotting the order book (int)
    Returns:
        output: list: volumes and prices for bid and ask curve (list of lists)

    """

    # convert string like input in timestamp
    start_time = pd.Timestamp(starttime, tz='UTC')

    # obtain end times for hourly like sequence
    end_time = start_time+pd.Timedelta(minute_depth, unit='minutes')

    output = assign_to_time_window_depth(df_liquidity,
                                         start_time,
                                         end_time,
                                         df_liquidity['Start Validity Date'],
                                         df_liquidity['End Validity Date']
                                         )

    return output
