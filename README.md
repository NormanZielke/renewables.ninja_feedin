# EE-Einspeisezeitreihen

Einspeisezeitreihen für Erneuerbare Energien, normiert auf 1 MW bzw. 1 p.u.
Als Wetterjahr wird 2011 verwendet.

Stündlich aufgelöste Zeitreihe der Wind- und Solarenergie über 1 Jahr auf Basis von [renewables.ninja](http://renewables.ninja).
Auflösung auf Gemeindeebene. Für beide Zeitreihen sind geografische Positionen erforderlich.

#### Position

Hierfür wird der Zentroid der Gemeinden, ein räumlicher Mittelwert,
anhand des Geodatensatzes "VG250" bestimmt. Dieser Geodatensatz wird vom Bundesamt für Kartographie und Geodäsie bereitgestellt und
enthält die Verwaltungsgrenzen der Gemeinden in Deutschland.
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
Nabenhöhe und Turbinentyp erforderlich. Das Python-Paket Open-mastr stellt den erforderlichen Datensatz aller installierten Windkraftanlagen 
in Deutschland bereit. Open-mastr  bietet eine Schnittstelle zum Herunterladen und Verarbeiten des Markstammdatenregisters [MaSTR].
Das [MaSTR](https://www.marktstammdatenregister.de/MaStR) liefert den Datensatz [bnetza_mastr_wind_raw.csv](../bnetza_mastr_wind_raw.csv) für Nabenhöhe und Turbinentyp.


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
unterscheidet, wird letztere sowohl für den Status quo als auch für die
Zukunftsszenarien verwendet."(s. main_wind_pv_ror.py)".


### Raw Data von [renewables.ninja](http://renewables.ninja) API

Es wird jeweils eine Zeitreihe je Gemeinde für die oben beschriebene Vergleichsanlage berechnet:

```
import json
import requests
import pandas as pd

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

df = get_df(change_wpt(
    position=position,
    height=159,
    turbine="Enercon E126 6500")
    )

```

* Einspeisezeitreihe: `wind_feedin_timeseries.csv`

## Freiflächen-Photovoltaik

### PV-Anlage

Für die Generierung der Zeitreihe über
[renewables.ninja](http://renewables.ninja)
wird eine Position(lat, lon), Nennleistung (capacity), Verluste (system_loss)
Nachführung (tracking), Neigung (tilt) und der Azimutwinkel (azim) benötigt.

```
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

```
Als Position wird analog zur Windenergieanlage der räumlicher Mittelwert
verwendet. Laut MaStR werden lediglich 19 Anlagen nachgeführt (0,01 % aller Anlagen, Stand 08.01.2024), die Nachführung wird daher vernachlässigt. Die Neigung wird nach 
[Ariadne Szenarienreport](https://ariadneprojekt.de/media/2022/02/Ariadne_Szenarienreport_Oktober2021_corr0222_lowres.pdf)
mit 30° angenommen. Für den Azimutwinkel wird eine Südausrichtung, d.h. 0° angenommen. Die Nennleistung Wird auf 1 MW gesetzt/normiert.

### Zukunftsszenarien

Die Status-quo-Zeitreihe wird sowohl für den Status quo als auch die
Zukunftsszenarien verwendet.

* Einspeisezeitreihe: `pv_feedin_timeseries.csv`


## Solarthermie

* Einspeisezeitreihe: `st_feedin_timeseries.csv` (Kopie von PV-Einspeisezeitreihe)

## Laufwasserkraft

Hier wird eine konstante Einspeisung angenommen.

* Einspeisezeitreihe: `ror_feedin_timeseries.csv`

## Agrar-PV

Bifaziale vertikale aufgeständerte PV Anlagen in Kombination mit landwirtschaftlicher Nutzung. <br>

##### Vorgehen
\- analog zum o.g. Vorgehen für PV-Anlagen wird der Input der Renewables ninja API um Azimut und Neigungswinkel = 90° erweitert <br>
\- Für die Zeitreihe einer Gemeinde werden mehrere Zeitreihen erstellt, wobei der Azimut in einem 
Bereich von 0° - 360° mit einer Schrittweite von 10° iteriert wird, und im Anschluss auf eine Zeitreihe gemittelt wird. <br>
\- Ost-West Panele: Azimut : [50° - 130°, 220° - 310°] -> Erträge * 0.95 wegen Bifaszilaität (\[1\] S.2)<br>
\- Süd Panele: Azimut : [0° - 40°, 320° - 360°] -> Bifaszilaität = 1 (\[1\] S.2) <br>
\- Nord Panele: Azimut: [140° - 210°] -> Erträge * 0.9 wegen Bifaszilaität (\[1\] S.2) <br>

#### Quellen
\[1\][Smart Energy](https://pdf.sciencedirectassets.com/778369/1-s2.0-S2666955222X00038/1-s2.0-S2666955222000211/main.pdf?X-Amz-Security-Token=IQoJb3JpZ2luX2VjEGkaCXVzLWVhc3QtMSJGMEQCIFEeRGT6INQhOEb3rhnbL9hryWaJgJzP89Csj4pkXwIWAiAXC8iI4IeMsNsTNJ57m619DO6ua4GcbM0TXi5%2BcxKbviq8BQii%2F%2F%2F%2F%2F%2F%2F%2F%2F%2F8BEAUaDDA1OTAwMzU0Njg2NSIMu9qF92sZRxE5ORF%2BKpAFyyQ354hh8XCE2QoydL1AzB9cs0alMC9ZNEIvOb14n1ASh922RVodhxVRz%2FWjers84PFyU%2BhaZ%2BZwApbstD3HPmaey1PBWmTH2FAWsHMBMs3cQFOSgr3IztaGSi5dmfHpBNLyDRlE1tgoq7U03syo%2BKwXpuf1OgMRzqwS5JsqySufG4zDetbIWuBwNEgPbRYBAhDv%2FRAKqlBx49kZQX9hS2GNfUnJGXDg7T50leh1HCDGOzoYPPhCOy2JgZhAl%2BFKcJZZl9QUzGD6NOJaI2oDMj9ITs3AK2DtZ2zg9mRQfYJpvcokwY95OVE%2Biif5cqRQMa%2FyV0OFadNKzfCP2nlcqqN4QqqEFIdtZ6s05asFOiS06r0nQgNqpYt6e%2BB7lSD6BYDaH6ZDvrEWrzxG2SlQpqGXw9tVcFzMfxMDqw9DNwfjCr7hQdwJ8FN%2BR2N6W1fit%2FoFd9a9FRTwwHQHphG2mfdfMCOHYECvK3Kpy7u%2B47vNo2w1n3sTK%2BcRgOurTPFAz8YR%2BY3Sq83fjHnIpeMWUha6kMGauxaNTLj2pY8XfoyuznZjnksIdcUhRDP8rUItUsoGOY3m%2FGwdfO4kjAM2fkiDbu%2Bcm%2FEikOM4db%2F8dTF8pF7is%2FmjDaPrZbJj1j06kAUSptQuojG2ajFoETiTERavkDhDr1QfCKwNwmS%2BXRRdPH%2Ff%2FdAv%2FdBLR31Ssp9Q4anfAIXwgx38ck8FqlscOdWkRMkDq%2F2y%2Bkm21Ucahanagb64%2F2biVTjaU1cQmpSyzvNv08i6OY%2FoJyNe2syfWDi80OFjdpx1xbW7uFST3xdi%2BCLWoVN5t0xeO7VKm2mtb9zj73Jtewo5VGeJBr0v0zT8eRiR9W%2FKn7s5Gn9VBoUws9jzsAY6sgF%2Bu1qHiK4ClksXjT%2BSZPWH5eH%2FApNkHYbzYteaTFJiSdgvPPgyBcMS2ocrohTVZqVWKi5ijKGYnIXKFrOn1En9ZMRu02MPt5w52Zcr8pPn43aeIYCP2Ep7Ua9%2BGAuXXcKB%2FwX84CfvTyuJU8wyBnGF4XmouQm0W1FamFJgESSpCe6Z5jF8n%2BDOFIdRUdAVtPyhfG2l31ZfIqavQpQYTiFhXZZ5SPlxD%2BPNw%2BYIP2E5q4v%2B&X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Date=20240415T100956Z&X-Amz-SignedHeaders=host&X-Amz-Expires=300&X-Amz-Credential=ASIAQ3PHCVTYYT46DZJF%2F20240415%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Signature=e38b250acebf290e5845a2dac6f00f1b79085fb28ec06d47971b9fad2c3a1abe&hash=4e1be39aae7d9e0b72209e591a50e2a82bb5f7555e671fd1793573a181e633df&host=68042c943591013ac2b2430a89b270f6af2c76d8dfd086a07176afe7c76c2c61&pii=S2666955222000211&tid=spdf-9b17c252-883d-47ea-ade3-83c9adc29e04&sid=f50cf85792e1824f06999d294cff8e235b24gxrqa&type=client&tsoh=d3d3LnNjaWVuY2VkaXJlY3QuY29t&ua=020758515b0c5353560f&rr=874b249a6d8e58de&cc=de)


```
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

df_agrar_pv = bifazial(ags_id)
```

* Einspeisezeitreihe: `agrar_pv_feedin_timeseries.csv`