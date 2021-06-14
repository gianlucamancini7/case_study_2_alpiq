import glob
import os
import pathlib
from tqdm import tqdm
import pandas as pd


def macro_analyis(folder_root_path='../data/processed/EPEX_spot_continous_baseline_pipeline_2019_14-03-2021 21:00:40'):

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
        r'../data/processed') / f'summary_analysis_baseline_window_interest_{time_pipeline_process}'
    os.makedirs(base_processed_folder)

    # set monthly quantities
    times = []
    avg_price_base = []
    max_price_base = []
    avg_price_update = []
    max_price_update = []
    volume_traded = []
    volume_traded_CH_DE = []
    revenue_max = []
    revenue_min = []
    contracts_closed_window = []
    contracts_closed_window_addition_CH_DE = []
    hours_counts = []
    hours_counts_match = []

    for opath in tqdm(ordered_paths):

        df = pd.read_csv(opath)

        # get day
        times.append(pd.Timestamp(opath.split('_')[-1].split('.')[0]))

        # prices
        avg_price_base.append(df['Execution Price'].mean())
        max_price_base.append(df['Execution Price'].max())
        avg_price_update.append(df['A posteriori Execution Price'].mean())
        max_price_update.append(df['A posteriori Execution Price'].max())

        # volumes
        volume_traded.append(df['Executed Volume'].sum())
        volume_traded_CH_DE.append(
            df[df['match_binary_outcome'] == 1]['Executed Volume'].sum())
        vol_add = df[df['match_binary_outcome'] == 1]['Executed Volume']

        # revenues
        pri_add = df[df['match_binary_outcome'] == 1]['Execution Price']
        pri_marg = df[df['match_binary_outcome']
                      == 1]['A posteriori Execution Price']
        rev_max = vol_add*pri_add
        rev_min = vol_add*pri_marg
        revenue_max.append(rev_max.sum())
        revenue_min.append(rev_min.sum())

        # n contracts closed
        contracts_closed_window.append(df.shape[0])
        contracts_closed_window_addition_CH_DE.append(
            df[df['match_binary_outcome'] == 1].shape[0])

        # contracts per hour
        hours_count = pd.to_datetime(df['Delivery Start']
                                     ).dt.hour.value_counts().to_dict()

        hours_count_match = pd.to_datetime(df['Delivery Start']
                                           [df['match_binary_outcome'] == 1]).dt.hour.value_counts().to_dict()

        hours_counts.append(hours_count)
        hours_counts_match.append(hours_count_match)

    df_summary = pd.DataFrame(
        data={
            'time': times,
            'Avg Historical Price': avg_price_base,
            'Max Historical Price': max_price_base,
            'Avg a Posteriori Price': avg_price_update,
            'Max a Posteriori Price': max_price_update,
            'Total Volume Traded': volume_traded,
            'Total Volume Traded CH-DE': volume_traded_CH_DE,
            'CH-DE Revenue Max': revenue_max,
            'CH-DE Revenue Min': revenue_min,
            'Number of Contracts Closed': contracts_closed_window,
            'Additional Contracts Closed': contracts_closed_window_addition_CH_DE,
            'Hours Count': hours_counts,
            'Hours Match Count': hours_counts_match
        }
    )

    summary_name = time_pipeline_process+'_summary.csv'
    df_summary.to_csv(base_processed_folder / summary_name, index=False)


if __name__ == "__main__":
    macro_analyis()
