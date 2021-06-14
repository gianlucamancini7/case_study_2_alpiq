import glob
import os
import pathlib
from tqdm import tqdm
import pandas as pd
import time
from datetime import datetime

from src.data.helper_closed_transactions import read_epex_file, filter_lead_time, extract_transactions, prepare_new_transactions
from src.data.welfare_complete import clean_transactions, clean_transactions_new, read_weekly_prices_file, read_NTC_file, NTC_preparation, match_transactions_both_sides, read_pw_file, pw_preparation


def complete_pipeline(folder_root_path='../data/external/prepared_EPEX_2019_Nov_Dec'):

    tic = time.time()

    # load static data

    # load weekly hydro prices
    wp = read_weekly_prices_file(
        "../data/external/Hydro Generation and Price_CH_2019.csv")

    # load NTC
    NTC = read_NTC_file("../data/external/NTC_DEandCH_2019.csv")
    NTC = NTC_preparation(NTC)

    # load power limit data
    power_lim = read_pw_file(
        "../data/external/Hydro Generation up- downscale Potential_CH_2019.csv")
    power_lim = pw_preparation(power_lim)

    time_ = []
    paths = []

    # skim through folder finding only old data type files
    for filepath in glob.glob(folder_root_path+'/ID_GDM_*.csv', recursive=True):

        # obtain time and path of each file
        t = filepath.split('/')[-1].split('.')[0][-8:]
        time_.append(pd.Timestamp(t))
        paths.append(filepath)

    print(
        f'\n The time frame of analysis is from the {min(time_)} to the {max(time_)}')

    # order the path correctly in time
    ordered_paths = [x for _, x in sorted(zip(time_, paths))]

    # time process
    time_pipeline_process = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

    # create interim folder
    base_interim_folder = pathlib.Path(
        r'../data/interim') / f'ALPIQ_transactions_complete_pipeline_2019_{time_pipeline_process}'

    base_processed_folder = pathlib.Path(
        r'../data/processed') / f'ALPIQ_transactions_complete_pipeline_2019_{time_pipeline_process}'
    os.makedirs(base_interim_folder)

    for opath in tqdm(ordered_paths):

        f_m = opath.split('/')[-1].split('_')[-1].split('.')[0]
        folder_month = f_m[:-4]+'-'+f_m[-4:-2]

        folder_name_df_transactions = 'Transactions'
        folder_name_updated_transactions = 'Updated Transactions'

        #### Daily Transaction Preparation ####

        pivoted_levels_list, file_names = prepare_new_transactions(opath)

        for pivoted_levels, file_name in zip(pivoted_levels_list, file_names):

            # save files to csv
            if os.path.isdir(base_interim_folder / folder_month):

                pivoted_levels.to_csv(base_interim_folder / folder_month /
                                      folder_name_df_transactions / file_name, index=False)

            else:

                os.makedirs(base_interim_folder / folder_month)

                os.makedirs(base_interim_folder /
                            folder_month / folder_name_df_transactions)

                pivoted_levels.to_csv(base_interim_folder / folder_month /
                                      folder_name_df_transactions / file_name, index=False)

            #### Welfare Model ####
            pivoted_levels = clean_transactions_new(pivoted_levels)
            pivoted_levels_updated = match_transactions_both_sides(
                pivoted_levels, NTC, wp, power_lim)

            #### Save Files to csv ####
            if os.path.isdir(base_processed_folder / folder_month):

                pivoted_levels_updated.reset_index().to_csv(base_processed_folder / folder_month /
                                                            folder_name_updated_transactions / file_name, index=False)

            else:

                os.makedirs(base_processed_folder / folder_month)

                os.makedirs(base_processed_folder /
                            folder_month / folder_name_updated_transactions)

                pivoted_levels_updated.reset_index().to_csv(base_processed_folder / folder_month /
                                                            folder_name_updated_transactions / file_name, index=False)

    toc = time.time()
    print(
        f'\n Reading, processing and deriving the possible transactions completely takes {toc-tic} seconds')


if __name__ == "__main__":
    complete_pipeline()
