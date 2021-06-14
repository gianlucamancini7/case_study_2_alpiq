import pandas as pd
import numpy as np


def clean_transactions(x):

    df = x.drop(['Executed Volume_S',
                 'Execution Price_S',
                 'Instrument Type_S',
                 'End Validity Date_S',
                 'Executed Price & Volume_S',
                 'Delivery Start_S',
                 'lead_time_S'], 1)
    df.rename(columns={'Executed Volume_B': 'Executed Volume',
                       'Execution Price_B': 'Execution Price',
                       'Instrument Type_B': 'Instrument Type',
                       'End Validity Date_B': 'End Validity Date',
                       'Executed Price & Volume_B': 'Executed Price & Volume',
                       'Delivery Start_B': 'Delivery Start',
                       'lead_time_B': 'lead_time'
                       }, inplace=True)

    return df


def clean_transactions_new(x):

    df = x.drop(columns=['problem_from_time',
                         'problem_to_time', 'problem_timestamp'])

    return df


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
    # account for new year shift
    df['start_date'].iloc[-1] = df['End Date'].iloc[-2]

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
    NTC['DE to CH_Actual value (MW) update'] = NTC['DE to CH_Actual value (MW)']

    return NTC


def read_pw_file(path):
    df = pd.read_csv(path,
                     sep=';',
                     decimal=".",
                     parse_dates=['VALUE_TIME'],
                     date_parser=lambda col: pd.to_datetime(col,
                                                            utc=True,
                                                            format='%d.%m.%Y %H:%M',
                                                            )
                     )
    return df


def pw_preparation(pw):
    # manipulate "Power Limit" file to obtain the same structure of NTC

    # from hourly to 15 minutes time resolution
    pw_pivoted = pd.pivot_table(pw,
                                values=['Max. von Generation [MWh]', 'Min. von Generation [MWh]',
                                        'Upscale Potential [MWh]', 'Donwnscale Potential'],
                                index=['VALUE_TIME'],
                                aggfunc=list,
                                ).apply(pd.Series.explode).sort_index()

    pw_resampled = pw_pivoted.resample('15T', convention='start').ffill()

    # restore normal range index
    pw_resampled = pw_resampled.reset_index()

    # create column start_time and end_time for the optimizer

    pw_resampled['start_time'] = pw_resampled['VALUE_TIME']
    pw_resampled['end_time'] = pw_resampled['VALUE_TIME'] + \
        pd.to_timedelta(15, unit='minutes')

    # create a column to store update capacity
    pw_resampled['Selling Actual value update [MW]'] = pw_resampled['Upscale Potential [MWh]']
    pw_resampled['Pumping Actual value update [MW]'] = pw_resampled['Donwnscale Potential']

    # drop unsued columns and rename columns with correct units
    pw_resampled['Upscale Potential [MW]'] = pw_resampled['Upscale Potential [MWh]']
    pw_resampled['Donwnscale Potential [MW]'] = pw_resampled['Donwnscale Potential']

    pw_resampled.drop(columns=['Max. von Generation [MWh]',
                               'Min. von Generation [MWh]',
                               'Donwnscale Potential',
                               'Upscale Potential [MWh]'
                               ], inplace=True)

    return pw_resampled


def optimize_selling(NTC, pw, ex_vol, time, instru_type, p_match):

    # check in the first place whether the contract was matchable according to marginal price of hydro considerations
    if p_match:

        multiplier_instr_type = {'Hour': 1, 'Half Hour': 2, 'Quarter Hour': 4}

        # get the corresponding index for NTC and Power DFs
        index_NTC = NTC[(NTC['start_time'] >= time) & (NTC['end_time'] <= time +
                                                       pd.Timedelta(60/multiplier_instr_type[instru_type], unit='min'))].index
        index_pw = pw[(pw['start_time'] >= time) & (pw['end_time'] <= time +
                                                    pd.Timedelta(60/multiplier_instr_type[instru_type], unit='min'))].index

        # check the difference_selling
        diff_NTC = np.array([NTC['CH to DE_Actual value (MW) update'].iloc[i] -
                             ex_vol*multiplier_instr_type[instru_type] for i in index_NTC])
        diff_pw = np.array([pw['Selling Actual value update [MW]'].iloc[i] -
                            ex_vol*multiplier_instr_type[instru_type] for i in index_pw])

        # update the value

        # check that NTC and ramping power constraints are not binding
        if np.product(diff_NTC >= 0) and np.product(diff_pw >= 0):
            NTC['CH to DE_Actual value (MW) update'].iloc[index_NTC] = diff_NTC
            pw['Selling Actual value update [MW]'].iloc[index_pw] = diff_pw

            return 1

        # check that NTC is binding while ramping power constraints is not binding
        elif np.product(diff_NTC < 0) and np.product(diff_pw >= 0):
            NTC['CH to DE_Actual value (MW) update'].iloc[index_NTC] = [
                0]*len(diff_NTC)
            pw['Selling Actual value update [MW]'].iloc[index_pw] = diff_pw
            return 2

        # check that NTC not is binding while ramping power constraints is binding
        elif np.product(diff_NTC >= 0) and np.product(diff_pw < 0):
            NTC['CH to DE_Actual value (MW) update'].iloc[index_NTC] = diff_NTC
            pw['Selling Actual value update [MW]'].iloc[index_pw] = [
                0]*len(diff_pw)
            return 3

        # check whether both conditions are binding
        else:
            NTC['CH to DE_Actual value (MW) update'].iloc[index_NTC] = [
                0]*len(diff_NTC)
            pw['Selling Actual value update [MW]'].iloc[index_pw] = [
                0]*len(diff_pw)
            return 4
    else:
        return 0


def optimize_pumping(NTC, pw, ex_vol, time, instru_type, p_match):

    # check in the first place whether the contract was matchable according to marginal price of hydro considerations
    if p_match:

        multiplier_instr_type = {'Hour': 1, 'Half Hour': 2, 'Quarter Hour': 4}

        # get the corresponding index for NTC and Power DFs
        index_NTC = NTC[(NTC['start_time'] >= time) & (NTC['end_time'] <= time +
                                                       pd.Timedelta(60/multiplier_instr_type[instru_type], unit='min'))].index
        index_pw = pw[(pw['start_time'] >= time) & (pw['end_time'] <= time +
                                                    pd.Timedelta(60/multiplier_instr_type[instru_type], unit='min'))].index

        # check the difference_selling
        diff_NTC = np.array([NTC['DE to CH_Actual value (MW) update'].iloc[i] -
                             ex_vol*multiplier_instr_type[instru_type] for i in index_NTC])
        diff_pw = np.array([pw['Pumping Actual value update [MW]'].iloc[i] -
                            ex_vol*multiplier_instr_type[instru_type] for i in index_pw])

        # update the value
        # check that NTC and ramping power constraints are not binding
        if np.product(diff_NTC >= 0) and np.product(diff_pw >= 0):
            NTC['DE to CH_Actual value (MW) update'].iloc[index_NTC] = diff_NTC
            pw['Pumping Actual value update [MW]'].iloc[index_pw] = diff_pw

            return 1

        # check that NTC is binding while ramping power constraints is not binding
        elif np.product(diff_NTC < 0) and np.product(diff_pw >= 0):
            NTC['DE to CH_Actual value (MW) update'].iloc[index_NTC] = [
                0]*len(diff_NTC)
            pw['Pumping Actual value update [MW]'].iloc[index_pw] = diff_pw
            return 2

        # check that NTC not is binding while ramping power constraints is binding
        elif np.product(diff_NTC >= 0) and np.product(diff_pw < 0):
            NTC['DE to CH_Actual value (MW) update'].iloc[index_NTC] = diff_NTC
            pw['Pumping Actual value update [MW]'].iloc[index_pw] = [
                0]*len(diff_pw)
            return 3

        # check whether both conditions are binding
        else:
            NTC['DE to CH_Actual value (MW) update'].iloc[index_NTC] = [
                0]*len(diff_NTC)
            pw['Pumping Actual value update [MW]'].iloc[index_pw] = [
                0]*len(diff_pw)
            return 4

    else:
        return 0


def update_execution_price(binary_outcome_s, binary_outcome_p, marginal_price_s, marginal_price_p, execution_price):

    if binary_outcome_s == 1 and binary_outcome_p == 0:

        return marginal_price_s

    elif binary_outcome_s == 0 and binary_outcome_p == 1:

        return marginal_price_p

    else:

        return execution_price


def match_transactions_both_sides(pivoted_levels, NTC, wp, power_lim):

    # sort the pivoted df in ascending way - useful to match pumping
    pivoted_levels_sort = pivoted_levels.sort_values(
        by=['Execution Price'], ascending=True)

    # this is the first date of the day, it is then used to find the week for the price
    # change pumping_threshold value to set the percentage of marginal cost for pumping

    pumping_threshold = 0.7
    date = pivoted_levels['End Validity Date'].iloc[0]
    weekly_price = [wp['Average Weekly Price [Euro/MWh]'][(wp['start_date'] < date) &
                                                          (wp['End Date'] >= date)].item(), pumping_threshold*wp['Average Weekly Price [Euro/MWh]'][(wp['start_date'] < date) &
                                                                                                                                                    (wp['End Date'] >= date)].item()]
    # do not account for contracts lower than weekly price for selling
    # do not account for contracts higher than pumping price for pumping
    pivoted_levels_sort['weekly_hydro_marginal_price_selling'] = weekly_price[0]
    pivoted_levels_sort['weekly_hydro_marginal_price_pumping'] = weekly_price[1]

    pivoted_levels_sort['possible_match_selling'] = pivoted_levels_sort['Execution Price'] >= weekly_price[0]
    pivoted_levels_sort['possible_match_pumping'] = pivoted_levels_sort['Execution Price'] <= weekly_price[1]

    # match between possible contracts, NTC and power capacity for pumping
    pivoted_levels_sort['match_binary_outcome_pumping'] = pivoted_levels_sort.apply(lambda x: optimize_pumping(NTC, power_lim,
                                                                                                               x['Executed Volume'],
                                                                                                               x['Delivery Start'],
                                                                                                               x['Instrument Type'],
                                                                                                               x['possible_match_pumping']), axis=1)

    # sort the df in a descending way - useful to match selling
    pivoted_levels_sort = pivoted_levels_sort.sort_values(
        by=['Execution Price'], ascending=False)

    pivoted_levels_sort['match_binary_outcome_selling'] = pivoted_levels_sort.apply(lambda x: optimize_selling(NTC, power_lim,
                                                                                                               x['Executed Volume'],
                                                                                                               x['Delivery Start'],
                                                                                                               x['Instrument Type'],
                                                                                                               x['possible_match_selling']), axis=1)

    # add column with updated execution price N.B. marginal
    pivoted_levels_sort['A posteriori Execution Price'] = pivoted_levels_sort.apply(
        lambda x: update_execution_price(x['match_binary_outcome_selling'], x['match_binary_outcome_pumping'], x['weekly_hydro_marginal_price_selling'], x['weekly_hydro_marginal_price_pumping'], x['Execution Price']), axis=1)

    # eventually sort the table in time order
    pivoted_levels_sort.sort_values(by='End Validity Date', inplace=True)

    return pivoted_levels_sort
