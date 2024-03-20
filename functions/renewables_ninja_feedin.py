# renewables ninja retrieval
import pandas as pd
import json
import requests

"""
  Abfragenlimits: 50/h!

  please use your own token
  https://www.renewables.ninja/register

  :param args:
  :return: pandas dataframe
  "electricity" in kW
  """

# wind data

# function to change input values for get_df() - function
def change_wpt(position, height, turbine):
    """
    function to change input data for wind timeseries from renewables.ninja
    :input:
    :param position: tupel: (lon, lat)
    :param height: dtype: integer/float
    :param turbine: dtype: string
    :return: args
    """

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

#    args['capacity'] = capacity
    args['height'] = height
    args['lat'] = position[1]
    args['lon'] = position[0]
    args['turbine'] = turbine

    return args

# function to get rawdata from renewables ninja

def get_df(args):
    """
    function to get wind timeseries from renewables.ninja
    :param args:
    :return: timerseries as pandas dataframe
            "electricity" in kW
    """
    token = "087de02f953c486ef9ffe4b9e8093268b0df881c" # please use your own token
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

def change_wpt_pv(position, system_loss):
    """
    function to change input data for pv timeseries from renewables.ninja
    :input:
    :param position: tupel: (lon, lat)
    :param system_loss: dtype: float
    :return: args
    """
    args = {
        'lat': 34.125,
        'lon': 39.814,
        'date_from': '2011-01-01',
        'date_to': '2011-12-31',
        'dataset': 'merra2',
        'capacity': 1000,
        'system_loss': 0.1,
        'tracking': 0,
        'tilt': 30,
        'azim': 180,
        'format': 'json',
        'local_time': 'true',
        'raw': 'false',
    }

#    args['capacity'] = capacity
    args['system_loss'] = system_loss
    args['lat'] = position[1]
    args['lon'] = position[0]

    return args

def get_df_pv(args):
    """
    function to get pv timeseries from renewables.ninja
    :param args:
    :return: timerseries as pandas dataframe
            "electricity" in kW
    """
    token = "087de02f953c486ef9ffe4b9e8093268b0df881c" # please use your own token
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
