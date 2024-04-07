# EE-Einspeisezeitreihen

Einspeisezeitreihen für Erneuerbare Energien, normiert auf 1 MW bzw. 1 p.u.
Als Wetterjahr wird 2011 verwendet.

Stündlich aufgelöste Zeitreihe der Wind- und Solarenergie über 1 Jahr auf Basis von [renewables.ninja](http://renewables.ninja).
Auflösung auf Gemeindeebene. Für beide Zeitreihen sind geografische Positionen erforderlich.

#### Position

Hierfür wird der Zentroid der Gemeinden, ein räumlicher Mittelwert,
anhand des Geodatensatzes "VG250" bestimmt. Dieser Geodatensatz enthält die Verwaltungsgrenzen der Gemeinden in Deutschland.
[VG250](\\FS01\RL-Institut\04_Projekte\360_Stadt-Land-Energie\03-Projektinhalte\AP2\vg250_01-01.utm32s.gpkg.ebenen\vg250_01-01.utm32s.gpkg.ebenen\vg250_ebenen_0101)
(`DE_VG250.gpkg`):

```
import geopandas as gpd

df = gpd.read_file(gdf)
points_of_muns = df.loc[df.loc[df.GEN == region].index, "geometry"].head(1).centroid.values
points_of_muns_crs = points_of_muns.to_crs(4326)
```

## Windenergie

Für renewables.ninja sind Position (lat, lon), Nennleistung (capacity),
Nabenhöhe und Turbinentyp erforderlich.
Das [MaSTr](https://www.marktstammdatenregister.de/MaStR) liefert den Datensatz [bnetza_mastr_wind_raw.csv](../bnetza_mastr_wind_raw.csv) für Nabenhöhe und Turbinentyp.

#### Nennleistung

Wird auf 1 MW gesetzt/normiert.

#### Nabenhöhe, Turbinentyp

##### Nabenhöhe 

Anhand des Datensatzes [bnetza_mastr_wind_raw.csv](../bnetza_mastr_wind_raw.csv),
wird für die Nabenhöhe ein Mittelwert gebildet. 

```
df = pd.read_csv("bnetza_mastr_wind_raw.csv", sep=",")
df.loc[:,"Nabenhoehe"].mean()
```
##### Turbinentyp

Annahme: Innerhalb eines Herstellers sind Leistungskurven sehr ähnlich.
Daher werden zwei größten Hersteller mit jeweiligen häufigsten Turbinentyp
ausgewählt. Die zwei größten Hersteller sind in diesem Fall Enercon und Vestas.

```
import geopandas as gpd

df = pd.read_csv("bnetza_mastr_wind_raw.csv", sep=",")
manufacturers = df[
    ["manufacturer_name", "status"]
].groupby("manufacturer_name").count().sort_values(
    by="status", ascending=False
)
```
Häufigste Turbinentypen sind "Enercon E70 2300" und "Vestas V90 2000".
Um die Charakteristika der beiden o.g. Anlagentypen zu berücksichtigen, erfolgt
eine gewichtete Summierung der Zeitreihen anhand der berechneten Häufigkeit.

```
man_1 = manufacturers.index[0]
man_2 = manufacturers.index[1]

type_1 = df[
    ["manufacturer_name", "type_name", "status"]
].where(df["manufacturer_name"] == man_1).groupby(
    "type_name").count().sort_values(by="status", ascending=False)

type_2 = df[
    ["manufacturer_name", "type_name", "status"]
].where(df["manufacturer_name"] == man_2).groupby(
    "type_name").count().sort_values(by="status", ascending=False)
```

Die o.g. Prozedur wird in der "main_wind_pv_ror_2.py" durchgeführt. 
Analog zum oben beschriebenen Vorgehen wird zusätzlich eine seperate 
Zuknunftszeitreihe für zukünftige WEA berechnet. 
Hierbei wird eine Enercon E126 6500 mit einer Nabenhöhe von 159 m angenommen.
([PV- und Windflächenrechner](https://zenodo.org/record/6794558))
Da die Zeitreihe sich nur marginal von der obigen Status-quo-Zeitreihe
unterscheidet, wird letztere sowohl für den Status quo als auch die
Zukunftsszenarien verwendet."(s. main_wind_pv_ror.py)".


### Raw Data von [renewables.ninja](http://renewables.ninja) API

Es werden 9 Zeitreihen für die oben beschriebene Vergleichsanlage berechnet:

```
import json
import requests
import pandas as pd
import geopandas as gpd

def change_wpt(position, height, turbine):
    
    function to change input data for wind timeseries from renewables.ninja
    :input:
    :param position: tupel: (lon, lat)
    :param height: dtype: integer/float
    :param turbine: dtype: string
    :return: args


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

    args['height'] = height
    args['lat'] = position[1]
    args['lon'] = position[0]
    args['turbine'] = turbine

    return args

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

regions = ["Rüdersdorf bei Berlin","Strausberg","Erkner","Grünheide (Mark)","Ingolstadt","Kassel","Bocholt","Kiel","Zwickau"]

for region in regions:
    df = get_df(change_wpt(
    position=df_ninja.loc[region, "centerposition"],
    height=159,
    turbine="Enercon E126 6500")
    )
    save_as_csv(df, region)

```

* Einspeisezeitreihe: `wind_feedin_timeseries.csv`

## Freiflächen-Photovoltaik

### PV-Anlage (2022)

Stündlich aufgelöste Zeitreihe der Photovoltaikeinspeisung über 1 Jahr auf Basis
von [MaStR](../bnetza_mastr/dataset.md) und
[renewables.ninja](http://renewables.ninja).
Wie bei der Windeinspeisung wird auf eine Auflsöung auf Gemeindeebene aufgrund
geringer regionaler Abweichungen verzichtet.

Für die Generierung der Zeitreihe über
[renewables.ninja](http://renewables.ninja)
wird eine Position(lat, lon), Nennleistung (capacity), Verluste (system_loss)
Nachführung (tracking), Neigung (tilt) und der Azimutwinkel (azim) benötigt.

Als Position wird analog zur Windenergieanlage der räumlicher Mittelwert
verwendet. Laut MaStR werden lediglich 13 Anlagen nachgeführt (0,01 % der
Kapazität), die Nachführung wird daher vernachlässigt. Die Neigung ist aus MaStR
nicht bekannt, es dominieren jedoch Anlagen auf Freiflächen sowie Flachdächern
im landwirtschaftlichen Kontext. Nach
[Ariadne Szenarienreport](https://ariadneprojekt.de/media/2022/02/Ariadne_Szenarienreport_Oktober2021_corr0222_lowres.pdf)
wird diese mit 30° angenommen.
Die Nennleistung Wird auf 1 MW gesetzt/normiert.

### Zukunftsszenarien

Die Status-quo-Zeitreihe wird sowohl für den Status quo als auch die
Zukunftsszenarien verwendet.

* Einspeisezeitreihe: `pv_feedin_timeseries.csv`

## Solarthermie

* Einspeisezeitreihe: `st_feedin_timeseries.csv` (Kopie von PV-Einspeisezeitreihe)

## Laufwasserkraft

Hier wird eine konstante Einspeisung angenommen.

* Einspeisezeitreihe: `ror_feedin_timeseries.csv`