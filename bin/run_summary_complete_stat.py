import glob
import os
import pathlib
from tqdm import tqdm
import pandas as pd
import numpy as np


def macro_analyis(folder_root_path='../data/processed/EPEX_spot_continous_complete_pipeline_2019_21-04-2021 21:54:04'):

    time_ = []
    paths = []

    # skim through folder finding only old data type files
    for filepath in glob.glob(folder_root_path+'/*/*/*.csv', recursive=True):

        # obtain time and path of each file
        t = filepath.split('/')[-1].split('.')[0][-8:]
        time_.append(pd.Timestamp(t))
        paths.append(filepath)

    print(
        f'\n The time frame of analysis is from the {min(time_)} to the {max(time_)}')

    # order the path correctly in time
    ordered_paths = [x for _, x in sorted(zip(time_, paths))]

    # time process
    time_pipeline_process = folder_root_path.split('/')[-1][-24:]

    # create folder
    base_processed_folder = pathlib.Path(
        r'../data/processed') / f'summary_analysis_complete_window_interest_{time_pipeline_process}'
    os.makedirs(base_processed_folder)

    # set monthly quantities
    times = []
    avg_price_base = []
    max_price_base = []
    avg_price_update = []
    max_price_update = []
    avg_price_update_ch_de = []
    max_price_update_ch_de = []
    avg_price_update_de_ch = []
    max_price_update_de_ch = []

    volume_traded = []
    volume_traded_CH_DE = []
    volume_traded_DE_CH = []
    revenue_max_CH_DE = []
    revenue_min_CH_DE = []
    revenue_max_DE_CH = []
    revenue_min_DE_CH = []
    contracts_closed_window = []
    contracts_closed_window_addition_CH_DE = []
    contracts_closed_window_addition_DE_CH = []
    hours_counts = []
    hours_counts_match = []

    hours_volume_CH_DE = []
    hours_volume_DE_CH = []

    for opath in tqdm(ordered_paths):

        df = pd.read_csv(opath)

        # get day
        times.append(pd.Timestamp(opath.split('_')[-1].split('.')[0]))

        # prices
        avg_price_base.append(df['Execution Price'].mean())
        max_price_base.append(df['Execution Price'].max())

        selling_p = df[df['match_binary_outcome_selling'] == 1]['A posteriori Execution Price'].values.tolist(
        )+df[df['match_binary_outcome_selling'] != 1]['Execution Price'].values.tolist()

        pumping_p = df[df['match_binary_outcome_pumping'] == 1]['A posteriori Execution Price'].values.tolist(
        )+df[df['match_binary_outcome_pumping'] != 1]['Execution Price'].values.tolist()

        avg_price_update_ch_de.append(np.mean(selling_p))
        max_price_update_ch_de.append(np.max(selling_p))

        avg_price_update_de_ch.append(np.mean(pumping_p))
        max_price_update_de_ch.append(np.max(pumping_p))

        avg_price_update.append(df['A posteriori Execution Price'].mean())
        max_price_update.append(df['A posteriori Execution Price'].max())

        # volumes
        volume_traded.append(df['Executed Volume'].sum())
        volume_traded_CH_DE.append(
            df[df['match_binary_outcome_selling'] == 1]['Executed Volume'].sum())
        volume_traded_DE_CH.append(
            df[df['match_binary_outcome_pumping'] == 1]['Executed Volume'].sum())

        vol_add_CH_DE = df[df['match_binary_outcome_selling']
                           == 1]['Executed Volume']
        vol_add_DE_CH = df[df['match_binary_outcome_pumping']
                           == 1]['Executed Volume']

        # revenues
        pri_add_CH_DE = df[df['match_binary_outcome_selling']
                           == 1]['Execution Price']
        pri_add_DE_CH = df[df['match_binary_outcome_pumping']
                           == 1]['Execution Price']

        pri_marg_CH_DE = df[df['match_binary_outcome_selling']
                            == 1]['A posteriori Execution Price']
        pri_marg_DE_CH = df[df['match_binary_outcome_pumping']
                            == 1]['A posteriori Execution Price']

        # the concept of maximum and minimum for revenue corresponding to the two flow is always from the swiss perspective
        rev_max_CH_DE = vol_add_CH_DE*pri_add_CH_DE
        rev_min_CH_DE = vol_add_CH_DE*pri_marg_CH_DE
        revenue_max_CH_DE.append(rev_max_CH_DE.sum())
        revenue_min_CH_DE.append(rev_min_CH_DE.sum())

        rev_max_DE_CH = vol_add_DE_CH*pri_add_DE_CH
        rev_min_DE_CH = vol_add_DE_CH*pri_marg_DE_CH
        revenue_max_DE_CH.append(rev_max_DE_CH.sum())
        revenue_min_DE_CH.append(rev_min_DE_CH.sum())

        # n contracts closed
        contracts_closed_window.append(df.shape[0])
        contracts_closed_window_addition_CH_DE.append(
            df[df['match_binary_outcome_selling'] == 1].shape[0])
        contracts_closed_window_addition_DE_CH.append(
            df[df['match_binary_outcome_pumping'] == 1].shape[0])

        # contracts per hour
        hours_count = pd.to_datetime(df['Delivery Start']
                                     ).dt.hour.value_counts().to_dict()

        hours_count_match = pd.to_datetime(df['Delivery Start']
                                           [(df['match_binary_outcome_selling'] == 1) | (df['match_binary_outcome_pumping'] == 1)]).dt.hour.value_counts().to_dict()

        hours_counts.append(hours_count)
        hours_counts_match.append(hours_count_match)

        time_dev_start = pd.to_datetime(df['Delivery Start'])
        CH_DE_volume_hour = dict(df[df['match_binary_outcome_selling'] == 1].groupby(
            time_dev_start.dt.hour)['Executed Volume'].sum())

        DE_CH_volume_hour = dict(df[df['match_binary_outcome_pumping'] == 1].groupby(
            time_dev_start.dt.hour)['Executed Volume'].sum())

        hours_volume_CH_DE.append(CH_DE_volume_hour)
        hours_volume_DE_CH.append(DE_CH_volume_hour)

    df_summary = pd.DataFrame(
        data={
            'time': times,
            'Avg Historical Price': avg_price_base,
            'Max Historical Price': max_price_base,
            'Avg a Posteriori Price': avg_price_update,
            'Max a Posteriori Price': max_price_update,
            'Avg a Posteriori Price CH-DE': avg_price_update_ch_de,
            'Max a Posteriori Price CH-DE': max_price_update_ch_de,
            'Avg a Posteriori Price DE-CH': avg_price_update_de_ch,
            'Max a Posteriori Price DE-CH': max_price_update_de_ch,
            'Total Volume Traded': volume_traded,
            'Total Volume Traded CH-DE': volume_traded_CH_DE,
            'Total Volume Traded DE-CH': volume_traded_DE_CH,
            'CH-DE Revenue Max': revenue_max_CH_DE,
            'CH-DE Revenue Min': revenue_min_CH_DE,
            'DE-CH Revenue Max': revenue_max_DE_CH,
            'DE-CH Revenue Min': revenue_min_DE_CH,
            'Number of Contracts Closed': contracts_closed_window,
            'CH-DE Additional Contracts Closed': contracts_closed_window_addition_CH_DE,
            'DE-CH Additional Contracts Closed': contracts_closed_window_addition_DE_CH,
            'Hours Count': hours_counts,
            'Hours Match Count': hours_counts_match,
            'Hours Volume CH-DE': hours_volume_CH_DE,
            'Hours Volume DE-CH': hours_volume_DE_CH

        }
    )

    summary_name = time_pipeline_process+'_summary.csv'
    df_summary.to_csv(base_processed_folder / summary_name, index=False)


if __name__ == "__main__":
    macro_analyis()
