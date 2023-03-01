"""
Functions for scraping BGT data used in Shayla Jansen's Spacial Gemeente Stuffs Intro Demo
The code is most likely taken from https://github.com/Amsterdam-AI-Team
"""
import requests
import pandas as pd
import geopandas as gpd

DATA_CRS = 'epsg:28992'

BGT_use_columns = ['geometry', 'identificatie_lokaalid', 'naam']
BGT_namedict = {'BGT': 'bgt_functie', 'BGTPLUS': 'plus_type'}
WFS_URL = 'https://map.data.amsterdam.nl/maps/bgtobjecten?'

def get_bgt_data_for_bbox(bbox, layers):
    """Scrape BGT data in a given bounding box."""
    gdf = gpd.GeoDataFrame(columns=BGT_use_columns,
                           geometry='geometry', crs=DATA_CRS)
    gdf.index.name = 'ogc_fid'

    content = []
    for layer in layers:
        # Scrape data from the Amsterdam WFS, this will return a json response.
        json_content = scrape_amsterdam_bgt(layer, bbox=bbox)
        layer_type = BGT_namedict[layer.split('_')[0]]

        # Parse the downloaded json response.
        if json_content is not None and len(json_content['features']) > 0:
            gdf = gpd.GeoDataFrame.from_features(
                                json_content, crs=DATA_CRS).set_index('ogc_fid')
            gdf = gdf[gdf['bgt_status'] == 'bestaand']
            try:
                gdf['naam'] = gdf[layer_type]
            except Exception:
                gdf['naam'] = layer
            content.append(gdf[BGT_use_columns])

    if len(content) > 0:
        gdf = pd.concat(content)
    return gdf


def scrape_amsterdam_bgt(layer_name, bbox=None):
    """
    Scrape BGT layer information from the WFS.
    Parameters
    ----------
    layer_name : str
        Information about the different layers can be found at:
        https://www.amsterdam.nl/stelselpedia/bgt-index/producten-bgt/prodspec-bgt-dgn-imgeo/
    Returns
    -------
    The WFS response in JSON format or a dict.
    """
    params = 'REQUEST=GetFeature&' \
             'SERVICE=wfs&' \
             'VERSION=2.0.0&' \
             'TYPENAME=' \
             + layer_name + '&'

    if bbox is not None:
        bbox_string = str(bbox[0][0]) + ',' + str(bbox[0][1]) + ',' \
                      + str(bbox[1][0]) + ',' + str(bbox[1][1])
        params = params + 'BBOX=' + bbox_string + '&'

    params = params + 'OUTPUTFORMAT=geojson'

    response = requests.get(WFS_URL + params)
    try:
        return response.json()
    except ValueError:
        return None
