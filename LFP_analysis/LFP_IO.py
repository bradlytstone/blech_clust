"""
Elemental functions for IO related to LFP processing
"""
# =============================================================================
# Import stuff
# =============================================================================

# import Libraries
# Built-in Python libraries
import os # functions for interacting w operating system
import sys
import glob

# 3rd-party libraries
import numpy as np # module for low-level scientific computing
#Hilbert transform to determine the amplitude envelope and 
#instantaneous frequency of an amplitude-modulated signal
from scipy.signal import hilbert 
from scipy.signal import butter
from scipy.signal import filtfilt
import matplotlib.pyplot as plt # makes matplotlib work like MATLAB. ’pyplot’ functions.
import easygui
import tables
from tqdm import trange
import pandas as pd
import collections

# =============================================================================
# Define Functions 
# =============================================================================

def getLFPList(hdf5_name):
    with tables.open_file(hdf5_name,'r+') as hf5:
        return [node[:] for node in hf5.list_nodes('/Parsed_LFP') if 'dig_in' in str(node)]

def getLFPFlagFrame(hdf5_name):
    # Load flagged channels from HDF5 if present
    try:
        flag_frame = pd.read_hdf(hdf5_name,'/Parsed_LFP/flagged_channels')
        flagged_channel_bool = 1
    except:
        flag_frame = pd.DataFrame()
        flagged_channel_bool = 0
       
    return flagged_channel_bool, flag_frame

def getFlaggedLFPs(hdf5_name):

    flagged_channel_bool, flag_frame = getLFPFlagFrame(hdf5_name)

    # Pull LFPS and spikes
    # Make sure not taking anything other than a dig_in
    lfps_dig_in = getLFPList(hdf5_name) 

    # If flagged channels dataset present
    if flagged_channel_bool > 0:
        good_channel_list = [list(flag_frame.\
                query('Dig_In == {} and Error_Flag == 0'.format(dig_in))['Channel']) \
                for dig_in in range(len(lfps_dig_in))]
    else:
        good_channel_list = [list(flag_frame.\
                query('Dig_In == {}'.format(dig_in))['Channel']) \
                for dig_in in range(len(lfps_dig_in))]

    # Load LFPs and remove flagged channels if present
    lfp_list = [dig_in[good_channel_list[dig_in_num],:] \
        for dig_in_num,dig_in in enumerate(lfps_dig_in)]

    return lfp_list

