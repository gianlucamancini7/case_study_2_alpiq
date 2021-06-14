import pandas as pd
import numpy as np


def clean_transactions(x):

    # check that instrument type of buy and sell is the same
    check = x['Instrument Type_S'] == x['Instrument Type_B']
    if len(check.unique()) == 1:

        df = x.drop(['Executed Volume_S', 'Execution Price_S',
                     'Instrument Type_S'], 1)
        df.rename(columns={'Executed Volume_B': 'Executed Volume',
                           'Execution Price_B': 'Execution Price',
                           'Instrument Type_B': 'Instrument Type'
                           }, inplace=True)

        return df

    else:
        print(f'\n An error as occured: the instrument type of at least one buy and sell order is different')


def read_weekly_prices_file(path):
    df = pd.read_csv(path,
                     sep=';',
                     decimal=",",
                     parse_dates=['End Date'],
                     date_parser=lambda col: pd.to_datetime(col,
                                                            utc=True,
                                                            format='%d/%m/%Y %H:%M',
                                                            ),
                     nrows=None,
                     encoding="ISO-8859-1"
                     )
    df['start_date'] = df['End Date']-pd.Timedelta(7, unit='days')

    return df


def read_NTC_file(path):
    df = pd.read_csv(path,
                     sep=',',
                     decimal=".",
                     parse_dates=['Date from'],
                     date_parser=lambda col: pd.to_datetime(col,
                                                            utc=True,
                                                            format='%d.%m.%Y',
                                                            )
                     )
    return df


def NTC_preparation(NTC):

    # START TIME
    NTC['Time from hour'] = NTC['Time from'].apply(
        lambda x: int(x.split(':')[0]))
    NTC['Time from min'] = NTC['Time from'].apply(
        lambda x: int(x.split(':')[1]))
    pd.to_timedelta(NTC['Time from hour'], unit='hours') + \
        pd.to_timedelta(NTC['Time from min'], unit='minutes')
    NTC['start_time'] = NTC['Date from']+pd.to_timedelta(
        NTC['Time from hour'], unit='hours')+pd.to_timedelta(NTC['Time from min'], unit='minutes')

    # END TIME
    NTC['Time to hour'] = NTC['Time to'].apply(lambda x: int(x.split(':')[0]))
    NTC['Time to min'] = NTC['Time to'].apply(lambda x: int(x.split(':')[1]))
    NTC['Time to hour'].loc[(NTC['Time to hour'] == 0) &
                            (NTC['Time to min'] == 0)] = 24
    pd.to_timedelta(NTC['Time to hour'], unit='hours') + \
        pd.to_timedelta(NTC['Time to min'], unit='minutes')
    NTC['end_time'] = NTC['Date from']+pd.to_timedelta(
        NTC['Time to hour'], unit='hours')+pd.to_timedelta(NTC['Time to min'], unit='minutes')

    # create a column to store update capacity
    NTC['CH to DE_Actual value (MW) update'] = NTC['CH to DE_Actual value (MW)']

    return NTC


def optimize(NTC, ex_vol, time, instru_type, p_match):

    # check in the first place whether the contract was matchable according to marginal price of hydro considerations
    if p_match:

        multiplier_instr_type = {'Hour': 1, 'Half Hour': 2, 'Quarter Hour': 4}

        # get the corresponding index
        index = NTC[(NTC['start_time'] == time) & (NTC['end_time'] == time +
                                                   pd.Timedelta(60/multiplier_instr_type[instru_type], unit='min'))].index

        # check the difference
        diff = np.array([NTC['CH to DE_Actual value (MW) update'].iloc[i] -
                         ex_vol*multiplier_instr_type[instru_type] for i in index])

        # update the value
        if np.product(diff >= 0):
            NTC['CH to DE_Actual value (MW) update'].iloc[index] = diff

            return 1
        else:
            NTC['CH to DE_Actual value (MW) update'].iloc[index] = [
                0]*len(diff)

            return 0
    else:
        return 0


def update_execution_price(binary_outcome, marginal_price, execution_price):

    if binary_outcome == 1:

        return marginal_price

    else:

        return execution_price


def match_transactions(pivoted_levels, NTC, wp):

    # sort the pivoted file
    pivoted_levels_sort = pivoted_levels.sort_values(
        by=['Execution Price'], ascending=False)

    # riccardo TO DO: implement code for DE-CH transactions and, after,  make clear with comments which part of this function is doing CH-DE and which on DE-CH

    ##############################

    ##############################

    # this is the first date of the day, it is then used to find the week for the price
    date = pivoted_levels['End Validity Date'].iloc[0]
    weekly_price = [wp['Average Weekly Price [Euro/MWh]'][(wp['start_date'] < date) &
                                                          (wp['End Date'] >= date)].item(), wp['Max Weekly Pumping Price [Euro/MWh]'][(wp['start_date'] < date) &
                                                                                                                                      (wp['End Date'] >= date)].item()]

    # do not account for contracts lower thank weekly price
    pivoted_levels_sort['weekly_hydro_marginal_price'] = weekly_price[0]
    pivoted_levels_sort['possible_match'] = pivoted_levels_sort['Execution Price'] >= weekly_price[0]

    pivoted_levels_sort['match_binary_outcome'] = pivoted_levels_sort.apply(lambda x: optimize(NTC,
                                                                                               x['Executed Volume'],
                                                                                               x['Delivery Start'],
                                                                                               x['Instrument Type'],
                                                                                               x['possible_match']
                                                                                               ), axis=1)
    # add column with updated execution price
    pivoted_levels_sort['A posteriori Execution Price'] = pivoted_levels_sort.apply(
        lambda x: update_execution_price(x['match_binary_outcome'], x['weekly_hydro_marginal_price'], x['Execution Price']), axis=1)

    # riccardo TO DO: add other columns with possible other prices that could be closed

    ##############################

    ##############################

    # eventually sort the table in time order
    pivoted_levels_sort.sort_values(by='End Validity Date', inplace=True)

    return pivoted_levels_sort
