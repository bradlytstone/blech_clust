#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Feb 14 10:23:58 2019

@author: abuzarmahmood/bradly

Created on Wed Feb 13 19:36:13 2019

"""

# ____       _               
#/ ___|  ___| |_ _   _ _ __  
#\___ \ / _ \ __| | | | '_ \ 
# ___) |  __/ |_| |_| | |_) |
#|____/ \___|\__|\__,_| .__/ 
#                     |_|    

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
import easygui
import tables
from tqdm import trange
import pandas as pd
import collections

# Import self-defined functions
from LFP_process import *
from LFP_IO import *

# =============================================================================
# Define common variables
# =============================================================================
#specify frequency bands
iter_freqs = [
        ('Theta', 4, 7),
        ('Alpha', 7, 12),
        ('Beta', 13, 25),
        ('Gamma', 30, 45)]

#Covert to dframe for storing
freq_dframe = pd.DataFrame.from_dict(iter_freqs)

colors = plt.get_cmap('winter_r')(np.linspace(0, 1, len(iter_freqs)))

# =============================================================================
# Import/Open HDF5 File
# =============================================================================

# If directory provided with script, use that otherwise ask
try:
    dir_name = os.path.dirname(sys.argv[1])
except:
    dir_name = easygui.diropenbox(msg = 'Select directory with HDF5 file')

hdf5_name = glob.glob(dir_name + '/*.h5')[0]

lfp_list = getFlaggedLFPs(hdf5_name)

hf5 = tables.open_file(hdf5_name, 'r+')
trains_dig_in = hf5.list_nodes('/spike_trains')
spike_array = np.asarray([spikes.spike_array[:] for spikes in trains_dig_in])

# ____                              _             
#|  _ \ _ __ ___   ___ ___  ___ ___(_)_ __   __ _ 
#| |_) | '__/ _ \ / __/ _ \/ __/ __| | '_ \ / _` |
#|  __/| | | (_) | (_|  __/\__ \__ \ | | | | (_| |
#|_|   |_|  \___/ \___\___||___/___/_|_| |_|\__, |
#                                           |___/ 

# =============================================================================
# Calculate phases
# =============================================================================

# Create lists of phase array
# Save data as namedTuple so band and taste are annotated
filtered_tuple = collections.namedtuple('BandpassFilteredData',['Band','Taste','Data'])
filtered_signal_list = [ filtered_tuple (band, taste,
                                butter_bandpass_filter(
                                            data = dig_in,
                                            lowcut = iter_freqs[band][1], 
                                            highcut =  iter_freqs[band][2], 
                                            fs = 1000)) \
                                            for taste,dig_in in enumerate(lfp_list)\
                    for band in trange(len(iter_freqs), desc = 'bands') \
                    if len(dig_in) > 0]

# =============================================================================
# Use mean LFP (across channels) to calculate phase (since all channels have same phase)
# =============================================================================
# Process filtered signals to extract hilbert transform and phase 

#mean_analytic_signal_list = \
#                [ filtered_tuple(x.Band, x.Taste, np.mean(hilbert(x.Data),axis=0)) \
#                    for x in filtered_signal_list ]

mean_phase_list = [ filtered_tuple(x.Band, x.Taste, np.mean(np.angle(x.Data),axis=0)) \
                        for x in filtered_signal_list ]
                           
# =============================================================================
# Calculate phase locking: for every spike, find phase for every band
# =============================================================================
# Find spiketimes
# Find what phase each spike occured
spike_times = spike_array.nonzero()
spikes_frame = pd.DataFrame(data = {'taste':spike_times[0],
                                    'trial':spike_times[1],
                                    'unit':spike_times[2],
                                    'time':spike_times[3]})


# Run through all groups of mean phase, convert to pandas dataframe
# and concatenate into single dataframe
phase_frame = pd.concat(
        [pd.DataFrame( data = { 'band' : dat.Band,
                                'taste' : dat.Taste,
                                'trial' : idx[0].flatten(),
                                'time' : idx[1].flatten(),
                                'phase' : dat.Data.flatten()}) \
                                for dat, idx in \
                    map(lambda dat: (dat, make_array_identifiers(dat.Data)),mean_phase_list)]
        )

# Merge : Gives dataframe with length of (bands x numner of spikes)
final_phase_frame = pd.merge(spikes_frame,phase_frame,how='inner')

#  ___        _               _   
# / _ \ _   _| |_ _ __  _   _| |_ 
#| | | | | | | __| '_ \| | | | __|
#| |_| | |_| | |_| |_) | |_| | |_ 
# \___/ \__,_|\__| .__/ \__,_|\__|
#                |_|              

#Save dframes into node within HdF5 file
final_phase_frame.to_hdf(hdf5_name,'Spike_Phase_Dframe/dframe')
freq_dframe.to_hdf(hdf5_name,'Spike_Phase_Dframe/freq_keys')

#Flush and close file
hf5.flush()
hf5.close()
