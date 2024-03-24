import pandas as pd
import numpy as np
# import functions
from functions.functions import get_position, save_as_csv, save_as_csv_pv
from functions.renewables_ninja_feedin import change_wpt, get_df, change_wpt_pv, get_df_pv

# --------------------------------------------------------------------------------------------------------------------->
# INPUT - data

# INPUT: choose regions by array
regions = ["Rüdersdorf bei Berlin", "Strausberg", "Erkner", "Grünheide (Mark)",
           "Kiel", "Ingolstadt", "Kassel", "Bocholt", "Zwickau"]

gemeindeschluessel = {
    "Rüdersdorf bei Berlin": "12064428",
    "Strausberg": "12064472",
    "Erkner": "12067124",
    "Grünheide (Mark)": "12067201",
    "Ingolstadt":"09161000",
    "Kassel": "06611000",
    "Bocholt": "05554008",
    "Kiel": "01002000",
    "Zwickau": "14524330",
}

import pickle

# dict gemeindeschluessel save as file
with open(r"functions\gemeindeschluessel.pkl", "wb") as datei:
    pickle.dump(gemeindeschluessel, datei)

# --------------------------------------------------------------------------------------------------------------------->
# CENTER - POSITIONS

# load dataset for Geo-data of Municipalities in germany
gdf =r"\\FS01\RL-Institut\04_Projekte\360_Stadt-Land-Energie\03-Projektinhalte\AP2\vg250_01-01.utm32s.gpkg.ebenen\vg250_01-01.utm32s.gpkg.ebenen\vg250_ebenen_0101\DE_VG250.gpkg"

center_positions = []
for region in regions:
    center_positions.append(get_position(gdf,region))

# create Dataframe df_ninja
    # collects centerposition input data for renewables ninja
data = { "centerposition": center_positions
}
df_ninja = pd.DataFrame(data, index=regions)

# save centerpositions in dataframe as input data for renewables.ninja retrieval

positions = []
keys = []
for region, ags_id in gemeindeschluessel.items():
    positions.append(get_position(gdf,region)[0].coords[0])
    keys.append(ags_id)

data = { "centerposition": positions
}
df_positions = pd.DataFrame(data, index=keys)
df_positions.to_csv("center_positions.csv")

# --------------------------------------------------------------------------------------------------------------------->

# --> collect data for wind_feedin_timeseries.csv

for region in regions:
    df = get_df(change_wpt(
    position=df_ninja.loc[region,"centerposition"][0].coords[0],
    height=126,
    turbine="Enercon E126 6500")
    )
    save_as_csv(df, region)

# --> collect data for pv_feedin_timeseries.csv

for region in regions:
    df = get_df_pv(change_wpt_pv(
    position=df_ninja.loc[region,"centerposition"][0].coords[0],
    system_loss=0.1)
    )
    save_as_csv_pv(df, region)

# --------------------------------------------------------------------------------------------------------------------->

# summarize data to one dataframe

dfs = []
for region in regions:
    dfs.append(pd.read_csv(f"timeseries/wind/timeseries_wind_{region}.csv",
                 parse_dates=True, index_col=0))

timeseries_wind = pd.concat(dfs, axis=1)

dfs = []
for region in regions:
    dfs.append(pd.read_csv(f"timeseries/pv/timeseries_pv_{region}.csv",
                 parse_dates=True, index_col=0))

timeseries_pv = pd.concat(dfs, axis=1)

# --------------------------------------------------------------------------------------------------------------------->

# calculate normed timeseries for wind and pv

# full load  hours
full_load_hours_wind = timeseries_wind.sum()/1000
full_load_hours_pv = timeseries_pv.sum()/1000

# standardize on installed capacity
timeseries_wind_normed = timeseries_wind/timeseries_wind.sum()
timeseries_pv_normed = timeseries_pv/timeseries_pv.sum()

# --------------------------------------------------------------------------------------------------------------------->

# --> collect data for ror_feedin_timeseries.csv
"""
Assumptions:
    - constant power flow
    - full load hours = 3800
        -> one ror_feedin_timeseries.csv for all regions
"""
# full_load_hours_ror = 3800

ror_dispatch_normed = 1/8760

global date_range
start_date = "2011-01-01 00:00:00"
end_date = "2011-12-31 23:00:00"
date_range = pd.date_range(start=start_date, end=end_date, freq='H')

data = {"power": np.full(len(date_range),ror_dispatch_normed)
}
timeseries_ror_normed = pd.DataFrame(data,index=date_range)

# --------------------------------------------------------------------------------------------------------------------->

# export data as .csv
# timeseries_wind_normed.to_csv("timeseries/wind_feedin_timeseries.csv")
timeseries_pv_normed.to_csv("timeseries/pv_feedin_timeseries.csv")
timeseries_pv_normed.to_csv("timeseries/st_feedin_timeseries.csv")
timeseries_wind_normed.to_csv("timeseries/wind_feedin_timeseries.csv")
timeseries_ror_normed.to_csv("timeseries/ror_feedin_timeseries.csv")
