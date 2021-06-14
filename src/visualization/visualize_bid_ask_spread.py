import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.dates as mdates


def hourly_bid_ask_spread_plot(df_validity):
    """
    This function takes  the hourly bid ask spread and plot it as a time series

    Args:
        df_validity: pandas dataframe with hours of the intraday market and the corresponding
        bid-ask spread (Pandas DataFrame)
    Returns:
        /

    """

    # define hours ticks
    hours = mdates.HourLocator(interval=1)
    h_fmt = mdates.DateFormatter('%H:%M')

    # plot
    fig, ax = plt.subplots(figsize=(15, 10))
    ax.plot(df_validity['Start'], df_validity['Hourly Bid-Ask Spread'])
    ax.set_xlabel('Hour of the day (h) [UTC]')
    ax.set_ylabel('Hourly Bid-Ask Spread')

    # add ticks
    ax.xaxis.set_major_locator(hours)
    ax.xaxis.set_major_formatter(h_fmt)

    ax.legend(fontsize=18)
    ax.tick_params(axis='both', which='major', labelsize=15)

    fig.tight_layout()  # otherwise the right y-label is slightly clipped


def hourly_bid_ask_spread_plot_comparison(df_validity, df_validity_update):
    """
    This function takes  the hourly bid ask spread and plot it as a time series

    Args:
        df_validity: pandas dataframe with hours of the intraday market and the corresponding
        bid-ask spread (Pandas DataFrame)
    Returns:
        /

    """

    # define hours ticks
    hours = mdates.HourLocator(interval=1)
    h_fmt = mdates.DateFormatter('%H:%M')

    # plot
    fig, ax = plt.subplots(figsize=(15, 10))
    ax.plot(df_validity['Start'], df_validity['Hourly Bid-Ask Spread'],
            color='blue', label='Original Bid-Ask Spread')
    ax.plot(df_validity['Start'], df_validity_update['Hourly Bid-Ask Spread'], color='red',
            label='Updated Bid-Ask Spread')
    ax.set_xlabel('Hour of the day (h) [UTC]', size=25)
    ax.set_ylabel('Hourly Bid-Ask Spread', size=25)

    ax.legend(fontsize=18)
    ax.tick_params(axis='both', which='major', labelsize=17)

    # add ticks
    ax.xaxis.set_major_locator(hours)
    ax.xaxis.set_major_formatter(h_fmt)
    ax.xaxis.set_tick_params(rotation=45)

    # fig.tight_layout()  # otherwise the right y-label is slightly clipped
