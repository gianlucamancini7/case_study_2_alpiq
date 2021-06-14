import glob
import os
import pathlib
from tqdm import tqdm
import pandas as pd
import numpy as np


def macro_analyis(folder_root_path='../data/processed/EPEX_spot_continous_complete_pipeline_2019_17-04-2021 18:38:10'):

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
        r'../data/processed') / f'summary_analysis_hystorical_transactions_{time_pipeline_process}'
    os.makedirs(base_processed_folder)

    # set monthly quantities
    times = []
    avg_price_base = []
    max_price_base = []
    volume_traded = []
    contracts_closed_window = []
    hours_counts = []
    hours_counts_match = []

    for opath in tqdm(ordered_paths):

        df = pd.read_csv(opath)

        # get day
        times.append(pd.Timestamp(opath.split('_')[-1].split('.')[0]))

        # prices
        avg_price_base.append(df['Execution Price'].mean())
        max_price_base.append(df['Execution Price'].max())

        # volumes
        volume_traded.append(df['Executed Volume'].sum())

        # n contracts closed
        contracts_closed_window.append(df.shape[0])

        # contracts per hour
        hours_count = pd.to_datetime(df['Delivery Start']
                                     ).dt.hour.value_counts().to_dict()

        hours_counts.append(hours_count)

    df_summary = pd.DataFrame(
        data={
            'time': times,
            'Avg Historical Price': avg_price_base,
            'Max Historical Price': max_price_base,
            'Total Volume Traded': volume_traded,
            'Number of Contracts Closed': contracts_closed_window,
            'Hours Count': hours_counts,
        }
    )

    summary_name = time_pipeline_process+'_summary.csv'
    df_summary.to_csv(base_processed_folder / summary_name, index=False)


if __name__ == "__main__":
    macro_analyis()
