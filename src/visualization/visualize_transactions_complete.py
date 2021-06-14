# import relevant modules
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sbn


def executed_transactions_bar_chart(pivoted_levels, plot=True, return_updated_transactions=False, new_data_type=False, side='CH-DE'):
    """

    This function plot the number of executed transactions in the time window of interest

    Args:
        pivoted_levels: pivoted table showing transactions matched (Pandas DataFrame)
        plot: defining whether to plot or only return organized dataset (bool)
        new_data_type: defining whether the input is a new or old data file (bool)
        side: indication of whether returning CH-DE (turbing) or DE-CH (pumping) transactions (string)
    Return:
        data_base: number of executed transactions per hour (Pandas DataFrame)
        data_updated: number of CH-DE executed transactions per hour with shorter lead-time (Pandas DataFrame)
    """
    binary_outcome = 'match_binary_outcome_selling' if side == 'CH-DE' else 'match_binary_outcome_pumping'
    # get column for hours
    pivoted_levels['Transaction Time Hour'] = pd.to_datetime(
        pivoted_levels['End Validity Date']).dt.hour

    if return_updated_transactions:
        data_base = pivoted_levels['Transaction Time Hour'].value_counts(
        ).sort_index()

        data_updated = pivoted_levels[pivoted_levels[binary_outcome] == 1]['Transaction Time Hour'].value_counts(
        ).sort_index()

        # plot
        fig, ax = plt.subplots(figsize=(15, 10))
        ax.bar(data_base.index, data_base.values, color='blue',
               label='Historical Transactions in Time Window')
        ax.bar(data_updated.index, data_updated.values, color='red',
               label=side+' Matched Historical Transactions in Time Window')
        ax.set_xlabel('Hour of the day (h) [UTC]', size=15)
        ax.set_ylabel(side+' closed transactions in time window', size=15)

        ax.legend(fontsize=18)
        ax.tick_params(axis='both', which='major', labelsize=15)

        return data_base, data_updated

    else:
        data_base = pivoted_levels['Transaction Time Hour'].value_counts(
        ).sort_index()

        # plot
        fig, ax = plt.subplots(figsize=(15, 10))
        ax.bar(data_base.index, data.values)
        ax.set_xlabel('Hour of the day (h) [UTC]')
        ax.set_ylabel(side+' closed transactions in time window')

        ax.legend(fontsize=18)
        ax.tick_params(axis='both', which='major', labelsize=15)

        return data_base


def executed_transactions_heatmap_summary(pivoted_levels, plot=True, return_updated_transactions=False, price_volume_p=True, new_data_type=False):
    """

    This function plot a summary heatmap of the daily transactions

    Args:
        pivoted_levels: pivoted table showing transactions matched (Pandas DataFrame)
        plot: defining whether to plot or only return organized dataset (bool)
        price_volume_p: defining whether to plot statistics about volumes or prices (bool)
        new_data_type: defining whether the input is a new or old data file (bool)
    Return:
        daily_execution_price_stat: price hourly summary statistics of executed transactions (Pandas DataFrame)
        daily_execution_volume_stat: volume hourly summary statistics of executed transactions (Pandas DataFrame)
        daily_execution_price_stat_marginal: price hourly summary statistics of executed transactions at Hydro marginal price (Pandas DataFrame)
    """

    # get column for hours
    pivoted_levels['Transaction Time Hour [UTC]'] = pd.to_datetime(
        pivoted_levels['End Validity Date']).dt.hour

    # aggregate by end validity date hour ( execution time )
    agg_hour = pivoted_levels[['Transaction Time Hour [UTC]', 'Execution Price',
                               'Executed Volume', 'A posteriori Execution Price']].groupby(by='Transaction Time Hour [UTC]').aggregate(list)

    daily_execution_price_stat = agg_hour['Execution Price'].apply(lambda x: np.percentile(
        x, [25, 50, 75]).tolist()+[np.mean(x), min(x), max(x)]).apply(pd.Series)

    daily_execution_price_stat_marginal = agg_hour['A posteriori Execution Price'].apply(lambda x: np.percentile(
        x, [25, 50, 75]).tolist()+[np.mean(x), min(x), max(x)]).apply(pd.Series)

    # rename columns
    daily_execution_price_stat.rename(columns={0: 'execution price 25%',
                                               1: 'execution price 50%',
                                               2: 'execution price 75%',
                                               3: ' mean execution price',
                                               4: ' min execution price',
                                               5: ' max execution price'}, inplace=True)

    # rename columns
    daily_execution_price_stat_marginal.rename(columns={0: 'execution price 25%',
                                                        1: 'execution price 50%',
                                                        2: 'execution price 75%',
                                                        3: ' mean execution price',
                                                        4: ' min execution price',
                                                        5: ' max execution price'}, inplace=True)

    daily_execution_volume_stat = agg_hour['Executed Volume'].apply(lambda x: np.percentile(
        x, [25, 50, 75]).tolist()+[np.mean(x), min(x), max(x)]).apply(pd.Series)
    daily_execution_volume_stat.rename(columns={0: 'execution volume 25%',
                                                1: 'execution volume 50%',
                                                2: 'execution volume 75%',
                                                3: ' mean volume price',
                                                4: ' min volume price',
                                                5: ' max volume price'}, inplace=True)

    # plot
    if plot:
        if return_updated_transactions:
            sbn.heatmap(daily_execution_price_stat_marginal)

        else:

            if price_volume_p:
                sbn.heatmap(daily_execution_price_stat)

            else:
                sbn.heatmap(daily_execution_volume_stat)

    return daily_execution_price_stat, daily_execution_volume_stat, daily_execution_price_stat_marginal


def executed_transactions_time_series(pivoted_levels, plot=True, output_series_='exec_price', rolling_time='1H', new_data_type=False):
    """

    This function plot the number of executed transactions in the time window of interest

    Args:
        pivoted_levels: pivoted table showing transactions matched (Pandas DataFrame)
        plot: defining whether to plot or only return organized dataset (bool)
        output_series: indication of what to plot in time (string) [exec_price, moving_avg_exec_price_updated_transactions_comparison, exec_price_updated_transactions_comparison, exec_volume, moving_avg_exec_price, moving_avg_exec_volume, moving_max_price, moving_min_price]
        rolling_time: strinf indicating the number of hours to find the moving averages one (string)
        new_data_type: defining whether the input is a new or old data file (bool)
    Return:
        time: time of analysis ( np.array )
        output_series: output series as indicated (np.array ) or list of arrays in case of comparison
    """

    # ensure to get time series
    pivoted_levels['End Validity Date'] = pd.to_datetime(
        pivoted_levels['End Validity Date'])

    t = pivoted_levels['End Validity Date']

    # set spread to None by default
    spread_b, spread_a = None, None

    if output_series_ == 'exec_price':

        output_series = pivoted_levels['Execution Price']
        spread_b = pivoted_levels['Price_B']
        spread_s = pivoted_levels['Price_S']
        output_series_name = 'price €'

    elif output_series_ == 'moving_avg_exec_price_updated_transactions_comparison':

        output_series_b = pivoted_levels.set_index(
            'End Validity Date')['Execution Price'].rolling(rolling_time).mean()

        output_series_u = pivoted_levels.set_index(
            'End Validity Date')['A posteriori Execution Price'].rolling(rolling_time).mean()

        output_series = [output_series_b, output_series_u]

        output_series_name = 'Moving average price ['+rolling_time+'] €'

    elif output_series_ == 'exec_price_updated_transactions_comparison':

        output_series_b = pivoted_levels['Execution Price']

        output_series_u = pivoted_levels['A posteriori Execution Price']

        output_series = [output_series_b, output_series_u]

        output_series_name = 'Moving average price ['+rolling_time+'] €'

    elif output_series_ == 'exec_volume':

        output_series = pivoted_levels['Executed Volume']
        spread_b = pivoted_levels['Volume_B']
        spread_s = pivoted_levels['Volume_S']
        output_series_name = 'volume MWh'

    elif output_series_ == 'moving_avg_exec_price':
        output_series = pivoted_levels.set_index(
            'End Validity Date')['Execution Price'].rolling(rolling_time).mean()
        output_series_name = 'moving average price ['+rolling_time+'] €'

    elif output_series_ == 'moving_avg_exec_volume':
        output_series = pivoted_levels.set_index(
            'End Validity Date')['Executed Volume'].rolling(rolling_time).mean()
        output_series_name = 'moving average volume ['+rolling_time+'] MWh'

    elif output_series_ == 'moving_max_price':
        output_series = pivoted_levels.set_index(
            'End Validity Date')['Execution Price'].rolling(rolling_time).max()
        output_series_name = 'moving average volume ['+rolling_time+'] MWh'

    elif output_series_ == 'moving_min_price':
        output_series = pivoted_levels.set_index(
            'End Validity Date')['Execution Price'].rolling(rolling_time).min()
        output_series_name = 'moving average volume ['+rolling_time+'] MWh'

    # plotting

    # define hours ticks
    hours = mdates.HourLocator(interval=1)
    h_fmt = mdates.DateFormatter('%H:%M:%S')

    if plot:
        # initiate plot
        fig, ax1 = plt.subplots(figsize=(15, 10))

        # set title
        # ax1.set_title(
        #     'Limit Order Daily Price-Volumes behaviour on Window of Interest')

        if output_series_ == 'exec_price_updated_transactions_comparison' or output_series_ == 'moving_avg_exec_price_updated_transactions_comparison':

            ax1.set_xlabel('time (h) [UTC]', size=25)
            ax1.set_ylabel(output_series_name, size=25)
            ax1.plot(t, output_series_b, color='red',
                     label='Original Price Level')
            ax1.plot(t, output_series_u, color='blue',
                     label='Max Variation Updated Price Level')
            ax1.legend()

        else:

            ax1.set_xlabel('time (h) [UTC]', size=15)
            ax1.set_ylabel(output_series_name, size=15)
            ax1.plot(t, output_series, color='red')

        if type(spread_b) != type(None):
            # plot price and volume bid ask difference
            plt.fill_between(t, spread_s.apply(pd.to_numeric),
                             spread_b.apply(pd.to_numeric), color='k', alpha=.4)

        # add ticks
        ax1.xaxis.set_major_locator(hours)
        ax1.xaxis.set_major_formatter(h_fmt)

        fig.autofmt_xdate()

        ax1.legend(fontsize=22)
        ax1.tick_params(axis='both', which='major', labelsize=20)

        fig.tight_layout()  # otherwise the right y-label is slightly clipped
        plt.show()

    return t, output_series


def update_price_dash(exec_price, post_exec_price, match):

    if match == 1:
        return post_exec_price
    else:
        return exec_price


def executed_transactions_time_series_dashboard(pivoted_levels,  which_effect='both'):
    """

    This function plot the number of executed transactions in the time window of interest

    Args:
        pivoted_levels: pivoted table showing transactions matched (Pandas DataFrame)
        which_effect: indication of which price effect to show (string) [ch_de, de_ch, both]
    Return:
        time: time of analysis ( np.array )
        output_series: output series as indicated (np.array ) or list of arrays in case of comparison
    """

    # ensure to get time series
    pivoted_levels['End Validity Date'] = pd.to_datetime(
        pivoted_levels['End Validity Date'])

    t = pivoted_levels['End Validity Date']

    if which_effect == 'both':

        output_series_b = pivoted_levels['Execution Price']

        output_series_u = pivoted_levels['A posteriori Execution Price']

        output_series = [output_series_b, output_series_u]

    elif which_effect == 'ch_de':

        output_series_b = pivoted_levels['Execution Price']

        output_series_u = pivoted_levels.apply(
            lambda x: update_price_dash(x['Execution Price'], x['A posteriori Execution Price'], x['match_binary_outcome_selling']), axis=1)

        output_series = [output_series_b, output_series_u]

    elif which_effect == 'de_ch':

        output_series_b = pivoted_levels['Execution Price']

        output_series_u = pivoted_levels.apply(
            lambda x: update_price_dash(x['Execution Price'], x['A posteriori Execution Price'], x['match_binary_outcome_pumping']), axis=1)

        output_series = [output_series_b, output_series_u]

    return t, output_series
