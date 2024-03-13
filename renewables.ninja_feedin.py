import os.path
import math as m
import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
plt.style.use("seaborn-v0_8")

import geopandas as gpd
import cartopy
import cartopy.crs as ccrs

# --------------------------------------------------------------------------------------------------------------------->
# POSITIONS
# load dataset for Municipalities in germany
gdf =r"\\FS01\RL-Institut\04_Projekte\360_Stadt-Land-Energie\03-Projektinhalte\AP2\vg250_01-01.utm32s.gpkg.ebenen\vg250_01-01.utm32s.gpkg.ebenen\vg250_ebenen_0101\DE_VG250.gpkg"

regions = ["Rüdersdorf bei Berlin", "Strausberg", "Erkner", "Grünheide (Mark)",
           "Kiel", "Ingolstadt", "Kassel", "Bocholt", "Zwickau"]

def get_position(gdf,region):
    df = gpd.read_file(gdf)
    points_of_muns = df.loc[df.loc[df.GEN == region].index, "geometry"].head(1).centroid.values
    points_of_muns_crs = points_of_muns.to_crs(4326)

    return points_of_muns_crs

center_positions = []
for region in regions:
    center_positions.append(get_position(gdf,region))

# --------------------------------------------------------------------------------------------------------------------->
# Check dataset for consistency

# load data of wind turbines from MaStr
wind_data = pd.read_csv("bnetza_mastr_wind_raw.csv",
                        sep=",")

nan_rows_Gemeinde = wind_data[wind_data.Gemeinde.isna()]
nan_rows_Gemeindeschluessel = wind_data[wind_data.Gemeindeschluessel.isna()]
# check if dataframes are the same
# nan_rows_Gemeinde['EinheitMastrNummer'].equals(nan_rows_Gemeindeschluessel['EinheitMastrNummer'])
nan_rows_Breitengrad = wind_data[wind_data.Breitengrad.isna()]
yes_rows_Breitengrad = wind_data[wind_data.Breitengrad.notna()]
# rows with no ags_id always have lon and lat
# nan_rows_Gemeinde[nan_rows_Gemeinde.Breitengrad.isna()]
    # = {}
# rows where position is missing -> ags_id available
    # nan_rows_Breitengrad.Gemeinde.isna().unique()

# check via plot where the wind turbines without ags_id are located
geometry = gpd.points_from_xy(nan_rows_Gemeindeschluessel["Laengengrad"],nan_rows_Gemeindeschluessel["Breitengrad"])
gdf = gpd.GeoDataFrame(nan_rows_Gemeindeschluessel, geometry=geometry, crs=4326)

url = "https://tubcloud.tu-berlin.de/s/RHZJrN8Dnfn26nr/download/NUTS_RG_10M_2021_4326.geojson"
nuts = gpd.read_file(url)
nuts = nuts.set_index("id")
# choose NUTS LVL
nuts3 = nuts.query("LEVL_CODE == 3") # ---> in LVL 3 Counties/Landkreise are illustrated
# save .geoson file with NUTS 3 LVL
nuts3.to_file("NUTS3.geojson")
# set NUTS 3 LVL to crs (3035) Projection
nuts3 = nuts3.to_crs(3035)
# set geodataframe to crs(3035) Projection
gdf = gdf.to_crs(3035)
# join the geodataframe with NUTS3 regions
joined = gdf.sjoin(nuts3)

fig = plt.figure(figsize=(7, 7))

ax = plt.axes(projection=ccrs.epsg(3035))
nuts3.plot(ax=ax, edgecolor="black", facecolor="lightgrey")
gdf.plot(
    ax=ax, column="AnlageBetriebsstatus", markersize=gdf.Bruttoleistung_extended / 200, legend=True
)
ax.set_extent([4.14, 16.49, 45.67, 63.10])
plt.tight_layout()
plt.savefig("plots/turbines_no_ags_id.jpg", format="jpg")
#plt.show()

# --------------------------------------------------------------------------------------------------------------------->

# cut out turbines which are not actually running
    # e.g. wind_data.loc[28128,"EinheitBetriebsstatus"] => "Vorübergehend stillgelegt"
wind_data = wind_data.loc[wind_data["EinheitBetriebsstatus"] == "In Betrieb"]

# columns of interest for input data --> renewables ninja
columns = ["Nabenhoehe","Hersteller","Typenbezeichnung","Bruttoleistung","EinheitBetriebsstatus"]
# save for every region a single dataframe
df_Rued = wind_data.loc[wind_data.Gemeinde == "Rüdersdorf bei Berlin"]
df_Rued = df_Rued[columns]
df_Straus = wind_data.loc[wind_data.Gemeinde == "Strausberg"]
df_Straus = df_Straus[columns]
df_Erkner = wind_data.loc[wind_data.Gemeinde == "Erkner"]
df_Erkner = df_Erkner[columns]
df_Grünh = wind_data.loc[wind_data.Gemeinde == "Grünheide (Mark)"]
df_Grünh = df_Grünh[columns]
df_Kiel = wind_data.loc[wind_data.Gemeinde == "Kiel"]
df_Kiel = df_Kiel[columns]
df_Ingolstadt = wind_data.loc[wind_data.Gemeinde == "Ingolstadt"]
df_Ingolstadt = df_Ingolstadt[columns]
df_Kassel = wind_data.loc[wind_data.Gemeinde == "Kassel"]
df_Kassel = df_Kassel[columns]
df_Bocholt = wind_data.loc[wind_data.Gemeinde == "Bocholt"]
df_Bocholt = df_Bocholt[columns]
df_Zwickau = wind_data.loc[wind_data.Gemeinde == "Zwickau"]
df_Zwickau = df_Zwickau[columns]

dataframes = [df_Rued,df_Straus,df_Erkner,df_Grünh,df_Kiel,df_Ingolstadt,df_Kassel,df_Bocholt,df_Zwickau]

# create Dataframe df_ninja
    # collects all necessary input data for renewables ninja
data = { "Nabenhoehe": {},
         "Hersteller_1": {},
         "Turbinentyp_1": {},
         "Anzahl_Typ1": {},
         "Brutto_1_kW": {},
         "Hersteller_2": {},
         "Turbinentyp_2": {},
         "Anzahl_Typ2": {},
         "Brutto_2_kW": {},
         "centerposition": center_positions
}
df_ninja = pd.DataFrame(data, index=regions)

# --------------------------------------------------------------------------------------------------------------------->

# Hub height
def hub_height(df):
    return df.loc[:,"Nabenhoehe"].mean()

Nabenhoehe = []
for df in dataframes:
    Nabenhoehe.append(hub_height(df))

df_ninja.Nabenhoehe = Nabenhoehe

# Turbinetype and installed quantity

# function to filter dataframes by "Turbinetyp" and "Anzahl_Turbinetyp"
    # input
    # df -> dataframe of a certain region
    # output
    # tuple -> (Turbinetype1,Turbinetype2,Quantity_Turbinetyp1,Quantity_Turbinetyp2,manufacturer1,manufacturer2,capacity1,capacity2)
def turbine_types(df):
    manufacturers = df.loc[:, ["Hersteller", "EinheitBetriebsstatus"]].groupby("Hersteller").count().sort_values(by="EinheitBetriebsstatus", ascending=False)
    # break function if there is no manufacturers
    if manufacturers.empty:
        type_1 = "NaN"
        type_2 = "NaN"
        count_1 = "NaN"
        count_2 = "NaN"
        man_1 = "NaN"
        man_2 = "NaN"
        brutto1 = "NaN"
        brutto2 = "NaN"
        return (type_1, type_2, count_1, count_2, man_1, man_2, brutto1, brutto2)

    man_1 = manufacturers.index[0]
    types = df.loc[:, ["Hersteller", "Typenbezeichnung", "EinheitBetriebsstatus"]].where(
        df["Hersteller"] == man_1).groupby(
        "Typenbezeichnung").count().sort_values(by="EinheitBetriebsstatus", ascending=False)
    type_1 = types.index[0]
    brutto1 = df.loc[df.loc[df["Typenbezeichnung"] == type_1].index[0],"Bruttoleistung"]
    count_1 = types["Hersteller"].max()
    # break function if there is only one manufacturer
    if len(manufacturers) == 1:
        type_2 = "NaN"
        count_2 = "NaN"
        man_2 = "NaN"
        brutto2 = "NaN"
        if len(types) >= 2:
            type_2 = types.index[1]
            brutto2 = df.loc[df.loc[df["Typenbezeichnung"] == type_2].index[0], "Bruttoleistung"]
            count_2 = types.loc[types.index[1],"Hersteller"]
        return (type_1, type_2, count_1, count_2, man_1, man_2, brutto1, brutto2)

    man_2 = manufacturers.index[1]
    types = df.loc[:, ["Hersteller", "Typenbezeichnung", "EinheitBetriebsstatus"]].where(
        df["Hersteller"] == man_2).groupby(
        "Typenbezeichnung").count().sort_values(by="EinheitBetriebsstatus", ascending=False)
    type_2 = types.index[0]
    brutto2 = df.loc[df.loc[df["Typenbezeichnung"] == type_2].index[0], "Bruttoleistung"]
    count_2 = types["Hersteller"].max()
    return (type_1, type_2, count_1, count_2, man_1, man_2, brutto1, brutto2)

# fill df_ninja with input data for renewables ninja

for df, region in zip(dataframes,regions):
    a = turbine_types(df)
    if not a:
        continue
    df_ninja.loc[region, "Turbinentyp_1"] = a[0]
    df_ninja.loc[region, "Turbinentyp_2"] = a[1]
    df_ninja.loc[region, "Anzahl_Typ1"] = a[2]
    df_ninja.loc[region, "Anzahl_Typ2"] = a[3]
    df_ninja.loc[region, "Hersteller_1"] = a[4]
    df_ninja.loc[region, "Hersteller_2"] = a[5]
    df_ninja.loc[region, "Brutto_1_kW"] = a[6]
    df_ninja.loc[region, "Brutto_2_kW"] = a[7]

# --------------------------------------------------------------------------------------------------------------------->
# renewables ninja retrieval
import json
import requests

#wind data

# function to change input values for get_df() - function
def change_wpt(position, capacity, height, turbine):
    args = {
        'lat': 51.8000,  # 51.5000-52.0000
        'lon': 12.2000,  # 11.8000-13.1500
        'date_from': '2011-01-01',
        'date_to': '2011-12-31',
        'capacity': 1000.0,
        'height': 100,
        'turbine': 'Vestas V164 7000',
        'format': 'json',
        'local_time': 'true',
        'raw': 'false',
    }

    args['capacity'] = capacity
    args['height'] = height
    args['lat'] = position[1]
    args['lon'] = position[0]
    args['turbine'] = turbine

    return args

# function to get rawdata from renewables ninja

def get_df(args):
    token = "087de02f953c486ef9ffe4b9e8093268b0df881c"
    api_base = 'https://www.renewables.ninja/api/'

    s = requests.session()
    # Send token header with each request
    s.headers = {'Authorization': 'Token ' + token}

    url = api_base + 'data/wind'

    r = s.get(url, params=args)

    parsed_response = json.loads(r.text)
    df = pd.read_json(
    json.dumps(parsed_response['data']),orient='index')
    metadata = parsed_response['metadata']
    return df

# pv data

def change_wpt_pv(position, capacity, system_loss):
    args = {
        'lat': 34.125,
        'lon': 39.814,
        'date_from': '2011-01-01',
        'date_to': '2011-12-31',
        'dataset': 'merra2',
        'capacity': 1.0,
        'system_loss': 0.1,
        'tracking': 0,
        'tilt': 35,
        'azim': 180,
        'format': 'json',
        'local_time': 'true',
        'raw': 'false',
    }

    args['capacity'] = capacity
    args['system_loss'] = system_loss
    args['lat'] = position[1]
    args['lon'] = position[0]

    return args

def get_df_pv(args):
    token = "087de02f953c486ef9ffe4b9e8093268b0df881c"
    api_base = 'https://www.renewables.ninja/api/'

    s = requests.session()
    # Send token header with each request
    s.headers = {'Authorization': 'Token ' + token}

    url = api_base + 'data/pv'

    r = s.get(url, params=args)

    parsed_response = json.loads(r.text)
    df = pd.read_json(
    json.dumps(parsed_response['data']),orient='index')
    metadata = parsed_response['metadata']
    return df

# --------------------------------------------------------------------------------------------------------------------->
# to interpolate regions without data -> evaluate the two top manufacturers with their top windturbinetypes
# cut out onshore wind_data from wind_data
wind_data_onshore = wind_data[wind_data.Gemeinde.notna()]

data = { "Nabenhoehe": {},
         "Hersteller_1": {},
         "Turbinentyp_1": {},
         "Anzahl_Typ1": {},
         "Brutto_1_kW": {},
         "Hersteller_2": {},
         "Turbinentyp_2": {},
         "Anzahl_Typ2": {},
         "Brutto_2_kW": {}
}
df_ninja_onshore = pd.DataFrame(data,index=[1])


df_ninja_onshore.loc[:, "Nabenhoehe"] = hub_height(wind_data_onshore)

a = turbine_types(wind_data_onshore)

df_ninja_onshore.loc[:, "Turbinentyp_1"] = a[0]
df_ninja_onshore.loc[:, "Turbinentyp_2"] = a[1]
df_ninja_onshore.loc[:, "Anzahl_Typ1"] = a[2]
df_ninja_onshore.loc[:, "Anzahl_Typ2"] = a[3]
df_ninja_onshore.loc[:, "Hersteller_1"] = a[4]
df_ninja_onshore.loc[:, "Hersteller_2"] = a[5]
df_ninja_onshore.loc[:, "Brutto_1_kW"] = a[6]
df_ninja_onshore.loc[:, "Brutto_2_kW"] = a[7]

# parameter to calculate the average of the capacityfactor of turbines

x = df_ninja_onshore.loc[1, "Anzahl_Typ1"]
y = df_ninja_onshore.loc[1, "Anzahl_Typ2"]
z = x+y

# --------------------------------------------------------------------------------------------------------------------->

# prepare functions to save timeseries of the regions

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

global date_range
start_date = "2011-01-01 00:00:00"
end_date = "2011-12-31 23:00:00"
date_range = pd.date_range(start=start_date, end=end_date, freq='H')

# functions to save data and rename columns, get from renewables ninja
def save_as_csv(df, region):
    df.rename(columns={"electricity": region}, inplace=True)
    df[region] = df[region].round(3)
    #df.insert(1, "ags_id", np.full(len(date_range), gemeindeschluessel[region]))
    filename = f"capacity_factors_2011_wind_{region}.csv"
    df.to_csv(f"timeseries/wind/{filename}", index=False)

def save_as_csv_pv(df, region):
    df.rename(columns={"electricity": region}, inplace=True)
    df[region] = df[region].round(3)
    #df.insert(1, "ags_id", np.full(len(date_range), gemeindeschluessel[region]))
    filename = f"capacity_factors_2011_pv_{region}.csv"
    df.to_csv(f"timeseries/pv/{filename}", index=False)

def save_as_csv_future(df, region):
    df.rename(columns={"electricity": region}, inplace=True)
    df[region] = df[region].round(3)
    #df.insert(1, "ags_id", np.full(len(date_range), gemeindeschluessel[region]))
    filename = f"capacity_factors_2011_future_{region}.csv"
    df.to_csv(f"timeseries/wind_future/{filename}", index=False)

# --------------------------------------------------------------------------------------------------------------------->

# --> collect data for wind_feedin_timeseries.csv

# "Ruedersdorf bei Berlin"
    # -> there is only one manufacturer with 2 types for turbines
        # GE 1.5sl available, but not GE 2.3
            # at renewables ninja --> GE 2.5xl is available

df_Rued_wind = get_df(change_wpt(
    position=df_ninja.loc["Rüdersdorf bei Berlin","centerposition"][0].coords[0],
    capacity=1,
    height=df_ninja.loc["Rüdersdorf bei Berlin","Nabenhoehe"],
    turbine="GE 1.5sl")
)

save_as_csv(df_Rued_wind,"Rüdersdorf bei Berlin")

# "Strausberg"
    # no installed wind turbines

df_Straus_wind_type1 = get_df(change_wpt(
    position=df_ninja.loc["Strausberg","centerposition"][0].coords[0],
    capacity=1,
    height=df_ninja_onshore.loc[1, "Nabenhoehe"],
    turbine="Enercon E70 2300")
)

df_Straus_wind_type2 = get_df(change_wpt(
    position=df_ninja.loc["Strausberg","centerposition"][0].coords[0],
    capacity=1,
    height=df_ninja_onshore.loc[1, "Nabenhoehe"],
    turbine="Vestas V90 2000")
)

df_Straus_wind = df_Straus_wind_type1.copy()
df_Straus_wind["electricity"] = df_Straus_wind_type1["electricity"] * (x/z) + df_Straus_wind_type2["electricity"] * (y/z)

save_as_csv(df_Straus_wind,"Strausberg")

# "Erkner"
    # no installed wind turbines

df_Erkner_wind_type1 = get_df(change_wpt(
    position=df_ninja.loc["Erkner","centerposition"][0].coords[0],
    capacity=1,
    height=df_ninja_onshore.loc[1, "Nabenhoehe"],
    turbine="Enercon E70 2300")
)

df_Erkner_wind_type2 = get_df(change_wpt(
    position=df_ninja.loc["Erkner","centerposition"][0].coords[0],
    capacity=1,
    height=df_ninja_onshore.loc[1, "Nabenhoehe"],
    turbine="Vestas V90 2000")
)

df_Erkner_wind = df_Erkner_wind_type1.copy()
df_Erkner_wind["electricity"] = df_Erkner_wind_type1["electricity"] * (x/z) + df_Erkner_wind_type2["electricity"] * (y/z)

save_as_csv(df_Erkner_wind,"Erkner")

# "Grünheide (Mark)"
    # only small installation -> 1 kW  -> hub_height = 1.8m

df_Grünh_wind_type1 = get_df(change_wpt(
    position=df_ninja.loc["Grünheide (Mark)","centerposition"][0].coords[0],
    capacity=1,
    height=df_ninja_onshore.loc[1, "Nabenhoehe"],
    turbine="Enercon E70 2300")
)

df_Grünh_wind_type2 = get_df(change_wpt(
    position=df_ninja.loc["Grünheide (Mark)","centerposition"][0].coords[0],
    capacity=1,
    height=df_ninja_onshore.loc[1, "Nabenhoehe"],
    turbine="Vestas V90 2000")
)

df_Grünh_wind = df_Grünh_wind_type1.copy()
df_Grünh_wind["electricity"] = df_Grünh_wind_type1["electricity"] * (x/z) + df_Grünh_wind_type2["electricity"] * (y/z)

save_as_csv(df_Grünh_wind,"Grünheide (Mark)")

# "Kiel"
    # 1 wind turbine
        # hub height not available

df_Kiel_wind_type1 = get_df(change_wpt(
    position=df_ninja.loc["Kiel","centerposition"][0].coords[0],
    capacity=1,
    height=df_ninja_onshore.loc[1, "Nabenhoehe"],
    turbine="Enercon E70 2300")
)

df_Kiel_wind_type2 = get_df(change_wpt(
    position=df_ninja.loc["Kiel","centerposition"][0].coords[0],
    capacity=1,
    height=df_ninja_onshore.loc[1, "Nabenhoehe"],
    turbine="Vestas V90 2000")
)

df_Kiel_wind = df_Kiel_wind_type1.copy()
df_Kiel_wind["electricity"] = df_Kiel_wind_type1["electricity"] * (x/z) + df_Kiel_wind_type2["electricity"] * (y/z)

save_as_csv(df_Kiel_wind,"Kiel")

# "Ingolstadt"
    # no installed wind turbines

df_Ingolstadt_wind_type1 = get_df(change_wpt(
    position=df_ninja.loc["Ingolstadt","centerposition"][0].coords[0],
    capacity=1,
    height=df_ninja_onshore.loc[1, "Nabenhoehe"],
    turbine="Enercon E70 2300")
)

df_Ingolstadt_wind_type2 = get_df(change_wpt(
    position=df_ninja.loc["Ingolstadt","centerposition"][0].coords[0],
    capacity=1,
    height=df_ninja_onshore.loc[1, "Nabenhoehe"],
    turbine="Vestas V90 2000")
)

df_Ingolstadt_wind = df_Ingolstadt_wind_type1.copy()
df_Ingolstadt_wind["electricity"] = df_Ingolstadt_wind_type1["electricity"] * (x/z) + df_Ingolstadt_wind_type2["electricity"] * (y/z)

save_as_csv(df_Ingolstadt_wind,"Ingolstadt")

# Kassel
# df_Kassel
    # there is only one manufacturer with 1 type for turbines
    # there is installed capacity 500 kW withiout identification

df_Kassel_wind = get_df(change_wpt(
    position=df_ninja.loc["Kassel","centerposition"][0].coords[0],
    capacity=1,
    height=df_ninja.loc["Kassel","Nabenhoehe"],
    turbine="Vestas V112 3000")
)
save_as_csv(df_Kassel_wind,"Kassel")

# "Bocholt"
    # 2 manufacturer with 2 turbinetypes
        # Enercon GmbH  -> E82 E1 = Enercon E82 2000 #6
            # but there are typing errors -> look df_Bocholt
        # Enercon GmbH  -> E82 E2 = Enercon E82 2300 #6
        # Nordex SE     -> S-70 -> not available at renewables.ninja
            # alternative -> N60/1300 -> similar performance curve #5

df_Bocholt_wind_type1 = get_df(change_wpt(
    position=df_ninja.loc["Bocholt","centerposition"][0].coords[0],
    capacity=1,
    height=df_ninja.loc["Bocholt","Nabenhoehe"],
    turbine="Enercon E82 2300")
)

df_Bocholt_wind_type2 = get_df(change_wpt(
    position=df_ninja.loc["Bocholt","centerposition"][0].coords[0],
    capacity=1,
    height=df_ninja.loc["Bocholt","Nabenhoehe"],
    turbine="Nordex N60 1300")
)

df_Bocholt_wind = df_Bocholt_wind_type1.copy()
df_Bocholt_wind["electricity"] = df_Bocholt_wind_type1["electricity"] * (6/11) + df_Bocholt_wind_type2["electricity"] * (5/11)

save_as_csv(df_Bocholt_wind,"Bocholt")

# "Zwickau"
    # there are 3 wind turbines in Zwickau
        # 1 small installation      -> 3.3 kW       #1
        # Vestas Deutschland GmbH   -> V150-5.6MW   #2
            # V150-5.6MW -> not available at renewables.ninja
                # alternative -> Vestas V150 4000

df_Zwickau_wind = get_df(change_wpt(
    position=df_ninja.loc["Zwickau","centerposition"][0].coords[0],
    capacity=1,
    height=df_ninja.loc["Zwickau","Nabenhoehe"],
    turbine="Vestas V150 4000")
)

save_as_csv(df_Zwickau_wind,"Zwickau")

# --------------------------------------------------------------------------------------------------------------------->

# --> collect data for pv_feedin_timeseries.csv

for region in regions:
    df = get_df_pv(change_wpt_pv(
    position=df_ninja.loc[region,"centerposition"][0].coords[0],
    capacity=1,
    system_loss=0.1)
    )
    save_as_csv_pv(df, region)

# --------------------------------------------------------------------------------------------------------------------->

# --> collect data for wind_future_feedin_timeseries.csv

for region in regions:
    df = get_df(change_wpt(
    position=df_ninja.loc[region,"centerposition"][0].coords[0],
    capacity=1,
    height=126,
    turbine="Enercon E126 6500")
    )
    save_as_csv_future(df, region)

# --------------------------------------------------------------------------------------------------------------------->

# summarize data to one dataframe

dfs = []
for region in regions:
    dfs.append(pd.read_csv(f"timeseries/wind/capacity_factors_2011_wind_{region}.csv",
                 parse_dates=True, index_col=0))

timeseries_wind = pd.concat(dfs, axis=1)

dfs = []
for region in regions:
    dfs.append(pd.read_csv(f"timeseries/pv/capacity_factors_2011_pv_{region}.csv",
                 parse_dates=True, index_col=0))

timeseries_pv = pd.concat(dfs, axis=1)

dfs = []
for region in regions:
    dfs.append(pd.read_csv(f"timeseries/wind_future/capacity_factors_2011_future_{region}.csv",
                 parse_dates=True, index_col=0))

timeseries_wind_future = pd.concat(dfs, axis=1)

# --------------------------------------------------------------------------------------------------------------------->

full_load_hours_wind = timeseries_wind.sum()

# export data as .csv

timeseries_wind.to_csv("timeseries/wind_feedin_timeseries.csv")
timeseries_pv.to_csv("timeseries/pv_feedin_timeseries.csv")
timeseries_wind_future.to_csv("timeseries/wind_future_feedin_timeseries.csv")