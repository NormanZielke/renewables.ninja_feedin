import geopandas as gpd




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