import easygui
import numpy as np
import glob
import tables
from itertools import product
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import sys
import os
from LFP_IO import *

# =============================================================================
# #Channel Check Processing
# =============================================================================

# If directory provided with script, use that otherwise ask
try:
    dir_name = os.path.dirname(sys.argv[1])
except:
    dir_name = easygui.diropenbox(msg = 'Select directory with HDF5 file')

hdf5_name = glob.glob(dir_name + '/*.h5')[0]

# Extract unflagged LFP from file
lfp_list = getLFPList(hdf5_name)
taste_num = len(lfp_list) 
channel_num = len(lfp_list[0]) 

#Ask user to check LFP traces to ensure channels are not shorted/bad in order to remove said channel from further processing
try:
    channel_check =  list(map(int,easygui.multchoicebox(
            msg = 'Choose the channel numbers that you '\
                    'want to REMOVE from further analyses. '
                    'Click clear all and ok if all channels are good', 
                    choices = tuple([i for i in range(channel_num)]))))
except:
    channel_check = []

try:
    taste_check = list(map(int, easygui.multchoicebox(
            msg = 'Chose the taste numbers that you want to '\
                    'REMOVE from further analyses. Click clear all '\
                    'and ok if all tastes are good',
                    choices = tuple([i for i in range(taste_num)]))))
except:
    taste_check = []

# Create dataframe with all tastes and channels
flag_frame = pd.DataFrame(list(product(range(taste_num),range(channel_num))),
                columns = ['Dig_In','Channel'])

# Create list of all flagged rows in dataframe and mark
flagged_rows = np.isin(list(flag_frame['Dig_In']),taste_check) + \
                    np.isin(list(flag_frame['Channel']),channel_check)
flag_frame['Error_Flag'] = flagged_rows * 1 

#Write out to file
flag_frame.to_hdf(hdf5_name, parsed_lfp_addr + '/flagged_channels')
hf5.close()
