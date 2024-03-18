import json
import requests
import pandas as pd
import time



def get_pv_data(args):
    """
    Abfragenlimits: 6/minute und 50/h!

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

def change_anlage(lat=52.34714000, lon=14.55062000, capacity=1000.0, system_loss=0.1, tilt=30, azim=180):
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

    args["lat"] = lat
    args["lon"] = lon
    args['capacity'] = capacity
    args['system_loss'] = system_loss
    args['tilt'] = tilt
    args['azim'] = azim

    return args


def bifazial():
    """
    erstellt eine Einspeisezeitreihe für bifasziale vertikale Agri-PV für 1MW in Frankfurt (Oder) über renewables.ninja
    "electricity" output pro Stunde in kW

    NUR 50/36 =  1,4 ANFRAGEN PRO STUNDE
    """
    # getting data from renewables.ninja
    pv_df = get_pv_data(change_anlage(tilt=90, azim=0))
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

        pv_df_container = get_pv_data(change_anlage(tilt=90, azim=10 * i))
        pv_df_container["electricity"] *= (1 / 36 * bifaszialitaet)
        pv_df["electricity"] += pv_df_container["electricity"]


    return pv_df