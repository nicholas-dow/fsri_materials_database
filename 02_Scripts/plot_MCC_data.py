# Micro-scale calorimeter html data processing script
#   by: ULRI's Fire Safety Research Institute
#   Questions? Submit them here: https://github.com/ulfsri/fsri_materials_database/issues

# ***************************** Usage Notes *************************** #
# - Script outputs as a function of temperature                         #
#   -  PDF Graphs dir: /03_Charts/{Material}/MCC                       #
#      Graphs: Specific HRR                                             #
#                                                                       #
#      CSV Tables dir: /01_Data/{Material}/MCC                         #
#      Tables: Heat of Combustion                                       #
# ********************************************************************* #

# --------------- #
# Import Packages #
# --------------- #
import os
import os.path # check for file existence
import glob
import numpy as np
import pandas as pd
import math
import matplotlib.pyplot as plt
from scipy.signal import savgol_filter
from scipy import integrate
import git

label_size = 20
tick_size = 18
line_width = 2
legend_font = 10
fig_width = 10
fig_height = 6


def clean_file(file_name):
    fin = open(file_name, 'rt', encoding='UTF-16')
    fout = open(f'{file_name}_TEMP.tst', 'wt', encoding='UTF-16')
    # output file to write the result to
    for line in fin:
        # read replace the string and write to output file
        fout.write(line.replace('\t\t', '\t'))
    # close input and output files
    fin.close()
    fout.close()


def search_string_in_file(file_name, string_to_search):
    line_number = 0
    list_of_results = []
    with open(file_name, 'r', encoding='UTF-16') as read_obj:
        for line in read_obj:
            line_number += 1
            if string_to_search in line:
                line_num = line_number
    return line_num

def unique(list1):

    unique_list = []

    for x in list1:
        if x not in unique_list:
            unique_list.append(x)

    return unique_list


def create_1plot_fig():
    # Define figure for the plot
    fig, ax1 = plt.subplots(figsize=(fig_width, fig_height))

    # Reset values for x & y limits
    x_min, x_max, y_min, y_max = 0, 0, 0, 0

    return(fig, ax1, x_min, x_max, y_min, y_max)


def plot_mean_data(df):
    ax1.plot(df.index, df.loc[:, 'HRR_mean'], color='k',
             ls='-', marker=None, label='Mean Data')
    ax1.fill_between(df.index, df['HRR_mean'] - 2 * df['HRR_std'],
                     df['HRR_mean'] + 2 * df['HRR_std'], color='k', alpha=0.2)

    y_max = max(df.loc[:, 'HRR_mean'] + 2 * df.loc[:, 'HRR_std'])
    y_min = min(df.loc[:, 'HRR_mean'] - 2 * df.loc[:, 'HRR_std'])

    x_max = max(df.index)
    x_min = min(df.index)
    return(y_min, y_max, x_min, x_max)


def format_and_save_plot(xlims, ylims, file_loc):
    # Set tick parameters
    ax1.tick_params(labelsize=tick_size, length=8,
                    width=0.75, direction='inout')

    # Scale axes limits & labels
    ax1.set_ylim(bottom=ylims[0], top=ylims[1])
    ax1.set_xlim(left=xlims[0], right=xlims[1])
    ax1.set_xlabel('Temperature (C)', fontsize=label_size)

    ax1.set_position([0.15, 0.3, 0.77, 0.65])

    y_range_array = np.arange(ylims[0], ylims[1] + 50, 50)
    ax1.set_ylabel('Specific HRR (W/g)', fontsize=label_size)

    yticks_list = list(y_range_array)

    x_range_array = np.arange(xlims[0], xlims[1] + 50, 50)
    xticks_list = list(x_range_array)

    ax1.set_yticks(yticks_list)
    ax1.set_xticks(xticks_list)

    ax2 = ax1.secondary_yaxis('right')
    ax2.tick_params(axis='y', direction='in', length=4)
    ax2.set_yticks(yticks_list)
    empty_labels = [''] * len(yticks_list)
    ax2.set_yticklabels(empty_labels)

    ax3 = ax1.secondary_xaxis('top')
    ax3.tick_params(axis='x', direction='in', length=4)
    ax3.set_xticks(xticks_list)
    empty_labels = [''] * len(xticks_list)
    ax3.set_xticklabels(empty_labels)

    # Get github hash to display on graph
    repo = git.Repo(search_parent_directories=True)
    sha = repo.head.commit.hexsha
    short_sha = repo.git.rev_parse(sha, short=True)

    ax1.text(1, 1, 'Repository Version: ' + short_sha,
             horizontalalignment='right',
             verticalalignment='bottom',
             transform=ax1.transAxes)

    # Add legend
    handles1, labels1 = ax1.get_legend_handles_labels()

    plt.legend(handles1, labels1, loc='upper center', bbox_to_anchor=(0.5, -0.23), fontsize=16,
               handlelength=2, frameon=True, framealpha=1.0, ncol=2)

    # Clean up whitespace padding
    # fig.tight_layout()

    # Save plot to file
    plt.savefig(file_loc)
    plt.close()

    # print()


data_dir = '../01_Data/'
save_dir = '../03_Charts/'

for d in sorted((f for f in os.listdir(data_dir) if not f.startswith(".")), key=str.lower):
    material = d
    ylims = [0, 0]
    xlims = [0, 0]
    fig, ax1, x_min, x_max, y_min, y_max = create_1plot_fig()
    data_df = pd.DataFrame()
    plot_data_df = pd.DataFrame()
    hoc_df = pd.DataFrame()
    all_col_names = []
    if os.path.isdir(f'{data_dir}{d}/MCC/'):
        print(material + ' MCC')
        for f in glob.iglob(f'{data_dir}{d}/MCC/*.txt'):
            if 'mass' in f.lower():
                continue
            else:
                # import data for each test
                header_df = pd.read_csv(f, header=None, sep='\t', nrows=3, index_col=0).squeeze()
                initial_mass = float(header_df.at['Sample Weight (mg):'])
                data_temp_df = pd.read_csv(f, sep='\t', header=10, index_col='Time (s)')
                fid = open(f.split('.txt')[0] + '_FINAL_MASS.txt', 'r')
                final_mass = float(fid.readlines()[0].split('/n')[0])

                col_name = f.split('.txt')[0].split('_')[-1]
                # print(col_name)
                if "O" not in col_name: # to ignore outliers (run code only for repetitions)

                    all_col_names.append(col_name) # collect repetition numbers to account for botched tests (ex. R2, R3, R4, if R1 was bad)
                    reduced_df = data_temp_df.loc[:, ['Temperature (C)', 'HRR (W/g)']]
                    reduced_df[f'Time_copy_{col_name[-1]}'] = reduced_df.index  #col_name[-1] to have the repetition number as -1 (not -R1) to help Regex later

                    # Correct from initial mass basis to mass lost basis
                    reduced_df['HRR (W/g)'] = reduced_df['HRR (W/g)'] * (initial_mass / (initial_mass - final_mass))

                    max_lim = reduced_df['Temperature (C)'].iloc[-1] - ((reduced_df['Temperature (C)'].iloc[-1]) % 50)
                    new_index = np.arange(150, int(max_lim) + 1)
                    new_data = np.empty((len(new_index),))
                    new_data[:] = np.nan
                    df_dict = {'Temperature (C)': new_index, 'HRR (W/g)': new_data}
                    temp_df = pd.DataFrame(df_dict)

                   # Resample data to every temperature
                    reduced_df = pd.concat([reduced_df, temp_df], ignore_index=True)
                    reduced_df.set_index('Temperature (C)', inplace=True)
                    reduced_df.sort_index(inplace=True)
                    reduced_df.interpolate(method='linear', axis=0, inplace=True)
                    reduced_df = reduced_df.loc[new_index, :]

                    reduced_df = reduced_df[~reduced_df.index.duplicated(keep='first')]

                    # Baseline Correction
                    reduced_df['HRR correction'] = reduced_df.loc[150, 'HRR (W/g)'] + ((reduced_df.index - 150) / (reduced_df.index.max() - 150)) * (reduced_df.loc[reduced_df.index.max(), 'HRR (W/g)'] - reduced_df.loc[150, 'HRR (W/g)'])
                    reduced_df[col_name] = reduced_df['HRR (W/g)'] - reduced_df['HRR correction']

                    data_df = pd.concat([data_df, reduced_df], axis=1)
                    data_array = data_df[col_name].to_numpy()
                    time_array = data_df[f'Time_copy_{col_name[-1]}'].to_numpy() #col_name[-1] to have the repetition number of the time column as -1 (not -R1) to help Regex later
                    data_array = data_array[~np.isnan(data_array)]
                    time_array = time_array[~np.isnan(time_array)]
                    hoc_df.at['Heat of Combustion (MJ/kg)', col_name] = (integrate.trapz(y=data_array, x=time_array)) / 1000
                    hoc_df.at['Heat of Combustion (MJ/kg)', 'Mean'] = np.nan
                    hoc_df.at['Heat of Combustion (MJ/kg)','Std. Dev.'] = np.nan

        corrected_data = data_df.filter(regex='R[0-9]')  # TESTS WITHOUT Rnumber (ex. R1) are ignored and not used in HRR averaging or HoC determination.
        plot_data_df.loc[:, 'HRR_mean'] = corrected_data.mean(axis=1)
        plot_data_df.loc[:, 'HRR_std'] = corrected_data.std(axis=1)

    else:
        continue

    if hoc_df.empty:
        continue
    mean_hoc = hoc_df.mean(axis=1)
    std_hoc = hoc_df.std(axis=1)


    hoc_df.at['Heat of Combustion (MJ/kg)', 'Mean'] = mean_hoc
    hoc_df.at['Heat of Combustion (MJ/kg)', 'Std. Dev.'] = std_hoc
    all_col_names.append('Mean')
    all_col_names.append('Std. Dev.')
    hoc_df = hoc_df[all_col_names] # sorting HoC dataframe, using repetition numbers

    ymin, ymax, xmin, xmax = plot_mean_data(plot_data_df)

    y_min = max(ymin, y_min)
    x_min = max(xmin, x_min)
    y_max = max(ymax, y_max)
    x_max = max(xmax, x_max)

    ylims[0] = 50 * (math.floor(y_min / 50) - 1)
    ylims[1] = 50 * (math.ceil(y_max / 50) + 1)
    xlims[0] = 50 * (math.floor(x_min / 50))
    xlims[1] = 50 * (math.ceil(x_max / 50))

    plot_dir = f'../03_Charts/{material}/MCC/'

    if not os.path.exists(plot_dir):
        os.makedirs(plot_dir)

    format_and_save_plot(xlims, ylims, f'{plot_dir}{material}_MCC_HRR.pdf')

    hoc_df.to_csv(f'{data_dir}{material}/MCC/{material}_MCC_Heats_of_Combustion.csv', float_format='%.2f')