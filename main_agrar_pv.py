import json
import requests
import pandas as pd
import time

"""
Create argar_pv timeseries for the regions in Brandenburg and five cities, which are
considered in SLE-Project
"""

# get dict "gemeindeschluessel"
import pickle

with open("gemeindeschluessel.pkl", "rb") as datei:
    gemeindeschluessel = pickle.load(datei)

# read in calculated centerpositions
df_positions = pd.read_csv("center_positions.csv",
                           index_col=0, sep=";", dtype={"ags_id": str})

df_positions.insert(0, "region", gemeindeschluessel.keys())

# in SLE-Project, for regions in Brandenburg, choose one timeseries because they differ only marginally
# cut out this line of code, if you choose your own regions and summary of regions is not necessary
df_positions = pd.concat([df_positions.iloc[[0]], df_positions.iloc[-5:]])

ags_id_list = df_positions.index
regions = df_positions.loc[:, "region"].values
#ags_id_list = df_positions.index[:2]
#regions = df_positions.loc[:, "region"].values[:2]


def get_pv_data(args):
    """
    Abfragenlimits: 50/h!

    bitte mein Token austauschen
    https://www.renewables.ninja/register

    :param args:
    :return: pandas dataframe
    "electricity" in kW
    """
    token = '087de02f953c486ef9ffe4b9e8093268b0df881c'
    api_base = 'https://www.renewables.ninja/api/'

    s = requests.session()
    # Send token header with each request
    s.headers = {'Authorization': 'Token ' + token}

    url = api_base + 'data/pv'

    r = s.get(url, params=args)

    # Parse JSON to get a pandas.DataFrame of data and dict of metadata
    parsed_response = json.loads(r.text)

    data = pd.read_json(json.dumps(parsed_response['data']), orient='index')
    metadata = parsed_response['metadata']

    return data

def change_anlage(position, system_loss, tilt, azim):
    args = {
        'lat': 52.34714000,  #Frankfurt Oder
        'lon': 14.55062000,  #Frankfurt Oder
        'date_from': '2011-01-01',
        'date_to': '2011-12-31',
        'dataset': 'merra2',
        'capacity': 1000.0, # ist 1 MW
        'system_loss': 0.1,
        'tracking': 0,
        'tilt': 30,
        'azim': 180,
        'format': 'json',
        'local_time': 'true',
        'raw': 'false'
    }

    args['lat'] = position[1]
    args['lon'] = position[0]
    args['system_loss'] = system_loss
    args['tilt'] = tilt
    args['azim'] = azim

    return args

def bifazial(ags_id):
    """
    creates a feed-in time series for bifascial vertical Agri-PV for 1MW in Frankfurt (Oder) via renewables.ninja
    "electricity" output per hour in kW
    limit of requests: 50/h!
    this function generate 36 requests!
    """
    # getting data from renewables.ninja
    pv_df = get_pv_data(change_anlage(
        position=df_positions.loc[ags_id,"centerposition"].strip("()").split(", "),
        system_loss=0.1,
        tilt=90,
        azim=0))
    bifaszialitaet = 1
    pv_df["electricity"] *= 1/36 * bifaszialitaet


    for i in range(1,36):
        time.sleep(1)
        if 0 < i < 5 or 31 < i < 36: #südausrichtung, also bifaszialität 1
            bifaszialitaet = 1
        elif 4 < i < 14 or 21 < i < 32: # west- und ostausrichtung, also bifaszialität 0,95
            bifaszialitaet = 0.95
        elif 13 < i < 22:  # nordausrichtung, also bifaszialität 0,9
            bifaszialitaet = 0.9

        pv_df_container = get_pv_data(change_anlage(position=df_positions.loc[ags_id,"centerposition"].strip("()").split(", "),
                                                    system_loss=0.1,
                                                    tilt=90,
                                                    azim=10 * i))
        pv_df_container["electricity"] *= (1 / 36 * bifaszialitaet)
        pv_df["electricity"] += pv_df_container["electricity"]

    return pv_df

def save_as_csv_agrar_pv(df, region):
    df.rename(columns={"electricity": gemeindeschluessel[region]}, inplace=True)
    filename = f"timeseries_agrar_pv_{region}.csv"
    df.to_csv(f"timeseries/agrar_pv/{filename}", index=False)

#df_agrar_pv = bifazial(ags_id_list[0])

# --------------------------------------------------------------------------------------------------------------------->

"""
request agrar_pv timeseries for all regions
    - 36 requests per region
    - 1h brake per agrar_pv timeseries because of request limit
"""

for region, ags_id in zip(regions, ags_id_list):
    df_agrar_pv = bifazial(ags_id)
    save_as_csv_agrar_pv(df_agrar_pv, region)
    time.sleep(3600)


# --------------------------------------------------------------------------------------------------------------------->
# Summarize data to one dataframe

dfs = []
for region in regions:
    dfs.append(pd.read_csv(f"timeseries/agrar_pv/timeseries_agrar_pv_{region}.csv",
                 parse_dates=True, index_col=0))

timeseries_agrar_pv = pd.concat(dfs, axis=1)

# --------------------------------------------------------------------------------------------------------------------->
# Calculate normed timeseries for agrar_pv

# full load  hours
full_load_agrar_pv = timeseries_agrar_pv.sum()/1000

# standardize timeseries
timeseries_agrar_pv_normed = timeseries_agrar_pv/timeseries_agrar_pv.sum()

# --------------------------------------------------------------------------------------------------------------------->
# Export data as .csv

timeseries_agrar_pv_normed.to_csv("timeseries/agrar_pv_feedin_timeseries.csv")
