import glob
import os
import pathlib
from tqdm import tqdm
import pandas as pd
import time
from datetime import datetime

from src.data.helper_closed_transactions import read_epex_file, filter_lead_time, extract_transactions
from src.data.welfare_complete import clean_transactions, read_weekly_prices_file, read_NTC_file, NTC_preparation, match_transactions_both_sides, read_pw_file, pw_preparation


def run_historical_transaction(new_data_type=False, folder_root_path='../data/external/EPEX_spot_continous_2019'):

    tic = time.time()

    if new_data_type:
        print("New type data analysis not implemented yet")

    else:

        time_ = []
        paths = []

        # skim through folder finding only old data type files
        for filepath in glob.glob(folder_root_path+'/*/DE *.csv', recursive=True):

            # obtain time and path of each file
            t = filepath.split('/')[-1].split('.')[0][-8:]
            time_.append(pd.Timestamp(t))
            paths.append(filepath)

        print(
            f'\n The time frame of analysis is from the {min(time_)} to the {max(time_)}')

        # order the path correctly in time
#         ordered_paths=[x for _,x in sorted(zip(time_,paths))]

        ordered_paths = [x for _, x in sorted(zip(time_, paths))]

        # time process
        time_pipeline_process = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

        # create interim folder
        base_interim_folder = pathlib.Path(
            r'../data/interim') / f'EPEX_spot_transaction_derivation_pipeline_2019_{time_pipeline_process}'

        os.makedirs(base_interim_folder)

        for opath in tqdm(ordered_paths):

            file_name = 'DE_'+opath.split('/')[-1].split(' ')[-1]
            folder_month = opath.split('/')[4].split(' ')[-1]
            folder_name_df_filtered = 'Filtered Orders'
            folder_name_df_transactions = 'Transactions'

            #### Daily Transaction Derivation ####

            # loading the daily csv file at day
            df = read_epex_file(opath)

            # filtering the daily csv file for the window of time of interest
            df_filtered = filter_lead_time(df)

            # derive transactions
            pivoted, pivoted_levels = extract_transactions(
                df_filtered)

            # save files to csv
            if os.path.isdir(base_interim_folder / folder_month):

                df_filtered.to_csv(base_interim_folder / folder_month /
                                   folder_name_df_filtered / file_name, index=False)

                pivoted_levels.reset_index().to_csv(base_interim_folder / folder_month /
                                                    folder_name_df_transactions / file_name, index=False)

            else:

                os.makedirs(base_interim_folder / folder_month)

                os.makedirs(base_interim_folder /
                            folder_month / folder_name_df_filtered)
                os.makedirs(base_interim_folder /
                            folder_month / folder_name_df_transactions)

                df_filtered.to_csv(base_interim_folder / folder_month /
                                   folder_name_df_filtered / file_name, index=False)

                pivoted_levels.reset_index().to_csv(base_interim_folder / folder_month /
                                                    folder_name_df_transactions / file_name, index=False)

    toc = time.time()
    print(
        f'\n Reading, processing and deriving the possible transactions completely takes {toc-tic} seconds')


if __name__ == "__main__":
    run_historical_transaction()
