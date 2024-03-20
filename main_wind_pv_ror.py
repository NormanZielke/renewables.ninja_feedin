import pandas as pd

# import functions
from functions.functions import get_position, save_as_csv, save_as_csv_pv

from functions.renewables_ninja_feedin import change_wpt, get_df, change_wpt_pv, get_df_pv

# --------------------------------------------------------------------------------------------------------------------->
# INPUT - data

# INPUT: choose regions by array
regions = ["Rüdersdorf bei Berlin", "Strausberg", "Erkner", "Grünheide (Mark)",
           "Kiel", "Ingolstadt", "Kassel", "Bocholt", "Zwickau"]

import pickle

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

# --------------------------------------------------------------------------------------------------------------------->

# --> collect data for wind_feedin_timeseries.csv

for region in regions:
    df = get_df(change_wpt(
    position=df_ninja.loc[region,"centerposition"][0].coords[0],
    height=126,
    turbine="Enercon E126 6500")
    )
    save_as_csv(df, region)

# --------------------------------------------------------------------------------------------------------------------->

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

# full load  hours
full_load_hours_wind = timeseries_wind.sum()/1000
full_load_hours_pv = timeseries_pv.sum()/1000

# standardize on installed capacity
timeseries_wind_normed = timeseries_wind/timeseries_wind.sum()
timeseries_pv_normed = timeseries_pv/timeseries_pv.sum()

# export data as .csv
# timeseries_wind_normed.to_csv("timeseries/wind_feedin_timeseries.csv")
timeseries_pv_normed.to_csv("timeseries/pv_feedin_timeseries.csv")
timeseries_pv_normed.to_csv("timeseries/st_feedin_timeseries.csv")
timeseries_wind_normed.to_csv("timeseries/wind_feedin_timeseries.csv")
