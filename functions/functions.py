import geopandas as gpd
import pandas as pd
import pickle

def get_position(gdf,region):
    """
    For the Position (lat,lon), calculate centroid as spatial mean value of the municipalities
    Input:
    Geodataframe with geometry of municipalities,
    List with regions of interest
    Output:
    List with Points as GeometryArray
    """
    df = gpd.read_file(gdf)
    points_of_muns = df.loc[df.loc[df.GEN == region].index, "geometry"].head(1).centroid.values
    points_of_muns_crs = points_of_muns.to_crs(4326)

    return points_of_muns_crs

def save_as_csv(df, region):
    """
    :param df: pandas Dataframe
    :param region: dtype: string
    :return: .csv
    """
    # import dictionary for ags_id's
    with open("gemeindeschluessel.pkl", "rb") as datei:
        gemeindeschluessel = pickle.load(datei)

    df.rename(columns={"electricity": gemeindeschluessel[region]}, inplace=True)
    filename = f"timeseries_wind_{region}.csv"
    df.to_csv(f"timeseries/wind/{filename}", index=False)

def save_as_csv_pv(df, region):
    """
    :param df: pandas Dataframe
    :param region: dtype: string
    :return: .csv
    """
    # import dictionary for ags_id's
    with open("gemeindeschluessel.pkl", "rb") as datei:
        gemeindeschluessel = pickle.load(datei)

    df.rename(columns={"electricity": gemeindeschluessel[region]}, inplace=True)
    filename = f"timeseries_pv_{region}.csv"
    df.to_csv(f"timeseries/pv/{filename}", index=False)
