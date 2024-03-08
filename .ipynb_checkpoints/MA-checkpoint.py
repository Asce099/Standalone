import os 
from glob import glob
import pandas as pd
import numpy as np
from tqdm import tqdm
from matplotlib import dates as mdates
import datetime as dt
import mplfinance as mpf
import matplotlib.pyplot as plt
from mplfinance.original_flavor import candlestick_ohlc
import talib as ta


select_tf = ["day" , "5minute",'15minute',"60minute", "minute", "38minute" ]
tables = [] 
final_data = {}

for filename in tqdm(glob('TI_Data/*')):
    names = (filename.split(os.sep)[-1].split('_'))
    company_name = names[0]
    if names[1] in select_tf:
        data = pd.read_csv(filename, index_col=0)
        tf = names[1]
        variable_name = f"{company_name}_{tf}"
        locals()[variable_name] = data
        tables.append(variable_name)
        final_data[variable_name] = data


def indexer(dicta):
    for df in dicta.values():
        df.reset_index(inplace=True)
        df.rename(columns={'index': 'Index_Column'}, inplace=True)
    return dicta


indexer(final_data)

data_day = {}
data_hour = {}
data_minute = {}
data_5minute = {}
data_15minute = {}
data_38minute = {}

for key, value in final_data.items():
    if key.endswith('_day'):
        data_day[key] = value
    elif key.endswith('_60minute'):
        data_hour[key] = value
    elif key.endswith('_minute'):
        data_minute[key] = value
    elif key.endswith('_5minute'):
        data_5minute[key] = value
    elif key.endswith('_15minute'):
        data_15minute[key] = value
    elif key.endswith('_38minute'):
        data_38minute[key] = value


class Trade:
    def __init__(self, *args, **kwargs):
        self.entry_flag = False
        self.entry_price = 0
        self.df = None
        self.profit_window = kwargs.get('profit_window', 3)
        self.loss_window = kwargs.get('loss_window', 1)

    def process_data(self, df):
        self.df = df.copy()  # Make a copy of the input DataFrame

        for i in range(len(self.df)):
            if i < 200:  # Adjust the skip condition to accommodate SMA_50
                self.df.loc[i, 'trade'] = 'n'
                continue
            elif (self.df.loc[i, 'SMA_20'] > self.df.loc[i, 'SMA_50'] and self.df.loc[i-1, 'SMA_20'] < self.df.loc[i, 'SMA_50'] or
                  self.df.loc[i, 'SMA_50'] > self.df.loc[i, 'SMA_200'] and self.df.loc[i-1, 'SMA_50'] < self.df.loc[i, 'SMA_200']) and not self.entry_flag:
                self.entry_price = self.df.loc[i, 'close']
                self.entry_flag = True
                self.df.loc[i, 'trade'] = 'E'  # Entry point marked with 'E'
            elif self.entry_flag:
                trade_value = ((self.df.loc[i, 'close'] - self.entry_price) / self.entry_price) * 100
                if trade_value >= self.profit_window:
                    self.df.loc[i, 'trade'] = 'P'
                    self.entry_flag = False
                elif trade_value <= -self.loss_window:
                    self.df.loc[i, 'trade'] = 'L'
                    self.entry_flag = False
                else:
                    self.df.loc[i, 'trade'] = 'C'
            else:
                self.df.loc[i, 'trade'] = 'C'

        return self.df

    def result_counts(self):
        entry_count = self.df[self.df['trade'] == 'E'].shape[0]
        profit_count = self.df[self.df['trade'] == 'P'].shape[0]
        loss_count = self.df[self.df['trade'] == 'L'].shape[0]
        
        total_trades = entry_count
        
        # Calculate percentage of profitable trades
                if total_trades > 0:
            percent_profitable = round((profit_count / total_trades) * 100, 2)
        else:
            percent_profitable = 0
        
        counts_array = [entry_count, profit_count, loss_count, percent_profitable
        ]
    
        return counts_array

# Assuming you have a list called profit_windows
results_df_list = [] 
# Assuming you have a list called profit_windows
profit_windows = [(1, 0.33), (3, 1), (15, 5), (30, 10)]

dict_list = [data_day, data_hour]
for i in dict_list:
    results_df = pd.DataFrame()
    file = list(i.keys())[0].split('_')[1]
    for key, df_day in tqdm(list(i.items())):
        df = df_day
        column_name = key.split('_')[0]
        for profit_window, loss_window in profit_windows:
            # Instantiate Trade class with the current profit_window and loss_window values
            trade_instance = Trade(profit_window=profit_window, loss_window=loss_window)
            
            # Process data using the Trade instance
            processed_data = trade_instance.process_data(df)
            
            # Get result counts using the result_counts method
            result_counts_array = trade_instance.result_counts()
            
            # Create a DataFrame from the current result
            current_result_df = pd.DataFrame({
                'Profit_Loss_Windows': [(profit_window, loss_window)],
                f'{column_name}': [result_counts_array]
            })
        
            # Append the current DataFrame to the list
            results_df_list.append(current_result_df)
    
    # Use pd.concat to concatenate the list of DataFrames
    results_df = pd.concat(results_df_list, ignore_index=True)
    
    # Display the final results DataFrame
    results_df
    grouped_df = results_df.groupby('Profit_Loss_Windows').agg(lambda x: pd.Series(x.dropna().values)).reset_index()
    grouped_df.to_csv('Results/MA/{file}.csv')