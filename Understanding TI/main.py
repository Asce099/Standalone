import subprocess
import time
import os
import warnings

warnings.filterwarnings("ignore")

current_directory = os.path.dirname(os.path.realpath(__file__))

run_list = ['BB.py', 'RSI.py', 'MA.py', 'BB-RSI-conventional.py', 'BB-RSI-unconventional.py', 'MA-RSI_conventional.py', 'MA-RSI_unconventional1.py', 'MA-RSI_unconventional2.py']



for file_name in run_list:
    file_path = os.path.join(current_directory, file_name)
    
    try:
        subprocess.run(['python', file_path], check=True)
        print(f"----------{file_name} Processed and results stored in Results folder----------")
        time.sleep(5)  # Sleep for 5 seconds

    except subprocess.CalledProcessError as e:
        print(f"Error processing {file_name}: {e}")